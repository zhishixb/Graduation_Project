from typing import List, Dict, Tuple, Optional


class DisciplineKeywordValidator:
    """
    验证岗位描述与专业名称是否合理匹配。
    针对通用学科（哲学、文学、历史学等）：只排除强排他性内容（工学、医学、法学的关键词），
    不因管理、市场等通用词汇而拒绝。
    """

    # ==================== 默认关键词表（含权重） ====================
    _DEFAULT_KEYWORDS: Dict[str, List[Tuple[str, int]]] = {
        "哲学": [
            ("哲学研究", 2), ("逻辑分析", 2), ("伦理咨询", 2), ("文化研究", 1),
            ("思想史", 2), ("宗教学", 2), ("美学评论", 1), ("批判思维", 1),
            ("思政教师", 2), ("党校", 2), ("形而上学", 2), ("现象学", 2)
        ],
        "经济学": [
            ("金融分析", 2), ("投资银行", 2), ("证券", 2), ("基金", 2), ("期货", 2),
            ("风险管理", 2), ("信贷", 2), ("保险精算", 2), ("财政税务", 2),
            ("国际贸易", 2), ("报关", 2), ("市场调研", 1), ("经济预测", 2),
            ("宏观策略", 1), ("微观定价", 1), ("计量经济学", 2), ("量化交易", 2),
            ("券商", 2), ("信托", 2), ("资产评估", 2), ("精算师", 2)
        ],
        "法学": [
            ("法律顾问", 2), ("律师", 2), ("法务", 2), ("合规", 2), ("知识产权", 2),
            ("专利代理", 2), ("合同审核", 2), ("诉讼", 2), ("仲裁", 2), ("公证", 2),
            ("司法考试", 2), ("法律文书", 2), ("法规解读", 2), ("反垄断", 2),
            ("劳动法", 2), ("律所", 2), ("公检法", 2), ("法律职业资格", 2),
            ("刑法", 2), ("民法", 2)
        ],
        "教育学": [
            ("教师", 2), ("教学", 2), ("课程设计", 2), ("班主任", 2), ("教育咨询", 2),
            ("培训讲师", 2), ("学习管理", 1), ("课件开发", 2), ("幼教", 2),
            ("中小学教育", 2), ("职业教育", 2), ("教育行政", 2), ("教学管理", 2),
            ("辅导员", 2), ("教务", 2), ("教研员", 2), ("学前教育", 2), ("特殊教育", 2)
        ],
        "文学": [
            ("文学编辑", 2), ("记者", 2), ("新媒体运营", 1), ("内容创作", 2),
            ("翻译", 2), ("出版", 2), ("校对", 2), ("撰稿", 2), ("语文教师", 2),
            ("文学评论", 2), ("剧本写作", 2), ("品牌文案", 1), ("文化传播", 1),
            ("汉语言", 2), ("秘书学", 2), ("对外汉语", 2), ("文字记者", 2),
            ("采编", 2), ("古籍整理", 2), ("创意写作", 2), ("新闻学", 2), ("传播学", 2)
        ],
        "历史学": [
            ("考古", 2), ("文物修复", 2), ("博物馆管理", 2), ("文化遗产", 2),
            ("历史研究", 2), ("档案管理", 2), ("地方志", 2), ("策展", 2),
            ("历史编辑", 2), ("文化导游", 1), ("古文献整理", 2), ("党史研究", 2),
            ("世界史", 2), ("中国史", 2), ("文物鉴定", 2)
        ],
        "理学": [
            ("数学建模", 2), ("算法设计", 2), ("统计分析师", 2), ("物理实验", 2),
            ("化学检测", 2), ("生物技术", 2), ("地理信息", 2), ("气象预测", 2),
            ("地质勘探", 2), ("遥感", 2), ("实验室技术", 2), ("科研助理", 2),
            ("科学计算", 2), ("量化分析", 2), ("生物信息", 2), ("应用数学", 2),
            ("统计学", 2), ("心理学", 2), ("认知科学", 2), ("声学", 2), ("光学", 2)
        ],
        "工学": [
            ("Java", 2), ("C++", 2), ("Python", 2), ("Go", 2), ("JavaScript", 2),
            ("Linux", 2), ("MySQL", 2), ("Redis", 2), ("Docker", 2), ("Kubernetes", 2),
            ("CAD", 2), ("SolidWorks", 2), ("PLC", 2), ("Matlab", 2), ("Hadoop", 2),
            ("Spark", 2), ("嵌入式", 2), ("硬件设计", 2), ("电路设计", 2), ("PCB", 2),
            ("单片机", 2), ("FPGA", 2), ("集成电路", 2), ("机械设计", 2), ("结构设计", 2),
            ("自动化控制", 2), ("电气工程", 2), ("建筑结构", 2), ("土木施工", 2),
            ("工程监理", 2), ("网络工程", 2), ("信息安全", 2), ("系统架构", 2),
            ("研发工程师", 2), ("测试工程师", 2), ("运维", 2), ("DevOps", 2),
            ("算法工程师", 2), ("AI开发", 2), ("机器学习", 2), ("深度学习", 2),
            ("计算机视觉", 2), ("自然语言处理", 2), ("大数据开发", 2), ("数据仓库", 2),
            ("计算机", 2), ("软件", 2),
            ("编程", 1), ("开发", 1), ("前端", 1), ("后端", 1), ("全栈", 1),
            ("移动端", 1), ("算法", 1), ("数据", 1), ("系统", 1), ("代码", 1),
            ("管理", 0), ("项目", 0), ("团队", 0), ("沟通", 0)
        ],
        "农学": [
            ("农业技术", 2), ("作物育种", 2), ("植保", 2), ("园艺师", 2),
            ("畜牧兽医", 2), ("动物营养", 2), ("水产养殖", 2), ("食品加工", 2),
            ("农产品质检", 2), ("农业规划", 2), ("土壤修复", 2), ("林业管理", 2),
            ("农药化肥", 2), ("农业推广", 2), ("兽医", 2), ("动植物检疫", 2),
            ("种子工程", 2)
        ],
        "医学": [
            ("临床医生", 2), ("护士", 2), ("药剂师", 2), ("检验技师", 2),
            ("影像诊断", 2), ("康复治疗", 2), ("公共卫生", 2), ("疾病预防", 2),
            ("医院管理", 2), ("医疗器械", 2), ("医药代表", 1), ("中医", 2),
            ("针灸推拿", 2), ("口腔医生", 2), ("眼科", 2), ("儿科", 2), ("妇产科", 2),
            ("外科手术", 2), ("麻醉", 2), ("病理分析", 2), ("执业医师", 2),
            ("护理学", 2), ("药学", 2), ("医学影像", 2), ("精神科", 2), ("全科医生", 2)
        ],
        "管理学": [
            ("人力资源", 2), ("招聘", 2), ("绩效管理", 2), ("薪酬福利", 2),
            ("财务管理", 2), ("会计", 2), ("审计", 2), ("税务", 2), ("出纳", 2),
            ("成本管理", 2), ("供应链管理", 2), ("采购", 2), ("物流", 2), ("仓储", 2),
            ("行政管理", 2), ("秘书", 2), ("前台", 2), ("酒店管理", 2), ("旅游管理", 2),
            ("物业管理", 2), ("工商管理", 2), ("市场营销", 2), ("品牌策划", 2),
            ("电商运营", 2), ("客服管理", 2), ("项目管理", 2),
            ("管理", 1), ("运营", 1), ("策划", 1)
        ],
        "艺术学": [
            ("平面设计", 2), ("UI设计", 2), ("UX设计", 2), ("交互设计", 2),
            ("插画", 2), ("动画制作", 2), ("视频剪辑", 2), ("后期制作", 2),
            ("摄影", 2), ("美术指导", 2), ("音乐制作", 2), ("舞蹈编导", 2),
            ("表演", 2), ("播音主持", 2), ("影视编导", 2), ("舞台设计", 2),
            ("服装设计", 2), ("室内设计", 2), ("游戏原画", 2), ("文创产品", 2),
            ("艺术策展", 2), ("化妆师", 2), ("视觉传达", 2), ("环境设计", 2),
            ("产品设计", 2), ("建筑设计", 2)
        ]
    }

    # ==================== 默认硬性黑名单（强冲突词） ====================
    _DEFAULT_BLACKLIST: Dict[str, List[str]] = {
        # --- 工学 (Engineering) ---
        "工学": [
            # 医学类（绝对不可跨界的硬壁垒）
            "护士", "临床医生", "医师", "医生", "药师", "药剂师", "检验师", "影像师",
            "康复师", "口腔", "眼科", "儿科", "妇产科", "外科", "内科", "中医",
            "针灸", "推拿", "兽医", "手术", "处方", "ICU", "诊疗", "护理", "药理",

            # 法学类（执照壁垒）
            "律师", "法务", "法官", "检察官", "公证员", "诉讼", "仲裁", "辩护",
            "刑法", "民法", "商法", "知识产权代理", "专利代理人", "法律职业资格",

            # 艺术/体育类（天赋壁垒）
            "演员", "模特", "歌手", "舞者", "运动员", "教练员", "裁判", "空姐", "空乘",

            # 极低端/无关岗位（明确降低数据质量的）
            "发传单", "地推", "电话销售", "房产中介", "保险销售", "网管", "装系统",
            "网吧管理", "流水线", "普工", "操作工", "搬运工", "保安", "保洁"
        ],

        # --- 医学 (Medicine) ---
        "医学": [
            # 工学/理学（逻辑与技术壁垒）
            "Java", "C++", "Python", "Go", "JavaScript", "代码", "编程", "开发", "算法",
            "CAD", "SolidWorks", "机械设计", "电路", "PCB", "单片机", "嵌入式", "FPGA",
            "建筑", "土木", "结构", "施工", "测绘", "化工", "数学建模", "物理实验", "计算机",

            # 法学/经管（强竞争性执照/逻辑）
            "律师", "法务", "诉讼", "仲裁", "精算", "证券交易", "期货交易", "投行", "审计",
            "会计证", "注册会计师", "税务师", "建筑师", "结构工程师",

            # 艺术/传媒（非严肃逻辑类）
            "直播", "主播", "网红", "编剧", "导演", "剪辑", "平面设计", "UI设计", "动画"
        ],

        # --- 法学 (Law) ---
        "法学": [
            # 工学/医学（技术与生命壁垒）
            "Java", "编程", "开发", "手术", "临床", "护士", "药剂", "诊疗", "康复",
            "CAD", "机械制图", "电路设计", "建筑施工", "土木工程", "化工", "物理实验",

            # 艺术/体育（非逻辑类）
            "演员", "模特", "歌手", "舞蹈", "运动员", "教练", "空姐", "空乘", "化妆师",

            # 强理工科专业名词
            "医师", "执业药师", "建筑师", "电气工程师", "精算师", "分析师",
            "计算机"
        ],

        # --- 经济学 (Economics) ---
        "经济学": [
            # 强技术壁垒
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",

            # 强执照壁垒
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",

            # 非严肃逻辑类
            "直播", "主播", "演员", "模特", "舞蹈", "运动员"
        ],

        # --- 管理学 (Management) ---
        "管理学": [
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",
            "演员", "模特", "舞蹈", "运动员", "空姐", "计算机"
        ],

        # --- 文学 (Literature) ---
        "文学": [
            # 只保留无法通过短期学习跨越的硬壁垒
            "Java", "C++", "手术", "临床医生", "律师", "法务", "精算师", "注册会计师",
            "建筑师", "电气工程师", "飞行员", "药剂师", "检验师", "计算机"
            # 注意：保留了“销售”、“行政”、“管理”，因为文学/新闻生常从事此类工作
        ],

        # --- 理学 (Science) ---
        "理学": [
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",
            "演员", "模特", "舞蹈", "运动员", "空姐"
        ],

        # --- 教育学 (Education) ---
        "教育学": [
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",
            "演员", "模特", "舞蹈", "运动员", "空姐"
        ],

        # --- 历史学 (History) ---
        "历史学": [
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",
            "演员", "模特", "舞蹈", "运动员", "空姐", "计算机"
        ],

        # --- 哲学 (Philosophy) ---
        "哲学": [
            "Java", "C++", "Python", "编程", "开发", "手术", "临床", "护士", "药剂",
            "CAD", "机械设计", "电路", "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师", "飞行员", "运动员",
            "计算机"
        ],

        # --- 农学 (Agriculture) ---
        "农学": [
            "Java", "编程", "手术", "临床", "护士", "药剂", "CAD", "机械设计", "电路",
            "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师",
            "演员", "模特", "舞蹈", "运动员", "空姐", "计算机"
        ],

        # --- 艺术学 (Art) ---
        "艺术学": [
            "Java", "C++", "Python", "编程", "开发", "手术", "临床", "护士", "药剂",
            "CAD", "机械设计", "电路", "建筑", "土木", "化工", "物理实验", "数学建模",
            "律师", "法务", "注册会计师", "精算师", "医师", "建筑师", "飞行员", "运动员",
            "计算机"
        ]
    }

    # ==================== 验证模式配置 ====================
    _VERIFICATION_MODE = {
        "哲学": "general",
        "文学": "general",
        "历史学": "general",
        "艺术学": "general",
        "教育学": "general",
        "工学": "strict",
        "医学": "strict",
        "法学": "strict",
        "经济学": "strict",
        "管理学": "strict",
        "理学": "strict",
        "农学": "strict",
    }

    def __init__(self,
                 custom_keywords: Optional[Dict[str, List[Tuple[str, int]]]] = None,
                 cross_discipline_factor: Optional[Dict[str, Dict[str, float]]] = None,
                 blacklist: Optional[Dict[str, List[str]]] = None,
                 ratio_threshold: float = 0.5,
                 min_score: float = 1.0,
                 min_total_score: float = 2.0,
                 use_cross_factor: bool = False,
                 use_blacklist: bool = True,
                 general_conflict_disciplines: Optional[List[str]] = None):
        """
        初始化验证器。
        :param custom_keywords: 自定义关键词表 {学科: [(词, 权重), ...]}
        :param cross_discipline_factor: 学科间调节因子矩阵
        :param blacklist: 硬性黑名单 {学科: [词, ...]}
        :param ratio_threshold: 严格模式下本学科得分占比阈值（默认0.5）
        :param min_score: 严格模式下本学科最低得分要求（默认1.0）
        :param min_total_score: 特征不明显阈值，总分低于此值直接保留（默认2.0）
        :param use_cross_factor: 是否启用学科间调节因子
        :param use_blacklist: 是否启用硬性黑名单
        :param general_conflict_disciplines: 通用模式下视为强冲突的学科列表（默认工学、医学、法学）
        """
        # 加载关键词表
        self.keywords = {}
        for disc, kw_list in self._DEFAULT_KEYWORDS.items():
            self.keywords[disc] = {kw: weight for kw, weight in kw_list}
        if custom_keywords:
            for disc, kw_list in custom_keywords.items():
                if disc not in self.keywords:
                    self.keywords[disc] = {}
                for kw, weight in kw_list:
                    self.keywords[disc][kw] = weight

        # 黑名单
        self.blacklist = {}
        if use_blacklist:
            self.blacklist = self._DEFAULT_BLACKLIST.copy()
            if blacklist:
                for disc, words in blacklist.items():
                    if disc not in self.blacklist:
                        self.blacklist[disc] = []
                    self.blacklist[disc].extend(words)

        # 学科间调节因子
        self.cross_factor = cross_discipline_factor or {}
        self.use_cross_factor = use_cross_factor

        self.ratio_threshold = ratio_threshold
        self.min_score = min_score
        self.min_total_score = min_total_score

        # 通用模式下视为强冲突的学科（即“非该专业不可”的学科）
        if general_conflict_disciplines is None:
            self.general_conflict_disciplines = ["工学", "医学", "法学", "农学"]
        else:
            self.general_conflict_disciplines = general_conflict_disciplines

    def _check_blacklist(self, text: str, discipline: str) -> bool:
        """检查文本是否包含当前学科的黑名单词，命中则直接否决"""
        if discipline not in self.blacklist:
            return False
        text_lower = text.lower()
        for kw in self.blacklist[discipline]:
            if kw.lower() in text_lower:
                return True
        return False

    def _get_discipline_scores(self, text: str) -> Dict[str, float]:
        """计算文本中各学科的关键词加权得分"""
        text_lower = text.lower()
        scores = {}
        for disc, kw_dict in self.keywords.items():
            total = 0.0
            for kw, weight in kw_dict.items():
                if weight == 0:
                    continue
                if kw.lower() in text_lower:
                    total += weight
            if total > 0:
                scores[disc] = total
        return scores

    def _apply_cross_factor(self, scores: Dict[str, float], target_discipline: str) -> Dict[str, float]:
        """应用学科间调节因子（可选）"""
        if not self.use_cross_factor:
            return scores
        adjusted = {}
        factor_dict = self.cross_factor.get(target_discipline, {})
        for disc, score in scores.items():
            factor = factor_dict.get(disc, 1.0)
            adjusted[disc] = score * factor
        adjusted[target_discipline] = scores.get(target_discipline, 0)
        return adjusted

    def is_reasonable(self, description: str, major_name: str) -> bool:
        """
        判断岗位描述与专业名称是否合理匹配。
        :param description: 岗位描述文本
        :param major_name: 专业名称（应映射到一级学科名，如“哲学”）
        :return: True 表示保留，False 表示丢弃
        """
        if not description or not description.strip():
            return False

        discipline = major_name.strip()
        if discipline not in self.keywords:
            # 未预定义的学科，保守处理：保留
            return True

        # 1. 黑名单检查（硬性否决）
        if self.blacklist and self._check_blacklist(description, discipline):
            return False

        # 2. 计算得分
        raw_scores = self._get_discipline_scores(description)
        total_score = sum(raw_scores.values())

        # 3. 特征不明显：总分低于阈值，直接保留（避免信息不足误删）
        if total_score < self.min_total_score:
            return True

        mode = self._VERIFICATION_MODE.get(discipline, "strict")

        if mode == "general":
            # 通用模式：只禁止强冲突学科的高权重词（得分≥2）
            # 这些词代表“非该专业不可”的硬技能
            for disc, score in raw_scores.items():
                if disc in self.general_conflict_disciplines and score >= 2.0:
                    return False
            return True

        else:  # strict 模式
            current_score = raw_scores.get(discipline, 0)
            if current_score == 0:
                return False
            scores = self._apply_cross_factor(raw_scores, discipline)
            current_score_adj = scores.get(discipline, 0)
            total_score_adj = sum(scores.values())
            if total_score_adj == 0:
                return False
            ratio = current_score_adj / total_score_adj
            return ratio >= self.ratio_threshold and current_score_adj >= self.min_score

    def get_disciplines(self) -> List[str]:
        return list(self.keywords.keys())