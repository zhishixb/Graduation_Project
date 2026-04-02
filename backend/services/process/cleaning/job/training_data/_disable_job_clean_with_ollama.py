import json
import requests
import time
from typing import Optional, List
from loguru import logger


class OllamaSkillExtractor:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"

        logger.info(f"初始化硬技能提取器 -> 模型: {model_name}")
        # 启动时预热，避免首次请求超时
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

    def _build_prompt(self, text: str) -> str:
        """构建针对硬技能提取的专用提示词"""
        safe_text = text[:3000] if len(text) > 3000 else text

        return f"""
            删除以下职位描述中**的软技能**。


            职位描述：
            {safe_text}

            提取结果：
        """

    def extract_skills(self, text: str, max_retries: int = 2) -> Optional[List[str]]:
        if not text or len(text.strip()) < 20:
            return []

        payload = {
            "model": self.model_name,
            "prompt": self._build_prompt(text),
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 500}  # 技能列表通常不需要太长
        }

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

                # 清洗输出：移除可能的 Markdown 代码块标记
                if raw_response.startswith("```"):
                    parts = raw_response.split("```")
                    raw_response = parts[1] if len(parts) > 1 else parts[0]
                    if raw_response.startswith("text"):  # 处理 ```text
                        raw_response = raw_response[4:]
                raw_response = raw_response.strip().rstrip("```").strip()

                # 按行分割并过滤空行
                skills = [line.strip() for line in raw_response.split('\n') if line.strip()]

                # 二次过滤：去除可能残留的非技能行（如包含“负责”、“要求”等词的整行，以防模型不听话）
                final_skills = []
                stop_words = ["负责", "职责", "要求", "优先", "具备", "拥有", "学历", "专业"]
                for skill in skills:
                    # 如果一行以这些词开头，且长度较短，可能是误提取的描述，跳过
                    if any(skill.startswith(word) for word in stop_words) and len(skill) < 15:
                        continue
                    final_skills.append(skill)

                logger.info(f"⏱️ 推理耗时: {infer_time:.2f}s, 提取技能数: {len(final_skills)}")
                return final_skills

            except requests.exceptions.Timeout:
                logger.warning(f"⏰ 请求超时 (尝试 {attempt + 1})")
                if attempt == max_retries: return None
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ 异常: {e}")
                if attempt == max_retries: return None
                time.sleep(1)

        return None


if __name__ == "__main__":
    # 配置您的模型名称
    MODEL_NAME = "hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M"

    # ⬇️⬇️⬇️ 请在此处填入您的职位描述文本 ⬇️⬇️⬇️
    test_text = """
主导或参与项目方案设计、图纸深化等环节，确保方案符合当地建筑规范及项目需求。
严格遵循欧美澳建筑标准，对项目施工过程中的技术问题进行指导与解决
准确传递技术要求，协调处理项目技术相关争议与问题。
参与项目技术文件的编制、审核与归档工作，包括施工图纸、技术交底文件、验收报告等，确保技术资料的完整性与规范性。
若具备统筹管理经验，把控项目技术节点
具备建筑工程相关工作经验，有集成房屋、轻钢/钢结构项目经验者优先。
精通欧美澳建筑标准及相关法规，能够独立完成符合当地标准的技术方案设计、图纸审核等工作。
具备良好的语言基础，能熟练使用英语作为工作语言（听说读写流利）
具备扎实的专业技术能力，熟悉建筑施工工艺、质量控制要点，能独立解决项目现场技术难题。
    """

    if len(test_text) < 50:
        print("⚠️ 请在代码中填入具体的职位描述文本后再运行。")
    else:
        extractor = OllamaSkillExtractor(model_name=MODEL_NAME)
        print("\n🔍 开始提取硬技能...\n")

        start_total = time.perf_counter()
        skills = extractor.extract_skills(test_text)
        total_time = time.perf_counter() - start_total

        if skills:
            print(f"✅ 提取完成 (总耗时: {total_time:.2f}s)，共发现 {len(skills)} 项硬技能：\n")
            for s in skills:
                print(f"- {s}")
        else:
            print("❌ 未提取到有效技能或发生错误。")