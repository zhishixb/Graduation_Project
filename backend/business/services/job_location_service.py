from typing import List, Dict
from collections import defaultdict

from backend.business.repository.job_location_repository import JobLocationRepository
from backend.business.utils.province_mapping import get_province_code, get_province_name


# 简称 → 全称映射（仅需处理自治区、直辖市、特别行政区）
PROVINCE_FULL_NAME_MAP = {
    "北京": "北京市",
    "上海": "上海市",
    "天津": "天津市",
    "重庆": "重庆市",
    "内蒙古": "内蒙古自治区",
    "广西": "广西壮族自治区",
    "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区",
    "香港": "香港特别行政区",
    "澳门": "澳门特别行政区",
}


class JobLocationService:
    def __init__(self, repo: JobLocationRepository):
        self._repo = repo

    def get_province_counts(self, job_names: List[str]) -> List[Dict]:
        raw = self._repo.get_province_counts(job_names)

        # 按省份维度汇总
        province_counter = defaultdict(int)
        for region_code, cnt in raw:
            province_code = get_province_code(region_code)
            province_counter[province_code] += cnt

        # 构建结果并转为全称
        result = []
        for province_code, total in province_counter.items():
            short_name = get_province_name(province_code)          # 原始简称
            full_name = PROVINCE_FULL_NAME_MAP.get(short_name, short_name)  # 转为全称
            result.append({
                "name": full_name,
                "value": total
            })

        result.sort(key=lambda x: x["value"], reverse=True)
        return result