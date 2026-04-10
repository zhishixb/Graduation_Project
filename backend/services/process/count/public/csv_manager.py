import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Union


class DataCountRecorder:
    """
    用于记录和读取 'data,count' 格式的 CSV 文件。
    特性：写入时自动检查日期，若今日已有记录则更新，否则新增。
    """

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path('.'):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_today_str(self) -> str:
        """获取当前日期的字符串格式 (YYYY-MM-DD)"""
        return datetime.now().strftime('%Y-%m-%d')

    def _read_last_line(self) -> Optional[Tuple[str, int]]:
        """读取文件的最后一行数据"""
        if not self.file_path.exists():
            return None

        try:
            with self.file_path.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                last_row = None
                for row in reader:
                    if len(row) >= 2:
                        last_row = row
                if last_row:
                    return last_row[0], int(last_row[1])
                return None
        except Exception:
            return None

    def _rewrite_file_with_updated_last(self, new_count: int):
        """重写整个文件，更新最后一行的 count"""
        if not self.file_path.exists():
            return

        rows = []
        with self.file_path.open('r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                rows.append(header)
            all_data_rows = list(reader)

        if not all_data_rows:
            return

        last_row = all_data_rows[-1]
        if len(last_row) >= 2:
            last_row[1] = str(new_count)
            rows.extend(all_data_rows)
            with self.file_path.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)

    def record_today(self, count: int):
        """记录今天的数据（同天更新，不同天追加）"""
        today_str = self._get_today_str()
        last_record = self._read_last_line()

        if last_record:
            last_date, _ = last_record
            if last_date == today_str:
                self._rewrite_file_with_updated_last(count)
                return

        write_header = not self.file_path.exists() or self.file_path.stat().st_size == 0
        mode = 'w' if not self.file_path.exists() else 'a'

        with self.file_path.open(mode, encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(['data', 'count'])
            writer.writerow([today_str, count])

    def read_all(self) -> List[Tuple[datetime, int]]:
        """读取所有记录并解析"""
        if not self.file_path.exists():
            return []

        results = []
        with self.file_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date_obj = datetime.strptime(row['data'], '%Y-%m-%d')
                    count_val = int(row['count'])
                    results.append((date_obj, count_val))
                except (ValueError, KeyError):
                    continue

        results.sort(key=lambda x: x[0])
        return results

    def get_latest_record(self) -> Optional[Tuple[datetime, int]]:
        """获取最后一条记录"""
        all_data = self.read_all()
        return all_data[-1] if all_data else None

    def get_last_n_records(self, n: int = 5) -> List[Tuple[datetime, int]]:
        """
        获取文件中最后的 N 条数据。

        :param n: 需要获取的记录数量，默认为 5
        :return: 列表 [(datetime, count), ...]，按时间正序排列
        """
        all_data = self.read_all()
        if not all_data:
            return []

        # 切片获取最后 N 条
        # 如果总数少于 N，则返回全部
        return all_data[-n:]