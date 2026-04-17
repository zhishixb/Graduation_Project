import csv
import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer


class MajorEmbedder:
    """
    读取专业数据 CSV，使用指定模型将“专业介绍”文本向量化，
    并将专业名称与向量（逗号分隔的浮点数）写入新 CSV 文件。
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: Optional[str] = None):
        """
        :param model_name: Hugging Face 模型名称或本地路径
        :param device: 运行设备，None 时自动选择 GPU/CPU
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name, device=self.device)
        print(f"模型已加载: {model_name}, 设备: {self.device}")

    def encode_texts(self, texts: List[str], batch_size: int = 32, normalize: bool = True) -> np.ndarray:
        """
        批量编码文本，返回归一化的嵌入向量（numpy 数组）。
        :param texts: 待编码文本列表
        :param batch_size: 批处理大小
        :param normalize: 是否对输出向量进行 L2 归一化
        :return: shape (len(texts), embedding_dim)
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=True,
            convert_to_numpy=True
        )

    def process_csv(
        self,
        input_csv: Path,
        output_csv: Path,
        name_column: str = "专业名称",
        text_column: str = "专业介绍",
        batch_size: int = 32
    ) -> int:
        """
        读取输入 CSV，对专业介绍进行向量化，写入输出 CSV。
        :param input_csv: 输入文件路径（包含“专业名称”和“专业介绍”列）
        :param output_csv: 输出文件路径（包含“专业名称”和“向量”列）
        :param name_column: 专业名称列名
        :param text_column: 专业介绍列名
        :param batch_size: 编码时的批大小
        :return: 成功处理的行数
        """
        # 1. 读取数据
        rows = []
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get(name_column, "").strip()
                desc = row.get(text_column, "").strip()
                if name and desc:
                    rows.append((name, desc))
        if not rows:
            print("警告：没有找到有效数据（专业名称和介绍均非空）")
            return 0

        names, texts = zip(*rows)
        print(f"已加载 {len(rows)} 条专业记录，开始向量化...")

        # 2. 批量编码
        embeddings = self.encode_texts(list(texts), batch_size=batch_size)

        # 3. 写入输出 CSV
        with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['专业名称', '向量'])
            for name, emb in zip(names, embeddings):
                # 将 numpy 数组转为逗号分隔的字符串
                vector_str = ','.join(map(str, emb))
                writer.writerow([name, vector_str])

        print(f"向量化完成，结果已保存至: {output_csv}")
        return len(rows)


# 使用示例
if __name__ == "__main__":
    embedder = MajorEmbedder()
    embedder.process_csv(
        input_csv=Path("major_data.csv"),
        output_csv=Path("major_embeddings.csv"),
        batch_size=64
    )