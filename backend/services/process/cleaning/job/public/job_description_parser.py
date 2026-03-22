import re
from typing import List, Optional, Dict, Callable

# 默认关键词（可被覆盖）
DEFAULT_SOFT_KEYWORDS = [
    '思维', '灵活', '吃苦', '耐劳', '责任心', '团队意识',
    '沟通', '协作', '抗压', '学习能力', '积极', '主动',
    '认真', '务实', '好胜心', '荣誉感', '挑战'
]

DEFAULT_HARD_KEYWORDS = [
    # 学历/证书
    '证书', '资格', '六级', '四级', '雅思', '托福', '普通话',
    # 经验/年限
    '经验', '相关经验', '项目经验', '实习经验', '销售经验',
    # 技能动词
    '熟悉', '掌握', '了解', '精通', '使用', '会', '能',
    # 技术/工具
    '工具', '软件', '系统', '平台', '框架', '语言', '数据库',
    # 专业/领域
    '专业', '相关专业', '计算机', '新闻', '影视', '设计', '动画',
    '英语', 'AI', 'Python', 'Java', 'MySQL', 'Docker', '拍摄', '制作', 'Go',

    # 1. 热门技术与架构 (补充现有列表)
    'C++', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Node.js',
    'Linux', 'Kubernetes', 'K8s', '云计算', '大数据', '机器学习', '深度学习',
    '前端', '后端', '全栈', '移动端', 'iOS', 'Android', '小程序',
    '算法', '数据结构', '网络安全', '运维', '测试', '自动化测试',

    # 2. 产品与运营类
    '产品', '产品经理', '运营', '用户运营', '内容运营', '活动运营',
    '数据分析', '商业分析', '市场调研', 'SEO', 'SEM', '新媒体',

    # 3. 设计与创意类
    'UI', 'UX', '交互设计', '视觉设计', '平面设计', '3D建模',
    '视频剪辑', '后期制作', '原画', '插画', '多媒体',

    # 4. 市场与销售类
    '市场', '营销', '品牌', '公关', '销售', '商务', '渠道',
    '大客户', '广告', '媒介',

    # 5. 职能与支持类
    '人力资源', '招聘', '财务', '会计', '行政', '法务', '客服',
    '供应链', '采购', '物流',

    # 6. 新兴行业与垂直领域
    '金融', '电商', '游戏', '医疗', '教育', '汽车', '新能源',
    '智能制造', '物联网', '区块链', '元宇宙', '跨境电商',

    # 7. 常见学科背景
    '数学', '统计', '物理', '化学', '生物', '电子', '通信',
    '机械', '土木', '建筑', '心理学', '社会学', '管理学', '经济学',
    '法学', '医学', '药学', '艺术', '文学'
]


# 正则模式集中管理
class Patterns:
    LEADING_MARKERS = [
        r'^\s*\d+[\.\)、，：:\-\s]*',
        r'^\s*[①②③④⑤⑥⑦⑧⑨⑩][\s\.\)、]*',
        r'^\s*[一二三四五六七八九十]+[\.、，\s]*',
        r'^\s*[a-zA-Z][\.\)\s]*',
        r'^\s*[\-–—•●◆▶★\*]+[\s\-–—•●◆▶★\*]*',
        r'^\s*[\(\[【]?[a-zA-Z\d]+[\)\]】]?[\s\.\)、:\-\s]*',
        r'^\s*[>＞»›]+[\s]*',
    ]
    EDUCATION_PHRASE = r'(?:大学)?(?:本科|硕士|博士|大专|专科|全日制)?(?:及以上|以上)?(?:学历|学位)\s*[，,、]?\s*'
    YEARS_EXPERIENCE = r'(?:[0-9]+|[一二两三四五六七八九十]+)\s*年\s*(?:及)?\s*(?:以上|以下|以内|左右)?\s*(?:相关(?:岗位|经验)|工作(?:经验|经历))?'
    RELATED_EXPERIENCE = r'(?:相关|工作)(经验|经历)'
    STANDALONE_RELATED_POST = r'相关岗位'
    REQUIREMENT_SIGNALS = r'(需|要求|具备|有.*[0-9一二两三四五六七八九十]+年|至少|以上|优先|加分|可接受|放宽)'
    CAN_OR_KNOW = r'^(能|会|可)[\u4e00-\u9fa5a-zA-Z]'
    TRAILING_PUNCT = r'[。.;；]+$'
    ONLY_SYMBOLS = r'^[\W\s]{3,}$'


class JobDescriptionParser:
    def __init__(
            self,
            text: str,
            soft_keywords: Optional[List[str]] = None,
            hard_keywords: Optional[List[str]] = None,
            custom_cleaning_steps: Optional[List[Callable[[str], str]]] = None,
    ):
        self.text = text
        self.lines = [line.strip() for line in text.splitlines() if line.strip()]

        self.soft_keywords = set(soft_keywords or DEFAULT_SOFT_KEYWORDS)
        self.hard_keywords = set(hard_keywords or DEFAULT_HARD_KEYWORDS)

        # 默认清洗步骤（可被替换或扩展）
        self.cleaning_steps = custom_cleaning_steps or [
            self._remove_leading_markers,
            self._remove_education_phrase,
            self._remove_years_experience,
            self._normalize_experience_terms,
            self._remove_standalone_related_post,
            self._remove_trailing_punctuation,
            self._normalize_whitespace,
            self._filter_symbol_only,
        ]

    # ================== 提取主流程 ==================
    def extract_requirements(self, clean: bool = True) -> List[str]:
        raw_lines = self._extract_raw_candidates()
        if not raw_lines:
            return ["未找到有效要求"]

        results = []
        for line in raw_lines:
            cleaned = self._clean_requirement(line) if clean else line
            if self._is_valid_requirement(cleaned):
                results.append(cleaned)

        return results if results else ["未找到有效要求"]

    def get_requirements_text(self, clean: bool = True, joiner: str = '\n') -> str:
        reqs = self.extract_requirements(clean=clean)
        if len(reqs) == 1 and ("未找到" in reqs[0] or "有效要求" in reqs[0]):
            return reqs[0]
        return joiner.join(reqs)

    # ================== 候选行提取 ==================
    def _extract_raw_candidates(self) -> List[str]:
        candidates = []
        for line in self.lines:
            if len(line) < 6:
                continue

            # 规则1: 包含硬关键词
            if any(kw in line for kw in self.hard_keywords):
                candidates.append(line)
                continue

            # 规则2: 包含要求类句式
            if re.search(Patterns.REQUIREMENT_SIGNALS, line, re.IGNORECASE):
                candidates.append(line)
                continue

            # 规则3: 以“能/会/可”开头的能力描述
            if re.match(Patterns.CAN_OR_KNOW, line):
                candidates.append(line)

        return candidates

    # ================== 清洗管道 ==================
    def _clean_requirement(self, line: str) -> str:
        cleaned = line
        for step in self.cleaning_steps:
            cleaned = step(cleaned)
        return cleaned

    def _remove_leading_markers(self, text: str) -> str:
        for pattern in Patterns.LEADING_MARKERS:
            text = re.sub(pattern, '', text)
        return text

    def _remove_education_phrase(self, text: str) -> str:
        return re.sub(Patterns.EDUCATION_PHRASE, '', text, flags=re.IGNORECASE)

    def _remove_years_experience(self, text: str) -> str:
        return re.sub(Patterns.YEARS_EXPERIENCE, '', text, flags=re.IGNORECASE)

    def _normalize_experience_terms(self, text: str) -> str:
        # 将“相关经验” → “经验”，但保留“经验”本身
        text = re.sub(Patterns.RELATED_EXPERIENCE, r'\1', text, flags=re.IGNORECASE)
        return text

    def _remove_standalone_related_post(self, text: str) -> str:
        return re.sub(Patterns.STANDALONE_RELATED_POST, '', text, flags=re.IGNORECASE)

    def _remove_trailing_punctuation(self, text: str) -> str:
        return re.sub(Patterns.TRAILING_PUNCT, '', text)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _filter_symbol_only(self, text: str) -> str:
        if re.match(Patterns.ONLY_SYMBOLS, text):
            return ""
        return text

    # ================== 过滤逻辑 ==================
    def _is_valid_requirement(self, line: str) -> bool:
        if not line or len(line) < 6:
            return False
        if self._is_soft_skill_only(line):
            return False
        return True

    def _is_soft_skill_only(self, line: str) -> bool:
        has_soft = any(kw in line for kw in self.soft_keywords)
        if not has_soft:
            return False

        # 检查是否有硬技能或年限
        has_hard = any(kw in line for kw in self.hard_keywords if kw not in {'能', '会'})

        # 特殊处理“能”“会”：避免误判“会议”“能力”等
        if '能' in line and '能力' not in line:
            has_hard = True
        if '会' in line and not any(x in line for x in ['会议', '会计', '机会']):
            has_hard = True

        has_year = bool(re.search(r'[0-9一二两三四五六七八九十]+年', line))

        return not (has_hard or has_year)


# ================== 测试用例 ==================
if __name__ == "__main__":
    jd_text = """
【工作内容】
- 负责日常超声检查工作，包括腹部、妇科、产科、心脏及浅表器官等部位的影像诊断；
- 根据临床需求完成超声检查，并出具准确的诊断报告；
- 参与科室的病例讨论及疑难病例分析，协助临床医生制定诊疗方案；
- 配合医院其他科室开展相关检查工作，确保诊疗流程顺畅。
【任职要求】
- 具备医学相关专业本科及以上学历，持有执业医师资格证；
- 熟悉超声设备操作及影像诊断流程，具备良好的沟通能力和团队协作精神；
- 有责任心，工作细致，能够承受一定工作压力；
- 不限工作经验，应届毕业生亦可考虑。
 
 可接受临床医师来院后进行转岗。
    """

    parser = JobDescriptionParser(jd_text)
    result = parser.get_requirements_text(clean=True)
    print("清洗后的任职要求：")
    print("=" * 50)
    print(result)