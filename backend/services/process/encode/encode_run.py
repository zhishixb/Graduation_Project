from pathlib import Path

from backend.services.process.encode.csv_load import load_cleaned_csv_to_memory
from backend.services.process.encode.model_encoder import BGE_M3_Encoder

if __name__ == "__main__":
    # 路径配置（请根据实际情况修改）
    project_root = Path.cwd().parent
    MODEL_PATH = project_root / "models" / "bge_m3" / "bge-m3"
    LORA_PATH = project_root / "models" / "bge_m3" / "bge_m3_adapter_v1" / "adapter"
    CLEANED_CSV_PATH = Path.cwd() / "cleaned_twice_all_jobs.csv"
    OUTPUT_EMBEDDING_CSV = Path.cwd() / "job_embeddings.csv"

    # 步骤1: 加载清洗数据
    jobs = load_cleaned_csv_to_memory(CLEANED_CSV_PATH, as_objects=True)
    print(f"加载了 {len(jobs)} 条清洗数据")

    # 步骤2: 初始化编码器
    encoder = BGE_M3_Encoder(
        model_path=MODEL_PATH,
        lora_adapter_path=LORA_PATH,
        device='cuda',          # 若无 GPU 可改为 'cpu'
        batch_size=512,
        max_length=512
    )
    # 输出当前运行模式
    print(f"当前运行模式: {encoder.device.upper()} ({'GPU' if encoder.device == 'cuda' else 'CPU'})")

    # 步骤3: 编码并保存
    encoder.process_jobs_to_csv(jobs, OUTPUT_EMBEDDING_CSV, embedding_sep=' ')