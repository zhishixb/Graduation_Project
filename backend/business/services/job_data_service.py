from backend.business.repository.job_data_repository import JobDataRepository
from backend.business.services.job_list_service import JobListService
from backend.business.utils.skill_extractor import SkillExtractor


class JobSkillService:
    def __init__(
        self,
        job_list_service: JobListService,
        skill_service: SkillExtractor,
        csv_repo: JobDataRepository
    ):
        self._job_list = job_list_service
        self._skill = skill_service
        self._csv_repo = csv_repo

    def get_skills_by_uid(self, uid: int) -> dict:
        function_name = self._job_list.get_job_name_by_uid(uid)
        if not function_name:
            return {"error": "未找到对应岗位"}

        text = self._csv_repo.get_merged_text_by_function(function_name)
        if text is None:
            return {"error": f"未找到 {function_name} 的文本数据"}

        result = self._skill.extract_skills_and_categories(text)

        return {
            "uid": uid,
            "function_name": function_name,
            "skills": result["skills"],
            "category": result["categories"]  # 新增分类字段
        }