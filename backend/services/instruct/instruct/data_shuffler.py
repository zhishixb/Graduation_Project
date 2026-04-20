import pandas as pd
from datasets import Dataset


class DataShuffler:
    """
    专门用于加载、清洗和打乱 CSV 数据的工具类
    """

    def __init__(self, csv_path, column_names):
        """
        初始化
        :param csv_path: CSV 文件路径
        :param column_names: 列名列表，例如 ['major_courses', 'cleaned_requirements']
        """
        self.csv_path = csv_path
        self.column_names = column_names
        self.df = None

    def load_and_shuffle(self, random_state=42):
        """
        执行全流程：加载 -> 清洗 -> 打乱 -> 转换为 HuggingFace Dataset
        :param random_state: 随机种子，保证结果可复现
        :return: datasets.Dataset 对象
        """
        print(f"📚 正在加载数据: {self.csv_path} ...")

        # 1. 读取 CSV
        # 假设 CSV 没有表头，如果原文件有表头，请去掉 header=None
        self.df = pd.read_csv(self.csv_path, header=None, names=self.column_names)

        # 2. 基础清洗
        # 删除包含空值的行 (防止训练报错)
        original_len = len(self.df)
        self.df = self.df.dropna()
        if len(self.df) < original_len:
            print(f"🧹 已清理 {original_len - len(self.df)} 条空值数据")

        # 3. 类型转换 (确保都是字符串)
        for col in self.column_names:
            self.df[col] = self.df[col].astype(str)

        # 4. 全局随机打乱 (核心功能)
        # frac=1 表示保留 100% 数据但打乱顺序
        self.df = self.df.sample(frac=1, random_state=random_state).reset_index(drop=True)

        print(f"✅ 数据已打乱并清洗完成！有效样本: {len(self.df)}")

        # 5. 转换为 HuggingFace Dataset 格式
        return Dataset.from_pandas(self.df)

    def preview(self, n=3):
        """
        预览前 N 行数据，用于检查
        """
        if self.df is not None:
            print(f"\n数据预览 (前 {n} 行):")
            print(self.df.head(n))
            print("-" * 30)