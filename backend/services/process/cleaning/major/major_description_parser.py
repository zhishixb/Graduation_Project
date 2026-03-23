import re


class MajorDescriptionParser:
    def _remove_trailing_keywords(self, text: str) -> str:
        """移除末尾的 '关键词：...' 部分"""
        return re.sub(r'关键词[:：]([^\n]*)$', r'\1', text)

    def _extract_after_verb(self, text: str) -> str:
        """
        从文本中提取第一个引导动词（如“主要研究”）之后的内容。
        如果没有匹配，则返回原文。
        """
        verbs = ['主要研究', '涉及', '进行', '包括', '涵盖', '是指', '即', '指']
        # 转义动词以防包含特殊字符
        escaped_verbs = [re.escape(v) for v in verbs]
        pattern = f'(?:{"|".join(escaped_verbs)})(.*)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return text

    def _remove_degree_granting_info(self, text: str) -> str:
        """
        删除关于授予学位的描述。
        """
        pattern = r'(?:授予|颁授|颁发)[\u4e00-\u9fa5]*?(?:学士|硕士|博士)(?:学位|文凭|证书)?'
        cleaned_text = re.sub(pattern, '', text)

        # 清理因删除产生的多余空格或标点
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
        cleaned_text = re.sub(r'[,，]\s*[,，]', ',', cleaned_text)

        return cleaned_text

    def clean(self, text: str) -> str:
        if not isinstance(text, str):
            return ""

        # 1. 先提取动词后的内容（聚焦技能部分）
        cleaned = self._extract_after_verb(text)

        # 2. 删除授予学位的描述
        cleaned = self._remove_degree_granting_info(cleaned)

        # 3. 删除末尾关键词
        cleaned = re.sub(r'[\n\s]*关键词[:：][^\n]*$', '', cleaned)

        # 4. 清理空白和标点
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'[。；;，,:：\s]+$', '', cleaned)

        # 如果删除学位信息后导致开头出现多余的逗号或连接词，再次清理
        cleaned = re.sub(r'^[，,;；]', '', cleaned)

        # 【新增】将文本中的英文逗号 ',' 替换为中文逗号 '，'
        cleaned = cleaned.replace(',', '，')

        return cleaned