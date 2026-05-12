import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

def load_job_data(db_path: Path) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """
    从 SQLite 数据库的 position_jobs 表中读取所有记录的 job_id, function, job_description，
    并返回列表，每个元素为 (job_id, function, job_description) 三元组。
    """
    conn = sqlite3.connect(db_path)  # Path 对象可直接使用
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, function, job_description FROM position_jobs")
    rows = cursor.fetchall()
    conn.close()
    return rows