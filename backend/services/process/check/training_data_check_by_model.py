# --- 适合沐曦GPGPU的运行代码 ---
import sys
import types

from backend.services.process.check.major_vector_lookup import MajorVectorLookup

# 1. 创建模块对象
fake_torchcodec = types.ModuleType('torchcodec')

# 2. 关键修复：补全 __spec__ 属性，欺骗 importlib
# 这行代码解决了 "ValueError: torchcodec.__spec__ is None" 的问题
fake_torchcodec.__spec__ = "mocked_spec"

# 3. 创建子模块 decoders
fake_decoders = types.ModuleType('torchcodec.decoders')
fake_decoders.AudioDecoder = None
fake_decoders.VideoDecoder = None

# 4. 组装模块结构
fake_torchcodec.decoders = fake_decoders

# 5. 注入到系统环境
sys.modules['torchcodec'] = fake_torchcodec
sys.modules['torchcodec.decoders'] = fake_decoders

print("✅ 已成功注入带元数据的假 torchcodec 模块，准备导入 SentenceTransformer...")

import numpy as np
import torch
import time
from sentence_transformers import SentenceTransformer
from peft import PeftModel

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from tqdm import tqdm

from backend.services.process.check.training_data_load import CsvRowReader


class BatchSimilarityCalculator:
    """
    单进程批量计算 CSV 中专业与岗位描述的相似度，并统计分布。
    使用预加载的专业向量，避免重复编码专业文本。
    """

    def __init__(
            self,
            base_model_path: Path,
            csv_path: Path,
            major_vectors_csv: Path,
            lora_path: Optional[Path] = None,
            batch_size: int = 32,  # 新增：编码时的批次大小
    ):
        """
        :param base_model_path: 基座模型路径
        :param csv_path: 输入 CSV 路径（表头: major_name, cleaned_requirements）
        :param major_vectors_csv: 专业向量 CSV 路径（由 MajorEmbedder 生成）
        :param lora_path: 可选，LoRA 适配器路径
        :param batch_size: 批量编码的批次大小（控制内存和速度）
        """
        self.base_model_path = base_model_path
        self.lora_path = lora_path
        self.csv_path = csv_path
        self.batch_size = batch_size

        # 读取所有数据（支持自定义表头）
        reader = CsvRowReader(csv_path, expected_headers=['major_name', 'cleaned_requirements'])
        self.rows = reader.all_rows()
        self.total = len(self.rows)
        logger.info(f"已加载 {self.total} 条记录")

        # 加载专业向量字典
        vector_lookup = MajorVectorLookup(major_vectors_csv)
        self.major_vectors = vector_lookup.get_all_vectors()
        logger.info(f"已加载 {len(self.major_vectors)} 个专业向量")

    def run(self, output_csv: Optional[Path] = None) -> Dict[str, Any]:
        if self.total == 0:
            logger.warning("CSV 文件为空")
            return {"total": 0, "low_count": 0, "high_count": 0, "low_percent": 0.0, "high_percent": 0.0}

        device = "cpu"

        if torch.cuda.is_available():
            device = "cuda"
            # 验证一下是不是 N260 (显存应该接近 64GB)
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
            device_name = torch.cuda.get_device_name(0)

            logger.success(f">>> 识别到加速卡: {device_name}")
            logger.success(f">>> 显存大小: {gpu_memory_gb:.1f} GB")

            if gpu_memory_gb > 60:  # 确认是 64GB 的大卡
                logger.info(">>> 确认为 MetaX N260 (或同级大显存卡)，性能极佳！")
        else:
            logger.warning(">>> 未检测到 CUDA 设备，将使用 CPU")

        logger.info(f"最终使用设备: {device}")

        # 加载模型
        model = SentenceTransformer(str(self.base_model_path), device=device)
        if self.lora_path:
            logger.info(f"注入 LoRA: {self.lora_path}")
            model._modules["0"].auto_model = PeftModel.from_pretrained(
                model._modules["0"].auto_model, str(self.lora_path)
            )
            model.eval()

        # 2. 准备有效数据（专业存在且岗位文本非空）
        valid_indices = []
        job_texts = []
        for idx, row in enumerate(self.rows):
            major_name = row.get("major_name", "")
            job_text = row.get("cleaned_requirements", "")
            if major_name and job_text and major_name in self.major_vectors:
                valid_indices.append(idx)
                job_texts.append(job_text)

        logger.info(f"有效记录数: {len(valid_indices)} / {self.total}")

        # 3. 批量编码所有岗位文本（显示进度条）
        t0 = time.time()
        all_job_vecs = model.encode(
            job_texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=self.batch_size,
            show_progress_bar=True  # sentence_transformers 自带进度条
        )  # shape: (len(job_texts), embedding_dim)
        print(f"编码耗时: {time.time() - t0:.2f}秒, 共{len(job_texts)}条")

        # 4. 计算相似度（可以使用进度条，但通常很快）
        t1 = time.time()
        all_scores = [0.0] * self.total
        # 用 tqdm 显示相似度计算进度（可选）
        with tqdm(total=len(valid_indices), desc="计算相似度", unit="条", colour="magenta") as pbar:
            for i, idx in enumerate(valid_indices):
                major_name = self.rows[idx]["major_name"]
                major_vec = self.major_vectors[major_name]
                job_vec = all_job_vecs[i]
                score = np.dot(major_vec, job_vec).item()
                all_scores[idx] = score
                pbar.update(1)
        print(f"相似度计算耗时: {time.time() - t1:.2f}秒")

        # 5. 统计结果
        low_count = sum(1 for s in all_scores if s < 0.3)
        high_count = self.total - low_count
        low_percent = (low_count / self.total) * 100
        high_percent = (high_count / self.total) * 100

        stats = {
            "total": self.total,
            "low_count": low_count,
            "high_count": high_count,
            "low_percent": round(low_percent, 2),
            "high_percent": round(high_percent, 2),
        }

        logger.success(
            f"统计完成: 低分(<0.3) {low_count} 条 ({low_percent:.2f}%), "
            f"高分(≥0.3) {high_count} 条 ({high_percent:.2f}%)"
        )

        if output_csv:
            self._save_results(output_csv, all_scores)

        return stats

    def _save_results(self, output_path: Path, scores: List[float]):
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['major_name', 'cleaned_requirements', 'similarity'])
            for row, score in zip(self.rows, scores):
                writer.writerow([row['major_name'], row['cleaned_requirements'], score])
        logger.info(f"结果已保存至: {output_path}")