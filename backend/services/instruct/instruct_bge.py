import torch
import pandas as pd
from sentence_transformers import SentenceTransformer, losses, InputExample
from sentence_transformers.training_args import SentenceTransformerTrainingArguments
from sentence_transformers.trainer import SentenceTransformerTrainer
from peft import LoraConfig, TaskType, get_peft_model
from datasets import Dataset

# ================= 配置区域 =================
MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 预训练模型
CSV_FILE_PATH = "test_training_with_major_intro.csv"  # 数据文件路径
OUTPUT_DIR = "./bge-lora-mnrl-output"  # 输出目录

# 训练超参数 (针对 CPU 优化)
NUM_EPOCHS = 3
PER_DEVICE_BATCH_SIZE = 16  # CPU 建议 8 或 16，防止内存溢出
GRADIENT_ACCUMULATION_STEPS = 4  # 梯度累积，等效 Batch Size = 16 * 4 = 64 (MNRL 需要大 batch)
LEARNING_RATE = 2e-4
WARMUP_RATIO = 0.1

# LoRA 配置
LORA_R = 16
LORA_ALPHA = 32
# ===========================================

print(f"🚀 正在加载数据：{CSV_FILE_PATH} ...")
# 1. 读取数据 (假设文件无表头或自动识别，根据文件内容自动推断)
# 文件内容显示为两列文本，pandas 默认会读取第一行为表头，如果文件没有表头需加 header=None
# 观察文件内容，第一行是数据而非表头，因此设置 header=None，并手动指定列名
df = pd.read_csv(CSV_FILE_PATH, header=None, names=['anchor', 'positive'])

# 转换为 InputExample 列表
train_examples = [
    InputExample(texts=[str(row['anchor']), str(row['positive'])])
    for _, row in df.iterrows()
]

print(f"✅ 数据加载完成！共 {len(train_examples)} 条样本。")
print(f"   示例 Anchor: {train_examples[0].texts[0][:30]}...")
print(f"   示例 Positive: {train_examples[0].texts[1][:30]}...")

# 转换为 HuggingFace Dataset
train_dataset = Dataset.from_list([{"anchor": ex.texts[0], "positive": ex.texts[1]} for ex in train_examples])

# 2. 加载模型
print("🤖 正在加载模型...")
model = SentenceTransformer(MODEL_NAME)

# 3. 配置并注入 LoRA
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["query", "value"],  # 针对 BGE/BERT 架构
    task_type=TaskType.FEATURE_EXTRACTION,
    lora_dropout=0.1,
    bias="none",
)

# 注入 LoRA 到底层 Transformer 模型
# SentenceTransformer 的底层模型在 _modules['0'].auto_model
model._modules["0"].auto_model = get_peft_model(
    model._modules["0"].auto_model,
    lora_config
)

model.print_trainable_parameters()

# 4. 定义损失函数
train_loss = losses.MultipleNegativesRankingLoss(model)

# 5. 配置训练参数
args = SentenceTransformerTrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,  # 关键：模拟大 Batch
    warmup_ratio=WARMUP_RATIO,
    learning_rate=LEARNING_RATE,
    fp16=False,  # CPU 通常不支持或不加速 FP16，设为 False 更稳定
    save_strategy="no",  # 训练结束再保存，节省中间步骤
    logging_steps=10,
    report_to="none",
    dataloader_num_workers=0,  # CPU 加载数据，设为 0 避免多进程开销
)


# 6. 初始化 Trainer
# 自定义 collator 来处理 anchor 和 positive 的 tokenize
def custom_collator(features):
    anchors = [f["anchor"] for f in features]
    positives = [f["positive"] for f in features]

    # 使用模型自带的 tokenizer
    anchor_inputs = model.tokenize(anchors, padding=True, truncation=True)
    positive_inputs = model.tokenize(positives, padding=True, truncation=True)

    return {
        "anchor": anchor_inputs,
        "positive": positive_inputs
    }


trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    loss=train_loss,
    data_collator=custom_collator
)

# 7. 开始训练
print("🔥 开始微调 (这可能需要在 CPU 上运行一段时间)...")
trainer.train()

# 8. 保存结果
print("💾 保存模型适配器...")
model.save_adapter(f"{OUTPUT_DIR}/adapter", adapter_name="default")
print(f"✅ 训练完成！LoRA 适配器已保存至：{OUTPUT_DIR}/adapter")
print("   (推理时请加载此 adapter，或将权重合并后保存)")