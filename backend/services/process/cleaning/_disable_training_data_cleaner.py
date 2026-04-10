import csv
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger
from tqdm import tqdm  # 导入 tqdm 用于显示进度条

# 确保导入路径与你的项目结构一致
# 假设这些模块在你的环境中可用
from backend.services.process.cleaning.job.public.csv_manager import MajorCourseFinder
from backend.services.process.cleaning.job.public.job_description_parser import SimpleExtractor, LineCleaner
from backend.services.process.cleaning.job.training_data.job_data_reader import JobDataReader


class TrainingDataCleaner:
    def __init__(self, db_path: Path, csv_path: Path, major_csv_path: Path):
        """
        初始化清洗器。
        :param db_path: SQLite 数据库路径
        :param csv_path: 输出清洗结果的 CSV 路径
        :param major_csv_path: 包含专业与课程映射的 CSV 路径 (major_data.csv)
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

    def clean_training_data(self, batch_size: int = 50) -> int:
        """
        主清洗与增强流程（集成 tqdm 进度条版）：
        1. 获取所有待处理数据的 ID 列表
        2. 使用 tqdm 遍历处理
        3. 批量写入 CSV
        """
        logger.info(f"开始增强清洗任务 | DB: {self.db_path} | Output: {self.csv_path}")

        if self.course_finder is None:
            logger.warning("未加载课程查找器，输出中将不包含课程信息。")

        # 1. 获取所有待处理数据的 ID 列表
        # 注意：这里假设 JobDataReader 有一个方法能获取所有待处理 ID
        # 如果没有 get_all_pending_ids，你需要在 JobDataReader 中实现它，或者沿用旧的 while 循环逻辑（见下方注释）
        pending_ids = self.db_manager.get_all_pending_ids()

        total_count = len(pending_ids)
        if total_count == 0:
            logger.info("没有待处理的数据，任务结束。")
            return 0

        logger.info(f"检测到 {total_count} 条待处理数据，开始处理...")

        processed_count = 0
        error_count = 0
        results_to_write: List[Tuple[str, str]] = []

        write_header = not self.csv_path.exists()

        try:
            # 2. 使用 tqdm 包裹循环
            # desc: 进度条左侧的描述文字
            # unit: 单位
            # colour: 颜色 (可选)
            with tqdm(total=total_count, desc="清洗进度", unit="条", colour="green") as pbar:

                for job_id in pending_ids:
                    # 3. 根据 ID 获取具体数据
                    # 假设 JobDataReader 有根据 ID 获取单条数据的方法
                    # 如果原方法是 get_next_unprocessed，你需要修改它支持传参 ID，或者在这里重新查询
                    raw_data = self.db_manager.get_data_by_id(job_id)

                    if raw_data is None:
                        continue

                    # 解包数据 (根据实际情况调整)
                    # 假设返回 (job_id, major_name, description)
                    if len(raw_data) == 3:
                        current_job_id, major_name, description = raw_data
                    elif len(raw_data) == 2:
                        current_job_id, description = raw_data
                        major_name = ""
                    else:
                        logger.error(f"数据格式异常: {raw_data}")
                        continue

                    try:
                        # --- 核心处理逻辑 ---

                        # A. 获取课程描述
                        major_courses_text = ""
                        if self.course_finder and major_name:
                            courses = self.course_finder.get_courses(major_name)
                            major_courses_text = courses if courses else ""

                        # B. 清洗职位描述
                        raw_sections = self.extractor.extract(description)
                        cleaned_text = self.cleaner.process_sections(raw_sections)

                        # C. 收集结果
                        results_to_write.append((major_courses_text, cleaned_text))

                        # D. 标记为已处理
                        if self.db_manager.mark_processed(current_job_id):
                            processed_count += 1
                        else:
                            logger.warning(f"标记失败 (可能已处理): {current_job_id}")

                        # E. 更新进度条
                        pbar.update(1)

                        # F. 批量写入 CSV
                        if len(results_to_write) >= batch_size:
                            self._write_to_csv(results_to_write, write_header=write_header)
                            write_header = False
                            results_to_write.clear()
                            # 注意：这里不再打印 logger.debug 进度，以免破坏 tqdm 的显示效果

                    except Exception as e:
                        logger.error(f"处理任务 {current_job_id} 时发生错误: {e}")
                        error_count += 1
                        # 出错也标记，防止死循环
                        self.db_manager.mark_processed(current_job_id)
                        pbar.update(1)
                        continue

            # 4. 写入剩余数据
            if results_to_write:
                self._write_to_csv(results_to_write, write_header=write_header)

            stats = self.db_manager.get_stats()
            logger.success(f"任务完成！本次成功处理：{processed_count} 条，失败：{error_count} 条。")
            logger.info(f"库状态更新 -> 总数:{stats['total']}, 待处理:{stats['pending']}, 已完成:{stats['processed']}")

            return processed_count

        except Exception as e:
            logger.critical(f"任务严重异常中断: {e}")
            raise

    def _write_to_csv(self, data: List[Tuple[str, str]], write_header: bool = False):
        """
        将结果写入 CSV。
        """
        mode = 'a' if not write_header else 'w'
        # utf-8-sig 确保 Excel 正常显示中文
        with open(self.csv_path, mode, encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            if write_header:
                writer.writerow(['major_courses', 'cleaned_requirements'])

            for row in data:
                writer.writerow(row)

        logger.debug(f"已批量写入 {len(data)} 条记录至 {self.csv_path}")


# --- 使用示例 ---
if __name__ == "__main__":
    # 配置路径
    db_file = Path("./data/jobs.db")
    output_csv = Path("./output/minimal_training_data.csv") # 建议换个文件名区分
    major_csv = Path("./data/major_data.csv")

    if db_file.exists() and major_csv.exists():
        cleaner = TrainingDataCleaner(
            db_path=db_file,
            csv_path=output_csv,
            major_csv_path=major_csv
        )
        count = cleaner.clean_training_data()
        print(f"\n处理结束，共生成 {count} 条最小微调数据。")
        print(f"输出文件位置：{output_csv.absolute()}")
    else:
        missing = []
        if not db_file.exists(): missing.append(str(db_file))
        if not major_csv.exists(): missing.append(str(major_csv))
        logger.error(f"文件缺失：{', '.join(missing)}")