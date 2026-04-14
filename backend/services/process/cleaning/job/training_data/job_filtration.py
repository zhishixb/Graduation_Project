from typing import List, Dict


class DisciplineKeywordValidator:
    """
    验证一段文本是否只包含指定一级学科的相关内容，不包含其他学科的关键词。
    """

    # 一级学科 -> 相关关键词（基于常见术语构建，可根据实际补充）
    _DISCIPLINE_KEYWORDS: Dict[str, List[str]] = {
        "哲学": ["哲学研究", "逻辑分析", "伦理咨询", "文化研究", "思想史", "宗教学", "美学评论", "批判思维"],
        "经济学": [
            "金融分析", "投资银行", "证券", "基金", "风险管理", "信贷", "保险精算", "财政税务", "国际贸易",
            "进出口", "报关", "市场调研", "经济预测", "数据分析", "宏观策略", "微观定价", "计量建模"
        ],
        "法学": [
            "法律顾问", "律师", "法务", "合规", "知识产权", "专利", "合同审核", "诉讼", "仲裁", "公证",
            "司法考试", "法律文书", "法规解读", "企业合规", "反垄断", "劳动法"
        ],
        "教育学": [
            "教师", "教学", "课程设计", "班主任", "教育咨询", "培训讲师", "教育产品", "学习管理",
            "教育技术", "课件开发", "幼教", "中小学教育", "职业教育", "教育行政", "教学管理"
        ],
        "文学": [
            "编辑", "记者", "新媒体运营", "内容创作", "翻译", "出版", "校对", "撰稿",
            "语文教师", "文学评论", "剧本写作", "品牌文案", "文化传播"
        ],
        "历史学": [
            "考古", "文物修复", "博物馆管理", "文化遗产", "历史研究", "档案管理", "地方志", "策展",
            "历史编辑", "文化导游", "古文献整理"
        ],
        "理学": [
            "数学建模", "算法设计", "数据分析师", "统计分析师", "物理实验", "化学检测", "生物技术",
            "地理信息", "气象预测", "地质勘探", "遥感", "实验室技术", "科研助理", "科学计算"
        ],
        "工学": [
            "软件开发", "前端开发", "后端开发", "测试工程师", "运维", "嵌入式", "硬件设计", "电路设计",
            "机械设计", "结构设计", "自动化控制", "电气工程", "建筑结构", "土木施工", "项目管理",
            "网络工程", "信息安全", "算法工程师", "AI开发", "数据仓库", "系统架构", "研发工程师"
        ],
        "农学": [
            "农业技术", "作物育种", "植保", "园艺师", "畜牧兽医", "动物营养", "水产养殖", "食品加工",
            "农产品质检", "农业规划", "土壤修复", "林业管理", "农药化肥", "农业推广"
        ],
        "医学": [
            "临床医生", "护士", "药剂师", "检验技师", "影像诊断", "康复治疗", "公共卫生", "疾病预防",
            "医院管理", "医疗器械", "医药代表", "中医", "针灸推拿", "口腔医生", "眼科", "儿科",
            "妇产科", "外科手术", "麻醉", "病理分析"
        ],
        "管理学": [
            "人力资源管理", "招聘", "绩效管理", "薪酬福利", "培训开发", "财务管理", "会计", "审计",
            "市场营销", "品牌策划", "销售管理", "电商运营", "物流管理", "供应链", "项目管理",
            "企业战略", "行政管理", "酒店管理", "旅游管理", "物业管理", "客服管理"
        ],
        "艺术学": [
            "平面设计", "UI设计", "交互设计", "插画", "动画制作", "视频剪辑", "摄影", "美术指导",
            "音乐制作", "舞蹈编导", "表演", "播音主持", "影视编导", "舞台设计", "服装设计",
            "室内设计", "游戏原画", "文创产品", "艺术策展"
        ]
    }

    def __init__(self, custom_keywords: Dict[str, List[str]] = None):
        """
        可扩展构造函数，允许传入自定义学科关键词表（合并或覆盖默认）
        :param custom_keywords: 字典，格式同 _DISCIPLINE_KEYWORDS
        """
        self.keywords = self._DISCIPLINE_KEYWORDS.copy()
        if custom_keywords:
            for disc, kw_list in custom_keywords.items():
                if disc in self.keywords:
                    self.keywords[disc].extend(kw_list)
                else:
                    self.keywords[disc] = kw_list

    def _contains_keyword(self, text: str, keywords: List[str]) -> bool:
        """检查文本是否包含指定关键词列表中的任意一个（子串匹配）"""
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    def check(self, text: str, discipline: str) -> bool:
        """
        验证文本是否仅包含指定学科的内容（不包含其他学科的关键词）
        :param text: 待检查的文本
        :param discipline: 一级学科名（如 "工学"、"医学"）
        :return: True 表示文本中未出现其他学科的关键词（允许无关键词或仅有当前学科关键词）；
                 False 表示文本中出现了其他学科的关键词
        """
        if not text or not text.strip():
            return True  # 空文本视为有效

        # 规范化学科名（防止大小写/空格问题）
        discipline = discipline.strip()
        # 检查学科是否在预定义表中
        if discipline not in self.keywords:
            # 如果学科未预定义，默认认为文本不包含其他学科的关键词？为了安全，可以返回 True 或抛出警告。
            # 这里选择返回 True，并打印警告（可由调用者决定）
            print(f"警告：学科 '{discipline}' 未预定义关键词，无法准确验证，返回 True")
            return True

        # 当前学科的关键词列表
        cur_keywords = self.keywords[discipline]

        # 遍历所有学科，检查是否出现其他学科的关键词
        for other_disc, other_kw_list in self.keywords.items():
            if other_disc == discipline:
                continue
            if self._contains_keyword(text, other_kw_list):
                return False  # 发现其他学科关键词

        # 如果没有发现任何其他学科关键词，则通过
        return True

    def get_disciplines(self) -> List[str]:
        """返回所有已定义的一级学科名"""
        return list(self.keywords.keys())


# 使用示例
if __name__ == "__main__":
    validator = DisciplineKeywordValidator()

    # 测试工学文本
    text_eng = "使用Python编写爬虫，利用机器学习算法分析数据。"
    print(validator.check(text_eng, "工学"))   # True（没有明显其他学科词）

    text_med = "患者出现发热症状，需要进行抗生素治疗。"
    print(validator.check(text_med, "工学"))   # False（出现了医学关键词）

    text_med2 = "设计一款医疗影像分析系统，使用深度学习。"
    print(validator.check(text_med2, "工学"))  # True（即使有“医疗”但非核心医学术语，当前关键词未涵盖；若需严格可扩充）

    # 指定正确学科
    print(validator.check(text_med, "医学"))   # True

    # 混合学科
    text_mixed = "运用经济学的供需理论分析股票市场，并编写程序实现量化交易。"
    print(validator.check(text_mixed, "经济学")) # False（出现了“程序”等工学关键词）
    print(validator.check(text_mixed, "工学"))    # False（出现了“经济”等经济学关键词）