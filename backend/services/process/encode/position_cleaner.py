from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import csv
from loguru import logger
from tqdm import tqdm

from backend.services.process.cleaning.job.public.job_description_parser import SimpleExtractor, LineCleaner


def _clean_single(job_id: str, description: str) -> Optional[str]:
    """清洗单条描述（模块级函数，便于多进程序列化）"""
    try:
        extractor = SimpleExtractor()
        cleaner = LineCleaner()
        raw_sections = extractor.extract(description)
        cleaned = cleaner.process_sections(raw_sections)
        if cleaned and cleaned.strip():
            return cleaned
        return None
    except Exception as e:
        logger.error(f"清洗 {job_id} 失败: {e}")
        return None


def _clean_single_wrapper(args):
    """包装函数，接收 (job_id, description) 元组，解包后调用 _clean_single"""
    return _clean_single(*args)


class PureMemoryCleaner:
    """纯内存多进程清洗器：利用多核 CPU，不依赖任何外部文件"""

    @staticmethod
    def clean_batch(
        data_list: List[Tuple[str, str, str]],
        max_workers: int = 4,
        output_csv_path: Optional[Path] = None
    ) -> List[Tuple[str, str, str]]:
        """
        多进程批量清洗
        :param data_list: 每条为 (job_id, function, job_description)
        :param max_workers: 并行进程数（建议不超过 CPU 核心数）
        :param output_csv_path: 可选，输出CSV文件路径，如果提供则保存清洗结果（列：job_id, function, cleaned_text）
        :return: 清洗成功的列表，每条为 (job_id, function, cleaned_text)
        """
        if not data_list:
            return []

        logger.info(f"开始内存多进程清洗，共 {len(data_list)} 条，进程数 {max_workers}")

        # 准备参数：每个任务需要 (job_id, description)
        args_list = [(job_id, desc) for job_id, _, desc in data_list]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 使用 map 配合模块级包装函数，避免 lambda 序列化问题
            results = list(tqdm(
                executor.map(_clean_single_wrapper, args_list),
                total=len(data_list),
                desc="清洗中",
                unit="条",
                colour="magenta"
            ))

        # 组装返回结果：保留清洗成功的条目
        cleaned_list = []
        for (job_id, function, _), cleaned_text in zip(data_list, results):
            if cleaned_text is not None:
                cleaned_list.append((job_id, function, cleaned_text))

        logger.success(f"清洗完成，成功 {len(cleaned_list)} / {len(data_list)} 条")

        # 如果提供了输出路径，写入CSV
        if output_csv_path:
            PureMemoryCleaner._write_to_csv(cleaned_list, output_csv_path)
            logger.info(f"清洗结果已保存至 {output_csv_path}")

        return cleaned_list

    @staticmethod
    def _write_to_csv(cleaned_list: List[Tuple[str, str, str]], output_path: Path):
        """将清洗结果写入CSV文件，列：job_id, function, cleaned_text"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['job_id', 'function', 'cleaned_text'])
            writer.writerows(cleaned_list)