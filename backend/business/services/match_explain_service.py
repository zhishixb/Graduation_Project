from pathlib import Path
from typing import List, Dict, Any, Optional
import torch

from backend.business.repository.job_data_repository import JobDataRepository
from backend.business.services.major_data_service import MajorDataService
from backend.business.utils.bge_m3_explainer import BGE_M3_Explainer


# ---------- 服务类 ----------
class MatchExplainService:
    _explainer: Optional[BGE_M3_Explainer] = None

    def __init__(self, major_data_service: MajorDataService, job_data_repo: JobDataRepository,
                 model_path: Path, lora_path: Optional[Path] = None):
        """
        :param major_data_service: MajorDataService 实例
        :param job_data_repo: JobDataRepository 实例
        :param model_path: bge-m3 模型路径
        :param lora_path: LoRA 路径 (可选)
        """
        self._major_svc = major_data_service
        self._job_repo = job_data_repo
        # 单例加载模型（类级别）
        if MatchExplainService._explainer is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            MatchExplainService._explainer = BGE_M3_Explainer(
                model_path, lora_path, device
            )

    def explain_for(self, major_name: str, function_name: str,
                    top_k: int = 5, num_samples: int = 5,
                    return_echarts: bool = True) -> List[Dict[str, Any]]:
        """
        返回解释列表，每个元素包含 job_text 和分析结果。
        """
        # 1. 获取专业介绍
        major_intro = self._major_svc.get_intro_by_major(major_name)  # 抛出 MajorNotFoundError

        # 2. 随机抽取岗位文本
        job_texts = self._job_repo.get_random_texts_by_function(function_name, k=num_samples)
        if not job_texts:
            raise ValueError(f"岗位 {function_name} 没有可用的文本数据")

        # 3. 逐条分析
        results = []
        for jt in job_texts:
            try:
                analysis = self._explainer.explain_matching(
                    major_intro, jt,
                    top_k=top_k,
                    return_echarts_json=return_echarts  # 传递开关
                )
            except Exception as e:
                analysis = {"lexical_contrib": [], "semantic_pairs": [], "echarts_json": None}

            item = {
                "job_text": jt,
                "lexical_contrib": analysis.get("lexical_contrib", []),
                "semantic_pairs": analysis.get("semantic_pairs", [])
            }
            if return_echarts:
                item["echarts_json"] = analysis.get("echarts_json")  # 可能为 None
            results.append(item)
        return results

    def get_domain_scores(
            self,
            major_name: str,
            function_name: str,
            skill_extractor: 'SkillExtractor',
            job_data_repo: JobDataRepository
    ) -> List[Dict[str, Any]]:
        """
        返回专业与岗位共同技能领域及其 ColBERT 语义匹配分，按分数降序排序。
        """
        # 1. 获取专业介绍（已通过 _major_svc）
        major_intro = self._major_svc.get_intro_by_major(major_name)

        # 2. 获取岗位合并文本
        job_text = job_data_repo.get_merged_text_by_function(function_name)
        if not job_text:
            raise ValueError(f"岗位 {function_name} 没有文本数据")

        # 3. 提取技能词（按分类分组）
        major_grouped = skill_extractor.extract_skills_grouped_by_category(major_intro)
        job_grouped = skill_extractor.extract_skills_grouped_by_category(job_text)

        # 4. 共同领域
        common_cats = set(major_grouped.keys()) & set(job_grouped.keys())
        if not common_cats:
            return []

        # 5. 逐领域计算分数
        results = []
        for cat in common_cats:
            major_str = ' '.join(major_grouped[cat])
            job_str = ' '.join(job_grouped[cat])
            score = self._explainer.get_colbert_score(major_str, job_str)
            results.append({"category": cat, "score": round(score, 4)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def score_aggregated_match(self, major_name: str, function_name: str) -> dict:
        """
        返回该专业与该岗位所有描述的聚合匹配分数（max/mean/median）。
        """
        # 1. 专业介绍
        major_intro = self._major_svc.get_intro_by_major(major_name)

        # 2. 获取该岗位的所有清洗文本
        all_texts = self._job_repo.get_all_texts_by_function(function_name)
        if not all_texts:
            raise ValueError(f"岗位 {function_name} 没有文本数据")

        # 3. 调用 explainer 的聚合方法
        agg = self._explainer.score_job_aggregated(
            profile=major_intro,
            descriptions=all_texts,
            normalize=True
        )
        return agg