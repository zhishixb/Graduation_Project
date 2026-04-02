import re
from typing import List


class SimpleExtractor:
    # 1. 定义目标关键词
    DUTY_KEYWORDS = ['岗位职责', '工作职责', '职责描述', '工作内容', '主要职责']
    REQ_KEYWORDS = ['任职要求', '职位要求', '岗位要求', '招聘要求', '资格要求', '任职资格']

    # 2. 定义废弃关键词
    ABANDON_KEYWORDS = [
        '福利', '薪资', '薪酬', '工资', '待遇',
        '晋升', '加薪', '奖金', '提成',
        '五险一金', '年假', '团建', '旅游',
        '工作地点', '办公地点', '公司地址',
        '联系方式', '邮箱', '电话', '投递',
        '公司优势', '公司介绍', '我们是谁'
    ]

    def extract(self, text: str) -> List[List[str]]:  # 修改返回类型：列表的列表
        lines = text.splitlines()
        sections = []

        current_type = None
        current_content = []

        for line in lines:
            line_stripped = line.strip()

            # --- 废弃词过滤 ---
            if current_type and any(kw in line_stripped for kw in self.ABANDON_KEYWORDS):
                continue

            # 1. 检查是否是目标标题行
            found_type = None
            for kw in self.DUTY_KEYWORDS:
                if kw in line_stripped:
                    found_type = 'duty'
                    break
            if not found_type:
                for kw in self.REQ_KEYWORDS:
                    if kw in line_stripped:
                        found_type = 'req'
                        break

            # 2. 逻辑处理
            if found_type:
                # --- 发现新目标标题 ---
                if current_type and current_content:
                    sections.append(current_content)  # 直接存列表，不合并

                # 开启新段落
                current_type = found_type
                current_content = []

            elif current_type:
                # --- 正在提取内容中 ---
                if not line_stripped:
                    if current_content:
                        sections.append(current_content)
                        current_type = None
                        current_content = []
                elif len(line_stripped) < 7 and not line_stripped.startswith('-') and not line_stripped.startswith(
                        '[') and not line_stripped.startswith('【'):
                    if current_content:
                        sections.append(current_content)
                        current_type = None
                        current_content = []
                else:
                    # 正常内容，加入列表
                    current_content.append(line_stripped)

        # 3. 处理最后一段
        if current_type and current_content:
            sections.append(current_content)

        return sections


class LineCleaner:
    KEYWORD_BLACKLIST = [
        # 福利与待遇
        '福利', '薪资', '薪酬', '工资', '待遇', '五险一金', '年终奖',
        '奖金', '补贴', '补助', '年假', '带薪', '团建', '旅游', '体检',
        '晋升', '提成', '股票', '期权',

        # 公司与地址
        '公司', '集团', '总部', '部门',
        '工作地点', '办公地点', '地址', '市', '县', '区',

        # 联系方式
        '联系方式', '邮箱', '电话', '微信', 'QQ', '简历', '投递',

        # 模糊/兜底条款
        '其他', '临时', '交办', '上级', '领导', '安排', '任务', '事宜',

        # 要求
        '岁', '气质', '能力优秀', '违法', '驾照', '年以上工作经验', '年工作经验',

        # 状态表示
        '热爱', '反馈', '出差', '顺利开展', '发展趋势', '提供', '总结', '顺利进行',
        '盈利', '提升', '淘汰', '结果', '长期', '浓厚兴趣', '成功', '文化氛围',
        '工作环境',

        # 宽泛的工作内容
        '实操指导', '利润', '全面评估', '项目进度', '保障', '资源调配', '风险',
        '推动',

        # 软技能
        '抗压能力', '学习能力', '沟通', '职业发展', '团队', '团体',
        '吃苦耐劳', '勤奋', '踏实', '认真', '细致', '细心', '积极', '主动',
        '服从', '形象', '气质', '口齿', '表达', '思维敏捷', '应变',
        '职业道德', '敬业精神', '责任心', '事业心', '激情', '自信', '执行力',

        # 学历
        '本科', '毕业生', '不限', '应届生',
    ]

    def __init__(self):
        # 序号匹配正则
        self.pattern = re.compile(
            r'^\s*' +
            r'(?:' +
            r'[-•●▪▸➢➔➣➤➥➦➧➨➩➪➫➬➭➮➯➱➲➳➴➵➶➷➸➹➺➻➼➽➾]' +
            r'|' +
            r'[0-9]+[\.、\)]' +
            r'|' +
            r'[一二三四五六七八九十]+[、\.．]' +
            r'|' +
            r'[(（][0-9]+[)）]' +
            r'|' +
            r'[(（][一二三四五六七八九十]+[)）]' +
            r'|' +
            r'【[0-9]+】' +
            r')' +
            r'\s*'
        )

        # 年限匹配正则
        self.year_pattern = re.compile(
            r'\d+[-~]\d+年(?:以上|及以下|及以上)?' +
            r'|' +
            r'\d+(?:\.\d+)?年(?:及)?以上' +
            r'|' +
            r'[一二三四五六七八九十\d]+年以上' +
            r'|' +
            r'(?:不少于|不低于|超过|多于)\d+(?:\.\d+)?年(?:以上|及以下|及以上)?'
        )

    def clean_line(self, line: str) -> str:
        # --- 第一步：去除行首序号 ---
        line = self.pattern.sub('', line)

        # --- 第二步：按逗号分割并过滤 ---
        parts = re.split(r'[，,]', line)
        valid_parts = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # 1. 检查是否包含废弃词（整段丢弃）
            if any(kw in part for kw in self.KEYWORD_BLACKLIST):
                continue

            # 2.局部清洗（去除年限，保留其余内容）
            part = self.year_pattern.sub('', part)

            # 清洗后再次去除首尾空格（因为删除了中间的词，可能留下多余空格）
            part = part.strip()

            # 如果清洗后不为空，则保留
            if part:
                valid_parts.append(part)

        return "，".join(valid_parts)

    def clean_lines(self, lines: List[str]) -> List[str]:
        return [self.clean_line(line) for line in lines]