from pathlib import Path
from typing import Dict, Optional, Any

# ================= 模型注册表 (Model Registry) =================
# 格式: "逻辑名称": { "base": "基础模型路径", "lora": "适配器路径(可选)" }
# 路径建议使用绝对路径，或者相对于项目根目录的路径
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- 基准bge-small ---
    "bge_small_zh": {
        "base": "models/models/bge-small-zh-v1.5",
        "lora": None,
        "description": "BGE-Small-ZH 原始版，无微调"
    },

    # --- 测试用20*50参数-lora微调-bge-small ---
    "bge_small_zh_lora-20": {
        "base": "models/models/bge-small-zh-v1.5",
        "lora": "models/models_instruct/bge-lora-mnrl-output-20/adapter",
        "description": "BGE-Small-ZH 微调版，适用于专业-岗位语义匹配"
    },

    # --- 测试用50*50参数-lora微调-bge-small ---
    "bge_large_zh_lora-50": {
        "base": "models/models/bge-small-zh-v1.5",
        "lora": "models/models_instruct/bge-lora-mnrl-output-50/adapter",
        "description": "BGE-Large-ZH 微调版，精度更高但速度较慢"
    },

}

# 默认使用的模型配置键名
DEFAULT_MODEL_KEY = "bge_small_zh"