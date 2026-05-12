import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any

class JSONLoader:
    """通用 JSON 文件加载器，支持懒加载和缓存"""
    def __init__(self, file_path: Path, lazy: bool = False):
        self.file_path = Path(file_path)
        self.lazy = lazy
        self._data: Optional[Any] = None

    def _load(self) -> Any:
        if not self.file_path.exists():
            raise FileNotFoundError(f"JSON 文件不存在: {self.file_path}")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @property
    def data(self) -> Any:
        if self._data is None:
            self._data = self._load()
        return self._data

    def reload(self) -> None:
        self._data = self._load()


class VectorRepository:
    """
    统一获取职位向量和专业介绍向量的类。
    全部数据（npy 矩阵 + JSON 元数据）均在初始化时加载到内存。
    """
    def __init__(
        self,
        job_npy_path: Path,
        job_json_path: Path,
        major_npy_path: Path,
        major_json_path: Path
    ):
        """
        :param job_npy_path: job_vectors.npy 文件路径
        :param job_json_path: job_vectors.json 文件路径
        :param major_npy_path: major_vectors.npy 文件路径
        :param major_json_path: major_vectors.json 文件路径
        """
        # 加载向量矩阵（全量内存）
        self.job_embeddings = np.load(job_npy_path)          # shape (N, D)
        self.major_embeddings = np.load(major_npy_path)      # shape (K, D)

        # 加载 JSON 元数据
        job_loader = JSONLoader(job_json_path)
        major_loader = JSONLoader(major_json_path)

        # job_dict: {function_name: [index1, index2, ...]}
        self.job_dict: Dict[str, List[int]] = job_loader.data
        # major_list: [name0, name1, ...] 顺序与 major_embeddings 的行索引一致
        self.major_list: List[str] = major_loader.data

        # 构建专业名称到索引的映射，便于 O(1) 查询
        self.major_name_to_idx: Dict[str, int] = {
            name: idx for idx, name in enumerate(self.major_list)
        }

        # 缓存岗位平均向量，避免重复计算
        self._cached_centroids: Optional[Dict[str, np.ndarray]] = None

    # ==================== 岗位向量相关 ====================
    def get_job_vectors(self, function_name: str) -> np.ndarray:
        """
        根据岗位名称返回该岗位下所有相关记录的向量矩阵。
        :param function_name: 岗位名称（例如 "销售工程师"）
        :return: shape (M, D) 的 numpy 数组，M 为该岗位的记录数，
                 若未找到则返回空数组 shape (0, D)
        """
        indices = self.job_dict.get(function_name, [])
        if not indices:
            return np.empty((0, self.job_embeddings.shape[1]), dtype=np.float32)
        return self.job_embeddings[indices]

    def get_all_function_names(self) -> List[str]:
        """返回所有可用的岗位名称列表"""
        return list(self.job_dict.keys())

    def get_job_count(self, function_name: str) -> int:
        """返回某个岗位的记录数量（不加载向量）"""
        return len(self.job_dict.get(function_name, []))

    def get_function_centroids(self, use_cache: bool = True) -> Dict[str, np.ndarray]:
        """
        计算每个岗位下所有职位向量的平均值（中心向量）。
        :param use_cache: 是否将结果缓存在实例中，避免重复计算
        :return: 字典，键为岗位名称，值为平均向量 (shape: (D,))
        """
        if use_cache and self._cached_centroids is not None:
            return self._cached_centroids

        centroids = {}
        for func, indices in self.job_dict.items():
            if indices:
                vectors = self.job_embeddings[indices]   # (M, D)
                centroid = np.mean(vectors, axis=0)      # (D,)
                centroids[func] = centroid
            else:
                # 没有数据则填充零向量
                centroids[func] = np.zeros(self.job_embeddings.shape[1], dtype=np.float32)

        if use_cache:
            self._cached_centroids = centroids
        return centroids

    # ==================== 专业向量相关 ====================
    def get_major_vector(self, major_name: str) -> Optional[np.ndarray]:
        """
        根据专业名称返回介绍向量。
        :param major_name: 专业名称（例如 "计算机科学与技术"）
        :return: shape (D,) 的向量，若未找到则返回 None
        """
        idx = self.major_name_to_idx.get(major_name)
        if idx is None:
            return None
        return self.major_embeddings[idx]

    def get_all_major_names(self) -> List[str]:
        """返回所有可用的专业名称列表"""
        return self.major_list.copy()

    def get_major_count(self) -> int:
        """返回专业总数"""
        return len(self.major_list)

    # ==================== 批量矩阵获取 ====================
    @property
    def function_vectors_matrix(self) -> np.ndarray:
        """
        返回所有岗位的平均向量矩阵（按 get_all_function_names 顺序）
        注意：每次调用会重新构建，建议预先获取并缓存
        """
        centroids = self.get_function_centroids()
        function_names = self.get_all_function_names()
        return np.array([centroids[name] for name in function_names])

    @property
    def major_vectors_matrix(self) -> np.ndarray:
        """返回专业向量矩阵（已加载）"""
        return self.major_embeddings