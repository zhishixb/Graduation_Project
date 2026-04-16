# batch_matcher.py
import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from loguru import logger
from tqdm import tqdm

from backend.services.instruct.compare.training_data_check.model_check import SingleModelMatcher
from backend.services.process.check.training_data_load import CsvRowReader


def _process_chunk(chunk_data: Tuple[int, List[Dict[str, str]], str]) -> List[Tuple[int, float]]:
    """
    模块级函数，多进程处理一个数据块。
    :param chunk_data: (start_index, chunk_rows, model_key)
    :return: [(original_index, score), ...]
    """
    start_idx, rows, model_key = chunk_data
    matcher = SingleModelMatcher(model_key)   # 每个进程独立加载模型
    results = []
    for i, row in enumerate(rows):
        text1 = row.get("major_courses", "")
        text2 = row.get("cleaned_requirements", "")
        if not text1 or not text2:
            score = 0.0
        else:
            try:
                score = matcher.predict(text1, text2)
            except Exception as e:
                logger.error(f"计算失败 (行 {start_idx + i}): {e}")
                score = 0.0
        results.append((start_idx + i, score))
    return results


class BatchSimilarityCalculator:
    """
    多进程批量计算 CSV 中专业描述与岗位描述的相似度，并统计分布。
    """

    def __init__(self, model_key: str, csv_path: Path, num_workers: int = 4):
        """
        :param model_key: 注册表中的模型名称
        :param csv_path: 输入 CSV 路径（表头: major_courses, cleaned_requirements）
        :param num_workers: 并行进程数
        """
        self.model_key = model_key
        self.csv_path = csv_path
        self.num_workers = num_workers

        # 读取所有数据
        reader = CsvRowReader(csv_path)
        self.rows = reader.all_rows()
        self.total = len(self.rows)
        logger.info(f"已加载 {self.total} 条记录，将使用 {num_workers} 个进程计算相似度")

    def run(self, output_csv: Path = None) -> Dict[str, Any]:
        """
        执行批量计算并统计。
        :param output_csv: 可选，输出结果 CSV 路径（追加 similarity 列）
        :return: 统计字典
        """
        if self.total == 0:
            logger.warning("CSV 文件为空")
            return {"total": 0, "low_count": 0, "high_count": 0, "low_percent": 0.0, "high_percent": 0.0}

        # 1. 数据分块
        chunk_size = max(1, self.total // self.num_workers)
        chunks = []
        for i in range(0, self.total, chunk_size):
            chunk_rows = self.rows[i:i + chunk_size]
            chunks.append((i, chunk_rows, self.model_key))

        # 2. 多进程执行
        all_scores = [0.0] * self.total   # 预分配，按索引填充
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(_process_chunk, chunk) for chunk in chunks]
            for future in tqdm(futures, desc="计算相似度", unit="块"):
                chunk_results = future.result()
                for idx, score in chunk_results:
                    all_scores[idx] = score

        # 3. 统计
        low_count = sum(1 for s in all_scores if s < 0.3)
        high_count = self.total - low_count
        low_percent = (low_count / self.total) * 100
        high_percent = (high_count / self.total) * 100

        stats = {
            "total": self.total,
            "low_count": low_count,
            "high_count": high_count,
            "low_percent": round(low_percent, 2),
            "high_percent": round(high_percent, 2),
        }

        logger.success(f"统计完成: 低分(<0.3) {low_count} 条 ({low_percent:.2f}%), 高分(≥0.3) {high_count} 条 ({high_percent:.2f}%)")

        # 4. 可选输出结果 CSV
        if output_csv:
            self._save_results(output_csv, all_scores)

        return stats

    def _save_results(self, output_path: Path, scores: List[float]):
        """将原始行和相似度分数写入新 CSV"""
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['major_courses', 'cleaned_requirements', 'similarity'])
            for row, score in zip(self.rows, scores):
                writer.writerow([row['major_courses'], row['cleaned_requirements'], score])
        logger.info(f"结果已保存至: {output_path}")


# 使用示例
if __name__ == "__main__":
    calculator = BatchSimilarityCalculator(
        model_key="your_model_key",           # 替换为实际模型 key
        csv_path=Path("data/cleaned_output.csv"),
        num_workers=4
    )
    stats = calculator.run(output_csv=Path("data/similarity_scores.csv"))
    print(stats)