from pathlib import Path
from typing import Dict, Optional, Any

# ================= 模型注册表 (Model Registry) =================
# 格式: "逻辑名称": { "base": "基础模型路径", "lora": "适配器路径(可选)" }
# 路径建议使用绝对路径，或者相对于项目根目录的路径
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- 基准bge-small ---
    "bge_small": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": None,
        "description": "BGE-Small-ZH 原始版，无微调"
    },

    # --- 测试用20*50参数-lora微调-bge-small ---
    "bge_small_lora-20": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-lora-1k/adapter",
        "description": "BGE-Small-ZH 微调版，适用于专业-岗位语义匹配"
    },

    # --- 测试用50*50参数-lora微调-bge-small ---
    "bge_small_lora-50": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-lora-2.5k/adapter",
        "description": "BGE-Small-ZH 微调版，精度更高但速度较慢"
    },

    # --- 实际参数下-lora微调-bge-small-512 ---
    "bge_small_lora-512_old": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-512-old",
        "description": "GE-Small-ZH 微调版，batch=512"
    },

    # --- 实际参数下-lora微调-bge-small-256-3 ---
    "bge_small_lora-256-3": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-256-3",
        "description": "GE-Small-ZH 微调版，batch=256"
    },

    # --- 实际参数下-lora微调-bge-small-256-5 ---
    "bge_small_lora-256-5": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-256-5",
        "description": "GE-Small-ZH 微调版，batch=256"
    },

    # --- 实际参数下-lora微调-bge-small-256-10 ---
    "bge_small_lora-256-10": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-256-10",
        "description": "GE-Small-ZH 微调版，batch=256"
    },

    # --- 实际参数下-lora微调-bge-small-256-10 ---
    "bge_small_lora-256-20": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-256-20",
        "description": "GE-Small-ZH 微调版，batch=256"
    },

    # --- 实际参数下-lora微调-bge-small-512 ---
    "bge_small_lora-512-3": {
        "base": "models/bge_small/bge-small-zh-v1.5",
        "lora": "models/bge_small/bge-small-lora-512-3",
        "description": "GE-Small-ZH 微调版，batch=512"
    },


    # --- bge-m3 基座模型 ---
    "bge_m3": {
        "base": "models/bge_m3/bge-m3",
        "lora": None,
        "description": "BGE-M3 全量微调版，精度更高但速度较慢"
    },

    # --- 实际参数下-lora微调-bge-small-256 ---
    "bge_m3_lora-256-1": {
        "base": "models/bge_m3/bge-m3",
        "lora": "models/bge_m3/bge-m3-lora-256-1",
        "description": "GE-Small-ZH 微调版，batch=256，Epoch=1"
    },

    "bge_m3_lora-256-3": {
        "base": "models/bge_m3/bge-m3",
        "lora": "models/bge_m3/bge-m3-lora-256-3",
        "description": "GE-Small-ZH 微调版，batch=256，Epoch=3"
    },

    "bge_m3_lora-256-10": {
        "base": "models/bge_m3/bge-m3",
        "lora": "models/bge_m3/bge-m3-lora-256-10",
        "description": "GE-Small-ZH 微调版，batch=256，Epoch=10"
    },

    "bge_m3_lora-256-20": {
        "base": "models/bge_m3/bge-m3",
        "lora": "models/bge_m3/bge-m3-lora-256-20",
        "description": "GE-Small-ZH 微调版，batch=256，Epoch=20"
    },


}

# 默认使用的模型配置键名
DEFAULT_MODEL_KEY = "bge_small_zh"