import json
import requests
import time
from typing import Optional, List, Dict, Any
from loguru import logger


class OllamaSkillExtractor:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"

        logger.info(f"初始化通用提取器 -> 模型: {model_name}")
        # 启动时预热
        self._warmup_model()

    def _warmup_model(self):
        """预热模型"""
        logger.info(f"🔥 正在预热模型 {self.model_name}...")
        start_time = time.perf_counter()
        try:
            payload = {"model": self.model_name, "prompt": "Hi", "stream": False}
            resp = requests.post(self.api_url, json=payload, timeout=120)
            duration = time.perf_counter() - start_time
            if resp.status_code == 200:
                logger.success(f"✅ 模型预热成功 (耗时: {duration:.2f}s)")
            else:
                logger.warning(f"⚠️ 预热状态码: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ 预热失败: {e}")

    def extract(
            self,
            text: str,
            prompt_template: str,
            prompt_vars: Optional[Dict[str, Any]] = None,
            max_retries: int = 2,
            temperature: float = 0.1,
            max_tokens: int = 500
    ) -> Optional[List[str]]:
        """
        通用提取方法。

        Args:
            text: 需要处理的原始文本。
            prompt_template: 提示词模板字符串。必须包含 '{text}' 占位符，也可以包含其他自定义占位符。
            prompt_vars: 额外的模板变量字典 (可选)。
            max_retries: 最大重试次数。
            temperature: 温度参数 (0.0 - 1.0)。
            max_tokens: 最大生成 token 数。

        Returns:
            提取结果的列表 (按行分割)，如果失败返回 None。
        """
        if not text or len(text.strip()) < 5:
            logger.warning("输入文本过短，跳过处理。")
            return []

        # 1. 构建最终 Prompt
        # 默认将输入文本放入 'text' 变量
        format_vars = {"text": text}
        if prompt_vars:
            format_vars.update(prompt_vars)

        try:
            final_prompt = prompt_template.format(**format_vars)
        except KeyError as e:
            logger.error(f"❌ 提示词模板错误：缺少变量 {e}")
            return None

        # 截断过长的 prompt 以防上下文溢出 (可选策略，视模型而定)
        if len(final_prompt) > 8000:
            logger.warning("⚠️ 提示词过长，已强制截断至 8000 字符。")
            final_prompt = final_prompt[:8000]

        payload = {
            "model": self.model_name,
            "prompt": final_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        # 2. 发送请求 (带重试)
        for attempt in range(max_retries + 1):
            try:
                t_start = time.perf_counter()
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                infer_time = time.perf_counter() - t_start

                if response.status_code == 404:
                    logger.error(f"❌ 404 错误：模型 '{self.model_name}' 未找到。")
                    return None
                response.raise_for_status()

                raw_response = response.json().get("response", "").strip()

                # 3. 清洗输出 (保持原有逻辑)
                if raw_response.startswith("```"):
                    parts = raw_response.split("```")
                    # 取第一个代码块内容，如果没有闭合则取剩余部分
                    raw_response = parts[1] if len(parts) > 1 else parts[0]
                    # 处理 ```language 标记
                    if '\n' in raw_response:
                        raw_response = raw_response.split('\n', 1)[1]
                    else:
                        # 如果只有一行且前面是语言标记，可能解析有误，尝试直接去除前缀
                        pass

                raw_response = raw_response.strip().rstrip("```").strip()

                # 按行分割并过滤空行
                results = [line.strip() for line in raw_response.split('\n') if line.strip()]

                # 注意：这里不再硬编码过滤 "负责/职责" 等词，因为通用提取器可能不需要这个过滤。
                # 如果需要特定过滤，应由调用者在获取结果后处理，或者通过 prompt_vars 传入过滤规则。
                # 为了保持一定的向后兼容性，如果用户明确是在做技能提取，可以在 prompt 里约束。
                # 这里我们直接返回清洗后的行列表。

                logger.info(f"⏱️ 推理耗时: {infer_time:.2f}s, 提取条目数: {len(results)}")
                return results

            except requests.exceptions.Timeout:
                logger.warning(f"⏰ 请求超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt == max_retries:
                    return None
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ 异常: {e}")
                if attempt == max_retries:
                    return None
                time.sleep(1)

        return None


if __name__ == "__main__":
    MODEL_NAME = "hf.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"

    # 初始化
    extractor = OllamaSkillExtractor(model_name=MODEL_NAME)

    test_text = """
    负责后端服务架构设计与开发，使用 Java Spring Cloud 体系
    参与高并发系统优化，熟悉 Redis 缓存策略及 MySQL 分库分表
    有 K8s 容器化部署经验者优先
    计算机相关专业
    精通 Python 或 Go 语言，熟悉 Linux 环境开发
    """

    print("\n--- 场景 1: 提取硬技能 (复用旧逻辑) ---")
    # 定义外部提示词模板
    skill_prompt = """
    请从以下文本中提取所有**明确、具体、可验证的硬性能力或资质要求**。

    仅输出满足以下条件的内容：
    - 是具体工具、方法、证书、系统、语言、标准或专业能力；
    - 不包括学历、年限、软技能、工作职责或模糊表述。

    适当简化描述，输出为自然语言，不要序号，不要解释，每行一个。

    文本内容：
    {text}

    提取结果：
    """

    skills = extractor.extract(
        text=test_text,
        prompt_template=skill_prompt,
        temperature=0.1
    )

    if skills:
        print(f"✅ 发现 {len(skills)} 项硬技能：")
        for s in skills:
            print(f"- {s}")

    print("\n--- 场景 2: 提取软技能 (新用途) ---")
    soft_skill_prompt = """
    请从以下文本中提取所有的**软技能** (如沟通能力、团队合作、领导力、抗压能力等)。
    不要提取技术栈或工具。
    每行输出一个软技能关键词。

    文本内容：
    {text}

    提取结果：
    """

    soft_skills = extractor.extract(
        text=test_text,
        prompt_template=soft_skill_prompt,
        temperature=0.3  # 软技能提取可以稍微高一点温度
    )

    if soft_skills:
        print(f"✅ 发现 {len(soft_skills)} 项软技能：")
        for s in soft_skills:
            print(f"- {s}")
    else:
        print("ℹ️ 未发现明显的软技能描述。")

    print("\n--- 场景 3: 多变量模板 (高级用法) ---")
    # 假设我们要根据指定的类别来提取
    category_prompt = """
    你是一个{role}专家。
    请从文本中找出与"{category}"相关的所有关键词。

    文本：
    {text}

    结果列表：
    """

    db_keywords = extractor.extract(
        text=test_text,
        prompt_template=category_prompt,
        prompt_vars={
            "role": "数据库架构师",
            "category": "数据库技术"
        },
        temperature=0.1
    )

    if db_keywords:
        print(f"✅ 数据库相关关键词：{db_keywords}")