from typing import List, Tuple

from backend.business.repository.vector_repository import VectorRepository
from backend.business.utils.cosine_similarity import CosineSimilarity


class VectorMatchService:
    def __init__(self, vector_repo: VectorRepository):
        self._vector_repo = vector_repo
        self._cosine_tool = CosineSimilarity()

    def compute_job_major_matches(
        self,
        major_name: str,
        job_name: str,
        top_k: int = None
    ) -> Tuple[str, str, List[Tuple[int, float]]]:
        """
        计算指定专业与指定岗位下所有职位向量的相似度并排序
        返回: (major_name, job_name, [(index, similarity), ...])
        """
        # 1. 获取专业向量
        major_vec = self._vector_repo.get_major_vector(major_name)
        if major_vec is None:
            raise ValueError(f"专业 {major_name} 不存在")

        # 2. 获取该岗位的所有职位向量矩阵
        job_vectors = self._vector_repo.get_job_vectors(job_name)   # shape (M, D)
        if job_vectors.size == 0:
            raise ValueError(f"岗位 {job_name} 没有对应的职位记录")

        # 3. 计算余弦相似度
        similarities = self._cosine_tool.compute_similarities(major_vec, job_vectors)

        # 4. 获取这些向量对应的原始索引（因为 job_dict 中存储了 indices）
        indices = self._vector_repo.job_dict.get(job_name, [])   # list[int]

        # 5. 排序
        matches = self._cosine_tool.sort_matches(similarities, indices, top_k)

        return major_name, job_name, matches