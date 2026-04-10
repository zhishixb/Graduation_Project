from pathlib import Path


class FlagFile:
    def __init__(self, path: Path):
        self.path = Path(path)

    def write(self, val: int) -> None:
        if val not in (0, 1):
            raise ValueError("只允许0或1")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(val))

    def read(self) -> int:
        content = self.path.read_text().strip()
        val = int(content)
        if val not in (0, 1):
            raise ValueError("文件内容不是0或1")
        return val


# 使用
flag = FlagFile(Path("./flag.txt"))
flag.write(1)
print(flag.read())  # 输出: 1