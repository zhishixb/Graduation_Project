import random

import pandas as pd
from pathlib import Path
from typing import Optional, List

class JobDataRepository:
    def __init__(self, file_path: Path):
        self._file_path = file_path

    def _read_df(self):
        """统一读取 CSV，避免重复 I/O"""
        return pd.read_csv(self._file_path)

    def get_cleaned_text_by_function(self, function_name: str) -> Optional[str]:
        """保持原逻辑：返回第一条匹配文本（如有其他依赖可继续使用）"""
        df = self._read_df()
        row = df[df['function'] == function_name]
        if not row.empty:
            return row.iloc[0]['cleaned_text']
        return None

    def get_all_texts_by_function(self, function_name: str) -> List[str]:
        """获取某个职能下所有清洗后文本的列表"""
        df = self._read_df()
        rows = df[df['function'] == function_name]
        return rows['cleaned_text'].tolist()

    def get_random_texts_by_function(self, function_name: str, k: int = 5) -> List[str]:
        """从某个职能的清洗后文本中随机选取最多 k 条（默认5条）"""
        texts = self.get_all_texts_by_function(function_name)
        if len(texts) <= k:
            return texts
        return random.sample(texts, k)

    def get_merged_text_by_function(self, function_name: str) -> Optional[str]:
        """
        【新增】获取某个职能下所有清洗后文本的合并字符串（用空格分隔）。
        若没有匹配行则返回 None。
        """
        texts = self.get_all_texts_by_function(function_name)
        if not texts:
            return None
        return " ".join(texts)