import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Union, Dict

from loguru import logger

# 确保导入路径正确
from backend.services.process.count.training_data.csv_manager import DataCountRecorder
from backend.services.process.cleaning.job.training_data.job_data_reader import JobDataReader


class TrainingDataRecorder:
    """
    训练数据统计协调器。
    负责协调 数据库(JobDataReader) 和 统计日志(DataCountRecorder)。
    """

    def __init__(self, db_path: Union[str, Path], stats_csv_path: Union[str, Path]):
        """
        :param db_path: 业务数据库文件路径 (.db)
        :param stats_csv_path: 统计日志文件路径 (.csv)
        """
        # 1. 分别处理两个路径
        self.db_path = Path(db_path)
        self.stats_csv_path = Path(stats_csv_path)

        # 确保 CSV 所在的目录存在
        if self.stats_csv_path.parent != Path('.'):
            self.stats_csv_path.parent.mkdir(parents=True, exist_ok=True)

        # 确保 DB 所在的目录存在 (可选，视具体需求)
        if self.db_path.parent != Path('.'):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.csv_manager = DataCountRecorder(self.stats_csv_path)

        self.db_reader = JobDataReader(self.db_path)

        logger.info(f"训练数据统计器已初始化 | DB: {self.db_path} | Stats: {self.stats_csv_path}")

    def update_training_data_count(self):
        """
        从数据库获取最新统计，并更新到 CSV 日志中。
        """
        try:
            # 1. 从 DB 获取数据
            data = self.db_reader.get_stats()
            count = data.get('total', 0)

            # 2. 写入 CSV
            self.csv_manager.record_today(count)

            logger.info(f"已更新训练数据统计: Total={count}")
            return count
        except Exception as e:
            logger.error(f"更新训练数据统计失败: {e}")
            raise

    def update_training_data_count_by_handel(self, count: int):
        """
        从数据库获取最新统计，并更新到 CSV 日志中。
        """
        try:
            # 2. 写入 CSV
            self.csv_manager.record_today(count)

            logger.info(f"已更新训练数据统计: Total={count}")
            return count
        except Exception as e:
            logger.error(f"更新训练数据统计失败: {e}")
            raise

    def get_last_n_records(self, n: int = 5) -> List[Tuple[datetime, int]]:
        """
        获取最近 N 条统计记录。
        """
        return self.csv_manager.get_last_n_records(n)