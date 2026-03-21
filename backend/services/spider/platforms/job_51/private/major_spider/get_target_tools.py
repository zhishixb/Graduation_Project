import math
from typing import List, Tuple

# 定义基准值
BASE_VALUE = 300


def get_geometric_probabilities(
        items: List[str],
        ratio: float = 0.7
) -> List[Tuple[str, int]]:
    """
    计算几何分布权重值（向上取整为整数）。
    越靠前的元素权重越高，按 ratio 指数递减。

    计算公式：value = ceil( (ratio^i / sum(ratio^k)) * BASE_VALUE )

    :param items: 元素列表
    :param ratio: 衰减比率 (0 < ratio <= 1)，默认 0.7
    :return: List[Tuple[str, int]]
             例如: [('财务', 130), ('银行', 91), ...]
             注意：由于向上取整，所有值的总和通常会 > BASE_VALUE (300)
    """
    n = len(items)
    if n == 0:
        return []
    if n == 1:
        # 如果只有一个元素，概率为 1.0，直接返回基准值 (int)
        return [(items[0], int(BASE_VALUE))]

    if not (0 < ratio <= 1):
        raise ValueError("Ratio must be between 0 and 1")

    # 1. 计算原始几何权重: [1, ratio, ratio^2, ...]
    weights = [ratio ** i for i in range(n)]

    # 2. 计算权重总和用于归一化
    total_weight = sum(weights)

    # 3. 计算最终值并向上取整
    result: List[Tuple[str, int]] = []
    for item, w in zip(items, weights):
        # 计算理论浮点值
        raw_value = (w / total_weight) * BASE_VALUE

        # 向上取整并转换为 int
        final_value = int(math.ceil(raw_value))

        result.append((item, final_value))

    return result


def normalize_weights(weights: List[float]) -> List[float]:
    """辅助方法：归一化权重列表"""
    total = sum(weights)
    return [w / total for w in weights] if total > 0 else weights