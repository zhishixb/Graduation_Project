import csv
import torch
import numpy as np
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel

# ------------------------- 1. PositionJob 定义 -------------------------
class PositionJob:
    """岗位数据对象，包含 job_id、function 和 job_description（清洗后文本）"""
    __slots__ = ('job_id', 'function', 'job_description')
    def __init__(self, job_id: str, function: Optional[str], job_description: Optional[str]):
        self.job_id = job_id
        self.function = function
        self.job_description = job_description   # 此处接收 cleaned_text


# ------------------------- 2. 加载清洗后 CSV 到内存 -------------------------
def load_cleaned_csv_to_memory(
    csv_path: Path,
    encoding: str = 'utf-8-sig',
    as_objects: bool = True
) -> List[PositionJob]:
    """
    将清洗后的 CSV 文件全部读入内存，返回 PositionJob 对象列表。
    CSV 应包含三列: job_id, function, cleaned_text
    :param csv_path: CSV 文件路径
    :param encoding: 文件编码
    :param as_objects: 若为 True，返回 List[PositionJob]；否则返回 List[Tuple]（此处固定为 True）
    :return: PositionJob 对象列表
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"文件不存在: {csv_path}")

    records = []
    with open(csv_path, 'r', encoding=encoding, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头
        # 可选验证列名
        expected = ['job_id', 'function', 'cleaned_text']
        if header != expected:
            print(f"警告: CSV 表头 {header} 与预期 {expected} 不一致，将按顺序解析")

        for row in reader:
            if len(row) < 3:
                print(f"跳过无效行（列数不足）: {row}")
                continue
            job_id, function, cleaned_text = row[0], row[1], row[2]
            if as_objects:
                # 将 cleaned_text 存入 job_description 字段
                records.append(PositionJob(job_id, function, cleaned_text))
            else:
                # 若需要元组形式，可修改，此处仅用对象形式
                records.append((job_id, function, cleaned_text))  # 但类型提示为 List[PositionJob]，最好统一
    if not as_objects:
        # 如果调用者要求元组，转换一下（实际使用中一般用对象）
        records = [PositionJob(jid, func, txt) for jid, func, txt in records]
    print(f"已从 {csv_path} 加载 {len(records)} 条记录到内存")
    return records