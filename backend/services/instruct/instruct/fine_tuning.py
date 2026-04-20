import torch
import pandas as pd
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer, losses
from sentence_transformers.training_args import SentenceTransformerTrainingArguments
from sentence_transformers.trainer import SentenceTransformerTrainer
from datasets import Dataset

# ================= 配置区域 =================
project_root = Path.cwd().parent
MODEL_NAME = str(project_root / "models" / "bge-small-zh-v1.5")
CSV_FILE_PATH = str(project_root / "instruct" / "cleaned_output.csv")
OUTPUT_DIR = str(project_root / "models" / "bge_small_finetuned_full")

# --- 全量微调参数建议 ---
NUM_EPOCHS = 1          # 9万数据，1轮足矣，多了容易过拟合
BATCH_SIZE = 128        # 全量微调显存占用比LoRA大，但N260有64G，128很安全
LEARNING_RATE = 2e-5    # 【关键】全量微调通常用较小的学习率 (1e-5 ~ 5e-5)
WARMUP_RATIO = 0.05
# ===========================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. 数据加载 (保持不变)
print(f"🚀 正在加载全量数据：{CSV_FILE_PATH} ...")
df = pd.read_csv(CSV_FILE_PATH, header=None, names=['major_courses', 'cleaned_requirements'])
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df = df.dropna()
df['major_courses'] = df['major_courses'].astype(str)
df['cleaned_requirements'] = df['cleaned_requirements'].astype(str)

train_dataset = Dataset.from_pandas(df)
print(f"✅ 数据已打乱并加载完成！总样本数: {len(train_dataset)}")

# 2. 加载模型 (保持不变)
print("🤖 正在加载模型...")
model = SentenceTransformer(MODEL_NAME)

# ================= 核心修改点 =================
# 3. 移除 LoRA 注入代码
# 全量微调不需要 LoraConfig, get_peft_model 等
# 直接使用原始 model 即可
print("⚡ 已跳过 LoRA 注入，准备进行全量参数更新...")
# =============================================

# 4. 损失函数 (保持不变)
train_loss = losses.MultipleNegativesRankingLoss(model)

# 5. 训练参数
args = SentenceTransformerTrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,

    # N260 性能核心
    fp16=True,            # 必须开启，节省显存并加速
    dataloader_num_workers=4,
    dataloader_pin_memory=True,

    # 优化策略
    learning_rate=LEARNING_RATE, # 使用较小的学习率
    warmup_ratio=WARMUP_RATIO,
    optim="adamw_torch",

    # 保存策略
    save_strategy="no",   # 跑完直接存
    logging_steps=50,

    report_to="none",
    remove_unused_columns=False,
)

# 6. 初始化 Trainer (保持不变)
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    loss=train_loss,
)

# 7. 开始训练
print("🔥 开始全量微调 (正在重塑模型权重)...")
trainer.train()

# 8. 保存 (直接保存整个模型，而不是adapter)
print(f"💾 保存完整模型至: {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
print("✅ 训练完成！")