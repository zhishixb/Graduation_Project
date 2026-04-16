from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer, util
from peft import PeftModel
from typing import List, Tuple, Union
from loguru import logger

from backend.services.instruct.compare.models_compare.MODEL_REGISTRY import MODEL_REGISTRY


class SingleModelMatcher:
    """
    加载一个特定模型（支持 LoRA），对输入文本对计算匹配分数（余弦相似度）。
    """

    def __init__(self, model_key: str):
        """
        :param model_key: 注册表中的模型逻辑名称
        """
        if model_key not in MODEL_REGISTRY:
            available = list(MODEL_REGISTRY.keys())
            raise ValueError(f"❌ 模型 '{model_key}' 未在注册表中找到。可用: {available}")

        self.model_key = model_key
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"项目根目录: {self.project_root}, 设备: {self.device}")

        self.model = self._load_model(model_key)

    def _resolve_path(self, relative_path_str: str) -> Path:
        """将相对路径转换为绝对路径"""
        if not relative_path_str:
            return None
        p = Path(relative_path_str)
        return (self.project_root / p).resolve()

    def _load_model(self, model_key: str) -> SentenceTransformer:
        config = MODEL_REGISTRY[model_key]
        base_path = self._resolve_path(config.get("base"))
        lora_path = self._resolve_path(config.get("lora")) if config.get("lora") else None

        if not base_path or not base_path.exists():
            raise FileNotFoundError(f"基座模型路径不存在: {base_path}")

        logger.info(f"加载基座模型: {base_path}")
        model = SentenceTransformer(str(base_path), device=self.device)

        if lora_path:
            if not lora_path.exists():
                raise FileNotFoundError(f"LoRA 适配器路径不存在: {lora_path}")
            logger.info(f"注入 LoRA: {lora_path}")
            try:
                model._modules["0"].auto_model = PeftModel.from_pretrained(
                    model._modules["0"].auto_model,
                    str(lora_path)
                )
                model.eval()
                logger.info("LoRA 注入成功")
            except Exception as e:
                logger.error(f"LoRA 注入失败: {e}")
                raise
        else:
            logger.info("未使用 LoRA，使用纯基座模型")

        return model

    def predict(self, text1: str, text2: str) -> float:
        """
        计算两个文本的匹配分数（余弦相似度）
        :return: 相似度分数 (0~1)
        """
        emb1 = self.model.encode(text1, normalize_embeddings=True, convert_to_tensor=True)
        emb2 = self.model.encode(text2, normalize_embeddings=True, convert_to_tensor=True)
        score = util.cos_sim(emb1, emb2).item()
        return round(score, 6)

    def predict_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        批量计算多个文本对的匹配分数
        :param pairs: [(text1, text2), ...]
        :return: 分数列表
        """
        texts1 = [p[0] for p in pairs]
        texts2 = [p[1] for p in pairs]

        embs1 = self.model.encode(texts1, normalize_embeddings=True, convert_to_tensor=True)
        embs2 = self.model.encode(texts2, normalize_embeddings=True, convert_to_tensor=True)

        scores = util.cos_sim(embs1, embs2).diag().tolist()
        return [round(s, 6) for s in scores]