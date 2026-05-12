import csv
from pathlib import Path
from typing import Optional
from loguru import logger


def filter_short_texts(
        csv_path: Path,
        min_length: int = 20,
        output_path: Optional[Path] = None
) -> int:
    """
    过滤 CSV 文件中 cleaned_text 列字符数小于 min_length 的行。
    CSV 应包含列：job_id, function, cleaned_text。

    :param csv_path: 输入 CSV 文件路径
    :param min_length: 文本最小长度（字符数），默认 20
    :param output_path: 输出文件路径（默认覆盖原文件）
    :return: 保留的行数（不含表头）
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"文件不存在: {csv_path}")

    # 读取所有行
    rows = []
    header = None
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        # 确定 cleaned_text 列索引
        try:
            text_idx = header.index('cleaned_text')
        except ValueError:
            raise ValueError("CSV 文件缺少 'cleaned_text' 列")

        for row in reader:
            if len(row) > text_idx:
                text = row[text_idx]
                # 计算字符数（含任何字符）
                if len(text) >= min_length:
                    rows.append(row)

    # 确定输出路径
    output_path = output_path or csv_path

    # 写入过滤后的数据
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    logger.info(f"过滤完成：原始记录数（不含表头）{len(rows)} 条，保留 {len(rows)} 条，保存至 {output_path}")
    return len(rows)