from pathlib import Path
from loguru import logger
from typing import Dict, Any, Optional

from backend.services.process.cleaning.major_clean import MajorCleaner


class CleanDataController:

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.default_db_path = self.project_root / 'data' / 'db' / 'majors.db'
        self.default_csv_path = self.project_root / 'data' / 'csv' / 'major_data.csv'

    def is_majors_cleand(self,
            db_path: Optional[Path] = None,
            output_csv_path: Optional[Path] = None):

        target_db = db_path if db_path else self.default_db_path
        target_csv = output_csv_path if output_csv_path else self.default_csv_path

        # 1. 基础预检 (文件是否存在)
        if not target_db.exists():
            logger.error(f"数据库文件不存在：{target_db}")
            return {
                "success": False,
                "data": None,
                "message": f"数据库文件不存在：{target_db}"
            }

        try:
            # 2. 实例化并运行
            cleaner = MajorCleaner(db_path=target_db, output_csv_path=target_csv)
            is_completed = cleaner.is_processing_complete()
            if is_completed:
                return {
                    "success": True,
                    "data": "",
                    "message": f"数据清洗已完成"
                }
            else:
                return {
                    "success": True,  # 接口调用成功，只是业务上没做完
                    "data": "",
                    "message": f"数据清洗未完成"
                }
        except Exception as e:
            logger.error(f"❌ 检查清洗状态时发生错误：{e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "message": f"检查状态失败：{str(e)}"
            }



    def clean_major_data(
            self,
            db_path: Optional[Path] = None,
            output_csv_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        调用 MajorCleaner 并返回标准 JSON 结构：
        {
            "success": bool,
            "data": dict | None,  # 成功时有统计数据，失败时为 None
            "message": str        # 成功时为成功提示，失败时为错误信息
        }
        """
        target_db = db_path if db_path else self.default_db_path
        target_csv = output_csv_path if output_csv_path else self.default_csv_path

        # 1. 基础预检 (文件是否存在)
        if not target_db.exists():
            return {
                "success": False,
                "data": None,
                "message": f"数据库文件不存在：{target_db}"
            }

        try:
            # 2. 实例化并运行
            cleaner = MajorCleaner(db_path=target_db, output_csv_path=target_csv)

            # 获取结果元组 (success_flag, error_msg)
            success_flag, error_msg = cleaner.run()

            # 3. 根据返回值组装 JSON
            if success_flag:
                # ✅ 成功情况
                stats = cleaner.stats
                return {
                    "success": True,
                    "data": {
                        "processed_count": stats["processed"],
                        "error_count": stats["errors"],
                        "output_file": str(target_csv),
                        "database_file": str(target_db)
                    },
                    "message": f"处理完成。成功 {stats['processed']} 条，错误 {stats['errors']} 条。"
                }
            else:
                # ❌ 失败情况 (MajorCleaner 返回了 False)
                # data 置空，message 传递错误信息
                return {
                    "success": False,
                    "data": None,
                    "message": error_msg if error_msg else "未知错误，请查看日志"
                }

        except Exception as e:
            # 🛡️ 兜底捕获控制器层面的异常 (理论上很少发生，因为 MajorCleaner 已经捕获了大部分)
            logger.critical(f"💥 控制器层捕获未预期异常：{e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "message": f"系统内部错误：{str(e)}"
            }