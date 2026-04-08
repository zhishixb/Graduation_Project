import json
from typing import Dict, List, Optional, Tuple, Any, Union
import re


class JobDataParser:
    """
    解析从网页获取的原始 JSON 数据，提取所需字段，并清洗年限描述。
    """

    REQUIRED_KEYWORDS = [
        '任职要求', '岗位要求', '职位要求', '任职资格',
    ]
    KEYWORD_PATTERN = re.compile('|'.join(map(re.escape, REQUIRED_KEYWORDS)), re.IGNORECASE)

    YEAR_CLEAN_PATTERN = re.compile(
        r'[\(（]'
        r'[^()（）]*?'
        r'\d+'
        r'[^()（）]*?'
        r'年'
        r'[^()（）]*?'
        r'[\)）]'
    )

    def _clean_job_describe(self, text: str) -> str:
        if not text:
            return text
        cleaned = self.YEAR_CLEAN_PATTERN.sub('', text)
        # cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def parse_listings(self, data: Union[str, Dict[str, Any]]) -> Tuple[bool, Optional[List[Dict[str, Any]]], str]:
        if data is None:
            return False, None, "输入数据为空 (None)"

        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                return False, None, f"JSON 解析失败: {str(e)}"
        elif isinstance(data, dict):
            parsed_data = data
        else:
            return False, None, f"输入数据类型错误，期望 str 或 dict，得到 {type(data)}"

        # 1. 获取 job 对象
        job_obj = parsed_data.get("resultbody", {}).get("job")
        if not isinstance(job_obj, dict):
            return False, None, "数据结构错误：未找到 resultbody.job 对象"

        # 2. 获取 items 列表
        items_list = job_obj.get("items")
        if not isinstance(items_list, list):
            return False, None, "数据结构错误：未在数据中找到有效的职位列表 (items)"

        # 3. 【关键修改】检查 totalCount 与 items 是否匹配
        # 兼容大小写 key (totalCount 或 totalcount)
        total_count = job_obj.get("totalCount") or job_obj.get("totalcount") or 0

        # 逻辑：如果服务器说总共有数据 (>0)，但 items 却是空的，说明数据获取异常
        # if total_count > 0 and len(items_list) == 0:
        #     return False, None, f"数据异常：服务器返回总数 {total_count}，但职位列表为空 (items=[])。可能触发了反爬或分页错误。"
        # 这一段修改为更新时间戳，实现url刷新以获得更多信息

        # 4. 正常解析流程
        extracted_data = []
        skipped_count = 0

        for item in items_list:
            processed_item = self.parse_single_item(item)
            if processed_item:
                extracted_data.append(processed_item)
            else:
                skipped_count += 1

        message = f"成功解析 {len(extracted_data)} 条职位信息"
        if skipped_count > 0:
            message += f"，跳过 {skipped_count} 条不符合要求的数据"

        if total_count == 0 and len(items_list) == 0:
            message = "当前搜索条件下无职位数据 (totalCount=0)"

        return True, extracted_data, message

    def parse_single_item(self, item_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job_describe = item_dict.get("jobDescribe")
        if not job_describe:
            return None

        cleaned_describe = self._clean_job_describe(job_describe)

        if self.KEYWORD_PATTERN.search(cleaned_describe):
            return {
                "jobId": item_dict.get("jobId"),
                "jobName": item_dict.get("jobName"),
                "industryType2Str": item_dict.get("industryType2Str"),
                "jobDescribe": cleaned_describe,
                "jobAreaCode": item_dict.get("jobAreaCode"),
                "provideSalaryString": item_dict.get("provideSalaryString"),
                "major1Str": item_dict.get("major1Str")
            }
        else:
            return None