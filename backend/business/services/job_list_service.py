from backend.business.repository.job_list_repository import JobListRepository


class JobListService:
    def __init__(self, repo: JobListRepository):
        self._repo = repo
        self._raw_data = None
        self._uid_to_name = {}
        self._uid_to_path = {}   # 可选，存储完整路径

    def _ensure_loaded(self):
        if self._raw_data is None:
            self._raw_data = self._repo.get_raw_data()
            self._build_index()

    def _build_index(self):
        for industry, categories in self._raw_data.items():
            for category, jobs in categories.items():
                for job_name, job_info in jobs.items():
                    uid = job_info.get("uid")
                    if uid is not None:
                        self._uid_to_name[uid] = job_name
                        self._uid_to_path[uid] = {
                            "industry": industry,
                            "category": category,
                            "job": job_name
                        }

    def get_job_name_by_uid(self, uid: int) -> str:
        self._ensure_loaded()
        return self._uid_to_name.get(uid, "")

    def get_job_data(self) -> dict:
        self._ensure_loaded()
        return self._raw_data