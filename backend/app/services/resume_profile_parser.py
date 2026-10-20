"""
中文简历本地规则解析器。

通过正则和关键词匹配从纯文本中提取结构化简历信息。
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.schemas import (
    EducationEntry,
    InternshipEntry,
    ProjectEntry,
    CampusEntry,
    HonorEntry,
    TrainingEntry,
    ResumeProfileInput,
    SkillsAndOther,
)

# ---------------------------------------------------------------------------
# 预编译正则（性能优化）
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"姓\s*名[：:\s]*(.+)")
_CN_NAME_RE = re.compile(r"^[\u4e00-\u9fa5]{2,4}$")
_CONTACT_LABEL_RE = re.compile(r"(?:手机|电话|联系|Tel)[：:\s]*(1[3-9]\d{9})")
_PHONE_RE = re.compile(r"1[3-9]\d{9}")
_LANDLINE_RE = re.compile(r"(?:电话|Tel)[：:\s]*(\d{3,4}[-]?\d{7,8})")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_BIRTH_RE = re.compile(r"(?:出生|生日|年龄|birth)[：:\s]*(\d{4}[年./-]\d{1,2}[月./-]?\d{0,2})", re.IGNORECASE)
_DATE_YMD_RE = re.compile(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})")
_SCHOOL_RE = re.compile(r"(大学|学院|学校|大专|university|college)", re.IGNORECASE)
_MAJOR_RE = re.compile(r"(?:专业|major)[：:\s]*(.+?)(?:\s|$)")
_INTENTION_LABEL_RE = re.compile(r"(?:求职意向|期望岗位|目标职位|应聘职位)[：:\s]*(.+)")
_EVAL_LABEL_RE = re.compile(r"(?:自我评价|个人总结|自我介绍|个人简介|about me)", re.IGNORECASE)
_EVAL_STRIP_RE = re.compile(r".*(?:自我评价|个人总结|自我介绍|个人简介|about me)[：:\s]*", re.IGNORECASE)
_HONOR_LABEL_RE = re.compile(r"(?:荣誉证书|荣誉奖项|获奖情况|所获奖项|证书)")
_HONOR_DATE_RE = re.compile(r"\s*\d{4}[年./-]\d{0,2}.*")
_COMPANY_RE = re.compile(r"(有限公司|科技|技术|集团|公司|实验室|工作室|项目|app|系统|平台|网站)", re.IGNORECASE)
_ACTION_RE = re.compile(r"(负责|参与|完成|实现|搭建|设计|开发|优化|部署|编写|测试|维护)")
_PUNCT_RE = re.compile(r"[。，；]")
_ROLE_RE = re.compile(r"\|\s*(.+)$")
_SECTION_RE = re.compile(
    "教育背景|教育经历|学历|工作经历|工作经验|职业经历|"
    "实习经历|实习经验|项目经历|项目经验|项目|"
    "校园经历|校园活动|学生工作|荣誉证书|荣誉奖项|获奖情况|所获奖项|证书|"
    "培训经历|培训|技能|专业技能|技术栈|"
    "自我评价|个人总结|自我介绍|求职意向|期望岗位"
)


# ---------------------------------------------------------------------------
# 技能词典（全词匹配，避免误命中）
# ---------------------------------------------------------------------------

_SKILLS: List[Tuple[str, str]] = [
    # 编程语言
    ("python", "Python"), ("java", "Java"), ("javascript", "JavaScript"),
    ("typescript", "TypeScript"), ("c++", "C++"), ("c#", "C#"), ("go", "Go"),
    ("rust", "Rust"), ("php", "PHP"), ("ruby", "Ruby"), ("swift", "Swift"),
    ("kotlin", "Kotlin"), ("scala", "Scala"), ("r语言", "R"), ("matlab", "MATLAB"),
    # 前端
    ("react", "React"), ("vue", "Vue"), ("vue.js", "Vue.js"), ("vuejs", "Vue.js"),
    ("angular", "Angular"), ("next.js", "Next.js"), ("nextjs", "Next.js"),
    ("nuxt", "Nuxt"), ("html", "HTML"), ("css", "CSS"), ("sass", "Sass"),
    ("tailwind", "Tailwind CSS"), ("webpack", "Webpack"), ("vite", "Vite"),
    ("jquery", "jQuery"), ("echarts", "ECharts"), ("ant design", "Ant Design"),
    ("element ui", "Element UI"), ("uni-app", "uni-app"), ("微信小程序", "微信小程序"),
    # 后端
    ("fastapi", "FastAPI"), ("flask", "Flask"), ("django", "Django"),
    ("spring", "Spring"), ("springboot", "Spring Boot"), ("spring boot", "Spring Boot"),
    ("express", "Express"), ("nestjs", "NestJS"), ("gin", "Gin"),
    ("laravel", "Laravel"), ("node.js", "Node.js"), ("nodejs", "Node.js"),
    # 数据库
    ("sql", "SQL"), ("mysql", "MySQL"), ("postgresql", "PostgreSQL"),
    ("sqlite", "SQLite"), ("mongodb", "MongoDB"), ("redis", "Redis"),
    ("elasticsearch", "Elasticsearch"), ("oracle", "Oracle"),
    ("hbase", "HBase"), ("cassandra", "Cassandra"), ("neo4j", "Neo4j"),
    # AI / 数据
    ("机器学习", "机器学习"), ("深度学习", "深度学习"), ("nlp", "NLP"),
    ("自然语言处理", "NLP"), ("计算机视觉", "计算机视觉"), ("cv", "计算机视觉"),
    ("pytorch", "PyTorch"), ("tensorflow", "TensorFlow"), ("keras", "Keras"),
    ("scikit-learn", "Scikit-learn"), ("sklearn", "Scikit-learn"),
    ("pandas", "Pandas"), ("numpy", "NumPy"), ("matplotlib", "Matplotlib"),
    ("spark", "Spark"), ("hadoop", "Hadoop"), ("hive", "Hive"),
    ("flink", "Flink"), ("kafka", "Kafka"),
    ("llm", "LLM"), ("大模型", "LLM"), ("大语言模型", "LLM"),
    ("prompt", "Prompt Engineering"), ("rag", "RAG"),
    ("langchain", "LangChain"), ("openai", "OpenAI API"),
    ("stable diffusion", "Stable Diffusion"), ("midjourney", "Midjourney"),
    # DevOps / 工具
    ("docker", "Docker"), ("kubernetes", "Kubernetes"), ("k8s", "Kubernetes"),
    ("jenkins", "Jenkins"), ("git", "Git"), ("gitlab", "GitLab"),
    ("github", "GitHub"), ("linux", "Linux"), ("nginx", "Nginx"),
    ("ci/cd", "CI/CD"), ("terraform", "Terraform"), ("ansible", "Ansible"),
    # 测试
    ("selenium", "Selenium"), ("playwright", "Playwright"), ("pytest", "pytest"),
    ("junit", "JUnit"), ("单元测试", "单元测试"), ("自动化测试", "自动化测试"),
    # 其他
    ("restful", "RESTful API"), ("grpc", "gRPC"), ("websocket", "WebSocket"),
    ("微服务", "微服务"), ("消息队列", "消息队列"),
    ("大数据", "大数据"), ("etl", "ETL"), ("数据仓库", "数据仓库"),
    ("fpga", "FPGA"), ("嵌入式", "嵌入式"), ("物联网", "IoT"),
    ("区块链", "区块链"), ("网络安全", "网络安全"), ("渗透测试", "渗透测试"),
]

# 技能匹配时用的正则（全词匹配）
_SKILL_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw, _ in _SKILLS),
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 章节识别
# ---------------------------------------------------------------------------

_SECTION_HEADERS = {
    "教育背景": "education", "教育经历": "education", "学历": "education",
    "工作经历": "work", "工作经验": "work", "职业经历": "work",
    "实习经历": "internship", "实习经验": "internship",
    "项目经历": "project", "项目经验": "project", "项目": "project",
    "校园经历": "campus", "校园活动": "campus", "学生工作": "campus",
    "荣誉证书": "honor", "荣誉奖项": "honor", "获奖情况": "honor",
    "所获奖项": "honor", "证书": "honor",
    "培训经历": "training", "培训": "training",
    "技能": "skills", "专业技能": "skills", "技术栈": "skills",
    "自我评价": "summary", "个人总结": "summary", "自我介绍": "summary",
    "求职意向": "intention", "期望岗位": "intention",
}


def infer_resume_profile_from_text(raw_text: str) -> ResumeProfileInput:
    """从简历纯文本中提取结构化信息。"""
    lines = _clean_lines(raw_text)

    full_name = _extract_name(lines, raw_text)
    job_intention = _extract_job_intention(lines, raw_text)
    contact = _extract_contact(raw_text)
    email = _extract_email(raw_text)
    education = _extract_education(lines)
    skills = _extract_skills(raw_text)
    self_evaluation = _extract_self_evaluation(lines)
    internships = _extract_internships(lines, skills)
    projects = _extract_projects(lines, skills)
    campus = _extract_campus(lines)
    honors = _extract_honors(lines)
    training = _extract_training(lines)

    return ResumeProfileInput(
        personal_info={
            "full_name": full_name,
            "job_intention": job_intention,
            "political_status": "",
            "birth_date": _extract_birth_date(raw_text),
            "hometown": "",
            "contact": contact,
            "email": email,
            "hobbies": "",
            "strengths": "",
        },
        self_evaluation={"content": self_evaluation},
        education_background=education,
        internship_experiences=internships,
        project_experiences=projects,
        campus_experiences=campus,
        honors_and_certificates=honors,
        training_experiences=training,
        skills_and_other=SkillsAndOther(skills=skills, other=""),
    )


# ---------------------------------------------------------------------------
# 行清洗
# ---------------------------------------------------------------------------

def _clean_lines(raw_text: str) -> List[str]:
    """清洗并分割行，去除空行和纯符号行。"""
    result = []
    for line in raw_text.splitlines():
        cleaned = line.strip().strip("-•●★☆▪▸►→»◆◇■□○●")
        if cleaned and len(cleaned) > 1:
            result.append(cleaned)
    return result


# ---------------------------------------------------------------------------
# 姓名提取
# ---------------------------------------------------------------------------

_NAME_PATTERN = re.compile(r"^[\u4e00-\u9fa5]{2,4}$")  # 2-4个汉字

def _extract_name(lines: List[str], raw_text: str) -> str:
    # 优先查找"姓名"标签
    for line in lines[:15]:
        m = _NAME_RE.search(line)
        if m:
            name = m.group(1).strip()[:10]
            if name:
                return name

    # 处理常见格式：姓名 | 职位（如"刘玮琦 | 测试工程师"）
    for line in lines[:5]:
        # 匹配 "中文名 | 任何内容" 格式
        m = re.match(r"^([\u4e00-\u9fa5]{2,4})\s*[|｜]\s*", line)
        if m:
            return m.group(1)

    # 尝试前 5 行中独立的中文姓名（2-4个汉字，无其他内容）
    for line in lines[:5]:
        cleaned = line.strip()
        if _CN_NAME_RE.match(cleaned):
            return cleaned

    # 最后回退到第一行的第一个词
    first_line = lines[0] if lines else ""
    # 尝试从 "姓名 | 职位" 格式中提取
    m = re.match(r"^([\u4e00-\u9fa5]{2,4})", first_line)
    if m:
        return m.group(1)
    return first_line[:10]


# ---------------------------------------------------------------------------
# 求职意向
# ---------------------------------------------------------------------------

_INTENTION_KEYWORDS = [
    "工程师", "开发", "测试", "产品", "算法", "运营", "设计", "分析",
    "运维", "架构", "前端", "后端", "全栈", "数据", "安全", "嵌入式",
    "人工智能", "机器学习", "深度学习", "数据分析", "产品经理", "项目经理",
    "ui设计", "ux设计", "市场营销", "人力资源", "财务", "审计",
    "咨询", "教师", "翻译", "编辑", "记者",
]

def _extract_job_intention(lines: List[str], raw_text: str) -> str:
    # 查找"求职意向"标签
    for line in lines[:20]:
        m = _INTENTION_LABEL_RE.search(line)
        if m:
            return m.group(1).strip()[:40]

    # 处理常见格式：姓名 | 职位（如"刘玮琦 | 测试工程师"）
    for line in lines[:5]:
        m = re.match(r"^[\u4e00-\u9fa5]{2,4}\s*[|｜]\s*(.+)", line)
        if m:
            intention = m.group(1).strip()[:40]
            # 确保不是纯地点（如"北京求职"）
            if not re.match(r"^[男女]$", intention) and len(intention) > 1:
                return intention

    # 查找"期望岗位"/"目标职位"等标签
    for line in lines[:20]:
        m = re.search(r"(?:期望岗位|目标职位|应聘职位)[：:\s]*(.+)", line)
        if m:
            return m.group(1).strip()[:40]

    # 在前 10 行查找含有意向关键词的行
    for line in lines[:10]:
        lower = line.lower()
        for kw in _INTENTION_KEYWORDS:
            if kw in lower:
                return line[:40]

    return ""


# ---------------------------------------------------------------------------
# 联系方式
# ---------------------------------------------------------------------------

def _extract_contact(text: str) -> str:
    # 手机号（带标签）
    m = _CONTACT_LABEL_RE.search(text)
    if m:
        return m.group(1)
    # 手机号（无标签）
    m = _PHONE_RE.search(text)
    if m:
        return m.group(0)
    # 座机
    m = _LANDLINE_RE.search(text)
    if m:
        return m.group(1)
    return ""


def _extract_email(text: str) -> str:
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else ""


def _extract_birth_date(text: str) -> str:
    """只提取明确标记为出生日期的字段，避免误匹配文本中的其他日期。"""
    m = _BIRTH_RE.search(text)
    if m:
        return m.group(1)
    # 只在"出生"/"生日"/"年龄"标签附近查找日期，不在全文搜索
    lines = text.splitlines()
    for line in lines[:30]:
        if any(kw in line for kw in ["出生", "生日", "年龄", "birth", "Birth"]):
            m = _DATE_YMD_RE.search(line)
            if m:
                return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
            # 尝试 YYYY年MM月DD日 格式
            m2 = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", line)
            if m2:
                return f"{m2.group(1)}-{m2.group(2).zfill(2)}-{m2.group(3).zfill(2)}"
            # 尝试 YYYY年MM月 格式
            m3 = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", line)
            if m3:
                return f"{m3.group(1)}-{m3.group(2).zfill(2)}"
    return ""


# ---------------------------------------------------------------------------
# 教育背景
# ---------------------------------------------------------------------------

_DEGREE_KEYWORDS = {"本科": "本科", "学士": "本科", "大专": "大专", "专科": "大专",
                    "硕士": "硕士", "研究生": "硕士", "博士": "博士", "mba": "MBA"}

# 学校名称必须包含的关键词
_SCHOOL_NAME_RE = re.compile(r"(大学|学院|学校|大专|university|college|institute)", re.IGNORECASE)

def _extract_education(lines: List[str]) -> List[EducationEntry]:
    entries = []
    for idx, line in enumerate(lines):
        if len(entries) >= 3:
            break
        # 必须在教育背景章节内
        if not _is_in_education_section(lines, idx):
            continue
        # 学校名必须以"大学/学院/学校"结尾或包含这些词
        if not _SCHOOL_NAME_RE.search(line):
            continue
        # 过滤掉包含"负责"、"完成"、"项目"等非学校名关键词的行
        if any(kw in line for kw in ["负责", "完成", "项目", "开发", "设计", "实现", "搭建", "测试", "维护"]):
            continue
        # 学校名不能太长（超过30字可能不是学校名）
        school = line.strip()[:50]
        if len(school) > 40:
            continue
        # 时间
        period = _pick_duration(line)
        if not period and idx + 1 < len(lines):
            period = _pick_duration(lines[idx + 1])
        # 学历
        degree = ""
        search_area = " ".join(lines[max(0, idx-1): min(len(lines), idx+3)])
        for kw, label in _DEGREE_KEYWORDS.items():
            if kw in search_area.lower():
                degree = label
                break
        # 专业
        major = ""
        m = _MAJOR_RE.search(search_area)
        if m:
            major = m.group(1).strip()[:30]

        entries.append(EducationEntry(
            school_name=school,
            attendance_period=period,
            degree=degree,
            ranking="",
            major_courses=major,
        ))
    return entries


def _is_in_education_section(lines: List[str], target_idx: int) -> bool:
    """检查目标行是否在教育背景章节内。"""
    # 向上查找最近的章节标题
    for i in range(target_idx - 1, max(-1, target_idx - 30), -1):
        line = lines[i].strip()
        # 找到章节标题
        if len(line) < 20 and _SECTION_RE.search(line):
            # 判断是否是教育相关章节
            return any(kw in line for kw in ["教育背景", "教育经历", "学历", "教育"])
    # 如果没找到章节标题，检查前5行是否有教育相关关键词
    for i in range(max(0, target_idx - 5), target_idx):
        if any(kw in lines[i] for kw in ["教育背景", "教育经历", "学历"]):
            return True
    return False


# ---------------------------------------------------------------------------
# 技能提取
# ---------------------------------------------------------------------------

def _extract_skills(text: str) -> List[str]:
    matched = []
    for keyword, label in _SKILLS:
        # 全词匹配：前后不能是字母（避免 "ai" 匹配 "detail"）
        pattern = re.compile(r"(?<![a-zA-Z])" + re.escape(keyword) + r"(?![a-zA-Z])", re.IGNORECASE)
        if pattern.search(text):
            if label not in matched:
                matched.append(label)
    return matched[:20]


# ---------------------------------------------------------------------------
# 自我评价
# ---------------------------------------------------------------------------

def _extract_self_evaluation(lines: List[str]) -> str:
    in_section = False
    content_lines = []
    for line in lines:
        # 进入章节
        if _EVAL_LABEL_RE.search(line):
            in_section = True
            # 如果标题行本身有内容
            after = _EVAL_STRIP_RE.sub("", line).strip()
            if after:
                content_lines.append(after)
            continue
        if in_section:
            # 遇到下一个章节标题则退出
            if _detect_section(line):
                break
            content_lines.append(line)
    return "\n".join(content_lines)[:500] if content_lines else ""


def _detect_section(line: str) -> bool:
    """检测是否为章节标题行。"""
    if len(line.strip()) > 20:
        return False
    return bool(_SECTION_RE.search(line))


# ---------------------------------------------------------------------------
# 经历提取（统一入口）
# ---------------------------------------------------------------------------

def _extract_internships(lines: List[str], skills: List[str]) -> List[InternshipEntry]:
    return _extract_experience_section(lines, skills, ["实习经历", "实习经验", "工作经历", "工作经验"], "internship")

def _extract_projects(lines: List[str], skills: List[str]) -> List[ProjectEntry]:
    return _extract_experience_section(lines, skills, ["项目经历", "项目经验", "项目"], "project")

def _extract_campus(lines: List[str]) -> List[CampusEntry]:
    return _extract_experience_section(lines, [], ["校园经历", "校园活动", "学生工作"], "campus")

def _extract_experience_section(lines: List[str], skills: List[str], headers: List[str], kind: str):
    """通用经历提取：定位章节 → 逐条提取。"""
    start_idx = -1
    for idx, line in enumerate(lines):
        for h in headers:
            if h in line:
                start_idx = idx + 1
                break
        if start_idx >= 0:
            break
    if start_idx < 0:
        return []

    # 找到章节范围
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        if _detect_section(lines[idx]):
            end_idx = idx
            break

    section_lines = lines[start_idx:end_idx]
    return _parse_experience_entries(section_lines, skills, kind)


def _parse_experience_entries(lines: List[str], skills: List[str], kind: str):
    """将章节内文本切分为多条经历。"""
    entries = []
    current_block = []  # type: List[str]

    for line in lines:
        # 新条目识别：含有公司/项目名特征 + 时间特征
        is_new = False
        if _pick_duration(line) and (
            _COMPANY_RE.search(line)
            or _ACTION_RE.search(line)
        ):
            is_new = True
        # 或者：时间格式单独一行 + 上一个 block 已有内容
        elif _pick_duration(line) and current_block:
            is_new = True
        # 短标题行（<30字）+ 无句号 → 可能是条目标题
        elif len(line) < 30 and not _PUNCT_RE.search(line) and current_block:
            # 如果上一行是空/时间行，这可能是新标题
            if current_block and _pick_duration(current_block[-1]):
                is_new = True

        if is_new and current_block:
            entry = _build_entry(current_block, skills, kind)
            if entry:
                entries.append(entry)
            current_block = []

        current_block.append(line)

        if len(entries) >= 5:
            break

    # 最后一个 block
    if current_block:
        entry = _build_entry(current_block, skills, kind)
        if entry:
            entries.append(entry)

    return entries


def _build_entry(block: List[str], skills: List[str], kind: str):
    """从一个文本块构建经历条目。"""
    title = block[0][:50] if block else ""
    duration = _pick_duration(" ".join(block[:3]))
    if not duration:
        duration = "时间待补充"

    # 角色：标题行之后的第一行，或从标题中提取
    role = ""
    if len(block) > 1:
        role = block[1][:40]
    # 尝试从标题提取角色
    m = _ROLE_RE.search(title)
    if m:
        role = m.group(1).strip()[:40]

    # 摘要：取中间的内容行
    summary_lines = block[1:4] if len(block) > 1 else []
    summary = " ".join(summary_lines)[:200] if summary_lines else "经历待补充。"

    # 亮点：含有"负责/参与/完成/实现/搭建"的行
    highlights = []
    for line in block[2:]:
        if _ACTION_RE.search(line):
            highlights.append(line[:120])
        if len(highlights) >= 3:
            break

    entry_skills = skills[:5] if skills else []

    if kind == "internship":
        return InternshipEntry(
            company=title, role=role, duration=duration,
            summary=summary, skills=entry_skills, highlights=highlights,
        )
    elif kind == "project":
        return ProjectEntry(
            project_name=title, role=role, duration=duration,
            summary=summary, skills=entry_skills, highlights=highlights,
        )
    elif kind == "campus":
        return CampusEntry(
            organization=title, role=role, duration=duration,
            summary=summary, highlights=highlights,
        )
    return None


# ---------------------------------------------------------------------------
# 荣誉证书
# ---------------------------------------------------------------------------

def _extract_honors(lines: List[str]) -> List[HonorEntry]:
    entries = []
    start_idx = -1
    for idx, line in enumerate(lines):
        if _HONOR_LABEL_RE.search(line):
            start_idx = idx + 1
            break
    if start_idx < 0:
        return []

    end_idx = min(start_idx + 20, len(lines))
    for idx in range(start_idx, len(lines)):
        if _detect_section(lines[idx]) and idx > start_idx:
            end_idx = idx
            break

    for line in lines[start_idx:end_idx]:
        if not line.strip():
            continue
        time_match = _pick_duration(line)
        name = _HONOR_DATE_RE.sub("", line).strip()
        if name:
            entries.append(HonorEntry(
                name=name[:60],
                time=time_match or "",
                issuer="",
            ))
        if len(entries) >= 10:
            break
    return entries


# ---------------------------------------------------------------------------
# 培训经历
# ---------------------------------------------------------------------------

def _extract_training(lines: List[str]) -> List[TrainingEntry]:
    entries = []
    start_idx = -1
    for idx, line in enumerate(lines):
        if "培训" in line:
            start_idx = idx + 1
            break
    if start_idx < 0:
        return []

    end_idx = min(start_idx + 15, len(lines))
    for idx in range(start_idx, len(lines)):
        if _detect_section(lines[idx]) and idx > start_idx:
            end_idx = idx
            break

    for line in lines[start_idx:end_idx]:
        if not line.strip():
            continue
        time_match = _pick_duration(line)
        entries.append(TrainingEntry(
            course_name=line[:60],
            institution="",
            duration=time_match or "",
            summary="",
        ))
        if len(entries) >= 5:
            break
    return entries


# ---------------------------------------------------------------------------
# 时间提取
# ---------------------------------------------------------------------------

_DURATION_PATTERN = re.compile(
    r"(20\d{2})\s*[年./-]\s*(\d{1,2})\s*月?\s*[-~—至到]\s*(20\d{2}|至今)\s*[年./-]?\s*(\d{0,2})\s*月?"
    r"|"
    r"(20\d{2})\s*[年./-]\s*(\d{1,2})\s*月?\s*[-~—至到]\s*(至今)"
    r"|"
    r"(20\d{2})\s*[-~—至到]\s*(20\d{2}|至今)"
    r"|"
    r"(\d{4})\s*[-~—至到]\s*(\d{4}|至今)"
    r"|"
    r"(\d+)\s*年"
)

def _pick_duration(text: str) -> str:
    m = _DURATION_PATTERN.search(text)
    if not m:
        return ""
    # 返回第一个匹配的 group 组合
    if m.group(1):
        end = f"{m.group(3)}年{m.group(4)}月" if m.group(4) else m.group(3)
        return f"{m.group(1)}年{m.group(2)}月-{end}"
    if m.group(5):
        return f"{m.group(5)}年{m.group(6)}月-{m.group(7)}"
    if m.group(8):
        return f"{m.group(8)}-{m.group(9)}"
    if m.group(10):
        return f"{m.group(10)}-{m.group(11)}"
    if m.group(12):
        return f"{m.group(12)}年"
    return ""
