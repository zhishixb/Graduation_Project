import torch
import pandas as pd
from sentence_transformers import SentenceTransformer, losses, InputExample
from sentence_transformers.training_args import SentenceTransformerTrainingArguments
from sentence_transformers.trainer import SentenceTransformerTrainer
from peft import LoraConfig, TaskType, get_peft_model
from datasets import Dataset
import os

# ================= 配置区域 =================
MODEL_NAME = "models/bge-small-zh-v1.5"
CSV_FILE_PATH = "data/test_training_50.csv"
OUTPUT_DIR = "models_instruct/bge-lora-mnrl-output-20-50"

NUM_EPOCHS = 3
PER_DEVICE_BATCH_SIZE = 16
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
WARMUP_RATIO = 0.1

LORA_R = 16
LORA_ALPHA = 32
# ===========================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"🚀 正在加载数据：{CSV_FILE_PATH} ...")
df = pd.read_csv(CSV_FILE_PATH, header=None, names=['anchor', 'positive'])

train_examples = [
    InputExample(texts=[str(row['anchor']), str(row['positive'])])
    for _, row in df.iterrows()
]

print(f"✅ 数据加载完成！共 {len(train_examples)} 条样本。")
if train_examples:
    print(f"   示例 Anchor: {train_examples[0].texts[0][:30]}...")
    print(f"   示例 Positive: {train_examples[0].texts[1][:30]}...")

# ⚠️ 关键修改：直接使用 anchor/positive 列，不转 InputExample
# SentenceTransformerTrainer 原生支持这些字段
train_dataset = Dataset.from_pandas(df)  # 保留列名 'anchor', 'positive'

# 2. 加载模型
print("🤖 正在加载 SentenceTransformer 模型...")
model = SentenceTransformer(MODEL_NAME)

# 3. 注入 LoRA
print("🔧 注入 LoRA 适配器到模型...")
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["query", "value"],
    task_type=TaskType.FEATURE_EXTRACTION,
    lora_dropout=0.1,
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
    per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
    warmup_ratio=WARMUP_RATIO,
    learning_rate=LEARNING_RATE,
    fp16=False,
    save_strategy="no",
    logging_steps=10,
    report_to="none",
    dataloader_num_workers=0,
    remove_unused_columns=False,  # 保留 anchor/positive
)

# 6. 初始化 Trainer —— 不传 data_collator！
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    loss=train_loss,
    # data_collator=custom_collator  # ❌ 删除这一行
)

# 7. 开始训练
print("🔥 开始微调（CPU 训练可能较慢，请耐心等待）...")
trainer.train()

# 8. 保存 LoRA 适配器
adapter_path = os.path.join(OUTPUT_DIR, "adapter")
print(f"💾 正在保存 LoRA 适配器至: {adapter_path}")

# ✅ 正确方式：通过底层 PEFT 模型保存
peft_model = model._modules["0"].auto_model
peft_model.save_pretrained(adapter_path)

print("✅ 训练与保存完成！")
print(f"📌 推理时请加载原模型 + 此 adapter 路径: {adapter_path}")