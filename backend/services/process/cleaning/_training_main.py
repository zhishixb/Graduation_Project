import os
import shutil
from pathlib import Path
from c2net.context import prepare

# 确保导入路径正确
from training_data_cleaner import TrainingDataCleaner


def run_pipeline_on_openi():
    # 1. 初始化 OpenI 上下文
    print("⏳ 正在初始化 OpenI 上下文...")
    c2net_context = prepare()

    # --- 配置路径 ---

    # A. 获取挂载的只读源路径 (仅数据库)
    source_db_path = Path(c2net_context.dataset_path) / "job_data" / "job_data.db"

    # B. 获取本地已上传的源路径 (CSV 和 JSON)
    source_csv_path = Path.cwd() / "major_data.csv"
    source_json_path = Path.cwd() / "51job_major_status.json"

    # C. 定义容器内的可写工作路径
    work_dir = Path("/tmp/work")
    work_dir.mkdir(exist_ok=True)

    local_db_path = work_dir / "job_data.db"
    local_major_csv_path = work_dir / "major_data.csv"
    local_major_status_json_path = work_dir / "51job_major_status.json"
    output_csv_path = work_dir / "cleaned_output.csv"
    output_major_csv_path = output_csv_path.with_stem(output_csv_path.stem + "_major")  # cleaned_output_major.csv

    # 2. 预处理：复制文件到可写目录
    print(f"📂 正在准备文件...")

    # --- 复制数据库 ---
    if not source_db_path.exists():
        print(f"❌ 错误：找不到数据库文件 {source_db_path}")
        return
    shutil.copy(source_db_path, local_db_path)
    print(f"✅ 数据库已就位: {local_db_path}")

    # --- 复制 CSV ---
    if not source_csv_path.exists():
        print(f"❌ 错误：找不到 CSV 文件 {source_csv_path}")
        return
    shutil.copy(source_csv_path, local_major_csv_path)
    print(f"✅ CSV 已就位: {local_major_csv_path}")

    if not source_json_path.exists():
        print(f"❌ 错误：找不到 JSON 文件 {source_json_path}")
        return
    shutil.copy(source_json_path, local_major_status_json_path)
    print(f"✅ JSON 已就位: {local_major_status_json_path}")

    # 3. 清除旧的输出文件（两个 CSV）
    for f in [output_csv_path, output_major_csv_path]:
        if f.exists():
            f.unlink()
            print(f"🧹 发现旧的输出文件，已清除: {f}")

    try:
        print(f"⚙️ 初始化清洗器...")
        cleaner = TrainingDataCleaner(
            db_path=local_db_path,
            csv_path=output_csv_path,
            major_csv_path=local_major_csv_path,
            subject_csv_path=local_major_status_json_path
        )

        print("🚀 开始多线程清洗任务 (内存预加载模式)...")
        count = cleaner.clean_training_data_in_memory(max_workers=4)
        print(f"🎉 任务结束！成功处理了 {count} 条数据。")

        # 4. 将结果复制回当前目录，方便查看和下载
        if output_csv_path.exists():
            final_result = Path.cwd() / "cleaned_output.csv"
            shutil.copy(output_csv_path, final_result)
            print(f"📥 结果已保存到当前目录: {final_result}")

        if output_major_csv_path.exists():
            final_major_result = Path.cwd() / "cleaned_output_major.csv"
            shutil.copy(output_major_csv_path, final_major_result)
            print(f"📥 结果已保存到当前目录: {final_major_result}")

        # 打印最终统计
        stats = cleaner.db_manager.get_stats()
        print(f"📊 数据库最终状态 -> 总数:{stats['total']}, 已完成:{stats['processed']}")

    except Exception as e:
        print(f"❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_pipeline_on_openi()