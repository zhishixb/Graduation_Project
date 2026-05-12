from typing import List

from backend.business.models.exceptions import NoDataFoundError
from backend.business.models.schemas import FunctionSimilarity, MajorSimilarity, MajorFunctionSimilarity
from backend.business.repository.job_major_repository import JobMajorRepository


class JobMajorService:
    def __init__(self, repo: JobMajorRepository):
        self.repo = repo

    def get_top_functions_for_major(self, major_name: str, limit: int = 15) -> List[FunctionSimilarity]:
        if limit <= 0:
            limit = 15
        raw_data = self.repo.get_top_functions_by_major(major_name, limit)
        if not raw_data:
            raise NoDataFoundError(f"未找到与专业 '{major_name}' 相关的岗位记录")
        return [FunctionSimilarity(**item) for item in raw_data]

    def get_top_majors_for_function(self, function_name: str, limit: int = 15) -> List[MajorSimilarity]:
        if limit <= 0:
            limit = 15
        raw_data = self.repo.get_top_majors_by_function(function_name, limit)
        if not raw_data:
            raise NoDataFoundError(f"未找到与岗位 '{function_name}' 相关的专业记录")
        return [MajorSimilarity(**item) for item in raw_data]

    def get_similarity_between_major_and_function(
            self, major_name: str, function_name: str
    ) -> MajorFunctionSimilarity:
        """
        返回专业与岗位的相似度分数。
        若未找到匹配记录，抛出 NoDataFoundError。
        """
        data = self.repo.get_similarity(major_name, function_name)
        if not data:
            raise NoDataFoundError(
                f"未找到专业 '{major_name}' 与岗位 '{function_name}' 的相似度记录"
            )
        return MajorFunctionSimilarity(**data)

    @staticmethod
    def get_domain_matching_scores(
            major_name: str,
            function_name: str,
            major_data_service: 'MajorDataService',
            skill_extractor: 'SkillExtractor',
            job_data_repo: 'JobDataRepository',
            bge_explainer: 'BGE_M3_Explainer'
    ) -> List[dict]:
        """
        返回专业与岗位共同技能领域及其语义相似度分数，按分数降序排列。
        """
        # 1. 专业介绍文本
        major_intro = major_data_service.get_intro_by_major(major_name)

        # 2. 岗位合并文本
        job_text = job_data_repo.get_merged_text_by_function(function_name)
        if not job_text:
            raise ValueError(f"岗位 {function_name} 没有文本数据")

        # 3. 提取技能词（按分类分组）
        major_grouped = skill_extractor.extract_skills_grouped_by_category(major_intro)
        job_grouped = skill_extractor.extract_skills_grouped_by_category(job_text)

        # 4. 共同技能领域
        common_categories = set(major_grouped.keys()) & set(job_grouped.keys())
        if not common_categories:
            return []

        # 5. 计算每个共同领域的语义匹配分
        results = []
        for cat in common_categories:
            # 将该领域下两边的技能词分别合成字符串
            major_skills_str = ' '.join(major_grouped[cat])
            job_skills_str = ' '.join(job_grouped[cat])
            score = bge_explainer.get_colbert_score(major_skills_str, job_skills_str)
            results.append({"category": cat, "score": round(score, 4)})

        # 6. 按分数降序排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results