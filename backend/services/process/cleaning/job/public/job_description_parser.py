import re
from typing import List, Optional, Callable, Set, Pattern

# ================== 配置区域 ==================

# 【强化】软技能关键词：加入逻辑思维、办公软件等容易混淆的词
DEFAULT_SOFT_KEYWORDS = [
    '思维', '灵活', '吃苦', '耐劳', '责任心', '团队意识', '团队', '合作',
    '沟通', '协作', '抗压', '学习能力', '积极', '主动',
    '认真', '务实', '好胜心', '荣誉感', '挑战',
    '适应力', '适应能力', '环境适应', '精神',
    '兴趣', '热情', '轮岗', '培训', '表达', '亲和力', '执行力',
    '逻辑思维', '办公软件', 'office', 'word', 'excel', 'ppt', '综合素质', '潜能'
]

# 技能关键词：只保留具体的专业、工具、技术、证书
DEFAULT_HARD_KEYWORDS = [
    '证书', '资格', '六级', '四级', '雅思', '托福', '普通话',
    '经验', '相关经验', '项目经验', '实习经验', '销售经验',
    '熟悉', '掌握', '了解', '精通', '使用', '会', '能',
    '工具', '软件', '系统', '平台', '框架', '语言', '数据库',
    '专业', '相关专业','教学'
    # 具体专业/领域
    '计算机', '新闻', '影视', '设计', '动画', '英语', 'AI',
    'Python', 'Java', 'MySQL', 'Docker', '拍摄', '制作', 'Go',
    'C++', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular', 'Node.js',
    'Linux', 'Kubernetes', 'K8s', '云计算', '大数据', '机器学习', '深度学习',
    '前端', '后端', '全栈', '移动端', 'iOS', 'Android', '小程序',
    '算法', '数据结构', '网络安全', '运维', '测试', '自动化测试',
    '产品', '产品经理', '运营', '用户运营', '内容运营', '活动运营',
    '数据分析', '商业分析', '市场调研', 'SEO', 'SEM', '新媒体',
    'UI', 'UX', '交互设计', '视觉设计', '平面设计', '3D建模',
    '视频剪辑', '后期制作', '原画', '插画', '多媒体',
    '市场', '营销', '品牌', '公关', '销售', '商务', '渠道',
    '大客户', '广告', '媒介',
    '人力资源', '招聘', '财务', '会计', '行政', '法务', '客服',
    '供应链', '采购', '物流',
    '金融', '电商', '游戏', '医疗', '教育', '汽车', '新能源',
    '智能制造', '物联网', '区块链', '元宇宙', '跨境电商',
    '数学', '统计', '物理', '化学', '生物', '电子', '通信',
    '机械', '土木', '建筑', '心理学', '社会学', '管理学', '经济学',
    '法学', '医学', '药学', '艺术', '文学',
    # 具体工程专业名
    '工业工程', '机械工程', '机械电子', '机械设计', '自动化', '电气', '材料', '化学工程',
    # 补充：确保“数据”单独出现时不被误判，必须结合“分析”等，这里保留“数据分析”
]

WORK_NATURE_PHRASES = [
    '适应频繁出差', '适应出差', '能接受出差', '可接受出差', '经常出差',
    '适应加班', '能接受加班', '可接受加班', '偶尔加班', '高强度工作',
    '适应快节奏', '抗压能力强', '能承受较大工作压力',
    '服从公司安排', '服从调配', '适应弹性工作',
    '愿意从基层做起', '吃苦耐劳', '具备良好的职业道德',
    '适应力强', '适应力佳', '适应能力佳', '适应能力强',
    '接受轮岗', '轮岗培训', '带薪培训', '统一培训', '入职培训'
]

COMMON_LOCATIONS = {
    '北京', '上海', '天津', '重庆', '广州', '深圳', '杭州', '南京', '武汉', '成都', '西安', '苏州', '郑州',
    '长沙', '沈阳', '青岛', '宁波', '无锡', '福州', '厦门', '合肥', '大连', '济南', '哈尔滨', '长春', '石家庄',
    '昆明', '南昌', '贵阳', '太原', '南宁', '海口', '兰州', '银川', '西宁', '乌鲁木齐', '拉萨', '呼和浩特',
    '鄂尔多斯', '烟台', '温州', '东莞', '佛山', '常州', '徐州', '南通', '泉州', '惠州', '珠海', '中山',
    '扬州', '泰州', '嘉兴', '绍兴', '洛阳', '开封', '桂林', '三亚', '秦皇岛', '保定', '唐山', '廊坊'
}


class Patterns:
    LEADING_MARKERS = [
        r'^\s*\d+[\.\)、，：:\-\s](?![年岁个])',
        r'^\s*[①②③④⑤⑥⑦⑧⑨⑩][\s\.\)、]*',
        r'^\s*[一二三四五六七八九十]+[\.、，\s](?![年岁个])',
        r'^\s*[a-zA-Z][\.\)\s]*',
        r'^\s*[\-–—•●◆▶★\*]+[\s\-–—•●◆▶★\*]*',
        r'^\s*[\(\[【]?[a-zA-Z\d]+[\)\]】]?[\s\.\)、:\-\s]*',
        r'^\s*[>＞»›]+[\s]*',
    ]

    # 删除学历描述
    EDUCATION_FULL_PATTERN = r'(?:985|211|双一流|重点大学|知名高校)?[/\s]*(?:本科|硕士|博士|大专|专科|研究生|海归|留学)?(?:及以上|以上|全日制)?(?:学历|学位)?\s*[，,、]?\s*'

    # 【新增】删除专业后缀
    MAJOR_SUFFIX_PATTERN = r'\s*(?:等相关?(?:专业)?)?\s*(?:优先 | 者优先 | 为佳 | 均可 | 背景)?\s*[,.。;；]?\s*$'

    YEARS_EXPERIENCE = r'(?:[0-9]+|[一二两三四五六七八九十]+)\s*年\s*(?:及)?\s*(?:以上|以下|以内|左右)?\s*(?:相关(?:岗位|经验)|工作(?:经验|经历))?'
    RELATED_EXPERIENCE = r'(?:相关|工作)(经验|经历)'
    STANDALONE_RELATED_POST = r'相关岗位'
    REQUIREMENT_SIGNALS = r'(需 | 要求 | 具备 | 有.*[0-9一二两三四五六七八九十]+年 | 至少 | 以上 | 优先 | 加分 | 可接受 | 放宽)'
    CAN_OR_KNOW = r'^(能 | 会 | 可)[\u4e00-\u9fa5a-zA-Z]'
    TRAILING_PUNCT = r'[。.;；]+$'
    ONLY_SYMBOLS = r'^[\W\s]{3,}$'
    LOCATION_PREFIX = r'(?:驻 | 位于 | 工作在 | 地点 [:：]?|base 在|base 地 [:：]?)\s*'

    # 【关键修改】加入顿号 '、' 作为分隔符
    SENTENCE_SPLITTERS = r'[，,;；/]'

    VAGUE_PATTERN = r'(?:不限 | 无经验 | 无需经验 | 零基础 | 应届 | 毕业生 | 小白 | 入门 | 可培训 | 带薪培训)'
    LEFTOVER_EDU_PATTERN = r'(?:985|211|双一流|本科|硕士|博士|大专|专科|研究生|学历|学位)'


class JobDescriptionParser:
    """
    实现岗位描述清洗的通用方法
    """
    def __init__(
            self,
            soft_keywords: Optional[List[str]] = None,
            hard_keywords: Optional[List[str]] = None,
            custom_cleaning_steps: Optional[List[Callable[[str], str]]] = None,
            location_list: Optional[Set[str]] = None,
            work_nature_phrases: Optional[List[str]] = None,
    ):
        self.soft_keywords = set(soft_keywords or DEFAULT_SOFT_KEYWORDS)
        self.hard_keywords = set(hard_keywords or DEFAULT_HARD_KEYWORDS)
        self.locations = location_list or COMMON_LOCATIONS
        self.work_nature_phrases = work_nature_phrases or WORK_NATURE_PHRASES

        self.location_detect_pattern = self._compile_location_detect_pattern()
        self.nature_pattern = self._compile_nature_pattern()
        self.vague_pattern = re.compile(Patterns.VAGUE_PATTERN, re.IGNORECASE)
        self.leftover_edu_pattern = re.compile(Patterns.LEFTOVER_EDU_PATTERN, re.IGNORECASE)
        self.major_suffix_pattern = re.compile(Patterns.MAJOR_SUFFIX_PATTERN, re.IGNORECASE)

        self.cleaning_steps = custom_cleaning_steps or [
            self._remove_years_experience,
            self._remove_education_full,
            self._remove_major_suffix,  # 新增步骤
            self._normalize_experience_terms,
            self._remove_standalone_related_post,
            self._remove_work_nature_phrases,
            self._remove_chinese_brackets,
            self._remove_leading_markers,
            self._remove_trailing_punctuation,
            self._normalize_whitespace,
            self._filter_symbol_only,
        ]

        self.title_exclude_patterns = [
            r'[【\[\(]?任职要求 [】\]\)]?', r'[【\[\(]?岗位要求 [】\]\)]?',
            r'[【\[\(]?招聘要求 [】\]\)]?', r'[【\[\(]?职位要求 [】\]\)]?',
            r'[【\[\(]?工作内容 [】\]\)]?', r'[【\[\(]?岗位职责 [】\]\)]?',
            r'[【\[\(]?职位描述 [】\]\)]?', r'Requirements?:?',
            r'Job Description:?', r'Responsibilities?:?'
        ]
        self.compiled_exclude_patterns = [re.compile(p, re.IGNORECASE) for p in self.title_exclude_patterns]

        self.invalid_title_set = {
            '任职要求', '岗位要求', '招聘要求', '职位要求', '工作内容', '岗位职责', '职位描述', '工作职责',
            '福利待遇', '薪资福利', '我们提供', '薪酬福利', '公司简介', '公司介绍', '关于我们',
            '联系方式', '投递方式', '简历发送', '应聘方式', '职位亮点', '团队介绍', '发展空间',
            '专业不限', '学历不限', '经验不限', '性别不限', '年龄不限', '不限专业', '不限学历',
            '不限经验', '无要求', '无硬性要求', '面议', ' negotiable ', '办公软件', '熟练使用办公软件'
        }

        self.generic_verbs = {'提升', '根据', '参与', '协助', '完成', '进行', '定期', '持续', '全面', '了解', '负责',
                              '配合', '学习', '掌握'}

    def _compile_location_detect_pattern(self) -> Optional[Pattern]:
        """
        删除地点
        """
        if not self.locations: return None
        sorted_locs = sorted(self.locations, key=len, reverse=True)
        escaped_locs = [re.escape(loc) for loc in sorted_locs]
        locs_str = "|".join(escaped_locs)
        prefix_group = f"(?:{Patterns.LOCATION_PREFIX.strip()})?"
        suffix_group = r"(?:省 | 市 | 区 | 县 | 路 | 街 | 道 | 镇)?"
        full_pattern = f"{prefix_group}({locs_str}){suffix_group}"
        return re.compile(full_pattern, flags=re.IGNORECASE)

    def _compile_nature_pattern(self) -> Optional[Pattern]:
        """
        删除多余标点符号
        """
        if not self.work_nature_phrases: return None
        sorted_phrases = sorted(self.work_nature_phrases, key=len, reverse=True)
        escaped_phrases = [re.escape(p) for p in sorted_phrases]
        pattern_str = r"(?:^|[,，;；\s/])(" + "|".join(escaped_phrases) + r")(?:[,，;；\s/]|$)"
        return re.compile(pattern_str, flags=re.IGNORECASE)

    def _contains_location(self, text: str) -> bool:
        if not self.location_detect_pattern: return False
        return bool(self.location_detect_pattern.search(text))

    def extract_requirements(self, text: str, clean: bool = True) -> List[str]:
        if not isinstance(text, str): return ["未找到有效要求"]
        raw_lines = self._extract_raw_candidates(text)
        if not raw_lines: return ["未找到有效要求"]
        results = []
        for line in raw_lines:
            if self._contains_location(line): continue
            cleaned_parts = self._clean_requirement_advanced(line) if clean else [line]
            for part in cleaned_parts:
                if self._is_valid_requirement(part):
                    results.append(part)
        return results if results else ["未找到有效要求"]

    def get_requirements_text(self, text: str, clean: bool = True, joiner: str = '；') -> str:
        reqs = self.extract_requirements(text, clean=clean)
        if len(reqs) == 1 and ("未找到" in reqs[0] or "有效要求" in reqs[0]): return reqs[0]
        return joiner.join(reqs)

    def _extract_raw_candidates(self, text: str) -> List[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidates = []
        for line in lines:
            if len(line) < 4: continue
            if self._contains_location(line): continue
            is_title = False
            for pattern in self.compiled_exclude_patterns:
                if pattern.search(line):
                    if len(line) < 10 and any(k in line for k in ['要求', '职责', '内容', '福利']):
                        is_title = True
                        break
            if is_title: continue

            if any(kw in line for kw in self.hard_keywords):
                candidates.append(line)
                continue
            if re.search(Patterns.REQUIREMENT_SIGNALS, line, re.IGNORECASE):
                candidates.append(line)
                continue
            if re.match(Patterns.CAN_OR_KNOW, line):
                candidates.append(line)
        return candidates

    def _clean_requirement_advanced(self, line: str) -> List[str]:
        parts = re.split(Patterns.SENTENCE_SPLITTERS, line)
        parts = [p.strip() for p in parts if p.strip()]
        valid_parts = []
        for part in parts:
            if self._contains_location(part): continue
            cleaned = part
            for step in self.cleaning_steps:
                cleaned = step(cleaned)
                if not cleaned: break

            if cleaned and len(cleaned) >= 2:
                if re.match(r'^[\W]+$', cleaned): continue
                if self.leftover_edu_pattern.fullmatch(cleaned): continue
                valid_parts.append(cleaned)

        if not valid_parts:
            fallback = line
            for step in self.cleaning_steps: fallback = step(fallback)
            if fallback and len(fallback) >= 6 and not self.leftover_edu_pattern.fullmatch(fallback):
                return [fallback]
            return []
        return valid_parts

    def _remove_leading_markers(self, text: str) -> str:
        for pattern in Patterns.LEADING_MARKERS:
            while True:
                new_text = re.sub(pattern, '', text)
                if new_text == text: break
                text = new_text
        return text

    def _remove_education_full(self, text: str) -> str:
        return re.sub(Patterns.EDUCATION_FULL_PATTERN, '', text, flags=re.IGNORECASE)

    # 【新增】去除专业后缀
    def _remove_major_suffix(self, text: str) -> str:
        return self.major_suffix_pattern.sub('', text)

    def _remove_years_experience(self, text: str) -> str:
        return re.sub(Patterns.YEARS_EXPERIENCE, '', text, flags=re.IGNORECASE)

    def _normalize_experience_terms(self, text: str) -> str:
        text = re.sub(Patterns.RELATED_EXPERIENCE, r'\1', text, flags=re.IGNORECASE)
        return text

    def _remove_standalone_related_post(self, text: str) -> str:
        return re.sub(Patterns.STANDALONE_RELATED_POST, '', text, flags=re.IGNORECASE)

    def _remove_work_nature_phrases(self, text: str) -> str:
        if not self.nature_pattern: return text
        cleaned = self.nature_pattern.sub('', text)
        return cleaned.strip()

    def _remove_chinese_brackets(self, text: str) -> str:
        return text.replace('【', '').replace('】', '')

    def _remove_trailing_punctuation(self, text: str) -> str:
        return re.sub(Patterns.TRAILING_PUNCT, '', text)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _filter_symbol_only(self, text: str) -> str:
        if re.match(Patterns.ONLY_SYMBOLS, text): return ""
        return text

    def _is_valid_requirement(self, line: str) -> bool:
        if not line or len(line) < 2: return False
        stripped = line.strip()

        if stripped in self.invalid_title_set: return False
        for pattern in self.compiled_exclude_patterns:
            if pattern.fullmatch(stripped): return False
        if self._contains_location(stripped): return False
        if self.leftover_edu_pattern.fullmatch(stripped): return False

        # 宽泛描述过滤
        if self.vague_pattern.search(stripped):
            has_specific_hard = False
            if re.search(r'[0-9一二两三四五六七八九十]+\s*年', stripped): has_specific_hard = True
            if any(kw in stripped for kw in self.hard_keywords): has_specific_hard = True
            if not has_specific_hard: return False

        # 【核心修改】软技能/通用能力过滤逻辑增强
        # 如果句子包含软技能词，且没有具体的“实体”硬技能（如具体的专业名、工具名），则删除
        has_soft = any(kw in stripped for kw in self.soft_keywords)
        if has_soft:
            # 定义什么是“实体硬技能”：排除掉通用的动词和抽象名词
            # 这里的 hard_keywords 里已经去除了学历，但还包含“经验”、“专业”、“掌握”等通用词
            # 我们需要更严格的检查：是否包含具体的技术/专业名词？
            specific_entities = [
                'Python', 'Java', 'C++', 'JavaScript', 'SQL', 'MySQL', 'Linux', 'AI', '大数据',
                '机械', '电子', '土木', '建筑', '化学', '生物', '物理', '数学', '统计',
                '金融', '财务', '会计', '法律', '医学', '新闻', '设计', '艺术',
                '运营', '产品', '市场', '销售', '人力', '行政', '客服',
                '工业工程', '机械工程', '自动化', '电气', '通信', '计算机', '软件',
                '数据分析', '商业分析', '市场调研', 'SEO', 'SEM', '新媒体',
                '视频剪辑', '后期制作', '3D建模', 'UI', 'UX', '交互设计'
            ]
            has_entity = any(entity in stripped for entity in specific_entities)

            # 如果没有实体技能，只有“能力”、“思维”、“软件”（已列入软技能），则视为无效
            if not has_entity:
                return False

        # 短句过滤 (万能动词 + 无硬技能)
        if len(stripped) < 6:
            has_generic_verb = any(v in stripped for v in self.generic_verbs)
            # 再次检查是否有实体技能
            specific_entities = [
                '机械', '电子', '土木', '建筑', '化学', '生物', '物理', '数学', '统计',
                '金融', '财务', '会计', '法律', '医学', '新闻', '设计', '艺术',
                '运营', '产品', '市场', '销售', '人力', '行政', '客服',
                '工业工程', '机械工程', '自动化', '电气', '通信', '计算机', '软件',
                '数据分析', '商业分析', '市场调研', 'SEO', 'SEM', '新媒体',
                'Python', 'Java', 'C++', 'JavaScript', 'SQL', 'MySQL', 'Linux', 'AI', '大数据'
            ]
            has_entity = any(entity in stripped for entity in specific_entities)

            if has_generic_verb and not has_entity:
                return False

        return True

    def _is_soft_skill_only(self, line: str) -> bool:
        # 此函数逻辑已整合进 _is_valid_requirement 的增强版中，保留以防万一
        has_soft = any(kw in line for kw in self.soft_keywords)
        if not has_soft: return False
        has_hard = any(kw in line for kw in self.hard_keywords)
        has_year = bool(re.search(r'[0-9一二两三四五六七八九十]+年', line))
        return not (has_hard or has_year)


if __name__ == "__main__":
    jd_text = """
湖北省松柏常青养老服务有限公司是一家以居家养老，家政服务，专业保洁，清洗，消毒、保健食品服务等为主营业务的大型服务公司。现面向社会招贤纳士。欢迎广大爱好者积极加入我们的大家庭。
岗位要求：1、统招(211院校)本科及以上学历 计算机科学与技术、软件工程、网络工程等专业毕业;
 2、3年以上网站平台搭建及网页设计相关经验，有完整的企业官网、电商网站或平台类网站设计案例（提供作品集优先考虑）；
 3、熟练掌握 Figma（核心）、Photoshop、Sketch ，UI等设计工具，会使用 Adobe XD、AE 做简单动效者优先；
 4、 具备扎实的视觉设计功底（色彩搭配、排版布局、字体运用），能独立完成从需求分析到设计落地的全流程；
岗位职责：1、负责公司网站平台的搭建及视觉优化，负责shofify的页面设计装修；后期网站内容更新，维护，推流等等；
2、负责网站整体视觉风格设计（含首页、内页、专题页等），输出高保真设计稿、图标、配图等视觉资产；
3、结合公司服务项目设计原则，优化页面布局、交互逻辑，确保设计既美观又符合用户使用习惯；
4、配合前端开发工程师还原设计效果，解决跨设备（PC/移动端）兼容性视觉问题，确保设计落地一致性；
5、 参与需求沟通与方案讨论，结合项目定位、品牌调性输出设计方案，迭代优化现有网站视觉表现；
 
工资：可面谈
    """

    parser = JobDescriptionParser()
    result = parser.get_requirements_text(jd_text, clean=True)

    print("清洗后的技能需求 (已剔除学历/软技能)：")
    print("=" * 50)
    print(result)
    print("=" * 50)

    raw_list = parser.extract_requirements(jd_text, clean=True)
    print("\n提取明细：")
    for i, item in enumerate(raw_list, 1):
        print(f"{i}. {item}")

    print("\n预期结果：")
    print("- 仅保留：工业工程、机械工程、机械电子工程、机械设计及其自动化、数据分析。")
    print("- 删除：所有学历词、软技能（沟通能力/适应能力/逻辑思维/办公软件）、轮岗培训。")