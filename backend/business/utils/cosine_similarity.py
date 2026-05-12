import numpy as np
from typing import List, Tuple

class CosineSimilarity:
    """余弦相似度计算工具（纯向量运算，无状态）"""

    @staticmethod
    def compute_similarities(
        query_vector: np.ndarray,
        candidate_vectors: np.ndarray
    ) -> np.ndarray:
        """
        计算 query_vector 与候选矩阵中每一行的余弦相似度
        :param query_vector: shape (D,)
        :param candidate_vectors: shape (N, D)
        :return: shape (N,) 相似度数组
        """
        # 归一化
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-12)
        candidate_norms = candidate_vectors / (np.linalg.norm(candidate_vectors, axis=1, keepdims=True) + 1e-12)
        similarities = np.dot(candidate_norms, query_norm)
        return similarities

    @staticmethod
    def sort_matches(
        similarities: np.ndarray,
        indices: List[int],
        top_k: int = None
    ) -> List[Tuple[int, float]]:
        """
        按相似度降序排序，返回 (index, similarity) 列表
        :param similarities: 相似度数组
        :param indices: 对应的原始索引列表
        :param top_k: 返回前 K 个结果，None 表示全部
        """
        sorted_idx = np.argsort(similarities)[::-1]
        results = [(indices[i], float(similarities[i])) for i in sorted_idx]
        if top_k:
            results = results[:top_k]
        return results