# 云算力使用版本

from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer, util
from peft import PeftModel
from typing import List, Tuple, Union, Optional
from loguru import logger


class SingleModelMatcher:
    """
    加载一个特定模型（支持 LoRA），对输入文本对计算匹配分数（余弦相似度）。
    直接传入模型路径，无需注册表。
    """

    def __init__(
        self,
        base_model_path: Union[str, Path],
        lora_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ):
        """
        :param base_model_path: 基座模型的本地路径（绝对路径或相对路径）
        :param lora_path: 可选，LoRA 适配器的本地路径
        :param device: 运行设备，若为 None 则自动检测 ("cuda" 或 "cpu")
        """
        self.base_model_path = Path(base_model_path)
        self.lora_path = Path(lora_path) if lora_path else None
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"设备: {self.device}")
        self.model = self._load_model()

    def _load_model(self) -> SentenceTransformer:
        """加载基座模型和 LoRA（如果提供）"""
        if not self.base_model_path.exists():
            raise FileNotFoundError(f"基座模型路径不存在: {self.base_model_path}")

        logger.info(f"加载基座模型: {self.base_model_path}")
        model = SentenceTransformer(str(self.base_model_path), device=self.device)

        if self.lora_path:
            if not self.lora_path.exists():
                raise FileNotFoundError(f"LoRA 适配器路径不存在: {self.lora_path}")
            logger.info(f"注入 LoRA: {self.lora_path}")
            try:
                # 假设模型结构为标准 SentenceTransformer，LoRA 加在 transformer 模块上
                model._modules["0"].auto_model = PeftModel.from_pretrained(
                    model._modules["0"].auto_model,
                    str(self.lora_path)
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