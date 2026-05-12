import json
from pathlib import Path
from typing import Dict

# 定位 location.json（项目根目录）
_location_path = Path(__file__).parent.parent.parent / "data" / "json" / "location.json"
with _location_path.open("r", encoding="utf-8") as f:
    _raw_data = json.load(f)

# code -> 省份代码
CODE_TO_PROVINCE_CODE: Dict[str, str] = {}
# 省份代码 -> 省份名称
PROVINCE_NAME_MAP: Dict[str, str] = {}

for item in _raw_data:
    code = item["code"]
    code_type = item.get("codeType", "")
    if code_type == "1":
        PROVINCE_NAME_MAP[code] = item["value"]
        CODE_TO_PROVINCE_CODE[code] = code
    else:
        parent_code = item.get("parentProvinceCode", "")
        if parent_code:
            CODE_TO_PROVINCE_CODE[code] = parent_code

def get_province_code(region_code: str) -> str:
    """返回任意区域码对应的省份代码，若无映射则返回原代码"""
    return CODE_TO_PROVINCE_CODE.get(region_code, region_code)

def get_province_name(province_code: str) -> str:
    """返回省份中文名，无映射则返回原代码"""
    return PROVINCE_NAME_MAP.get(province_code, province_code)