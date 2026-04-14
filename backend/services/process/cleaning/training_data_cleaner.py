# 适合云算力的全量内存多进程处理版本
import csv
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
from loguru import logger
from tqdm import tqdm

# 确保导入路径正确
from backend.services.process.cleaning.job.public.csv_manager import MajorCourseFinder
from backend.services.process.cleaning.job.public.job_description_parser import SimpleExtractor, LineCleaner
from backend.services.process.cleaning.job.training_data.job_data_reader import JobDataReader


def _process_single_item(data_item, major_csv_path):
    """
    模块级函数，用于多进程处理单个数据项。
    :param data_item: (job_id, major_name, description)
    :param major_csv_path: 专业课程 CSV 文件路径（字符串或 Path），在子进程中重新创建 MajorCourseFinder
    :return: (job_id, (major_courses_text, cleaned_text)) 或 (job_id, None) 如果出错或清洗后文本为空
    """
    job_id, major_name, description = data_item
    try:
        # 在子进程中重新创建无状态对象（每个进程独立）
        if major_csv_path:
            course_finder = MajorCourseFinder(Path(major_csv_path))
        else:
            course_finder = None

        extractor = SimpleExtractor()
        cleaner = LineCleaner()

        # 获取课程描述
        major_courses_text = ""
        if course_finder and major_name:
            courses = course_finder.get_courses(major_name)
            major_courses_text = courses if courses else ""

        # 清洗职位描述
        raw_sections = extractor.extract(description)
        cleaned_text = cleaner.process_sections(raw_sections)

        # 检查清洗后的文本是否为空
        if not cleaned_text or not cleaned_text.strip():
            return job_id, None

        return job_id, (major_courses_text, cleaned_text)
    except Exception as e:
        logger.error(f"处理任务 {job_id} 时发生错误: {e}")
        return job_id, None

class TrainingDataCleaner:
    def __init__(self, db_path: Path, csv_path: Path, major_csv_path: Path):
        """
        初始化清洗器。
        """
        self.db_path = db_path
        self.csv_path = csv_path
        self.major_csv_path = major_csv_path

        # 初始化组件（主要用于单线程模式，多进程模式下子进程会自己创建）
        self.db_manager = JobDataReader(self.db_path)
        self.extractor = SimpleExtractor()
        self.cleaner = LineCleaner()
        try:
            self.course_finder = MajorCourseFinder(major_csv_path)
            logger.info(f"成功加载专业课程数据：{self.major_csv_path}")
        except FileNotFoundError as e:
            logger.error(f"专业数据文件未找到，将跳过课程增强步骤：{e}")
            self.course_finder = None

        # 确保输出目录存在
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def clean_training_data_in_memory(self, max_workers: int = 4) -> int:
        """
        【高性能多进程版】内存预加载 + 多进程处理
        1. 一次性读取所有数据到内存
        2. 多进程并行清洗（真正利用多核）
        3. 批量写入 CSV 和 批量更新数据库
        """
        logger.info(f"🚀 启动内存预加载多进程模式 | 进程数: {max_workers}")

        # 1. 主进程读取所有待处理数据
        all_data = self.db_manager.get_all_pending_data()
        total_count = len(all_data)
        if total_count == 0:
            logger.info("没有待处理的数据，任务结束。")
            return 0

        logger.info(f"✅ 已加载 {total_count} 条数据到内存，开始多进程处理...")

        # 准备传递给子进程的参数（将路径转为字符串，便于 pickle）
        major_csv_path_str = str(self.major_csv_path) if self.major_csv_path else None

        # 2. 多进程并行处理
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # map 保持输入顺序，结果列表与 all_data 顺序一致
            results = list(tqdm(
                executor.map(_process_single_item, all_data, [major_csv_path_str] * total_count),
                total=total_count,
                desc="多进程清洗中",
                unit="条",
                colour="magenta",
                mininterval=0.5,
                smoothing=0.1
            ))

        # 3. 收集结果
        successful_count = 0
        results_to_write: List[Tuple[str, str]] = []
        processed_ids: List[str] = []

        for job_id, result in results:
            if result is not None:
                results_to_write.append(result)
                processed_ids.append(job_id)
                successful_count += 1

        # 4. 批量写入 CSV
        if results_to_write:
            write_header = not self.csv_path.exists()
            self._write_to_csv(results_to_write, write_header=write_header)

            # 5. 批量更新数据库状态（主进程执行）
            self.db_manager.batch_mark_processed(processed_ids)

            logger.success(f"✅ 任务完成！成功处理：{successful_count} 条。")
        else:
            logger.warning("没有生成任何有效数据。")

        return successful_count

    def _write_to_csv(self, data: List[Tuple[str, str]], write_header: bool = False):
        """
        将结果写入 CSV。
        """
        mode = 'a' if not write_header else 'w'
        with open(self.csv_path, mode, encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['major_courses', 'cleaned_requirements'])
            for row in data:
                writer.writerow(row)
        logger.debug(f"已批量写入 {len(data)} 条记录")