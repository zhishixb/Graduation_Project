from pathlib import Path
import numpy as np

from backend.services.instruct.match.vector_retriever import VectorRetriever
from backend.services.instruct.match.db_manager import DatabaseManager

def compute_and_store_similarity():
    # 1. 初始化向量检索器
    vector_retriever = VectorRetriever(
        job_npy_path=Path("job_vectors.npy"),
        job_json_path=Path("job_vectors.json"),
        major_npy_path=Path("major_vectors.npy"),
        major_json_path=Path("major_vectors.json")
    )

    # 2. 获取每个岗位类别的平均向量（字典：岗位名 → 向量）
    average_vector = vector_retriever.get_function_centroids()  # Dict[str, np.ndarray]

    # 3. 准备岗位矩阵
    function_names = list(average_vector.keys())  # 岗位名称列表，长度 M
    if not function_names:
        print("未找到任何岗位数据，退出")
        return
    function_vectors = np.array([average_vector[name] for name in function_names])  # shape (M, D)

    # 4. 获取专业矩阵和名称列表
    major_vectors = vector_retriever.major_embeddings  # shape (K, D)
    major_names = vector_retriever.major_list  # 专业名称列表，长度 K

    print(f"岗位数量: {len(function_names)}, 专业数量: {len(major_names)}")

    # 5. 计算相似度矩阵（余弦相似度，因向量已L2归一化，点积即为余弦）
    similarity_matrix = np.dot(function_vectors, major_vectors.T)  # shape (M, K)
    # 确保数值在 [-1, 1] 范围内（浮点误差可能导致微小超出）
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    # 6. 存储到 SQLite 数据库
    db_path = Path("job_major_similarity.db")
    db = DatabaseManager(db_path)
    db.create_table()

    # 准备批量数据 (function_name, major_name, similarity)
    batch_size = 100000  # 可选：分批插入，避免一次内存占用过大（实际百万条数据一次性也可以）
    total_pairs = len(function_names) * len(major_names)
    print(f"总相似度对: {total_pairs}, 开始写入数据库...")

    data_batch = []
    for i, func in enumerate(function_names):
        row = similarity_matrix[i]
        for j, major in enumerate(major_names):
            data_batch.append((func, major, float(row[j])))
            # 每积累 batch_size 条就插入一次并清空
            if len(data_batch) >= batch_size:
                db.insert_batch(data_batch)
                data_batch.clear()
    # 插入剩余数据
    if data_batch:
        db.insert_batch(data_batch)

    db.close()
    print(f"相似度计算完成并已保存至 {db_path}")


if __name__ == "__main__":
    compute_and_store_similarity()