import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Union, Optional

from loguru import logger

from backend.services.process.cleaning.job.job.position_data_reader import PositionDataReader
from backend.services.process.count.public.csv_manager import DataCountRecorder


class PositionDataRecorder:
    """
    训练数据统计协调器。
    负责协调 数据库(JobDataReader) 和 统计日志(DataCountRecorder)。
    """

    def __init__(self, db_path: Union[str, Path], stats_csv_path: Union[str, Path]):
        """
        :param db_path: 业务数据库文件路径 (.db)
        :param stats_csv_path: 统计日志文件路径 (.csv)
        """
        self.db_path = Path(db_path)
        self.stats_csv_path = Path(stats_csv_path)

        # 确保目录存在
        self.stats_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.csv_manager = DataCountRecorder(self.stats_csv_path)
        self.db_reader = PositionDataReader(self.db_path)

        logger.info(f"训练数据统计器已初始化 | DB: {self.db_path} | Stats: {self.stats_csv_path}")

    def update_from_database(self) -> Optional[int]:
        """
        从数据库获取最新统计，并更新到 CSV 日志中。

        :return: 更新的数量，失败返回 None
        """
        try:
            # 1. 从 DB 获取数据
            data = self.db_reader.get_stats()

            # 2. 验证数据
            if not data or 'total' not in data:
                logger.error(f"数据库返回无效统计信息: {data}")
                return None

            count = data.get('total', 0)

            # 3. 验证数量的合理性
            if not isinstance(count, int) or count < 0:
                logger.error(f"无效的数据量: {count}")
                return None

            # 4. 写入 CSV
            self.csv_manager.record_today(count)

            logger.info(f"已更新训练数据统计: Total={count}")
            return count

        except Exception as e:
            logger.error(f"从数据库更新统计失败: {e}")
            return None
        finally:
            # 确保关闭数据库连接
            if hasattr(self.db_reader, 'disconnect'):
                self.db_reader.disconnect()

    def update_with_count(self, count: int) -> bool:
        """
        手动指定数量并更新到 CSV 日志中。

        :param count: 要记录的数据量
        :return: 是否更新成功
        """
        try:
            # 验证数量
            if not isinstance(count, int) or count < 0:
                logger.error(f"无效的数据量: {count}")
                return False

            # 写入 CSV
            self.csv_manager.record_today(count)

            logger.info(f"已手动更新训练数据统计: Total={count}")
            return True

        except Exception as e:
            logger.error(f"手动更新训练数据统计失败: {e}")
            return False

    def get_last_n_records(self, n: int = 5) -> List[Tuple[datetime, int]]:
        """
        获取最近 N 条统计记录。

        :param n: 要获取的记录数量
        :return: 记录列表
        """
        if n <= 0:
            logger.warning(f"请求的记录数量无效: {n}")
            return []

        return self.csv_manager.get_last_n_records(n)

    def get_latest_record(self) -> Optional[Tuple[datetime, int]]:
        """
        获取最新的统计记录。

        :return: 最新记录或 None
        """
        return self.csv_manager.get_latest_record()

    def get_all_records(self) -> List[Tuple[datetime, int]]:
        """
        获取所有统计记录。

        :return: 所有记录列表
        """
        return self.csv_manager.read_all()