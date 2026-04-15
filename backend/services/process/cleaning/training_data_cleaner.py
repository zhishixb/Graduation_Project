# 适合云算力的全量内存多进程处理版本
import csv
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from loguru import logger
from tqdm import tqdm

# 确保导入路径正确
from backend.services.process.cleaning.job.public.csv_manager import MajorCourseFinder
from backend.services.process.cleaning.job.public.job_description_parser import SimpleExtractor, LineCleaner
from backend.services.process.cleaning.job.training_data.job_data_reader import JobDataReader
from backend.services.process.cleaning.job.training_data.job_filtration import DisciplineKeywordValidator
from backend.services.process.cleaning.job.training_data.subject_check import MajorToCategoryFinder


def _process_single_item(data_item, major_csv_path, category_finder, validator):
    """
    模块级函数，用于多进程处理单个数据项。
    先清洗，再判断合理性。
    返回 (job_id, major_name, result)，其中 result 为 (major_courses_text, cleaned_text) 或 None。
    """
    job_id, major_name, description = data_item
    try:
        # 1. 课程增强（若需要）
        if major_csv_path:
            course_finder = MajorCourseFinder(Path(major_csv_path))
        else:
            course_finder = None

        extractor = SimpleExtractor()
        cleaner = LineCleaner()

        major_courses_text = ""
        if course_finder and major_name:
            courses = course_finder.get_courses(major_name)
            major_courses_text = courses if courses else ""

        # 2. 清洗职位描述
        raw_sections = extractor.extract(description)
        cleaned_text = cleaner.process_sections(raw_sections)

        if not cleaned_text or not cleaned_text.strip():
            return job_id, major_name, None

        # 3. 学科合理性判断（使用清洗后的文本）
        category = category_finder.get_category(major_name)
        if category is None:
            return job_id, major_name, None
        if not validator.is_reasonable(cleaned_text, category):
            return job_id, major_name, None

        return job_id, major_name, (major_courses_text, cleaned_text)
    except Exception as e:
        logger.error(f"处理任务 {job_id} 时发生错误: {e}")
        return job_id, major_name, None


class TrainingDataCleaner:
    def __init__(self, db_path: Path, csv_path: Path, major_csv_path: Path, subject_csv_path: Path):
        """
        初始化清洗器。
        :param db_path: 原始岗位数据库路径
        :param csv_path: 输出 CSV 路径
        :param major_csv_path: 专业课程映射 CSV 路径
        :param subject_csv_path: 专业→一级学科映射 JSON 路径
        """
        self.db_path = db_path
        self.csv_path = csv_path
        self.major_csv_path = major_csv_path
        self.subject_csv_path = subject_csv_path

        # 初始化组件（单线程模式或主进程使用）
        self.db_manager = JobDataReader(self.db_path)
        self.extractor = SimpleExtractor()
        self.cleaner = LineCleaner()
        try:
            self.course_finder = MajorCourseFinder(major_csv_path)
            logger.info(f"成功加载专业课程数据：{self.major_csv_path}")
        except FileNotFoundError as e:
            logger.error(f"专业数据文件未找到，将跳过课程增强步骤：{e}")
            self.course_finder = None

        # 初始化学科映射器和验证器（会被传递给子进程）
        try:
            self.category_finder = MajorToCategoryFinder(subject_csv_path)
            logger.info(f"成功加载专业→学科映射：{self.subject_csv_path}")
        except FileNotFoundError as e:
            logger.error(f"学科映射文件未找到，将无法进行合理性过滤：{e}")
            self.category_finder = None

        self.validator = DisciplineKeywordValidator()  # 使用默认配置

        # 确保输出目录存在
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def clean_training_data_in_memory(self, max_workers: int = 4) -> int:
        """
        【高性能多进程版】内存预加载 + 多进程处理
        1. 一次性读取所有数据到内存
        2. 多进程并行清洗（真正利用多核）
        3. 批量写入 CSV 和 批量更新数据库
        """
        # 重置所有处理标记，确保全量重新处理（可选，根据需求注释）
        self.db_manager.reset_all_processed_at()

        if self.category_finder is None:
            logger.warning("未加载学科映射器，将跳过合理性过滤，所有数据均会保留")
        if self.validator is None:
            logger.warning("未加载验证器，将跳过合理性过滤，所有数据均会保留")

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
            results = list(tqdm(
                executor.map(_process_single_item,
                             all_data,
                             [major_csv_path_str] * total_count,
                             [self.category_finder] * total_count,
                             [self.validator] * total_count),
                total=total_count,
                desc="多进程清洗中",
                unit="条",
                colour="magenta",
                mininterval=0.5,
                smoothing=0.1
            ))

        # 3. 收集结果，统计各专业成功数量
        successful_count = 0
        results_to_write: List[Tuple[str, str]] = []
        major_counter = Counter()
        successful_pairs: List[Tuple[str, str]] = []  # 存储 (job_id, major_name) 用于数据库更新

        for job_id, major_name, result in results:
            if result is not None:
                results_to_write.append(result)
                successful_pairs.append((job_id, major_name))
                successful_count += 1
                major_counter[major_name] += 1   # 累加专业统计

        # 4. 批量写入 CSV
        if results_to_write:
            write_header = not self.csv_path.exists()
            self._write_to_csv(results_to_write, write_header=write_header)

            # 5. 批量更新数据库状态（使用复合主键精确标记）
            self.db_manager.batch_mark_processed(successful_pairs)

            logger.success(f"✅ 任务完成！成功处理：{successful_count} 条（已过滤不匹配数据）。")
            # 输出各专业写入统计（按数量降序排列）
            if major_counter:
                logger.info("各专业写入 CSV 记录数量统计：")
                for major, cnt in major_counter.most_common():
                    logger.info(f"  {major}: {cnt} 条")
            else:
                logger.info("无任何专业写入记录。")
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