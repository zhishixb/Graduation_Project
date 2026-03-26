import re
from typing import List, Optional, Callable, Set, Pattern

# ================== 全局配置区域 ==================

GLOBAL_SOFT_KEYWORDS = [
    '思维', '灵活', '吃苦', '耐劳', '责任心', '团队意识', '团队', '合作',
    '沟通', '协作', '抗压', '学习能力', '积极', '主动',
    '认真', '务实', '好胜心', '荣誉感', '挑战',
    '适应力', '适应能力', '环境适应', '精神', '承受能力'
    '兴趣', '热情', '轮岗', '培训', '表达', '亲和力', '执行力',
    '逻辑思维', '办公软件', 'office', 'word', 'excel', 'ppt', '综合素质', '潜能'
]

GLOBAL_HARD_KEYWORDS = [
    '证书', '资格', '六级', '四级', '雅思', '托福', '普通话',
    '经验', '相关经验', '项目经验', '实习经验', '销售经验',
    '熟悉', '掌握', '了解', '精通', '使用', '会', '能',
    '工具', '软件', '系统', '平台', '框架', '语言', '数据库',
    '专业', '相关专业', '教学',
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
    '工业工程', '机械工程', '机械电子', '机械设计', '自动化', '电气', '材料', '化学工程'
]

GLOBAL_WORK_NATURE_PHRASES = [
    '适应频繁出差', '适应出差', '能接受出差', '可接受出差', '经常出差',
    '适应加班', '能接受加班', '可接受加班', '偶尔加班', '高强度工作',
    '适应快节奏', '抗压能力强', '能承受较大工作压力',
    '服从公司安排', '服从调配', '适应弹性工作',
    '愿意从基层做起', '吃苦耐劳', '具备良好的职业道德',
    '适应力强', '适应力佳', '适应能力佳', '适应能力强',
    '接受轮岗', '轮岗培训', '带薪培训', '统一培训', '入职培训',

    # ================== 新增内容 ==================
    '培训资源丰富', '海外培训', '出国培训', '培训机会',
    '职业进阶', '职业晋升', '晋升空间', '发展空间', '成长空间',
    '助力职业', '广阔的晋升平台', '完善的培训体系',
    '沟通表达能力', '性格外向', '活泼', '吃苦耐劳', '上进心', '野心',
    '想赚钱', '付诸行动', '素质好', '心态良好', '规范行为', '形象',
    '团队合作', '团队精神', '抗压能力', '适应力', '学习能力',
]

GLOBAL_COMMON_LOCATIONS = {
    '北京', '上海', '天津', '重庆', '广州', '深圳', '杭州', '南京', '武汉', '成都', '西安', '苏州', '郑州',
    '长沙', '沈阳', '青岛', '宁波', '无锡', '福州', '厦门', '合肥', '大连', '济南', '哈尔滨', '长春', '石家庄',
    '昆明', '南昌', '贵阳', '太原', '南宁', '海口', '兰州', '银川', '西宁', '乌鲁木齐', '拉萨', '呼和浩特',
    '鄂尔多斯', '烟台', '温州', '东莞', '佛山', '常州', '徐州', '南通', '泉州', '惠州', '珠海', '中山',
    '扬州', '泰州', '嘉兴', '绍兴', '洛阳', '开封', '桂林', '三亚', '秦皇岛', '保定', '唐山', '廊坊'
}

GLOBAL_PATTERNS = {
    'leading_markers': [
        r'^\s*\d+[\.\)、，：:\-\s](?![年岁个])',
        r'^\s*[①②③④⑤⑥⑦⑧⑨⑩][\s\.\)、]*',
        r'^\s*[一二三四五六七八九十]+[\.、，\s](?![年岁个])',
        r'^\s*[a-zA-Z][\.\)\s]*',
        r'^\s*[\-–—•●◆▶★\*]+[\s\-–—•●◆▶★\*]*',
        r'^\s*[\(\[【]?[a-zA-Z\d]+[\)\]】]?[\s\.\)、:\-\s]*',
        r'^\s*[>＞»›]+[\s]*',
    ],
    'education_full': r'(?:985|211|双一流|重点大学|知名高校)?[/\s]*(?:本科|硕士|博士|大专|专科|研究生|海归|留学)?(?:及以上|以上|全日制)?(?:学历|学位)?\s*[，,、]?\s*',
    'major_suffix': r'\s*(?:等相关?(?:专业)?)?\s*(?:优先 | 者优先 | 为佳 | 均可 | 背景)?\s*[,.。;；]?\s*$',
    'years_experience': r'(?:[0-9]+|[一二两三四五六七八九十]+)\s*年\s*(?:及)?\s*(?:以上|以下|以内|左右)?\s*(?:相关(?:岗位|经验)|工作(?:经验|经历))?',
    'related_experience': r'(?:相关|工作)(经验|经历)',
    'standalone_related_post': r'相关岗位',
    'requirement_signals': r'(需 | 要求 | 具备 | 有.*[0-9一二两三四五六七八九十]+年 | 至少 | 以上 | 优先 | 加分 | 可接受 | 放宽)',
    'can_or_know': r'^(能 | 会 | 可)[\u4e00-\u9fa5a-zA-Z]',
    'trailing_punct': r'[。.;；]+$',
    'only_symbols': r'^[\W\s]{3,}$',
    'location_prefix': r'(?:驻 | 位于 | 工作在 | 地点 [:：]?|base 在|base 地 [:：]?)\s*',
    'sentence_splitters': r'[，,;；/]',
    'vague_pattern': r'(?:不限 | 无经验 | 无需经验 | 零基础 | 应届 | 毕业生 | 小白 | 入门 | 可培训 | 带薪培训)',
    'leftover_edu': r'(?:985|211|双一流|本科|硕士|博士|大专|专科|研究生|学历|学位)',
    # 匹配括号及其内容（包括中文全角和英文半角）
    'brackets_content': r'[（(][^）)]*[）)]',
    # 匹配 Emoji 表情和常见特殊符号 (✅ 🔥 ➕ ★ 等)
    'special_symbols': r'[✅❌🔥★☆●○▲△■□►◄➕➖➗💰📌📍👉👇🌟✨💡🛠️🔧🔨📢📣🔔🔕🚀🌈💪👍👎🙏💼🏢🏭🏬]'
}

GLOBAL_TITLE_EXCLUDE_PATTERNS = [
    r'[【\[\(]?任职要求 [】\]\)]?', r'[【\[\(]?岗位要求 [】\]\)]?',
    r'[【\[\(]?招聘要求 [】\]\)]?', r'[【\[\(]?职位要求 [】\]\)]?',
    r'[【\[\(]?工作内容 [】\]\)]?', r'[【\[\(]?岗位职责 [】\]\)]?',
    r'[【\[\(]?加分项[】\]\)]?',
    r'[【\[\(]?备注[】\]\)]?',
    r'[【\[\(]?注[：:：\s]?',
    r'[【\[\(]?说明[】\]\)]?',
    r'[【\[\(]?特别说明[】\]\)]?',
    r'[【\[\(]?薪资福利[】\]\)]?',
    r'[【\[\(]?薪资待遇[】\]\)]?',
    r'[【\[\(]?岗位升职空间[】\]\)]?',
    r'[【\[\(]?晋升空间[】\]\)]?',
    r'[【\[\(]?面试流程[】\]\)]?',
    r'[【\[\(]?职位描述 [】\]\)]?', r'Requirements?:?',
    r'Job Description:?', r'Responsibilities?:?'
]


class JobDescriptionParser:
    def __init__(
            self,
            soft_keywords: Optional[List[str]] = None,
            hard_keywords: Optional[List[str]] = None,
            custom_cleaning_steps: Optional[List[Callable[[str], str]]] = None,
            location_list: Optional[Set[str]] = None,
            work_nature_phrases: Optional[List[str]] = None,
            target_section_titles: Optional[List[str]] = None,  # 新增参数
    ):
        self.soft_keywords = set(soft_keywords or GLOBAL_SOFT_KEYWORDS)
        self.hard_keywords = set(hard_keywords or GLOBAL_HARD_KEYWORDS)
        self.locations = location_list or GLOBAL_COMMON_LOCATIONS
        self.work_nature_phrases = work_nature_phrases or GLOBAL_WORK_NATURE_PHRASES

        # 新增：目标区域标题配置
        self.target_section_titles = target_section_titles or [
            '岗位职责', '工作职责', '职责描述',
            '任职要求', '职位要求', '岗位要求', '招聘要求', '资格要求'
        ]
        # 编译标题匹配正则（支持序号、冒号等）
        title_pattern = r'^[一二三四五六七八九十、①②③\d]*[\.、）)]*\s*(?:' + \
                        '|'.join(re.escape(title) for title in self.target_section_titles) + \
                        r')\s*[:：]?\s*'
        self.title_pattern = re.compile(title_pattern, re.IGNORECASE)

        # 新增：通用标题边界正则（匹配任何类似标题的行，用于终止区域）
        self.general_title_pattern = re.compile(
            r'^\s*(?:[一二三四五六七八九十]+|[①②③④⑤⑥⑦⑧⑨⑩]|\d+)[、.．\)]?\s*[^:：]+[:：]?\s*$',
            re.IGNORECASE
        )

        self.location_detect_pattern = self._compile_location_detect_pattern()
        self.nature_pattern = self._compile_nature_pattern()
        self.vague_pattern = re.compile(GLOBAL_PATTERNS['vague_pattern'], re.IGNORECASE)
        self.leftover_edu_pattern = re.compile(GLOBAL_PATTERNS['leftover_edu'], re.IGNORECASE)
        self.major_suffix_pattern = re.compile(GLOBAL_PATTERNS['major_suffix'], re.IGNORECASE)
        # 预编译括号正则
        self.brackets_pattern = re.compile(GLOBAL_PATTERNS['brackets_content'])

        self.cleaning_steps = custom_cleaning_steps or [
            self._remove_years_experience,
            self._remove_education_full,
            self._remove_major_suffix,
            self._normalize_experience_terms,
            self._remove_standalone_related_post,
            # self._remove_work_nature_phrases,
            self._remove_brackets_content,
            self._remove_special_symbols,
            self._remove_chinese_brackets,
            self._remove_leading_markers,
            self._remove_trailing_punctuation,
            self._normalize_whitespace,
            self._filter_symbol_only,
            self._filter_blacklist_phrases,
        ]

        self.compiled_exclude_patterns = [re.compile(p, re.IGNORECASE) for p in GLOBAL_TITLE_EXCLUDE_PATTERNS]

    def _compile_location_detect_pattern(self) -> Optional[Pattern]:
        if not self.locations: return None
        sorted_locs = sorted(self.locations, key=len, reverse=True)
        escaped_locs = [re.escape(loc) for loc in sorted_locs]
        locs_str = "|".join(escaped_locs)
        prefix_group = f"(?:{GLOBAL_PATTERNS['location_prefix'].strip()})?"
        suffix_group = r"(?:省 | 市 | 区 | 县 | 路 | 街 | 道 | 镇)?"
        full_pattern = f"{prefix_group}({locs_str}){suffix_group}"
        return re.compile(full_pattern, flags=re.IGNORECASE)

    def _compile_nature_pattern(self) -> Optional[Pattern]:
        if not self.work_nature_phrases: return None
        sorted_phrases = sorted(self.work_nature_phrases, key=len, reverse=True)
        escaped_phrases = [re.escape(p) for p in sorted_phrases]
        pattern_str = r"(?:^|[,，;；\s/])(" + "|".join(escaped_phrases) + r")(?:[,，;；\s/]|$)"
        return re.compile(pattern_str, flags=re.IGNORECASE)

    def _contains_location(self, text: str) -> bool:
        if not self.location_detect_pattern: return False
        return bool(self.location_detect_pattern.search(text))

    # ================== 提取目标标题区域 ==================
    def _get_target_sections(self, text: str) -> List[str]:
        """提取目标标题下的所有行（不含标题行本身），遇到任何其他标题则终止当前区域"""
        lines = text.splitlines()
        sections = []
        current_block = []
        active = False

        for line in lines:
            line_stripped = line.strip()
            # 判断是否为目标标题
            target_match = self.title_pattern.search(line_stripped)
            # 判断是否为通用标题（包括目标标题和其他标题）
            is_any_title = target_match or self.general_title_pattern.match(line_stripped)

            if target_match:
                # 遇到目标标题：关闭之前的区域（如果有）
                if active and current_block:
                    sections.extend(current_block)
                    current_block = []
                    active = False
                # 激活新区域
                active = True
                # 标题行剩余内容加入当前块
                remainder = self.title_pattern.sub('', line_stripped).strip()
                if remainder:
                    current_block.append(remainder)
            elif is_any_title:
                # 遇到非目标的通用标题：仅关闭当前区域，不激活新区域
                if active and current_block:
                    sections.extend(current_block)
                    current_block = []
                    active = False
                # 其他标题行的内容不收集
            else:
                # 普通行：若区域激活则收集
                if active:
                    current_block.append(line_stripped)

        # 处理最后一个区域
        if active and current_block:
            sections.extend(current_block)

        return sections

    def extract_requirements(self, text: str, clean: bool = True) -> List[str]:
        if not isinstance(text, str):
            return ["未找到有效要求"]

        # 第一步：提取目标标题区域的行
        target_lines = self._get_target_sections(text)
        if not target_lines:
            return ["未找到有效要求"]

        # 将目标区域的行合并为字符串（保留原始换行结构）
        region_text = '\n'.join(target_lines)

        # 后续处理保持不变，使用原有逻辑
        raw_lines = self._extract_raw_candidates(region_text)
        if not raw_lines:
            return ["未找到有效要求"]

        results = []
        for line in raw_lines:
            if self._contains_location(line):
                continue
            cleaned_parts = self._clean_requirement_advanced(line) if clean else [line]
            for part in cleaned_parts:
                if part:
                    results.append(part)

        return results if results else ["未找到有效要求"]

    def get_requirements_text(self, text: str, clean: bool = True, joiner: str = '；') -> str:
        reqs = self.extract_requirements(text, clean=clean)
        if len(reqs) == 1 and ("未找到" in reqs[0] or "有效要求" in reqs[0]):
            return reqs[0]
        return joiner.join(reqs)

    def _extract_raw_candidates(self, text: str) -> List[str]:
        preprocessed_text = re.sub(r'[:：]', '\n', text)
        lines = preprocessed_text.splitlines()
        filtered_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            is_list_item = False
            if re.match(r'^\s*(\d+|[一二三四五六七八九十]+|[①②③])[\.、\)\s]', line):
                is_list_item = True
            if len(line) < 60:
                if any(kw in line for kw in self.hard_keywords) or re.search(GLOBAL_PATTERNS['requirement_signals'],
                                                                             line):
                    is_list_item = True
            if is_list_item:
                filtered_lines.append(line)

        text = '\n'.join(filtered_lines)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidates = []

        for line in lines:
            if len(line) < 4:
                continue
            if self._contains_location(line):
                continue
            is_title = False
            for pattern in self.compiled_exclude_patterns:
                if pattern.search(line):
                    if len(line) < 10 and any(k in line for k in ['要求', '职责', '内容', '福利']):
                        is_title = True
                        break
            if is_title:
                continue

            if any(kw in line for kw in self.hard_keywords):
                candidates.append(line)
                continue
            if re.search(GLOBAL_PATTERNS['requirement_signals'], line, re.IGNORECASE):
                candidates.append(line)
                continue
            if re.match(GLOBAL_PATTERNS['can_or_know'], line):
                candidates.append(line)
        return candidates

    def _clean_requirement_advanced(self, line: str) -> List[str]:
        parts = re.split(GLOBAL_PATTERNS['sentence_splitters'], line)
        parts = [p.strip() for p in parts if p.strip()]
        valid_parts = []

        for part in parts:
            if self._contains_location(part):
                continue
            cleaned = part
            for step in self.cleaning_steps:
                cleaned = step(cleaned)
                if not cleaned:
                    break

            if cleaned and len(cleaned) >= 2:
                if re.match(r'^[\W]+$', cleaned):
                    continue
                if self.leftover_edu_pattern.fullmatch(cleaned):
                    continue
                valid_parts.append(cleaned)

        if not valid_parts:
            fallback = line
            for step in self.cleaning_steps:
                fallback = step(fallback)
            if fallback and len(fallback) >= 6 and not self.leftover_edu_pattern.fullmatch(fallback):
                return [fallback]
            return []
        return valid_parts

    # ================== 清洗步骤方法 ==================

    def _remove_leading_markers(self, text: str) -> str:
        for pattern in GLOBAL_PATTERNS['leading_markers']:
            while True:
                new_text = re.sub(pattern, '', text)
                if new_text == text:
                    break
                text = new_text
        return text

    def _remove_education_full(self, text: str) -> str:
        return re.sub(GLOBAL_PATTERNS['education_full'], '', text, flags=re.IGNORECASE)

    def _remove_major_suffix(self, text: str) -> str:
        return self.major_suffix_pattern.sub('', text)

    def _remove_years_experience(self, text: str) -> str:
        return re.sub(GLOBAL_PATTERNS['years_experience'], '', text, flags=re.IGNORECASE)

    def _normalize_experience_terms(self, text: str) -> str:
        text = re.sub(GLOBAL_PATTERNS['related_experience'], r'\1', text, flags=re.IGNORECASE)
        return text

    def _remove_standalone_related_post(self, text: str) -> str:
        return re.sub(GLOBAL_PATTERNS['standalone_related_post'], '', text, flags=re.IGNORECASE)

    def _remove_work_nature_phrases(self, text: str) -> str:
        if not self.nature_pattern:
            return text
        cleaned = self.nature_pattern.sub('', text)
        return cleaned.strip()

    # 【新增】去除括号及其内容
    def _remove_brackets_content(self, text: str) -> str:
        return self.brackets_pattern.sub('', text)

    def _remove_chinese_brackets(self, text: str) -> str:
        # 这一步作为兜底，去除可能残留的单独括号
        return text.replace('【', '').replace('】', '')

    def _remove_trailing_punctuation(self, text: str) -> str:
        return re.sub(GLOBAL_PATTERNS['trailing_punct'], '', text)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def _filter_symbol_only(self, text: str) -> str:
        if re.match(GLOBAL_PATTERNS['only_symbols'], text):
            return ""
        return text

    # 去除 Emoji 和特殊装饰符号
    def _remove_special_symbols(self, text: str) -> str:
        # 使用正则替换特殊符号为空字符串
        cleaned_text = re.sub(GLOBAL_PATTERNS['special_symbols'], '', text)
        # 替换后可能会产生多余的空格（例如 "✅ 职责" 变成 "  职责"），需要再次标准化空格
        return re.sub(r'\s+', ' ', cleaned_text).strip()

    def _filter_blacklist_phrases(self, text: str) -> str:
        """
        专门用于在句子切分后，过滤掉包含黑名单关键词的整行。
        这一步放在清洗流程的靠后位置。
        """
        blacklist = self.work_nature_phrases or []
        for phrase in blacklist:
            if phrase in text:
                return ""
        return text


if __name__ == "__main__":
    jd_text = """
南通复源新材公司主营碳纤维复合材料回收与再利用，是全球碳纤维回收再利用领域的领军企业。碳纤维及复合材料废弃物回收处理能力和业务量居全球领先。技术及核心团队均来自上海交通大学化学化工学院。
公司主要产品是短切碳纤维，产品包括PCR-CF、PIR-CF以及原生CF等三类来源、90余种规格，是短碳纤维产品分类标准、质量标准的制定者。产品主要客户是改性塑料企业、热固SMC/BMC企业，终端应用领域是高端消费电子、新能源汽车轨交、无人机、3D打印、高端体育休闲用品及航空航天。
公司总部在南通，研发中心在上海，在华南、西南地区分别设有办事处。公司正处在快速发展阶段，经营理念是以客户为中心、以创新为驱动、质量至上、可持续发展。


产品工程师助理、工艺工程师助理
一、岗位职责：
1、开发短切碳纤维新产品：负责新产品开发实验的实施及生产导入的落实与跟踪，及时记录、整理实验/生产数据、图片，并输出报告； 
2、管设备：负责实验室仪器设备的日常操作、维护、管理； 
3、收集制作技术资料：查阅文献，协助研发工程师，制作各类工艺、产品和技术资料；
4、其他：完成上级交办的其他临时工作。
二、任职要求：
（必须条件）本科或以上学历；高分子材料、复合材料、化学、化工相关专业；
1、为人诚实、敬业、上进心强；
2、熟练制作文档、图表，熟悉Word，Excel等基本的软件操作；
3、具备一定的文献检索、查阅、归纳分析能力； 
4、有实验室安全意识，动手能力强，善于思考，能积极寻找解决实验问题的方法；
5、学习能力强，善于沟通，有团队合作精神。
三、员工福利：
1、法定节假日公休假及福利性假期；
2、节日礼品（春节、三八妇女节、端午节、儿童节、中秋节、国庆节）、婚礼贺金、住院尉问金、防暑降温费；
3、13薪、入职即交五险一金；
4、其他福利：免费提供人才公寓、通讯补贴、餐饮补贴、定期体检、旅游和团建活动、全勤奖、加班补贴、带薪年假、年终奖金、专业培训；
5、公司属于科技创新人才引进综合补贴企业，符合条件的大学生本科以上者可享受政府每月1000至3000元生活补贴、购房补贴等。
工作地：南通市通州区
社保缴纳地：南通
"""

    parser = JobDescriptionParser()
    result = parser.get_requirements_text(jd_text, clean=True)

    print("清洗后的技能需求 (已去除括号内容)：")
    print("=" * 50)
    print(result)
    print("=" * 50)

    raw_list = parser.extract_requirements(jd_text, clean=True)
    print("\n提取明细：")
    for i, item in enumerate(raw_list, 1):
        print(f"{i}. {item}")