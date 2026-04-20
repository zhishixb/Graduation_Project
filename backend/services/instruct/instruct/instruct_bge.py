import torch
import pandas as pd
import os
from sentence_transformers import SentenceTransformer, losses
from sentence_transformers.training_args import SentenceTransformerTrainingArguments
from sentence_transformers.trainer import SentenceTransformerTrainer
from peft import LoraConfig, TaskType, get_peft_model
from datasets import Dataset

# ================= 配置区域 =================
MODEL_NAME = "models/bge-small-zh-v1.5"
CSV_FILE_PATH = "data/train_90k.csv"  # 确保路径正确
OUTPUT_DIR = "models_instruct/bge-lora-90k-major-req"

# --- 针对 9万数据 + N260 的暴力参数 ---
NUM_EPOCHS = 1  # 9万条数据，1轮足矣
BATCH_SIZE = 256  # N260 64GB 显存拉满，Batch 越大效果越好
LEARNING_RATE = 1e-4
WARMUP_RATIO = 0.05

LORA_R = 16
LORA_ALPHA = 32
# ===========================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. 数据加载
print(f"🚀 正在加载全量数据：{CSV_FILE_PATH} ...")
# 修改点：指定列名为 major_courses 和 cleaned_requirements
df = pd.read_csv(CSV_FILE_PATH, header=None, names=['major_courses', 'cleaned_requirements'])

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# 简单的清洗：确保没有 NaN 值，防止训练报错
df = df.dropna()
# 确保是字符串格式
df['major_courses'] = df['major_courses'].astype(str)
df['cleaned_requirements'] = df['cleaned_requirements'].astype(str)

train_dataset = Dataset.from_pandas(df)

print(f"✅ 数据已打乱并加载完成！总样本数: {len(train_dataset)}")
print(f"   前8行专业预览: {df.iloc[:8]['major_courses'].tolist()}")

# 2. 加载模型
print("🤖 正在加载模型...")
model = SentenceTransformer(MODEL_NAME)

# 3. 注入 LoRA
print("🔧 注入 LoRA...")
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["query", "value"],
    task_type=TaskType.FEATURE_EXTRACTION,
    lora_dropout=0.05,
    bias="none",
)

base_auto_model = model._modules["0"].auto_model
model._modules["0"].auto_model = get_peft_model(base_auto_model, lora_config)

print("📊 可训练参数统计:")
model._modules["0"].auto_model.print_trainable_parameters()

# 4. 损失函数
train_loss = losses.MultipleNegativesRankingLoss(model)

# 5. 训练参数
args = SentenceTransformerTrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,

    # N260 性能核心
    fp16=True,
    dataloader_num_workers=4,
    dataloader_pin_memory=True,

    # 优化策略
    learning_rate=LEARNING_RATE,
    warmup_ratio=WARMUP_RATIO,
    optim="adamw_torch",

    # 保存策略
    save_strategy="no",  # 9万数据跑完也就几分钟，直接不保存中间态，最后一次性保存
    logging_steps=50,  # 每 50 步打印一次 Loss

    report_to="none",
    remove_unused_columns=False,
)

# 6. 初始化 Trainer
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    loss=train_loss,
)

# 7. 开始训练
print("🔥 开始全量微调 (N260 暴力计算中)...")
trainer.train()

# 8. 保存
adapter_path = os.path.join(OUTPUT_DIR, "adapter")
print(f"💾 保存适配器至: {adapter_path}")
model._modules["0"].auto_model.save_pretrained(adapter_path)
print("✅ 训练完成！")