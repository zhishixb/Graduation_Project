import torch
import numpy as np
import shutil
import atexit
import tempfile
from pathlib import Path
from typing import Optional, Set, Dict, List, Tuple, Any
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
from FlagEmbedding import BGEM3FlagModel
import json

# ========== 停用词集合 ==========
STOP_TOKENS: Set[str] = {
    '，', '。', '；', '：', '“', '”', '‘', '’', '！', '？', '、', '…', '—', '～',
    '《', '》', '（', '）', '【', '】', '〈', '〉', '．', '·',
    '.', ',', ';', ':', '!', '?', '-', '(', ')', '[', ']', '{', '}', '/', '\\',
    '的', '了', '在', '是', '与', '和', '及', '或', '而', '但', '且', '向', '对', '为', '以', '等',
    '之', '所', '把', '被', '从', '就', '到', '说', '也', '又', '不', '没', '很', '都', '还', '更',
    '能', '要', '会', '着', '过', '这', '那', '其', '中', '上', '下', '前', '后', '里', '外',
    '应', '可', '将', '让', '于', '比', '除', '因为', '所以', '如果', '虽然',
    '什么', '怎么', '哪', '呢', '吗', '啊', '哦', '嗯', '吧', '嘛', '若', '则', '主要',

    # 常见功能性词汇
    '需', '需要', '需求', '系统', '路', '制定', '工作', '方案', '写', '学', '年', '描述',
    '难', '至少', '使用', '过程', '交付', '能够', '熟悉', '有', '主要', '脚', '本', '斗',
    '各', '参与', '定期', '概', '民', '的基本', '样', '抽', '代', '样', '大', '升级', '旧',
    '问题', '后续', '并', '满足',

    # 其他字符
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
}


def filter_stopwords(weights_dict: dict) -> dict:
    """移除停用词及空白 token"""
    return {t: w for t, w in weights_dict.items() if t not in STOP_TOKENS and t.strip()}


class BGE_M3_Explainer:
    """BGE‑M3 模型解释器（用于 API 服务，返回结构化数据）"""

    def __init__(self, model_path: Path, lora_adapter_path: Optional[Path] = None,
                 device: Optional[str] = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Device: {self.device}")

        # 根据设备选择加载参数，修复 CPU 下 device_map='auto' 导致的权重卸载错误
        if self.device == 'cpu':
            base = AutoModel.from_pretrained(
                str(model_path),
                trust_remote_code=True,
                dtype=torch.float32,
                device_map=None   # CPU 下不启用自动设备分配
            )
        else:
            # GPU 环境使用 float16，自动设备映射，并提供 offload_folder 以防权重需要卸载
            base = AutoModel.from_pretrained(
                str(model_path),
                trust_remote_code=True,
                dtype=torch.float16,
                device_map='auto',
                offload_folder='offload'   # 任意可写目录，会自动创建
            )

        if lora_adapter_path is not None:
            print(f"LoRA: {lora_adapter_path}")
            model = PeftModel.from_pretrained(base, str(lora_adapter_path)).merge_and_unload()
        else:
            model = base

        self._tmp_model_dir = tempfile.mkdtemp(prefix="bge_m3_merged_")
        model.save_pretrained(self._tmp_model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
        self.tokenizer.save_pretrained(self._tmp_model_dir)
        self.flag_model = BGEM3FlagModel(self._tmp_model_dir, use_fp16=(self.device == 'cuda'),
                                         device=self.device)
        atexit.register(self._cleanup)
        print("Model ready.\n")

    def _cleanup(self):
        if hasattr(self, '_tmp_model_dir') and Path(self._tmp_model_dir).exists():
            shutil.rmtree(self._tmp_model_dir, ignore_errors=True)

    def _id_to_text_map(self, token_ids: dict) -> dict:
        return {self.tokenizer.decode([int(tid)]): w for tid, w in token_ids.items()}

    def explain_matching(self, text_a: str, text_b: str, top_k: int = 10,
                         filter_heatmap_tokens: bool = True,
                         return_echarts_json: bool = True) -> Dict[str, Any]:
        """
        分析两段文本的匹配原因，返回结构化数据（不生成 HTML）：
            - lexical_contrib: 词法贡献列表 [(token, score), ...]
            - semantic_pairs: 语义对齐对 [(tok_a, tok_b, score), ...]
            - echarts_json: 可选热力图数据（JSON 字符串）
        """
        out = self.flag_model.encode([text_a, text_b], return_dense=False,
                                     return_sparse=True, return_colbert_vecs=True,
                                     batch_size=2, max_length=512)

        # --- 1. 词法权重贡献 ---
        sw_a = filter_stopwords(self._id_to_text_map(out['lexical_weights'][0]))
        sw_b = filter_stopwords(self._id_to_text_map(out['lexical_weights'][1]))

        common = set(sw_a) & set(sw_b)
        contrib_lex = sorted(((t, sw_a[t] * sw_b[t]) for t in common),
                             key=lambda x: x[1], reverse=True)
        lexical_contrib = [(t, round(float(s), 4)) for t, s in contrib_lex[:top_k]]

        # --- 2. ColBERT 语义对齐 ---
        vecs_a = out['colbert_vecs'][0]
        vecs_b = out['colbert_vecs'][1]

        raw_a = [t.replace('▁', '').replace('</s>', '') for t in
                 self.tokenizer.convert_ids_to_tokens(
                     self.tokenizer.encode(text_a, add_special_tokens=False))]
        raw_b = [t.replace('▁', '').replace('</s>', '') for t in
                 self.tokenizer.convert_ids_to_tokens(
                     self.tokenizer.encode(text_b, add_special_tokens=False))]

        if filter_heatmap_tokens:
            keep_a = [i for i, t in enumerate(raw_a) if t not in STOP_TOKENS and t.strip()]
            keep_b = [i for i, t in enumerate(raw_b) if t not in STOP_TOKENS and t.strip()]
            vecs_a = vecs_a[keep_a]
            vecs_b = vecs_b[keep_b]
            tokens_a = [raw_a[i] for i in keep_a]
            tokens_b = [raw_b[i] for i in keep_b]
        else:
            tokens_a, tokens_b = raw_a, raw_b

        # 处理空分词情况
        if len(tokens_a) == 0 or len(tokens_b) == 0:
            return {
                "lexical_contrib": lexical_contrib,
                "semantic_pairs": [],
                "echarts_json": None
            }

        # 归一化并计算余弦相似度
        norm_a = vecs_a / (np.linalg.norm(vecs_a, axis=1, keepdims=True) + 1e-12)
        norm_b = vecs_b / (np.linalg.norm(vecs_b, axis=1, keepdims=True) + 1e-12)
        sim = np.dot(norm_a, norm_b.T)

        # 限制展示长度防止前端数据过密
        max_disp = 40
        if len(tokens_a) > max_disp:
            tokens_a = tokens_a[:max_disp]
            sim = sim[:max_disp, :]
        if len(tokens_b) > max_disp:
            tokens_b = tokens_b[:max_disp]
            sim = sim[:, :max_disp]

        # 双向匹配收集对齐对
        best_b_idx = np.argmax(sim, axis=1)
        best_a_idx = np.argmax(sim, axis=0)
        pairs_dict = {}
        for i in range(sim.shape[0]):
            j = best_b_idx[i]
            pair = (tokens_a[i], tokens_b[j])
            pairs_dict[pair] = max(pairs_dict.get(pair, 0), float(sim[i, j]))
        for j in range(sim.shape[1]):
            i = best_a_idx[j]
            pair = (tokens_a[i], tokens_b[j])
            pairs_dict[pair] = max(pairs_dict.get(pair, 0), float(sim[i, j]))

        sorted_pairs = sorted(pairs_dict.items(), key=lambda x: x[1], reverse=True)
        semantic_pairs = [(a, b, round(s, 4)) for (a, b), s in sorted_pairs[:top_k * 2]]

        # --- 3. ECharts 热力图数据 ---
        echarts_json = None
        if return_echarts_json:
            echarts_data = [[i, j, round(float(sim[i, j]), 4)]
                            for i in range(sim.shape[0])
                            for j in range(sim.shape[1])]
            echarts_json = json.dumps({
                "tokens_a": tokens_a,
                "tokens_b": tokens_b,
                "echarts_data": echarts_data
            }, ensure_ascii=False)

        return {
            "lexical_contrib": lexical_contrib,
            "semantic_pairs": semantic_pairs,
            "echarts_json": echarts_json
        }

    def get_colbert_score(self, text_a: str, text_b: str) -> float:
        """
        计算两段文本的 ColBERT 语义匹配分数（归一化 MaxSim）
        分数落在 [-1, 1]，越高表示越匹配。
        """
        out = self.flag_model.encode(
            [text_a, text_b],
            return_dense=False,
            return_sparse=False,
            return_colbert_vecs=True,
            batch_size=2,
            max_length=512
        )
        vecs_a = out['colbert_vecs'][0]  # [L1, D]
        vecs_b = out['colbert_vecs'][1]  # [L2, D]

        L1 = vecs_a.shape[0]
        if L1 == 0:  # 空文本保护
            return 0.0

        # L2 归一化
        norm_a = vecs_a / (np.linalg.norm(vecs_a, axis=1, keepdims=True) + 1e-12)
        norm_b = vecs_b / (np.linalg.norm(vecs_b, axis=1, keepdims=True) + 1e-12)

        # 计算每个 text_a token 与 text_b 中最佳匹配的相似度，求和后归一化
        sim = np.dot(norm_a, norm_b.T)  # [L1, L2]
        max_sim_per_token = np.max(sim, axis=1)
        score = np.sum(max_sim_per_token) / L1  # 归一化

        return round(float(score), 6)

    def score_jobs(self, profile: str, jobs: List[str],
                   top_k: Optional[int] = None,
                   normalize: bool = True) -> List[Tuple[str, float]]:
        """
        对多个岗位文本计算匹配分数，返回排序后的 (岗位, 分数) 列表。
        Args:
            normalize: 是否用专业描述 token 数进行长度归一化（推荐 True）
            top_k: 只返回前 top_k 个岗位，None 则全部返回
        """
        if not jobs:
            return []

        # 将所有文本一次编码：专业描述 + 所有岗位
        all_texts = [profile] + jobs
        out = self.flag_model.encode(
            all_texts,
            return_dense=False,
            return_sparse=False,
            return_colbert_vecs=True,
            batch_size=min(len(all_texts), 16),  # 根据显存调整
            max_length=512
        )

        # 专业描述的 ColBERT vectors，形状 [L_pro, D]
        vec_profile = out['colbert_vecs'][0]
        norm_profile = vec_profile / (np.linalg.norm(vec_profile, axis=1, keepdims=True) + 1e-12)
        L_profile = vec_profile.shape[0]

        # 计算每个岗位的归一化 MaxSim 分数
        scores = []
        for idx, vec_job in enumerate(out['colbert_vecs'][1:]):
            if vec_job.shape[0] == 0:  # 空岗位保护
                scores.append(0.0)
                continue

            norm_job = vec_job / (np.linalg.norm(vec_job, axis=1, keepdims=True) + 1e-12)
            sim = np.dot(norm_profile, norm_job.T)  # [L_pro, L_job]
            raw_score = np.sum(np.max(sim, axis=1))

            if normalize and L_profile > 0:
                score = raw_score / L_profile
            else:
                score = raw_score

            scores.append(round(float(score), 6))

        # 组装并排序
        scored_jobs = list(zip(jobs, scores))
        scored_jobs.sort(key=lambda x: x[1], reverse=True)

        if top_k is not None:
            scored_jobs = scored_jobs[:top_k]

        return scored_jobs

    def score_job_aggregated(
            self,
            profile: str,
            descriptions: List[str],
            normalize: bool = True
    ) -> Dict[str, float]:
        """
        计算同一个岗位的多条描述与专业匹配的聚合分数。
        返回 {'max': ..., 'mean': ..., 'median': ...}
        """
        if not descriptions:
            return {'max': 0.0, 'mean': 0.0, 'median': 0.0}

        # 批量计算所有描述的匹配分数，返回 [(desc, score), ...]
        results = self.score_jobs(profile, descriptions, normalize=normalize)
        scores = [s for _, s in results]

        return {
            'max': round(max(scores), 6),
            'mean': round(sum(scores) / len(scores), 6),
            'median': round(float(np.median(scores)), 6)
        }