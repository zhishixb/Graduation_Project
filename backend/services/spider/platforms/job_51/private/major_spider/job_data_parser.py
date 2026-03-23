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

    # 新增：匹配括号内的年限描述（支持中英文括号）
    # 示例匹配: (2年及以上), （3年以上）, (1-3年), (应届毕业生优先) 也常含"年"
    YEAR_CLEAN_PATTERN = re.compile(
        r'[\(（]'              # 左括号（英文或中文）
        r'[^()（）]*?'         # 非贪婪匹配括号内任意字符
        r'\d+'                 # 至少一个数字
        r'[^()（）]*?'         # 可能有连接符如 -
        r'年'                  # 必须包含“年”字
        r'[^()（）]*?'         # 其他修饰词（如“以上”“以下”）
        r'[\)）]'              # 右括号
    )

    def _clean_job_describe(self, text: str) -> str:
        """
        清洗 jobDescribe 文本：
        - 移除括号内的年限描述（如 (2年及以上)）
        """
        if not text:
            return text
        # 移除年限括号
        cleaned = self.YEAR_CLEAN_PATTERN.sub('', text)
        # 可选：进一步清理多余空格或连续空白
        # cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def parse_listings(self, data: Union[str, Dict[str, Any]]) -> Tuple[bool, Optional[List[Dict[str, Any]]], str]:
        """

        Args:
            data: 网页返回的数据

        Returns:
            解析得到的岗位数据

        """
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

        items_list = parsed_data.get("resultbody", {}).get("job", {}).get("items")

        if not isinstance(items_list, list):
            return False, None, "未在数据中找到有效的职位列表 (resultbody.job.items)"

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

        return True, extracted_data, message

    def parse_single_item(self, item_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        略微清洗岗位描述并组装为字典

        Args:
            item_dict: 岗位数据

        Returns:
            处理后的岗位数据字典
        """
        job_describe = item_dict.get("jobDescribe")

        if not job_describe:
            return None

        # 先清洗年限描述
        cleaned_describe = self._clean_job_describe(job_describe)

        # 检查清洗后的文本是否仍包含关键词（避免因清洗导致关键词丢失）
        if self.KEYWORD_PATTERN.search(cleaned_describe):
            return {
                "jobId": item_dict.get("jobId"),
                "jobName": item_dict.get("jobName"),
                "industryType2Str": item_dict.get("industryType2Str"),
                "jobDescribe": cleaned_describe,  # 返回清洗后的描述
            }
        else:
            return None