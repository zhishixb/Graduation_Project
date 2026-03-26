from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer, util
from peft import PeftModel
from tqdm import tqdm
from typing import List, Dict, Any, Callable, Optional, Tuple
from loguru import logger
import json

# 假设这是你的注册表文件路径
from backend.services.instruct.compare.models_compare.MODEL_REGISTRY import MODEL_REGISTRY
from backend.services.instruct.compare.models_compare.job_major_data_exactor import JobMajorDataExactor


class ModelMatcher:
    """
    通用双模型对比匹配器。
    支持加载注册表中的任意两个模型进行并行对比。
    自动处理 project_root 与相对路径的拼接。
    """

    def __init__(
            self,
            model_key_a: str,
            model_key_b: str,
    ):
        """
        :param model_key_a: 第一个模型的逻辑名称
        :param model_key_b: 第二个模型的逻辑名称
        """
        self.registry = MODEL_REGISTRY
        self.model_key_a = model_key_a
        self.model_key_b = model_key_b

        self.project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.db_path = self.project_root / "data" / "db" / "jobs.db"
        self.csv_path = self.project_root / "data" / "csv" / "major_data.csv"

        self.data_exactor = JobMajorDataExactor(db_path=self.db_path, csv_path=self.csv_path)

        logger.info(f"项目根目录识别为: {self.project_root}")

        # 验证模型是否存在
        for key in [model_key_a, model_key_b]:
            if key not in self.registry:
                available = list(self.registry.keys())
                raise ValueError(f"❌ 模型 '{key}' 未在注册表中找到。可用: {available}")

        # 自动检测设备
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"初始化双模型对比任务")

        # 分别加载两个模型
        logger.info(f"\n--- 模型 A: [{model_key_a}] ---")
        self.model_a, self.config_a = self._load_single_model(model_key_a)

        logger.info(f"\n--- 模型 B: [{model_key_b}] ---")
        self.model_b, self.config_b = self._load_single_model(model_key_b)

    def _resolve_path(self, relative_path_str: str) -> Path:
        """
        内部辅助方法：将相对路径字符串转换为基于 project_root 的绝对 Path 对象。
        如果输入已经是绝对路径，则直接返回。
        """
        if not relative_path_str:
            return None

        p = Path(relative_path_str)

        # 否则拼接 project_root
        absolute_path = (self.project_root / p).resolve()
        return absolute_path

    def _load_single_model(self, model_key: str) -> Tuple[SentenceTransformer, Dict]:
        """
        内部方法：根据 key 加载单个模型实例
        返回: (模型实例, 配置字典（包含解析后的绝对路径）)
        """
        config = self.registry[model_key]

        # 获取原始相对路径
        base_path_str = config.get("base")
        lora_path_str = config.get("lora")

        # 2. 【核心修改】拼接路径
        base_path = self._resolve_path(base_path_str)
        lora_path = self._resolve_path(lora_path_str) if lora_path_str else None

        # 路径检查
        if not base_path or not base_path.exists():
            logger.error(f"❌ 基座模型路径不存在: {base_path}")
            logger.error(f"   尝试拼接: {self.project_root} + {base_path_str}")
            raise FileNotFoundError(f"基座模型路径不存在: {base_path}")

        logger.info(f"加载基座: {base_path}...")
        model = SentenceTransformer(str(base_path), device=self.device)

        # 如果有 LoRA，注入权重
        if lora_path:
            if not lora_path.exists():
                logger.error(f"❌ LoRA 适配器路径不存在: {lora_path}")
                logger.error(f"   尝试拼接: {self.project_root} + {lora_path_str}")
                raise FileNotFoundError(f"LoRA 适配器路径不存在: {lora_path}")

            logger.info(f"🔧 注入 LoRA: {lora_path}...")
            try:
                # 注意：这里假设模型结构一致，通常 '0' 是 encoder
                model._modules["0"].auto_model = PeftModel.from_pretrained(
                    model._modules["0"].auto_model,
                    str(lora_path)  # PeftModel.from_pretrained 通常接受字符串或 Path
                )
                model.eval()
                logger.info("✅ LoRA 注入成功")
            except Exception as e:
                logger.error(f"❌ LoRA 注入失败: {e}")
                raise e
        else:
            logger.info("ℹ️ 无 LoRA 适配器，使用纯基座模型")

        # 更新 config 字典，存入解析后的绝对路径字符串，方便后续记录日志或保存
        result_config = config.copy()
        result_config['resolved_base'] = str(base_path)
        if lora_path:
            result_config['resolved_lora'] = str(lora_path)

        return model, result_config

    def calculate_match_scores(
            self,
            major: str,
            jobs: List[str]  # 输入依然是岗位名称列表
    ) -> Dict[str, Dict[str, float]]:
        """
        计算单个专业数据与多个岗位列表的匹配度。
        【修改版】内部直接处理数据提取，不再依赖 text_fetcher。
        假设 get_cleaned_requirements_by_functions 返回的是【清洗后的岗位描述文本列表】。
        """
        final_results = {
            self.model_key_a: {},
            self.model_key_b: {}
        }

        pairs_data = []

        # --- 1. 数据获取阶段 ---

        try:
            job_texts = self.data_exactor.get_cleaned_requirements_by_functions(jobs)
            print(job_texts)
        except Exception as e:
            logger.error(f"❌ 岗位数据清洗/提取失败: {e}")
            return final_results

        # 安全检查：确保名称列表和文本列表长度一致
        if len(jobs) != len(job_texts):
            logger.error(f"❌ 岗位名称数量 ({len(jobs)}) 与提取的数据条目数量 ({len(job_texts)}) 不匹配!")
            return final_results

        # B. 获取专业详情数据
        try:
            major_data = self.data_exactor.get_major_detail(major)
        except Exception as e:
            logger.error(f"❌ 获取专业 '{major}' 详情失败: {e}")
            return final_results

        if not major_data:
            logger.error(f"❌ 专业 '{major}' 数据为空")
            return final_results

        # 遍历名称和文本 (使用 zip 确保对齐)
        for job_name, item in zip(jobs, job_texts):
            try:
                # ✅ 关键修改：判断 item 是字典还是字符串，并提取文本
                if isinstance(item, dict):
                    # 从字典中获取 'requirement' 字段，如果没有则默认为空字符串
                    job_text = item.get('requirement', '')
                    # 可选：如果字典里的 function 名和传入的 job_name 不一致，也可以在这里校验或覆盖
                    # actual_func_name = item.get('function', job_name)
                elif isinstance(item, str):
                    # 兼容旧逻辑：如果直接返回的是字符串
                    job_text = item
                else:
                    logger.warning(f"⚠️ 岗位 '{job_name}' 返回了未知类型的数据: {type(item)}")
                    continue

                if not job_text or not job_text.strip():
                    logger.debug(f"⚠️ 岗位 '{job_name}' 的提取文本为空，跳过")
                    continue

                # 构建数据对
                pairs_data.append({
                    "job_name": job_name,
                    "major_text": major_data,
                    "job_text": job_text.strip()
                })
            except Exception as e:
                logger.warning(f"⚠️ 处理 '{job_name}' 时出错: {e}", exc_info=True)
                continue

        if not pairs_data:
            logger.error("❌ 没有有效的数据对可计算。")
            return final_results

        # --- 3. 批量编码 (保持不变) ---
        all_major_texts = [p["major_text"] for p in pairs_data]
        all_job_texts = [p["job_text"] for p in pairs_data]

        logger.info(f"⚡ 模型 A ({self.model_key_a}) 生成嵌入...")
        emb_a_major = self.model_a.encode(all_major_texts, normalize_embeddings=True, convert_to_tensor=True,
                                          show_progress_bar=False)
        emb_a_job = self.model_a.encode(all_job_texts, normalize_embeddings=True, convert_to_tensor=True,
                                        show_progress_bar=False)

        logger.info(f"⚡ 模型 B ({self.model_key_b}) 生成嵌入...")
        emb_b_major = self.model_b.encode(all_major_texts, normalize_embeddings=True, convert_to_tensor=True,
                                          show_progress_bar=False)
        emb_b_job = self.model_b.encode(all_job_texts, normalize_embeddings=True, convert_to_tensor=True,
                                        show_progress_bar=False)

        # --- 4. 计算相似度 (保持不变) ---
        logger.info("🔢 计算相似度...")
        for i, data in enumerate(tqdm(pairs_data, desc="Matching")):
            job_name = data["job_name"]

            score_a = util.cos_sim(emb_a_major[i], emb_a_job[i]).item()
            final_results[self.model_key_a][job_name] = round(score_a, 6)

            score_b = util.cos_sim(emb_b_major[i], emb_b_job[i]).item()
            final_results[self.model_key_b][job_name] = round(score_b, 6)

        logger.info(f"✅ 完成 {len(pairs_data)} 个岗位匹配。")
        return final_results


class ModelRegistryManager:
    def get_available_models(self) -> list:
        """轻量级获取模型列表，无任何依赖"""
        return list(MODEL_REGISTRY.keys())

    def get_model_config(model_key: str) -> dict:
        """获取单个模型配置"""
        if model_key not in MODEL_REGISTRY:
            raise ValueError(f"Model {model_key} not found")
        return MODEL_REGISTRY[model_key]