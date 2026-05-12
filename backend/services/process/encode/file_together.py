import csv
from pathlib import Path
from typing import List, Union
from loguru import logger


def merge_csv_parts(
        input_pattern: Union[str, Path],
        output_path: Union[str, Path],
        part_count: int = 3,
        encoding: str = 'utf-8-sig'
) -> int:
    """
    将分片 CSV 文件合并为一个完整的 CSV 文件。

    :param input_pattern: 分片文件的路径模式，例如 "/path/to/cleaned_part*.csv"
                          或基础路径（会自动添加 _part1, _part2 等）
    :param output_path: 合并后的输出文件路径
    :param part_count: 分片的数量（从1到part_count）
    :param encoding: 文件编码，默认 utf-8-sig
    :return: 合并的总行数（不含表头）

    示例：
        merge_csv_parts("/tmp/cleaned_jobs.csv", "/tmp/merged.csv", part_count=3)
        会合并 /tmp/cleaned_jobs_part1.csv, part2.csv, part3.csv
    """
    input_base = Path(input_pattern)
    output_path = Path(output_path)

    # 生成分片文件路径列表
    if input_base.suffix == '.csv':
        stem = input_base.stem
        part_paths = [
            input_base.with_name(f"{stem}_part{i}{input_base.suffix}")
            for i in range(1, part_count + 1)
        ]
    else:
        # 如果传入的是目录/基础名，按模式拼接
        part_paths = [
            input_base.parent / f"{input_base.name}_part{i}.csv"
            for i in range(1, part_count + 1)
        ]

    # 过滤掉不存在的文件
    existing_paths = [p for p in part_paths if p.exists()]
    if not existing_paths:
        logger.error("没有找到任何分片文件")
        return 0

    logger.info(f"找到 {len(existing_paths)} 个分片文件: {', '.join(str(p) for p in existing_paths)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0

    with open(output_path, 'w', encoding=encoding, newline='') as out_f:
        writer = None
        for i, part_path in enumerate(existing_paths):
            with open(part_path, 'r', encoding=encoding, newline='') as in_f:
                reader = csv.reader(in_f)
                header = next(reader)  # 读取表头

                if writer is None:
                    # 第一个文件，写入表头
                    writer = csv.writer(out_f)
                    writer.writerow(header)

                # 写入数据行
                rows = list(reader)
                writer.writerows(rows)
                total_rows += len(rows)
                logger.debug(f"已合并 {part_path}: {len(rows)} 行")

    logger.success(f"合并完成，总行数（不含表头）: {total_rows}，输出文件: {output_path}")
    return total_rows