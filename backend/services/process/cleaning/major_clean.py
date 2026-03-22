from pathlib import Path
from loguru import logger
from typing import Dict, Any, Tuple
import time
import csv

from backend.services.process.cleaning.major.dao import MajorDatabaseManager
from backend.services.process.cleaning.major.major_course_parser import MedicalMajorExtractor
from backend.services.process.cleaning.major.major_description_parser import MajorDescriptionParser


class MajorCleaner:
    def __init__(self, db_path: Path, output_csv_path: Path):
        self.db_path = db_path
        self.output_csv_path = output_csv_path

        # 初始化组件
        self.db_manager = MajorDatabaseManager(self.db_path)
        self.parser = MajorDescriptionParser()
        self.medical_extractor = MedicalMajorExtractor()

        # 统计字典
        self.stats = {
            "processed": 0,
            "errors": 0,
            "skipped": 0
        }

    def is_processing_complete(self) -> bool:
        """检查是否所有数据都已处理完毕（仅用于内部逻辑或额外检查，不影响 run 返回）"""
        try:
            count = self.db_manager.get_major_count(only_pending=True)
            return count == 0
        except Exception:
            return False

    def _combine_texts(self, record: Dict[str, Any]) -> str:
        learn_what = record.get('learn_what') or ""
        is_what = record.get('is_what') or ""

        try:
            medical_data = self.medical_extractor.extract_all(learn_what)
            courses = medical_data.get('courses', []) if medical_data else []
            directions = medical_data.get('directions', []) if medical_data else []
        except Exception as e:
            logger.warning(f"⚠️ 提取课程/方向失败 (ID: {record.get('special_id')}): {e}")
            courses, directions = [], []

        cleaned_is_what = self.parser.clean(is_what)
        parts = []

        if courses:
            parts.append("主要课程：" + "、".join(courses))
        if directions:
            parts.append("培养方向：" + "、".join(directions))
        if cleaned_is_what:
            parts.append("专业描述：" + cleaned_is_what)

        if not parts:
            return f"原始信息：{learn_what[:50]}..." if learn_what else "无详细信息"

        return "; ".join(parts)

    def run(self) -> Tuple[bool, str]:
        """
        执行清洗任务。

        Returns:
            Tuple[bool, str]:
                - 成功: (True, "")
                - 失败: (False, "错误原因字符串")
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("🚀 开始构建映射表 (带断点续传模式)")
        logger.info(f"📂 数据库：{self.db_path}")
        logger.info(f"💾 输出文件：{self.output_csv_path}")
        logger.info("=" * 60)

        try:
            self.db_manager.reset_processed_results()

            # 1. 统计待处理数量
            pending_count = self.db_manager.get_major_count(only_pending=True)

            if pending_count == 0:
                logger.success("✅ 所有数据均已处理完毕，无需重新运行。")
                # 即使没干活，也算成功执行
                return True, ""

            logger.info(f"📊 检测到 {pending_count} 条待处理数据。")

            # 确保输出目录存在
            self.output_csv_path.parent.mkdir(parents=True, exist_ok=True)
            file_exists = self.output_csv_path.exists()

            # 2. 执行写入逻辑
            with open(self.output_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['name', 'combined_text']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                for record in self.db_manager.stream_majors():
                    special_id = record.get('special_id')
                    name = record.get('name', 'Unknown')

                    try:
                        combined_text = self._combine_texts(record)

                        writer.writerow({
                            'name': name,
                            'combined_text': combined_text
                        })

                        status_mark = "MAPPING_GENERATED_" + time.strftime("%Y-%m-%d")
                        success = self.db_manager.update_skills_result(special_id, status_mark)

                        if success:
                            self.stats["processed"] += 1
                        else:
                            logger.warning(f"⚠️ 无法更新数据库状态 ID: {special_id}")
                            self.stats["errors"] += 1
                            continue

                        if self.stats["processed"] % 50 == 0:
                            logger.info(f"⏳ 已处理并保存 {self.stats['processed']} 条...")

                    except Exception as e:
                        logger.error(f"❌ 处理专业 '{name}' (ID: {special_id}) 时发生异常: {e}", exc_info=True)
                        self.stats["errors"] += 1
                        continue

            elapsed = time.time() - start_time
            logger.success("=" * 60)
            logger.success("✅ 映射表构建完成！")
            logger.success(f"📈 本次新增处理：{self.stats['processed']} 条")
            logger.success(f"⚠️ 遇到错误：{self.stats['errors']} 条")
            logger.success(f"⏱️ 总耗时：{elapsed:.2f} 秒")
            logger.success("=" * 60)

            # 正常结束，返回成功
            return True, ""

        except FileNotFoundError as e:
            err_msg = f"文件未找到：{str(e)}"
            logger.critical(f"💥 {err_msg}")
            return False, err_msg

        except PermissionError as e:
            err_msg = f"权限不足，无法访问文件或数据库：{str(e)}"
            logger.critical(f"💥 {err_msg}")
            return False, err_msg

        except Exception as e:
            # 捕获所有其他未预期异常
            err_msg = f"程序执行严重错误：{str(e)}"
            logger.critical(f"💥 {err_msg}", exc_info=True)
            return False, err_msg