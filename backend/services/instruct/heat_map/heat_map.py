import torch
import numpy as np
import shutil
import atexit
import tempfile
from pathlib import Path
from typing import Optional, Set
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
from FlagEmbedding import BGEM3FlagModel
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from IPython.display import HTML, display
import warnings

# ========== 字体 ==========
def set_matplotlib_chinese_font():
    fm._load_fontmanager(try_read_cache=False)
    preferred = ['WenQuanYi Micro Hei', 'SimHei', 'Microsoft YaHei',
                 'PingFang SC', 'Heiti SC', 'Noto Sans CJK SC', 'AR PL UMing CN']
    available = {f.name for f in fm.fontManager.ttflist}
    selected = next((f for f in preferred if f in available), None)
    if selected is None:
        cjk = [f.name for f in fm.fontManager.ttflist
               if any(k in f.name for k in ['CJK','Hei','Song','Ming','SimSun'])]
        if cjk:
            selected = cjk[0]
            warnings.warn(f"Auto select: {selected}")
        else:
            warnings.warn("No Chinese font found! Install or upload one.")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            return
    plt.rcParams['font.sans-serif'] = [selected, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    print(f"[Font] {selected}")

set_matplotlib_chinese_font()

# ========== 停用词集合 ==========
STOP_TOKENS: Set[str] = {
    '，','。','；','：','“','”','‘','’','！','？','、','…','—','～',
    '《','》','（','）','【','】','〈','〉','．','·',
    '.',',',';',':','!','?','-','(',')','[',']','{','}','/','\\',
    '的','了','在','是','与','和','及','或','而','但','且','向','对','为','以','等',
    '之','所','把','被','从','就','到','说','也','又','不','没','很','都','还','更',
    '能','要','会','着','过','这','那','其','中','上','下','前','后','里','外',
    '应','可','将','让','于','比','除','因为','所以','如果','虽然',
    '什么','怎么','哪','呢','吗','啊','哦','嗯','吧','嘛','若','则'
}

def filter_stopwords(weights_dict: dict) -> dict:
    return {t: w for t, w in weights_dict.items() if t not in STOP_TOKENS and t.strip()}

# ========== 解释器 ==========
class BGE_M3_Explainer:
    def __init__(self, model_path: Path, lora_adapter_path: Optional[Path] = None,
                 device: Optional[str] = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Device: {self.device}")

        base = AutoModel.from_pretrained(str(model_path), trust_remote_code=True,
                                          torch_dtype=torch.float16 if self.device=='cuda' else torch.float32,
                                          device_map='auto')
        if lora_adapter_path is not None:
            print(f"LoRA: {lora_adapter_path}")
            model = PeftModel.from_pretrained(base, str(lora_adapter_path)).merge_and_unload()
        else:
            model = base

        self._tmp_model_dir = tempfile.mkdtemp(prefix="bge_m3_merged_")
        model.save_pretrained(self._tmp_model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
        self.tokenizer.save_pretrained(self._tmp_model_dir)
        self.flag_model = BGEM3FlagModel(self._tmp_model_dir, use_fp16=(self.device=='cuda'), device=self.device)
        atexit.register(self._cleanup)
        print("Model ready.\n")

    def _cleanup(self):
        if hasattr(self, '_tmp_model_dir') and Path(self._tmp_model_dir).exists():
            shutil.rmtree(self._tmp_model_dir, ignore_errors=True)

    def _id_to_text_map(self, token_ids: dict) -> dict:
        return {self.tokenizer.decode([int(tid)]): w for tid, w in token_ids.items()}

    def explain_matching(self, text_a: str, text_b: str, top_k: int = 10,
                         filter_heatmap_tokens: bool = True):
        out = self.flag_model.encode([text_a, text_b], return_dense=False,
                                     return_sparse=True, return_colbert_vecs=True,
                                     batch_size=2, max_length=512)

        # 稀疏权重过滤
        sw_a = filter_stopwords(self._id_to_text_map(out['lexical_weights'][0]))
        sw_b = filter_stopwords(self._id_to_text_map(out['lexical_weights'][1]))

        common = set(sw_a) & set(sw_b)
        contrib = sorted(((t, sw_a[t]*sw_b[t]) for t in common), key=lambda x: x[1], reverse=True)
        top_set = {t for t, _ in contrib[:top_k]}

        def highlight(text, weights, hl_set):
            for t in sorted(weights, key=len, reverse=True):
                if t in hl_set:
                    text = text.replace(t, f'<mark style="background-color:#FFEB3B">{t}</mark>')
            return text
        html_a = highlight(text_a, sw_a, top_set)
        html_b = highlight(text_b, sw_b, top_set)

        # ---- ColBERT 热力图 ----
        vecs_a = out['colbert_vecs'][0]
        vecs_b = out['colbert_vecs'][1]

        raw_a = [t.replace('▁','').replace('</s>','') for t in
                 self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text_a, add_special_tokens=False))]
        raw_b = [t.replace('▁','').replace('</s>','') for t in
                 self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text_b, add_special_tokens=False))]

        if filter_heatmap_tokens:
            keep_a = [i for i, t in enumerate(raw_a) if t not in STOP_TOKENS and t.strip()]
            keep_b = [i for i, t in enumerate(raw_b) if t not in STOP_TOKENS and t.strip()]
            vecs_a = vecs_a[keep_a]
            vecs_b = vecs_b[keep_b]
            tokens_a = [raw_a[i] for i in keep_a]
            tokens_b = [raw_b[i] for i in keep_b]
        else:
            tokens_a, tokens_b = raw_a, raw_b

        norm_a = vecs_a / np.linalg.norm(vecs_a, axis=1, keepdims=True)
        norm_b = vecs_b / np.linalg.norm(vecs_b, axis=1, keepdims=True)
        sim = np.dot(norm_a, norm_b.T)

        max_disp = 40
        if len(tokens_a) > max_disp:
            tokens_a = tokens_a[:max_disp]; sim = sim[:max_disp, :]
        if len(tokens_b) > max_disp:
            tokens_b = tokens_b[:max_disp]; sim = sim[:, :max_disp]

        # 展示关键词
        n = min(top_k, len(contrib))
        display(HTML(f"""<h4>📌 关键词贡献 Top-{n}（已忽略停用词）</h4>
        <div style="display:flex; gap:2rem;"><div><b>A:</b><p>{html_a}</p></div>
        <div><b>B:</b><p>{html_b}</p></div></div>
        <ul>{''.join(f'<li>“{t}” → {s:.4f}</li>' for t,s in contrib[:top_k])}</ul>"""))

        # 热力图
        plt.figure(figsize=(max(8, len(tokens_b)*0.3), max(4, len(tokens_a)*0.3)))
        sns.heatmap(sim, xticklabels=tokens_b, yticklabels=tokens_a, cmap='YlOrRd', linewidths=0.5)
        plt.title('Token 级语义对齐热力图 (ColBERT)', fontsize=14)
        plt.xlabel('Text B', fontsize=10); plt.ylabel('Text A', fontsize=10)
        plt.xticks(rotation=45, ha='right'); plt.tight_layout(); plt.show()


if __name__ == "__main__":
    project_root = Path.cwd()
    MODEL_PATH = project_root / "models" / "bge_m3" / "bge-m3"
    LORA_PATH = project_root / "models" / "bge_m3" / "bge_m3_adapter_v1" / "adapter"

    explainer = BGE_M3_Explainer(MODEL_PATH, LORA_PATH, device='cuda')

    # ========== 示例：比较两段文本 ==========
    text_a = "C++程序设计、Java语言程序设计、数据库系统原理、计算机网络原理、计算机系统结构、数据结构、操作系统、软件工程、离散数学；NET、JAVA、大数据、云计算、软件工程、金融信息化、嵌入式软件、传媒设计与制作、计算机网络技术、移动互联网信息与技术；计算机的设计与制造，包含计算机软件、硬件的基本理论、技能与方法，进行计算机系统和软件的开发与维护、硬件的组装等。Windows系统的维护，手机APP的开发，台式电脑的整机装配等。相较于网络工程、软件工程，计算机科学与技术专业所学范围更广"
    text_b = "学习并应用主流开发框架与工具；熟悉至少一种编程语言（如 Java、Python、Go 等）；了解数据库原理，具备基本的 SQL 编写能力"

    explainer.explain_matching(text_a, text_b, top_k=5)