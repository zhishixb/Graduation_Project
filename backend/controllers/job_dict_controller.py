from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import datetime
from loguru import logger

from backend.services.process.count.position_data_count import PositionDataRecorder
from backend.services.process.count.training_data_count import TrainingDataRecorder
from backend.services.spider.platforms.job_51.private.major_spider.major_dictionary import MajorDictionary
from backend.services.spider.platforms.job_51.private.position_spider.job_dictionary import JobDictionary


class JobDictController:
    """
    职位字典数据控制器。
    职责：提供 HTTP 接口访问静态/动态更新的 JSON 字典数据。
    特点：无状态，每次请求独立实例化。
    """

    def get_full_major_dictionary(self) -> Dict[str, Any]:
        """
        获取完整的职位层级字典数据。

        :return: 包含数据的字典，格式为 {"success": True, "data": {...}} 或错误信息
        """
        try:
            storage = MajorDictionary()
            logger.info("正在读取专业字典数据...")
            data = storage.get_all_state()

            # 简单的数据校验
            if not isinstance(data, dict):
                logger.warning("读取到的数据格式非字典，返回空对象")
                return {"success": True, "data": {}}

            logger.success(f"成功读取职位字典，键数量: {len(data)}")
            return {
                "success": True,
                "data": data,
                "message": "获取成功"
            }

        except Exception as e:
            logger.exception(f"获取职位字典时发生未预期错误: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"服务器内部错误: {str(e)}"
            }

    def get_full_job_dictionary(self) -> Dict[str, Any]:
        """
        获取完整的职位层级字典数据。

        :return: 包含数据的字典，格式为 {"success": True, "data": {...}} 或错误信息
        """
        try:
            storage = JobDictionary()
            logger.info("正在读取职位字典数据...")
            data = storage.get_all_state()

            # 简单的数据校验
            if not isinstance(data, dict):
                logger.warning("读取到的数据格式非字典，返回空对象")
                return {"success": True, "data": {}}

            logger.success(f"成功读取职位字典，键数量: {len(data)}")
            return {
                "success": True,
                "data": data,
                "message": "获取成功"
            }

        except Exception as e:
            logger.exception(f"获取职位字典时发生未预期错误: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"服务器内部错误: {str(e)}"
            }


class SpiderDataCountController:

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.default_db_path = self.project_root / 'data' / 'db' / 'job_data.db'
        self.default_csv_path = self.project_root / 'data' / 'other' / 'training_data.csv'
        self.default_position_db_path = self.project_root / 'data' / 'db' / 'jobs.db'
        self.default_position_csv_path = self.project_root / 'data' / 'other' / 'position_data.csv'

        self.data_controller = TrainingDataRecorder(self.default_db_path, self.default_csv_path)
        self.position_controller = PositionDataRecorder(self.default_position_db_path, self.default_position_csv_path)

    def get_training_data_count(self) -> Dict[str, Any]:
        boss_csv_path = self.project_root / 'data' / 'other' / 'boss_data.csv'
        boss_csv_manager = TrainingDataRecorder(self.default_db_path, boss_csv_path)
        # 尝试手动写入
        result = boss_csv_manager.update_training_data_count_by_handel(23009)

        # 同样检查其他控制器
        self.data_controller.update_training_data_count()
        self.position_controller.update_from_database()  # 注意方法名

        data_1 = self.position_controller.get_last_n_records()
        data_2 = self.data_controller.get_last_n_records()
        data_3 = boss_csv_manager.get_last_n_records()

        print(f"Position records: {data_1}")

        return {
            "success": True,
            "message": "获取训练数据统计成功",
            "data": {
                "51position": data_1,
                "51job": data_2,
                "boss": data_3,
            }
        }