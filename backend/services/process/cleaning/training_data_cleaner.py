# 适合云算力的全量内存多线程处理版本
import csv
import threading
import queue
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from tqdm import tqdm

# 确保导入路径正确
from backend.services.process.cleaning.job.public.csv_manager import MajorCourseFinder
from backend.services.process.cleaning.job.public.job_description_parser import SimpleExtractor, LineCleaner
from backend.services.process.cleaning.job.training_data.job_data_reader import JobDataReader


class TrainingDataCleaner:
    def __init__(self, db_path: Path, csv_path: Path, major_csv_path: Path):
        """
        初始化清洗器。
        """
        self.db_path = db_path
        self.csv_path = csv_path
        self.major_csv_path = major_csv_path

        # 初始化组件
        self.db_manager = JobDataReader(self.db_path)
        self.extractor = SimpleExtractor()
        self.cleaner = LineCleaner()

        # 初始化专业课程查找器
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
        【高性能版】内存预加载 + 多线程处理
        1. 一次性读取所有数据到内存
        2. 多线程并行清洗
        3. 批量写入 CSV 和 批量更新数据库
        """
        logger.info(f"🚀 启动内存预加载多线程模式 | 线程数: {max_workers}")

        if self.course_finder is None:
            logger.warning("未加载课程查找器，输出中将不包含课程信息。")

        # --- 1. 主线程：全量读取数据到内存 ---
        # 调用 JobDataReader 的新方法
        all_data = self.db_manager.get_all_pending_data()

        total_count = len(all_data)
        if total_count == 0:
            logger.info("没有待处理的数据，任务结束。")
            return 0

        logger.info(f"✅ 已加载 {total_count} 条数据到内存，开始多线程处理...")

        # 线程安全的结果队列
        result_queue = queue.Queue()
        # 进度条锁（防止多线程同时更新进度条导致显示错乱）
        pbar_lock = threading.Lock()

        def process_single_item(data_item):
            """
            工作线程执行的具体任务
            """
            job_id, major_name, description = data_item

            try:
                # --- 核心业务逻辑 (同之前) ---

                # A. 获取课程描述
                major_courses_text = ""
                if self.course_finder and major_name:
                    courses = self.course_finder.get_courses(major_name)
                    major_courses_text = courses if courses else ""

                # B. 清洗职位描述
                raw_sections = self.extractor.extract(description)
                cleaned_text = self.cleaner.process_sections(raw_sections)

                # C. 将结果放入队列 (job_id, (courses, cleaned_text))
                result_queue.put((job_id, (major_courses_text, cleaned_text)))

            except Exception as e:
                logger.error(f"处理任务 {job_id} 时发生错误: {e}")
                # 出错也放入队列，标记为 None，防止主线程等待
                result_queue.put((job_id, None))

        # --- 2. 多线程并行处理 ---
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            # map 会保持提交顺序，但我们需要的是并发执行，所以用 submit + as_completed 或者直接 list(executor.map)
            # 这里为了简单展示进度，我们使用 list 消费，配合 tqdm
            list(tqdm(
                executor.map(process_single_item, all_data),
                total=total_count,
                desc="多线程清洗中",
                unit="条",
                colour="magenta",
                mininterval = 0.5,  # 👈 加上这个：每 0.5 秒刷新一次界面，极大提升流畅度
                smoothing = 0.1  # 👈 加上这个：减少平滑预测，显示更实时的速度
            ))

        # --- 3. 收集结果并写入 ---
        logger.info("处理完成，正在写入 CSV 和更新数据库...")

        successful_count = 0
        results_to_write: List[Tuple[str, str]] = []
        processed_ids: List[str] = []

        # 从队列取出所有结果
        while not result_queue.empty():
            job_id, result = result_queue.get()
            if result:
                results_to_write.append(result)
                processed_ids.append(job_id)
                successful_count += 1

        # 批量写入 CSV
        if results_to_write:
            write_header = not self.csv_path.exists()
            self._write_to_csv(results_to_write, write_header=write_header)

            # 批量更新数据库状态 (一次性更新所有 ID)
            self.db_manager.batch_mark_processed(processed_ids)

            logger.success(f"✅ 任务完成！成功处理：{successful_count} 条。")
        else:
            logger.warning("没有生成任何有效数据。")

        return successful_count

    def clean_training_data(self, batch_size: int = 500) -> int:
        """
        【旧版】单线程顺序处理
        保留此方法作为备用，或者用于调试。
        """
        logger.info(f"开始单线程清洗任务...")

        pending_ids = self.db_manager.get_all_pending_ids()
        total_count = len(pending_ids)
        if total_count == 0: return 0

        processed_count = 0
        error_count = 0
        results_to_write: List[Tuple[str, str]] = []
        write_header = not self.csv_path.exists()

        try:
            with tqdm(total=total_count, desc="单线程清洗", unit="条", colour="green") as pbar:
                for job_id in pending_ids:
                    raw_data = self.db_manager.get_data_by_id(job_id)
                    if not raw_data: continue

                    if len(raw_data) == 3:
                        current_job_id, major_name, description = raw_data
                    elif len(raw_data) == 2:
                        current_job_id, description = raw_data
                        major_name = ""
                    else:
                        continue

                    try:
                        major_courses_text = ""
                        if self.course_finder and major_name:
                            courses = self.course_finder.get_courses(major_name)
                            major_courses_text = courses if courses else ""

                        raw_sections = self.extractor.extract(description)
                        cleaned_text = self.cleaner.process_sections(raw_sections)

                        results_to_write.append((major_courses_text, cleaned_text))

                        if self.db_manager.mark_processed(current_job_id):
                            processed_count += 1

                        pbar.update(1)

                        if len(results_to_write) >= batch_size:
                            self._write_to_csv(results_to_write, write_header=write_header)
                            write_header = False
                            results_to_write.clear()

                    except Exception as e:
                        logger.error(f"处理任务 {current_job_id} 时发生错误: {e}")
                        error_count += 1
                        self.db_manager.mark_processed(current_job_id)
                        pbar.update(1)
                        continue

            if results_to_write:
                self._write_to_csv(results_to_write, write_header=write_header)

            logger.success(f"单线程任务完成！成功：{processed_count}, 失败：{error_count}")
            return processed_count

        except Exception as e:
            logger.critical(f"任务严重异常中断: {e}")
            raise

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