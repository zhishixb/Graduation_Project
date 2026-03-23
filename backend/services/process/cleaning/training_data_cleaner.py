import csv
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger

# 确保导入路径与你的项目结构一致
from backend.services.process.cleaning.job.public.job_description_parser import JobDescriptionParser
from backend.services.process.cleaning.job.training_data.csv_manager import MajorCourseFinder
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
        self.data_cleaner = JobDescriptionParser()

        # 初始化专业课程查找器
        try:
            self.course_finder = MajorCourseFinder(str(self.major_csv_path))
            logger.info(f"成功加载专业课程数据：{self.major_csv_path}")
        except FileNotFoundError as e:
            logger.error(f"专业数据文件未找到，将跳过课程增强步骤：{e}")
            self.course_finder = None

        # 确保输出目录存在
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def clean_training_data(self, batch_size: int = 50) -> int:
        """
        主清洗与增强流程：
        1. 从数据库获取未处理数据
        2. 根据 major_name 查询课程描述
        3. 清洗 job_description 提取要求
        4. 组合数据 (仅课程+要求) 写入 CSV
        5. 标记数据库记录为已处理
        """
        logger.info(f"开始增强清洗任务 | DB: {self.db_path} | Output: {self.csv_path}")

        if self.course_finder is None:
            logger.warning("未加载课程查找器，输出中将不包含课程信息。")

        pending_count = self.db_manager.get_pending_count()
        if pending_count == 0:
            logger.info("没有待处理的数据，任务结束。")
            return 0

        logger.info(f"检测到 {pending_count} 条待处理数据，开始处理...")

        processed_count = 0
        # 修改数据结构：只保留 (major_courses_text, cleaned_requirements)
        results_to_write: List[Tuple[str, str]] = []

        write_header = not self.csv_path.exists()

        try:
            while True:
                raw_data = self.db_manager.get_next_unprocessed()
                if raw_data is None:
                    break

                # 解包数据 (假设 get_next_unprocessed 返回 job_id, major_name, description)
                # 如果原方法只返回两个值，请确保这里与你实际的 JobDataReader 实现一致
                # 根据之前的上下文，这里假设已修正为返回三元组，或者我们在内部处理了 major_name
                if len(raw_data) == 3:
                    job_id, major_name, description = raw_data
                elif len(raw_data) == 2:
                    # 兼容旧版返回 (job_id, description)，此时 major_name 未知，需特殊处理或跳过课程增强
                    job_id, description = raw_data
                    major_name = ""
                else:
                    logger.error(f"数据格式异常：{raw_data}")
                    continue

                try:
                    # 1. 获取课程描述
                    major_courses_text = ""
                    if self.course_finder and major_name:
                        courses = self.course_finder.get_courses(major_name)
                        major_courses_text = courses if courses else ""

                    # 2. 清洗职位描述
                    cleaned_text = self.data_cleaner.get_requirements_text(description, clean=True)

                    # 3. 收集结果 (仅两列)
                    results_to_write.append((major_courses_text, cleaned_text))

                    # 4. 标记为已处理
                    if self.db_manager.mark_processed(job_id):
                        processed_count += 1
                    else:
                        logger.warning(f"标记失败 (可能已处理): {job_id}")

                    # 批量写入
                    if len(results_to_write) >= batch_size:
                        self._write_to_csv(results_to_write, write_header=write_header)
                        write_header = False
                        results_to_write.clear()
                        logger.debug(f"进度：{processed_count}/{pending_count}")

                except Exception as e:
                    logger.error(f"处理任务 {job_id} 时发生错误: {e}")
                    # 出错也标记，防止死循环
                    self.db_manager.mark_processed(job_id)
                    continue

            # 写入剩余数据
            if results_to_write:
                self._write_to_csv(results_to_write, write_header=write_header)

            stats = self.db_manager.get_stats()
            logger.success(f"任务完成！本次成功处理：{processed_count} 条。")
            logger.info(f"库状态更新 -> 总数:{stats['total']}, 待处理:{stats['pending']}, 已完成:{stats['processed']}")

            return processed_count

        except Exception as e:
            logger.critical(f"任务严重异常中断: {e}")
            raise

    def _write_to_csv(self, data: List[Tuple[str, str]], write_header: bool = False):
        """
        将结果写入 CSV。
        写入两列：major_courses, cleaned_requirements
        """
        mode = 'a' if not write_header else 'w'
        # utf-8-sig 确保 Excel 正常显示中文
        with open(self.csv_path, mode, encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            if write_header:
                # 只写入这两个表头
                writer.writerow(['major_courses', 'cleaned_requirements'])

            for row in data:
                # row 现在是 (major_courses_text, cleaned_text)
                writer.writerow(row)

        logger.debug(f"已写入 {len(data)} 条记录至 {self.csv_path}")


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