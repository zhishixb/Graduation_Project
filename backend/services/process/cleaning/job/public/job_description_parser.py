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

    CONTENT_KEYWORDS = {
        # 编程语言（含缩写）
        'java', 'python', 'c++', 'c#', 'go', 'rust', 'r', 'ruby', 'php', 'swift',
        'kotlin', 'scala', 'perl', 'lua', 'dart', 'julia', 'ts', 'js', 'html', 'css',

        # 数据库与缓存
        'sql', 'nosql', 'mysql', 'redis', 'mongo', 'oracle', 'db2', 'hbase', 'cas',
        'es', 'solr', 'neo4j', 'cass',  # cass 为 Cassandra 常见缩写

        # 框架与库（缩写/短名）
        'react', 'vue', 'node', 'next', 'nuxt', 'flask', 'django', 'spring', 'keras',
        'pandas', 'numpy', 'scrapy', 'k8s', 'babel', 'vite', 'cmake', 'gdb', 'llvm',

        # 开发工具与版本控制
        'git', 'svn', 'docker', 'maven', 'gradle', 'npm', 'yarn', 'eslint', 'webpack',

        # 云平台与基础设施
        'aws', 'gcp', 'azure', 'k8s', 'oci', '阿里云', '腾讯云', '华为云',

        # 操作系统与命令行
        'linux', 'unix', 'macos', 'bsd', 'cli', 'shell', 'bash', 'zsh',

        # 网络与协议
        'tcp', 'udp', 'http', 'https', 'ftp', 'ssh', 'ssl', 'tls', 'dns', 'dhcp',
        'ip', 'arp', 'mqtt',

        # 数据科学、AI与算法
        'ai', 'ml', 'nlp', 'cv', 'ocr', 'asr', 'rl', 'gan', 'etl', 'bi', 'olap',
        'spark', 'hadoop', 'flink', 'storm', 'kafka', 'hive', 'pig',

        # 认证与标准
        'pmp', 'cfa', 'cpa', 'acca', 'cisa', 'cissp', 'ceh', 'cism', 'itil', 'togaf',
        'scrum', 'agile',

        # 设计与多媒体
        'ps', 'ai', 'ae', 'pr', 'cad', '3d', 'ui', 'ux', 'sketch', 'figma', 'maya',
        'unity', 'unreal',

        # 企业管理与业务系统
        'erp', 'crm', 'scm', 'hrm', 'bi', 'sap', '金蝶', '用友', '钉钉', '飞书',
        '企业微信',

        # 常用技术缩写
        'api', 'sdk', 'ide', 'cli', 'gui', 'jit', 'aop', 'oop', 'ioc', 'di', 'orm',
        'rest', 'soap', 'xml', 'json', 'yaml', 'csv', 'pdf', 'rtf',

        # 硬件/嵌入式/物联网
        'fpga', 'arm', 'dsp', 'rtos', 'iot', 'mcu',

        # 安全
        'waf', 'ids', 'ips', 'soc', 'siem',
    }

    @staticmethod
    def _remove_periods(s: str) -> str:
        """移除中英文句号"""
        return s.replace('。', '').replace('.', '').replace('；','').replace(';', '')

    def extract(self, text: str) -> List[List[str]]:
        lines = text.splitlines()
        sections = []
        current_type = None
        current_content = []

        for line in lines:
            line_stripped = line.strip()

            # 1. 检查目标标题（不变）
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

            if found_type:
                if current_type and current_content:
                    sections.append(current_content)
                current_type = found_type
                current_content = []
            elif current_type:
                if not line_stripped:  # 空行截断
                    if current_content:
                        sections.append(current_content)
                        current_type = None
                        current_content = []
                elif len(line_stripped) < 7:
                    if any(kw in line_stripped for kw in self.ABANDON_KEYWORDS):
                        if current_content:
                            sections.append(current_content)
                            current_type = None
                            current_content = []
                    elif any(kw in line_stripped for kw in self.CONTENT_KEYWORDS):
                        cleaned = self._remove_periods(line_stripped)
                        if cleaned:
                            current_content.append(cleaned)
                    else:
                        if current_content:
                            sections.append(current_content)
                            current_type = None
                            current_content = []
                else:  # 长行
                    cleaned = self._remove_periods(line_stripped)
                    if cleaned:
                        current_content.append(cleaned)

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
        '工作地点', '办公地点', '地址', '市', '县', '区', '海外',

        # 联系方式
        '联系方式', '邮箱', '电话', '微信', 'QQ', '简历', '投递', '面试',

        # 模糊/兜底条款
        '其他', '临时', '交办', '上级', '领导', '安排', '任务', '事宜', 'cm',


        # 要求
        '岁', '气质', '能力优秀', '违法', '驾照', '年以上工作经验', '年工作经验',
        '有经验者优先', '优秀者', '差错', '高质量', '独立', '弹性工作', '交接班',
        '遵守',

        # 状态表示
        '热爱', '反馈', '出差', '顺利开展', '发展趋势', '提供', '总结', '顺利进行',
        '盈利', '提升', '淘汰', '结果', '长期', '浓厚兴趣', '成功', '文化氛围',
        '工作环境', '按时完成', '预期效果', '确保', '清晰', '排班', '学员',
        '得到', '渴望', '收获', '获得', '螺旋式', '均可', '平庸', '入住', '盖章',
        '开证明',

        # 宽泛的工作内容
        '实操指导', '利润', '全面评估', '项目进度', '保障', '资源调配', '风险',
        '推动', '新工具', '技术规范', '日常', '协助完成', '拓展', '内部资源',
        '目标', '指导', '痛点', '反映', '玩', '攻克',

        # 软技能
        '抗压', '学习能力', '沟通', '职业发展', '团队', '团体',
        '吃苦耐劳', '勤奋', '踏实', '认真', '细致', '细心', '积极', '主动',
        '服从', '形象', '气质', '口齿', '表达', '思维敏捷', '应变',
        '职业道德', '敬业精神', '责任心', '事业心', '激情', '自信', '执行力',
        '思维活跃', '创意', '时事', '亲和力', '职业素养', '有想法', '审美能力',
        '审美情趣', '耐心', '专注', '逻辑', '思维', '问题分析',
        '热情', '热爱', '责任心', '团队合作', '沟通能力', '抗压能力', '学习能力',
        '逻辑思维', '分析能力', '快节奏', '意识', '亲和', '正直', '善良', '谈吐',
        '工作压力', '时间观', '适应', '不良', '韧性', '求知欲', '外向', '新事物',
        '身体健康',

        # 学历
        '学历', '本科', '毕业生', '不限', '应届生', '大专', '专业', '资格证',
        '211', '985', '实习',

        # 补充

        # 个人品质
        '诚信', '诚实', '守信', '忠诚', '敬业', '负责', '担当', '勇敢', '果断',
        '细致入微', '精益求精', '一丝不苟', '严谨', '稳重', '成熟', '干练',

        # 沟通/表达类虚词
        '沟通协调', '协调沟通', '上传下达', '信息同步', '意见反馈', '建议', '汇报',
        '请示', '审批', '报备', '通告', '公示',

        # 假大空修饰词
        '有梦想', '有激情', '有闯劲', '有抱负', '有担当', '有责任感', '正能量', '阳光', '开朗', '乐观向上',
        '踏实肯干', '任劳任怨', '兢兢业业', '勤恳', '吃苦耐劳', '勤奋好学',

        # 团队协作空话
        '融入团队', '配合团队', '协助团队', '团队精神', '团队意识', '跨部门协作', '跨职能协作',

        # 成长发展空话
        '成长空间', '发展空间', '晋升空间', '晋升通道', '职业规划', '职业生涯', '个人成长',

        # 企业文化
        '企业愿景', '企业使命', '核心价值观', '企业文化', '狼性文化', '家文化', '军队文化',

        # 招聘流程
        '简历筛选', '笔试', '复试', '终面', 'offer', '入职', '试用期', '转正',

        # 软技能补充
        '协调能力', '组织能力', '策划能力', '写作能力', '表达能力', '执行力强', '主人翁意识',

        # 学历补充
        '统招本科', '专升本', '本科以上', '大专以上',

        # 其他
        '会开车', '驾驶执照', '能适应高强度', '能适应快节奏',

        # 额外补充
        '餐补', '交通补贴', '通讯补贴', '住房补贴', '节日福利', '生日福利', '绩效奖金',
        '全勤奖', '季度奖', '年底双薪', '13薪', '14薪', '补充医疗保险', '员工旅游',
        '零食下午茶', '加班补助', '弹性工作制', '定期体检', '带薪年假', '带薪病假',
        '扁平化管理', '开放式办公', '创业公司氛围', '快速成长', '自我驱动', '结果导向',
        '目标导向', '适应加班', '工作强度大', '多任务处理', '抗压能力强', '能接受挑战',
        '硕士', '博士', '研究生', '全日制', '统招', '学历要求', '学位', '毕业证',
        '学位证', 'CET', '英语四级', '六级', '计算机二级', '普通话', '教师资格证',
        '双休', '大小周', '单休', '轮班', '夜班', '倒班', '8小时工作制', '加班费', '调休',
        '驻场', '外派', '异地', '经常出差', '短期出差', '长期出差',

    ]

    def __init__(self):
        # 导引符号匹配正则（新增）
        self.leader_pattern = re.compile(
            r'^\s*' +
            r'(?:' +
            r'[\*\-•●▪▸➢➔➣➤➥➦➧➨➩➪➫➬➭➮➯➱➲➳➴➵➶➷➸➹➺➻➼➽➾〉\uf0b7]' +
            r'|' +
            r'[0-9]+[\.．、\)]' +
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
            r'(?:不少于|不低于|超过|多于)\d+(?:\.\d+)?年(?:以上|及以下|及以上)?' +
            r'|' +
            r'年(?:及)?以上'
        )

    def clean_line(self, line: str) -> str:
        # --- 第一步：去除行首序号 ---
        line = self.leader_pattern.sub('', line)
        line = re.sub(r'^\s*\d+(?:[\.、\)）]\s*|\s+)', '', line)

        line = re.sub(r'有\s*\d+(?:\.\d+)?\s*年(?:以上)?\s*(?:工作)?经验', '', line)
        line = line.replace('优先考虑', '')
        line = line.replace('经验', '')
        line = line.replace('者优先', '')
        line = line.replace('优先', '')

        # --- 第二步：按逗号分割并过滤 ---
        parts = re.split(r'[，,]', line)
        valid_parts = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            part = re.sub(r'^.*?[：:]', '', part)
            part = part.lstrip()

            # 1. 检查是否包含废弃词（整段丢弃）
            if any(kw in part for kw in self.KEYWORD_BLACKLIST):
                continue

            part = re.sub(r'^\s*\d+', '', part)
            part = part.lstrip()

            # 2.局部清洗（去除年限，保留其余内容）
            part = self.year_pattern.sub('', part)
            part = part.strip()

            # 如果清洗后不为空，则保留
            if part:
                valid_parts.append(part)

        return "，".join(valid_parts)

    def clean_lines(self, lines: List[str]) -> List[str]:
        return [self.clean_line(line) for line in lines]

    def process_sections(self, sections: List[List[str]]) -> str:
        """
        对每个文本块（section）执行清洗，然后将所有有效行（跨板块）用中文分号拼接成一个字符串。

        Args:
            sections: 由 SimpleExtractor.extract() 返回的结构，例如 [[line1, line2, ...], [line3, ...]]

        Returns:
            str: 清洗并拼接后的完整文本，所有内容用中文分号连接，无换行符。
        """
        all_lines = []
        for section in sections:
            cleaned_lines = self.clean_lines(section)
            non_empty_lines = [line for line in cleaned_lines if line.strip()]
            all_lines.extend(non_empty_lines)
        return "；".join(all_lines)