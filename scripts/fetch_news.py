#!/usr/bin/env python3
"""
MedAI Hub 资讯自动化采集脚本
==================================
接入深部真菌、耐药菌(CRAB/CRE)、重症影像与 AI 临床等顶级权威源，
智能清洗、打分过滤后输出至 src/data/auto/industry.json 与 research.json。

【硬约束】本脚本仅写入 src/data/auto/ 目录，严禁触碰受保护内容。
"""
import json
import re
import sys
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

# ============================================================
# 路径与常量
# ============================================================
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "src" / "data" / "auto"
INDUSTRY_PATH = OUTPUT_DIR / "industry.json"
RESEARCH_PATH = OUTPUT_DIR / "research.json"

REQUEST_TIMEOUT = 20
MAX_ITEMS_PER_FEED = 15
RELEVANCE_THRESHOLD = 1  # 至少命中一个高价值关键词组
TOTAL_SCORE_THRESHOLD = 28  # 准入线（满分50）
TZ_CN = timezone(timedelta(hours=8))

# 本地缓存配置
CACHE_DIR = BASE_DIR / "scripts" / ".cache"
FEED_CACHE_FILE = CACHE_DIR / "feed_cache.json"
FAILURE_CACHE_FILE = CACHE_DIR / "failure_cache.json"
CACHE_TTL_HOURS = 6         # 成功响应缓存有效期（与 CI 定时任务对齐）
FAILURE_COOLDOWN_HOURS = 12 # 失败源冷却期，避免重复请求已知失效源

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MedAIHubBot/1.0; +https://medaihub.example)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# 浏览器级请求头（用于 403 重试，模拟真实浏览器）
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
}

# ============================================================
# 权威源清单
# ============================================================
# type: rss 表示可直接抓取；curated 表示无 RSS，需人工/静态录入
RSS_FEEDS = [
    # ---- 国际原生 RSS / 顶刊 ----
    {
        "id": "cidrap",
        "name": "CIDRAP",
        "url": "https://www.cidrap.umn.edu/rss.xml",
        "kind": "news",          # news → 行业资讯
        "authority": 9,          # 来源权威度（影响 timelinessAuthority / evidenceLevel）
        "default_category": "耐药监测",
        "content_type": "news",            # 业务内容类型（源级默认值）
        "source_type": "media",            # 来源性质
        "language": "en",
        "geographic_scope": "global",
    },
    {
        "id": "idcm",
        "name": "IDCM Journal",
        "url": "https://www.idcmjournal.org/feed",
        "base_url": "https://www.idcmjournal.org",  # 相对链接据此解析为绝对 URL
        "kind": "research",
        "authority": 8,
        "content_type": "research",
        "source_type": "journal",
        "language": "en",
        "geographic_scope": "global",
    },
    {
        "id": "cdc-eid",
        "name": "CDC EID",
        "url": "https://wwwnc.cdc.gov/eid/rss/eid.xml",
        "fallback_urls": [
            "https://wwwnc.cdc.gov/eid/rss/current.xml",
            "https://www.cdc.gov/eid/rss/eid.xml",
            "https://wwwnc.cdc.gov/eid/rss/ahead.xml",
        ],
        "kind": "research",
        "authority": 9,
        "content_type": "research",
        "source_type": "journal",
        "language": "en",
        "geographic_scope": "global",
    },
    {
        "id": "cid",
        "name": "Clinical Infectious Diseases",
        "url": "https://academic.oup.com/rss/site_10.1093/cid/",
        "fallback_urls": [
            "https://academic.oup.com/rss/site_10.1093/cid/current.xml",
            "https://academic.oup.com/cid/rss",
        ],
        "kind": "research",
        "authority": 9,
        "content_type": "research",
        "source_type": "journal",
        "language": "en",
        "geographic_scope": "global",
    },
    {
        "id": "jcm",
        "name": "Journal of Clinical Microbiology",
        "url": "https://journals.asm.org/rss/jcm",
        "fallback_urls": [
            "https://journals.asm.org/rss/journal/JCM",
            "https://journals.asm.org/action/showFeed?type=etoc&feed=rss&jc=jcm",
        ],
        "kind": "research",
        "authority": 8,
        "content_type": "research",
        "source_type": "journal",
        "language": "en",
        "geographic_scope": "global",
    },
    # ---- 中文与 RSSHub 源 ----
    {
        "id": "iidf",
        "name": "感染医线",
        "url": "https://rsshub.app/iidf/home",
        "kind": "news",
        "authority": 7,
        "default_category": "真菌与耐药",
        "content_type": "news",
        "source_type": "media",
        "language": "zh",
        "geographic_scope": "china",
    },
    {
        "id": "medxy",
        "name": "MedXY.ai",
        "url": "https://rsshub.app/medxy/news",
        "kind": "news",
        "authority": 7,
        "default_category": "AI临床",
        "content_type": "news",
        "source_type": "enterprise",
        "language": "zh",
        "geographic_scope": "china",
    },
]

# PubMed 通过 E-utilities API 抓取（RSS 接口已变更）
PUBMED_QUERIES = [
    {
        "name": "PubMed (CRAB / CRE 耐药)",
        "term": '(Acinetobacter baumannii carbapenem-resistant OR CRAB OR carbapenem-resistant Enterobacteriaceae OR CRE OR CRKP)',
        "authority": 9,
    },
    {
        "name": "PubMed (CRPA / 嗜麦芽窄食单胞菌 / MRSA / VRE)",
        "term": '(Pseudomonas aeruginosa carbapenem-resistant OR CRPA OR Stenotrophomonas maltophilia OR MRSA OR vancomycin-resistant enterococci)',
        "authority": 9,
    },
    {
        "name": "PubMed (真菌感染：曲霉/念珠菌/毛霉/隐球菌)",
        "term": '(Aspergillus OR Candida OR Mucor OR Cryptococcus) AND (treatment OR diagnosis)',
        "authority": 9,
    },
    {
        "name": "PubMed (侵袭性真菌病 CT 影像特征)",
        "term": '(invasive fungal infection OR invasive aspergillosis OR mucormycosis) AND (computed tomography OR CT imaging OR radiology)',
        "authority": 9,
    },
    {
        "name": "PubMed (CRAB / CRE 混合感染)",
        "term": '(polymicrobial OR mixed infection OR co-infection) AND (CRAB OR CRE OR carbapenem-resistant OR Acinetobacter baumannii)',
        "authority": 9,
    },
    {
        "name": "PubMed (CRRT / ECMO 药物剂量调整)",
        "term": '(continuous renal replacement therapy OR CRRT OR extracorporeal membrane oxygenation OR ECMO) AND (antibiotic dosing OR drug dosing OR pharmacokinetics)',
        "authority": 9,
    },
    {
        "name": "PubMed (真菌/耐药菌 TDM 与疗效比较)",
        "term": '(therapeutic drug monitoring OR TDM) AND (voriconazole OR isavuconazole OR polymyxin OR colistin OR tigecycline OR eravacycline OR sulbactam-durlobactam)',
        "authority": 9,
    },
]

# ClinicalTrials.gov 通过 API v2 抓取抗感染相关临床试验注册信息
# query.cond 精确匹配「疾病/适应症」字段，避免命中摘要中的无关提及
CLINICALTRIALS_QUERIES = [
    {
        "name": "ClinicalTrials (侵袭性真菌感染)",
        "cond": "aspergillosis OR candidiasis OR mucormycosis OR cryptococcosis OR invasive fungal infection",
        "authority": 9,
    },
    {
        "name": "ClinicalTrials (耐药菌 CRAB/CRE/CRPA)",
        "cond": "carbapenem-resistant OR Acinetobacter baumannii OR CRAB OR CRE OR Pseudomonas aeruginosa",
        "authority": 9,
    },
    {
        "name": "ClinicalTrials (MRSA / VRE / 嗜麦芽窄食单胞菌)",
        "cond": "MRSA OR methicillin-resistant Staphylococcus aureus OR vancomycin-resistant enterococci OR VRE OR Stenotrophomonas maltophilia",
        "authority": 9,
    },
]

# WHO ICTRP（国际临床试验注册平台聚合门户）检索：一次检索覆盖其下所有一级注册中心，
# 含 ChiCTR、ClinicalTrials.gov(NCT)、EU CTR(EudraCT)、CTIS 等。按注册号模式识别注册中心，
# 详情页补齐研究设计与疾病/干预；NCT 记录因已有 ClinicalTrials.gov 直连源而在抓取阶段跳过。
ICTRP_QUERIES = [
    {
        "name": "WHO ICTRP (侵袭性真菌感染)",
        "term": "aspergillosis OR candidiasis OR mucormycosis OR cryptococcosis",
        "authority": 9,
    },
    {
        "name": "WHO ICTRP (耐药菌 CRAB/CRE/CRPA)",
        "term": "carbapenem-resistant OR acinetobacter OR Pseudomonas aeruginosa",
        "authority": 9,
    },
    {
        "name": "WHO ICTRP (MRSA / VRE / 嗜麦芽窄食单胞菌)",
        "term": "vancomycin-resistant OR MRSA OR Stenotrophomonas maltophilia",
        "authority": 9,
    },
]

# ============================================================
# 官方药品审批/监管数据源（B4）：FDA / EMA / NMPA
# ============================================================
# 统一纳入行业资讯模块，按现有 Schema 映射 approvalStatus / policyStatus / marketAccessType。
# 仅采集本项目聚焦的抗感染领域（深部真菌 + 耐药菌抗菌药）内容。

# 抗感染领域关键词（用于官方数据源标题/文本的领域过滤，英文 + 中文）
ANTI_INFECTIVE_PATTERNS = [
    # 抗真菌
    r"antifungal", r"抗真菌", r"voriconazole", r"伏立康唑", r"isavuconazole", r"艾沙康唑",
    r"amphotericin", r"两性霉素", r"echinocandin", r"棘白菌素", r"caspofungin", r"卡泊芬净",
    r"micafungin", r"米卡芬净", r"anidulafungin", r"阿尼芬净", r"fluconazole", r"氟康唑",
    r"posaconazole", r"泊沙康唑", r"itraconazole", r"伊曲康唑", r"triazole", r"三唑",
    # 抗细菌 / 耐药菌
    r"antibiotic", r"抗生素", r"antibacterial", r"抗菌", r"antimicrobial", r"抗菌药物",
    r"ceftazidime", r"头孢他啶", r"cefepime", r"头孢吡肟", r"cefiderocol", r"头孢地尔",
    r"ceftolozane", r"头孢洛扎", r"avibactam", r"阿维巴坦", r"durlobactam", r"度洛巴坦",
    r"sulbactam", r"舒巴坦", r"tazobactam", r"他唑巴坦", r"carbapenem", r"碳青霉烯",
    r"meropenem", r"美罗培南", r"imipenem", r"亚胺培南", r"eravacycline", r"依拉环素",
    r"tigecycline", r"替加环素", r"colistin", r"黏菌素", r"多黏菌素", r"polymyxin",
    r"vancomycin", r"万古霉素", r"daptomycin", r"达托霉素", r"linezolid", r"利奈唑胺",
    r"tedizolid", r"泰地唑胺", r"aztreonam", r"氨曲南", r"piperacillin", r"哌拉西林",
    r"levofloxacin", r"左氧氟沙星", r"moxifloxacin", r"莫西沙星", r"amikacin", r"阿米卡星",
    r"\bMRSA\b", r"\bCRE\b", r"\bCRAB\b", r"\bCRPA\b", r"\bESBL\b", r"耐药菌",
]

# 官方端点
FDA_DRUGSFDA_URL = "https://api.fda.gov/drug/drugsfda.json"
# FDA.gov RSS（MedWatch / Recalls）现被 Akamai 反爬拦截，安全/召回改走 openFDA 执法报告 API
FDA_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"
EMA_MEDICINES_URL = "https://www.ema.europa.eu/en/documents/report/medicines-output-medicines_json-report_en.json"
EMA_NEWS_URL = "https://www.ema.europa.eu/en/news.xml"
# NMPA 官方静态 HTML 栏目（标题 + 链接 + 真实发布日期）
NMPA_COLUMNS = [
    ("NMPA 药品公告通告", "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html", "policy"),
    ("NMPA 药品监管动态", "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html", "policy"),
    ("NMPA 药品批件发布", "https://www.nmpa.gov.cn/zwfw/zwfwpjfbzs/pjfbzsyp/yppjfbzs/index.html", "approval"),
]

# ============================================================
# 官方监测数据源（B5）：WHO GLASS 全球耐药监测
# ============================================================
# WHO GLASS 主页「GLASS Reports」区块为官方发布的 AMR/AMU 监测报告列表
# （含标题、发布日期、摘要、官方页面链接与 PDF 下载地址）。
# GLASS 数据可视化仪表盘为 Shiny 交互应用（JS 渲染），无法用 requests 直连，故仅采集报告。
GLASS_PAGE_URL = "https://www.who.int/initiatives/glass"

# 无 RSS 的权威专业源（作为静态知识库条目录入）
CURATED_SOURCES = [
    {
        "id": "ecmm",
        "name": "ECMM（欧洲医学真菌学联合会）",
        "url": "https://www.ecmm.info/",
        "kind": "research",
        "authority": 9,
        "content_type": "resource",
        "source_type": "society",
        "language": "en",
        "geographic_scope": "eu",
        "category": "真菌与耐药",
        "description": "欧洲医学真菌学权威机构，发布曲霉、毛霉、念珠菌指南与药敏折点更新。",
    },
    {
        "id": "isham",
        "name": "ISHAM（国际人畜真菌学会）",
        "url": "https://www.isham.org/",
        "kind": "research",
        "authority": 9,
        "content_type": "resource",
        "source_type": "society",
        "language": "en",
        "geographic_scope": "global",
        "category": "真菌与耐药",
        "description": "国际临床真菌学与 TDM 权威学术组织。",
    },
    {
        "id": "gardp",
        "name": "GARDP（全球抗生素研发伙伴关系）",
        "url": "https://gardp.org/",
        "kind": "news",
        "authority": 8,
        "content_type": "resource",
        "source_type": "enterprise",
        "language": "en",
        "geographic_scope": "global",
        "category": "AMR",
        "description": "全球 AMR/CRAB 新药研发与可及性动向权威来源。",
    },
    {
        "id": "mycology-online",
        "name": "Mycology Online（阿德莱德真菌网）",
        "url": "https://mycology.adelaide.edu.au/",
        "kind": "research",
        "authority": 8,
        "content_type": "resource",
        "source_type": "database",
        "language": "en",
        "geographic_scope": "global",
        "category": "真菌与耐药",
        "description": "临床真菌鉴别与影像图谱知识库。",
    },
    {
        "id": "chinet",
        "name": "CHINET 中国细菌耐药监测网",
        "url": "http://www.chinets.com",
        "kind": "news",
        "authority": 9,
        "content_type": "surveillance",
        "source_type": "database",
        "language": "zh",
        "geographic_scope": "china",
        "category": "AMR",
        "description": "全国三甲医院耐药菌（含 CRAB、CRE）最新变迁数据。",
    },
    {
        "id": "china-fungal-surveillance",
        "name": "中国侵袭性真菌病监测网",
        "url": "http://www.chinets.com",  # 与 CHINET 同域，作为专题入口
        "kind": "news",
        "authority": 8,
        "content_type": "surveillance",
        "source_type": "database",
        "language": "zh",
        "geographic_scope": "china",
        "category": "真菌与耐药",
        "description": "国内 ICU/血液科侵袭性真菌流行病学、曲霉毛霉耳念珠菌耐药趋势。",
    },
]

# ============================================================
# 高价值关键词组（用于相关性打分与标签提取）
# ============================================================
KEYWORD_GROUPS = {
    "fungal": {
        "label": "真菌",
        "weight": 3,
        "patterns": [
            r"aspergill", r"曲霉", r"mucor", r"毛霉", r"candida", r"念珠菌",
            r"cryptococcus", r"隐球菌", r"c\.?auris", r"耳念珠菌",
            r"fusarium", r"镰刀菌", r"zygomyc", r"接合菌", r"fungal",
            r"真菌", r"mycos", r"antifungal", r"抗真菌", r"voriconazole",
            r"伏立康唑", r"isavuconazole", r"艾沙康唑", r"amphotericin",
            r"两性霉素", r"echinocandin", r"棘白菌素", r"caspofungin",
            r"卡泊芬净", r"micafungin", r"米卡芬净", r"triazole", r"三唑",
        ],
    },
    "amr": {
        "label": "AMR耐药",
        "weight": 3,
        "patterns": [
            r"acinetobacter\s*baumannii", r"鲍曼不动杆菌", r"\bCRAB\b",
            r"\bCRE\b", r"\bCRKP\b", r"carbapenem.?resistant",
            r"碳青霉烯耐药", r"\bCRPA\b", r"pseudomonas\s*aeruginosa",
            r"铜绿假单胞菌", r"stenotrophomonas", r"嗜麦芽窄食单胞菌",
            r"\bMRSA\b", r"耐甲氧西林", r"\bVRE\b", r"万古霉素耐药",
            r"vancomycin.?resistant", r"\bESBL\b", r"超广谱\s*β?\s*内酰胺酶",
            r"\bAMR\b", r"antimicrobial\s*resistance", r"抗菌药物耐药",
            r"耐药菌", r"multidrug.?resistant", r"多重耐药", r"colistin",
            r"黏菌素", r"polymyxin", r"多黏菌素", r"ceftazidime.?avibactam",
            r"头孢他啶阿维巴坦", r"meropenem", r"美罗培南", r"imipenem",
            r"亚胺培南", r"eravacycline", r"依拉环素", r"依嘉",
            r"sulbactam.?durlobactam", r"舒巴坦度洛巴坦", r"度洛巴坦",
            r"双坦", r"tigecycline", r"替加环素", r"polymicrobial",
            r"混合感染", r"co.?infection", r"联合治疗",
            r"\bCRRT\b", r"continuous\s*renal\s*replacement", r"连续肾脏替代",
            r"\bECMO\b", r"extracorporeal\s*membrane", r"体外膜肺氧合",
            r"\bARDS\b", r"急性呼吸窘迫",
        ],
    },
    "imaging": {
        "label": "感染影像",
        "weight": 2,
        "patterns": [
            r"imaging", r"影像", r"\bCT\b", r"computed\s*tomography",
            r"\bMRI\b", r"magnetic\s*resonance", r"radiolog", r"放射",
            r"ultrasound", r"超声", r"chest\s*x.?ray", r"胸片",
            r"pulmonary\s*nodule", r"肺结节", r"infection\s*imaging",
            r"感染影像", r"radiomic", r"影像组学", r"肺部\s*CT", r"胸部\s*CT",
            r"halo\s*sign", r"晕征", r"air\s*crescent", r"空气新月征",
            r"invasive\s*fungal\s*infection.*(?:CT|imaging|radiology)",
            r"影像鉴别", r"imaging\s*differential",
        ],
    },
    "ai_clinical": {
        "label": "AI临床",
        "weight": 2,
        "patterns": [
            r"\bAI\b", r"人工智能", r"machine\s*learning", r"机器学习",
            r"deep\s*learning", r"深度学习", r"neural\s*network",
            r"神经网络", r"computer.?aided", r"计算机辅助", r"algorithm",
            r"算法", r"diagnostic\s*model", r"诊断模型", r"clinical\s*decision",
            r"临床决策", r"natural\s*language", r"大语言模型", r"\bLLM\b",
        ],
    },
}

# 标签候选词（命中后加入 tags）
TAG_KEYWORDS = {
    "曲霉": "曲霉",
    "毛霉": "毛霉",
    "念珠菌": "念珠菌",
    "耳念珠菌": "耳念珠菌",
    "隐球菌": "隐球菌",
    "鲍曼不动杆菌": "鲍曼不动杆菌",
    "CRAB": "CRAB",
    "CRE": "CRE",
    "CRKP": "CRKP",
    "CRPA": "CRPA",
    "铜绿假单胞菌": "铜绿假单胞菌",
    "嗜麦芽窄食单胞菌": "嗜麦芽窄食单胞菌",
    "MRSA": "MRSA",
    "碳青霉烯": "碳青霉烯耐药",
    "多重耐药": "多重耐药",
    "混合感染": "混合感染",
    "联合治疗": "多病原联合治疗",
    "抗菌药物耐药": "AMR",
    "AMR": "AMR",
    "CRRT": "CRRT",
    "连续肾脏替代": "CRRT",
    "ECMO": "ECMO",
    "体外膜肺氧合": "ECMO",
    "ARDS": "ARDS",
    "急性呼吸窘迫": "ARDS",
    "CT": "CT影像",
    "肺部CT": "肺部CT影像",
    "影像": "感染影像",
    "影像鉴别": "影像鉴别",
    "晕征": "真菌影像",
    "空气新月征": "真菌影像",
    "AI": "AI临床",
    "人工智能": "AI临床",
    "机器学习": "AI临床",
    "深度学习": "AI临床",
    "伏立康唑": "伏立康唑",
    "艾沙康唑": "艾沙康唑",
    "两性霉素": "两性霉素B",
    "棘白菌素": "棘白菌素",
    "卡泊芬净": "卡泊芬净",
    "依拉环素": "依拉环素",
    "依嘉": "依拉环素",
    "舒巴坦度洛巴坦": "舒巴坦/度洛巴坦",
    "度洛巴坦": "舒巴坦/度洛巴坦",
    "替加环素": "替加环素",
    "多黏菌素": "多黏菌素",
    "黏菌素": "多黏菌素",
    "TDM": "TDM",
    "血药浓度": "TDM",
    "ICU": "重症感染",
    "脓毒症": "脓毒症",
}

# 研究类型识别
STUDY_TYPE_PATTERNS = {
    "RCT": [r"\bRCT\b", r"randomized.?controlled", r"随机对照"],
    "meta-analysis": [r"meta.?analysis", r"meta分析", r"systematic\s*review", r"系统综述"],
    "cohort": [r"cohort", r"队列"],
    "real-world": [r"real.?world", r"真实世界"],
    "review": [r"\breview\b", r"综述"],
    "preprint": [r"preprint", r"预印本", r"medrxiv", r"biorxiv"],
}


# ============================================================
# 统一 Schema 常量（与 src/types/content.ts 保持一致，camelCase）
# ============================================================
# 证据质量/推荐等级：仅原文明确提供或经规范评价时才填写；否则一律「原文未评估」。
UNASSESSED = "原文未评估"

# sourceType 枚举（与 src/types/content.ts 完全一致；CIDRAP/感染医线使用 media）
SOURCE_TYPES = {"regulatory", "society", "enterprise", "journal", "database", "media", "other"}

# contentType 枚举（与 src/types/content.ts 完全一致；resource=机构资源入口）
CONTENT_TYPES = {
    "policy", "approval", "safety", "research", "guideline",
    "consensus", "surveillance", "news", "resource", "other",
}

# 预印本来源提示（结合来源期刊名与原文元数据判定，不做纯标题猜测）
PREPRINT_SOURCE_HINTS = (
    "research square", "medrxiv", "biorxiv", "ssrn", "preprints.org", "preprint",
)

# 旧 studyType → 新 studyDesign（研究设计类型，与证据质量正交，不代表证据等级）
STUDY_DESIGN_MAP = {
    "RCT": "rct",
    "cohort": "cohort",
    "real-world": "realWorld",
    "meta-analysis": "metaAnalysis",
    "review": "other",  # 普通综述不自动升级为系统综述；无法区分时保守归为 other
    "preprint": "preprint",
    "other": "other",
}

# 旧 publishStatus → 新 publicationStatus（保留 in-review，不静默丢失）
PUBLICATION_STATUS_MAP = {
    "published": "published",
    "preprint": "preprint",
    "in-review": "inReview",
}

# 自动采集字段：合并时始终以最新来源为准，不保留旧值
AUTO_FIELDS = {
    "id", "title", "sourceName", "sourceUrl", "sourceType", "language",
    "geographicScope", "category", "tags", "summary", "abstract", "impact",
    "eventTime", "publishTime", "sourceUpdatedAt", "ingestedAt", "lastCheckedAt",
    "contentType", "factType", "scores", "totalScore", "isCluster",
    "studyType", "studyDesign", "publishStatus", "publicationStatus",
    "sampleSize", "coreFindings", "limitations", "inspiration", "isPreprint",
    "externalId", "authors", "doi", "pmid", "licenseUrl",
    "trialId", "trialStatus", "diseases", "drugs",
    "approvalStatus", "policyStatus", "marketAccessType",
}

# 人工字段：合并时旧数据中「非默认值」优先保留（防止被新采集默认值覆盖）
MANUAL_FIELDS = {
    "recordStatus": "active",
    "verificationStatus": "pending",
    "reviewStatus": "autoProcessed",
    "licenseStatus": "unknown",
    "licensePermissions": [],
    "evidenceQuality": UNASSESSED,
    "recommendationGrade": None,
}

# 试验注册号识别（NCT=ClinicalTrials.gov；ChiCTR=中国临床试验注册中心，含旧式 ChiCTR-XXX-XXXX）
TRIAL_ID_RE = re.compile(r"\bNCT\d{8}\b|\bChiCTR[-\w]+\b", re.IGNORECASE)


def _norm_trial_id(tid: str) -> str:
    """归一化试验注册号（去空白 + 大写），用于跨来源精确匹配。"""
    return (tid or "").strip().upper()


def _extract_trial_ids(text: str) -> list[str]:
    """从文本中提取 NCT/ChiCTR 注册号（去重、排序、大写归一化）。"""
    if not text:
        return []
    ids = {_norm_trial_id(m.group(0)) for m in TRIAL_ID_RE.finditer(text)}
    return sorted(ids)


# ============================================================
# 本地缓存机制
# ============================================================
def _load_json_cache(path: Path) -> dict:
    """加载 JSON 缓存文件，不存在则返回空字典"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json_cache(path: Path, data: dict) -> None:
    """写入 JSON 缓存文件"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_cache_valid(timestamp_str: str, ttl_hours: int) -> bool:
    """判断缓存时间戳是否在 TTL 内"""
    try:
        ts = datetime.fromisoformat(timestamp_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=TZ_CN)
        return (datetime.now(TZ_CN) - ts) < timedelta(hours=ttl_hours)
    except (ValueError, TypeError):
        return False


def get_cached_feed(feed_id: str) -> list[dict] | None:
    """获取成功缓存的条目列表（TTL 内有效），无缓存返回 None"""
    cache = _load_json_cache(FEED_CACHE_FILE)
    entry = cache.get(feed_id)
    if entry and is_cache_valid(entry.get("timestamp", ""), CACHE_TTL_HOURS):
        return entry.get("items", [])
    return None


def save_cached_feed(feed_id: str, items: list[dict]) -> None:
    """保存成功抓取的条目到缓存"""
    cache = _load_json_cache(FEED_CACHE_FILE)
    cache[feed_id] = {
        "timestamp": datetime.now(TZ_CN).isoformat(),
        "items": items,
    }
    _save_json_cache(FEED_CACHE_FILE, cache)


def is_failure_cooled_down(feed_id: str) -> bool:
    """检查源是否处于失败冷却期内（返回 True 表示需跳过）"""
    cache = _load_json_cache(FAILURE_CACHE_FILE)
    entry = cache.get(feed_id)
    if entry and is_cache_valid(entry.get("timestamp", ""), FAILURE_COOLDOWN_HOURS):
        return True
    return False


def record_failure(feed_id: str, reason: str, url: str = "") -> None:
    """记录失败源到冷却缓存"""
    cache = _load_json_cache(FAILURE_CACHE_FILE)
    cache[feed_id] = {
        "timestamp": datetime.now(TZ_CN).isoformat(),
        "reason": reason,
        "url": url,
    }
    _save_json_cache(FAILURE_CACHE_FILE, cache)


def clear_failure(feed_id: str) -> None:
    """源恢复后清除失败记录"""
    cache = _load_json_cache(FAILURE_CACHE_FILE)
    if feed_id in cache:
        del cache[feed_id]
        _save_json_cache(FAILURE_CACHE_FILE, cache)


# ============================================================
# RSS 解析
# ============================================================
def parse_rss(xml_text: str) -> tuple[bool, list[dict]]:
    """解析 RSS/Atom XML，返回 (是否有效 XML, 条目列表)。

    有效 XML 但 0 条 = 「有效空」（采集成功但无内容），区别于 XML 解析失败。
    """
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return False, items

    # RSS 2.0
    for item in root.iter("item"):
        entry = {}
        for child in item:
            tag = child.tag.split("}")[-1].lower()
            if tag == "title":
                entry["title"] = (child.text or "").strip()
            elif tag == "link":
                entry["link"] = (child.text or "").strip()
            elif tag in ("description", "content:encoded", "content"):
                entry["description"] = (child.text or "").strip()
            elif tag == "pubdate":
                entry["pubdate"] = (child.text or "").strip()
            elif tag == "guid":
                entry["guid"] = (child.text or "").strip()
        if entry.get("title"):
            items.append(entry)

    # Atom
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry_el in root.findall(".//atom:entry", ns):
            entry = {}
            title_el = entry_el.find("atom:title", ns)
            if title_el is not None:
                entry["title"] = (title_el.text or "").strip()
            link_el = entry_el.find("atom:link", ns)
            if link_el is not None:
                entry["link"] = link_el.get("href", "").strip()
            summary_el = entry_el.find("atom:summary", ns) or entry_el.find("atom:content", ns)
            if summary_el is not None:
                entry["description"] = (summary_el.text or "").strip()
            updated_el = entry_el.find("atom:updated", ns) or entry_el.find("atom:published", ns)
            if updated_el is not None:
                entry["pubdate"] = (updated_el.text or "").strip()
            id_el = entry_el.find("atom:id", ns)
            if id_el is not None:
                entry["guid"] = (id_el.text or "").strip()
            if entry.get("title"):
                items.append(entry)

    return True, items


def _request_with_fallback(urls: list[str], feed_name: str) -> tuple[str, str] | None:
    """
    依次尝试多个 URL，对 403 使用浏览器头重试。
    返回 (xml_text, working_url)，全部失败返回 None。
    """
    for idx, url in enumerate(urls):
        # 第一次用普通头，403 时用浏览器头重试同一 URL
        for headers in (HEADERS, BROWSER_HEADERS):
            try:
                resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 403:
                    if headers is HEADERS:
                        # 普通头被拒，用浏览器头重试同一 URL
                        continue
                    else:
                        # 浏览器头也被拒，跳到下一个 URL
                        print(f"  [{feed_name}] {url} → 403（浏览器头也被拒），尝试备用 URL")
                        break
                resp.raise_for_status()
                return resp.text, url
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else "?"
                if headers is HEADERS and status == 403:
                    continue  # 让浏览器头重试
                print(f"  [{feed_name}] {url} → HTTP {status}，尝试下一个 URL")
                break
            except requests.RequestException as e:
                print(f"  [{feed_name}] {url} → {type(e).__name__}，尝试下一个 URL")
                break
    return None


def fetch_feed(feed: dict) -> tuple[bool, list[dict]]:
    """
    抓取并解析单个 RSS 源（带本地缓存 + 失败冷却 + 多 URL 回退）。
    返回 (是否成功, 条目列表)：成功但 0 条 = 有效空；失败 = False。
    """
    feed_id = feed["id"]

    # 1. 失败冷却期内直接跳过（避免重复请求已知失效源，如 RSSHub 超时）
    if is_failure_cooled_down(feed_id):
        print(f"  [{feed['name']}] 跳过（失败冷却期内，{FAILURE_COOLDOWN_HOURS}h 后重试）")
        return False, []

    # 2. 优先使用成功缓存（TTL 内）
    cached = get_cached_feed(feed_id)
    if cached is not None:
        print(f"  [{feed['name']}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]

    # 3. 构造待尝试 URL 列表（主 URL + 备用 URL）
    urls = [feed["url"]]
    urls.extend(feed.get("fallback_urls", []))

    # 4. 抓取（多 URL 回退 + 403 浏览器头重试）
    result = _request_with_fallback(urls, feed["name"])
    if result is None:
        record_failure(feed_id, "所有 URL 均失败", feed["url"])
        print(f"  [{feed['name']}] 抓取失败（已记录冷却）")
        return False, []

    xml_text, working_url = result

    # 5. 解析（区分「解析失败」与「有效空」）
    ok, items = parse_rss(xml_text)
    if not ok:
        record_failure(feed_id, f"解析失败（非 XML），URL={working_url}", working_url)
        print(f"  [{feed['name']}] 解析失败（已记录冷却）")
        return False, []

    # 6. 成功（items 可为空 = 有效空）：保存缓存 + 清除失败记录
    save_cached_feed(feed_id, items)
    clear_failure(feed_id)
    print(f"  [{feed['name']}] 抓取 {len(items)} 条")
    return True, items[:MAX_ITEMS_PER_FEED]


def _pubmed_date(art: dict) -> str | None:
    """提取 PubMed 文献真实发表日期。
    优先电子发表日期（epubdate），其次期刊卷期日期（pubdate）。
    不使用数据库排序日期（sortpubdate）；不可确认时返回 None（留空不伪造）。"""
    for key in ("epubdate", "pubdate"):
        raw = art.get(key, "")
        if raw:
            d = parse_date_or_none(raw)
            if d:
                return d
    return None


def fetch_pubmed_abstracts(pmids: list[str]) -> dict[str, str]:
    """通过 efetch 批量抓取 PubMed 摘要（rettype=abstract），失败/限流返回空字典，不伪装成功。"""
    if not pmids:
        return {}
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={','.join(pmids)}&rettype=abstract&retmode=xml"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return {}
    abstracts: dict[str, str] = {}
    for art in root.iter("PubmedArticle"):
        pmid_el = art.find(".//PMID")
        pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else ""
        parts = []
        for at in art.iter("AbstractText"):
            label = at.get("Label")
            txt = (at.text or "").strip()
            if label:
                parts.append(f"{label}: {txt}")
            elif txt:
                parts.append(txt)
        if pmid and parts:
            abstracts[pmid] = " ".join(parts).strip()
    return abstracts


def fetch_pubmed(query: dict) -> tuple[bool, list[dict]]:
    """通过 NCBI E-utilities API 抓取 PubMed 文献（带本地缓存）。
    返回 (是否成功, 条目列表)：成功但无结果 = 有效空（True, []）；失败 = (False, [])。"""
    cache_id = "pubmed-" + hashlib.md5(query["term"].encode("utf-8")).hexdigest()[:8]

    # 1. 失败冷却检查
    if is_failure_cooled_down(cache_id):
        print(f"  [{query['name']}] 跳过（失败冷却期内）")
        return False, []

    # 2. 成功缓存检查
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{query['name']}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]

    items = []
    try:
        # 1. esearch 获取 PMID 列表
        search_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={requests.utils.quote(query['term'])}"
            "&retmax=10&sort=date&retmode=json"
        )
        resp = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        id_list = resp.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            print(f"  [{query['name']}] 无结果（有效空）")
            return True, []

        # 2. esummary 获取文献详情
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pubmed&id={','.join(id_list)}&retmode=json"
        )
        resp = requests.get(summary_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json().get("result", {})

        for uid in result.get("uids", []):
            art = result.get(uid, {})
            title = art.get("title", "").strip()
            if not title:
                continue
            journal = art.get("fulljournalname", "") or art.get("source", "")
            pubdate = _pubmed_date(art) or ""  # 真实发表日期，不可得则为空串（不伪造）
            author_list = [a.get("name", "") for a in art.get("authors", [])]
            authors_str = ", ".join(author_list[:3])
            # 引文线索占位（真实摘要由 efetch 补充，此处不把日期伪造进摘要）
            description = f"{authors_str} et al. {journal}." if authors_str else journal

            # 提取 DOI（esummary 的 articleids / elocationid）
            doi = ""
            for aid in art.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value", "")
                    break
            if not doi:
                eloc = art.get("elocationid", "")
                if eloc.startswith("doi:"):
                    doi = eloc[4:].strip()

            items.append({
                "title": title,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "description": description,
                "pubdate": pubdate,
                "guid": uid,
                "pmid": uid,
                "journal": journal,
                "source": art.get("source", ""),
                "pubstatus": art.get("pubstatus", ""),
                "authors": author_list,
                "doi": doi,
                "query": query["name"],
            })

        # 3. efetch 补充真实摘要（失败/限流则留空，不伪装成功）
        abstracts = fetch_pubmed_abstracts([it["pmid"] for it in items])
        for it in items:
            it["abstract"] = abstracts.get(it["pmid"], "")

        # 成功：保存缓存 + 清除失败记录
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{query['name']}] 抓取 {len(items)} 条")
        return True, items[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{query['name']}] 抓取失败（已记录冷却）: {e}")
        return False, []


# ============================================================
# ClinicalTrials.gov API v2
# ============================================================
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"

# overallStatus → 统一 TrialStatus 枚举（与 src/types/content.ts 保持一致）
# registered=已注册未启动；recruiting=招募/进行中；completed=已完成；terminated=终止/撤回；unknown=未知
CLINICALTRIALS_STATUS_MAP = {
    "NOT_YET_RECRUITING": "registered",
    "RECRUITING": "recruiting",
    "ENROLLING_BY_INVITATION": "recruiting",
    "ACTIVE_NOT_RECRUITING": "recruiting",
    "COMPLETED": "completed",
    "APPROVED_FOR_MARKETING": "completed",
    "AVAILABLE": "completed",
    "TERMINATED": "terminated",
    "WITHDRAWN": "terminated",
    "SUSPENDED": "terminated",
    "NO_LONGER_AVAILABLE": "terminated",
    "TEMPORARILY_NOT_AVAILABLE": "terminated",
    "UNKNOWN": "unknown",
}


def _map_clinicaltrials_study_design(study_type: str, design_info: dict) -> str:
    """将 ClinicalTrials 的 studyType + designInfo 映射为统一 StudyDesign 枚举。

    - 干预性 + 随机分配 → rct
    - 观察性 + 队列 → cohort；观察性 + 病例对照 → caseControl
    - 其余（非随机干预、单臂、其他观察设计）→ other（不做过度推断）
    """
    st = (study_type or "").upper()
    info = design_info or {}
    if st == "INTERVENTIONAL":
        if (info.get("allocation") or "").upper() == "RANDOMIZED":
            return "rct"
        return "other"
    if st == "OBSERVATIONAL":
        model = (info.get("observationalModel") or "").upper()
        if model == "COHORT":
            return "cohort"
        if model in ("CASE_CONTROL", "CASE_CROSSOVER", "CASE_ONLY"):
            return "caseControl"
        return "other"
    return "other"


def _parse_clinicaltrials_study(study: dict) -> dict | None:
    """将单个 ClinicalTrials API v2 study 对象映射为内部 item 字典；无效返回 None。"""
    ps = study.get("protocolSection") or {}
    im = ps.get("identificationModule") or {}
    nct_id = (im.get("nctId") or "").strip()
    if not nct_id:
        return None

    title = (im.get("briefTitle") or "").strip() or (im.get("officialTitle") or "").strip()
    if not title:
        return None

    st = ps.get("statusModule") or {}
    dm = ps.get("designModule") or {}
    cm = ps.get("conditionsModule") or {}
    dsm = ps.get("descriptionModule") or {}
    aim = ps.get("armsInterventionsModule") or {}

    overall_status = (st.get("overallStatus") or "").upper()
    trial_status = CLINICALTRIALS_STATUS_MAP.get(overall_status, "unknown")
    study_design = _map_clinicaltrials_study_design(dm.get("studyType") or "", dm.get("designInfo") or {})

    # 发布时间优先取最近一次更新；不可得则回退首次发布，仍不可得留空（不伪造）
    last_update = st.get("lastUpdatePostDateStruct") or {}
    first_post = st.get("studyFirstPostDateStruct") or {}
    pub_date = last_update.get("date") or first_post.get("date") or ""

    enrollment = dm.get("enrollmentInfo") or {}
    sample_size = str(enrollment["count"]) if enrollment.get("count") is not None else None

    interventions = [inv.get("name") for inv in (aim.get("interventions") or []) if inv.get("name")]

    # 关联 PMID：来自 referencesModule（结果/背景/衍生参考文献），RESULT 类型优先。
    # 仅捕获 PMID 用于试验↔论文关联，不把试验记录误判为论文。
    refs = ps.get("referencesModule", {}).get("references", [])
    pmids: list[str] = []
    for ref in refs:
        p = (ref.get("pmid") or "").strip()
        if not p:
            continue
        if ref.get("type") == "RESULT":
            pmids.insert(0, p)
        elif p not in pmids:
            pmids.append(p)
    # 去重且保持 RESULT 优先顺序
    seen: set[str] = set()
    pmids = [p for p in pmids if not (p in seen or seen.add(p))]

    return {
        "title": title,
        "link": f"https://clinicaltrials.gov/study/{nct_id}",
        "description": (dsm.get("briefSummary") or "").strip(),
        "pubdate": pub_date,
        "nctId": nct_id,
        "trialStatus": trial_status,
        "studyDesign": study_design,
        "conditions": cm.get("conditions") or [],
        "interventions": interventions,
        "sampleSize": sample_size,
        "sponsor": (im.get("organization") or {}).get("fullName", ""),
        "pmids": pmids,
    }


def fetch_clinicaltrials(query: dict) -> tuple[bool, list[dict]]:
    """通过 ClinicalTrials.gov API v2 抓取临床试验注册信息（带本地缓存 + 失败冷却）。
    返回 (是否成功, 条目列表)：成功但无结果 = 有效空（True, []）；失败 = (False, [])。"""
    cache_id = "clinicaltrials-" + hashlib.md5(query["cond"].encode("utf-8")).hexdigest()[:8]

    # 1. 失败冷却检查
    if is_failure_cooled_down(cache_id):
        print(f"  [{query['name']}] 跳过（失败冷却期内）")
        return False, []

    # 2. 成功缓存检查
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{query['name']}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]

    try:
        resp = requests.get(
            CLINICALTRIALS_API,
            params={
                "query.cond": query["cond"],
                "format": "json",
                "pageSize": MAX_ITEMS_PER_FEED,
                "sort": "LastUpdatePostDate:desc",
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        studies = resp.json().get("studies", [])
        if not studies:
            print(f"  [{query['name']}] 无结果（有效空）")
            return True, []

        items = []
        for study in studies:
            item = _parse_clinicaltrials_study(study)
            if item:
                item["query"] = query["name"]
                items.append(item)

        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{query['name']}] 抓取 {len(items)} 条")
        return True, items[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{query['name']}] 抓取失败（已记录冷却）: {e}")
        return False, []


# ============================================================
# WHO ICTRP 全注册中心（经 WHO ICTRP 聚合平台检索）
# ============================================================
WHO_ICTRP_URL = "https://trialsearch.who.int/"
WHO_ICTRP_DETAIL_URL = "https://trialsearch.who.int/Trial2.aspx?TrialID={}"
WHO_TIMEOUT = 40  # WHO ICTRP 为 ASP.NET 页面，响应较慢，需更长超时

# WHO ICTRP 专用请求头：用精简 HTML 头而非 RSS 头。
# 经实测，BROWSER_HEADERS 的 RSS Accept 与 br 编码会使该站挂起超时；
# 仅带 UA + HTML Accept + Accept-Language 即可稳定返回 200。
WHO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# WHO ICTRP 招募状态 → 统一 TrialStatus 枚举（与 src/types/content.ts 保持一致）
WHO_STATUS_MAP = {
    "Recruiting": "recruiting",
    "Enrolling by invitation": "recruiting",
    "Active, not recruiting": "recruiting",
    "Pending": "registered",
    "Not yet recruiting": "registered",
    "Completed": "completed",
    "Complete": "completed",
    "Terminated": "terminated",
    "Withdrawn": "terminated",
    "Suspended": "terminated",
    "Not recruiting": "completed",  # 保守：不再招募多为已结束/随访期
    "Unknown status": "unknown",
}


def _html_to_text(html: str) -> str:
    """去除脚本/样式块与标签，返回纯文本（用于 WHO ICTRP 页面解析）。"""
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _map_who_study_design(study_type: str, study_design: str) -> str:
    """将 WHO ICTRP 的 Study type + Study design 映射为统一 StudyDesign 枚举。

    - 干预性 + 随机（非「非随机」）→ rct；其余干预性 → other
    - 观察性 + 队列 → cohort；观察性 + 病例对照 → caseControl；其余 → other
    """
    st = (study_type or "").lower()
    sd = (study_design or "").lower()
    if "interventional" in st:
        if "random" in sd and "non" not in sd:
            return "rct"
        return "other"
    if "observational" in st:
        if "cohort" in sd:
            return "cohort"
        if "case-control" in sd or "case control" in sd:
            return "caseControl"
        return "other"
    return "other"


# 各注册中心元数据（用于 sourceName / language / geographicScope 回填）。
# NCT 由 ClinicalTrials.gov 直连源覆盖，此处仅识别不新增。
WHO_REGISTRY_META = {
    "chictr": {
        "sourceName": "中国临床试验注册中心（ChiCTR）",
        "language": "zh",
        "geographicScope": "china",
    },
    "euctr": {
        "sourceName": "EU Clinical Trials Register（EudraCT）",
        "language": "en",
        "geographicScope": "eu",
    },
    "ctis": {
        "sourceName": "EU Clinical Trials Information System（CTIS）",
        "language": "en",
        "geographicScope": "eu",
    },
}


def _classify_who_trial(trial_id: str) -> str | None:
    """按注册号模式识别 WHO ICTRP「主 ID」所属注册中心，返回 sourceId（无法识别返回 None）。

    - NCT + 8 位数字 → clinicaltrials（已有直连源，抓取阶段跳过）
    - ChiCTR 前缀 → chictr
    - `YYYY-NNNNNN-NN`（EudraCT / EU CT 号共用格式）→ 按年份区分：>=2022 为 CTIS，否则 EU CTR(EudraCT)
    """
    tid = (trial_id or "").strip()
    if re.match(r"^NCT\d{8}$", tid, re.I):
        return "clinicaltrials"
    if re.match(r"^ChiCTR", tid, re.I):
        return "chictr"
    m = re.match(r"^(\d{4})-\d{4,7}-\d{1,3}$", tid)
    if m:
        return "ctis" if int(m.group(1)) >= 2022 else "euctr"
    return None


def _parse_who_list(html: str) -> list[dict]:
    """解析 WHO ICTRP 搜索结果表格，返回 [{trial_id,title,status,date,sourceId}]。"""
    results = []
    for tr in re.findall(r"<tr[\s\S]*?</tr>", html, flags=re.I):
        tds = re.findall(r"<td[\s\S]*?</td>", tr, flags=re.I)
        if len(tds) < 6:
            continue
        status = _html_to_text(tds[0])
        trial_id = _html_to_text(tds[2])
        title = _html_to_text(tds[4])
        date = _html_to_text(tds[5])
        # 主 ID 须能被注册号模式识别（NCT / ChiCTR / EudraCT / EU CT 号）
        sid = _classify_who_trial(trial_id)
        if sid is None:
            continue
        results.append({"trial_id": trial_id, "title": title, "status": status, "date": date, "sourceId": sid})
    return results


def _parse_who_detail(html: str) -> dict:
    """解析 WHO ICTRP 试验详情页，提取状态/研究类型/设计/申办方/疾病/干预。"""
    text = _html_to_text(html)

    def extract(label: str, ends: tuple[str, ...]) -> str:
        i = text.find(label)
        if i < 0:
            return ""
        s = i + len(label)
        e = len(text)
        for end in ends:
            j = text.find(end, s)
            if 0 <= j < e:
                e = j
        return text[s:e].strip()

    status = extract("Recruitment status:", ("URL:", "Study type:", "Countries of recruitment"))
    study_type = extract("Study type:", ("Study design:", "Phase:"))
    study_design = extract("Study design:", ("Phase:", "Countries of recruitment"))
    sponsor = extract("Primary sponsor:", ("Public title:", "Scientific title:", "Secondary sponsor:", "Source of funding:", "Date of registration"))
    condition = extract("Condition(s) or Problem(s) studied", ("Intervention", "Key inclusion", "Outcome"))
    interventions = extract("Intervention(s)", ("Key inclusion", "Primary Outcome", "Outcome"))
    if not interventions:
        interventions = extract("Intervention:", ("Key inclusion", "Primary Outcome", "Outcome"))
    if not interventions:
        interventions = extract("Intervention", ("Key inclusion", "Primary Outcome", "Outcome"))
    # Secondary ID(s)：跨平台注册号（如 NCT），用于识别同一试验在不同注册平台的重复记录。
    secondary_text = extract("Secondary ID(s)", ("Source(s) of Monetary Support", "Secondary Sponsor(s)", "Ethics review"))

    def split_list(s: str) -> list[str]:
        parts = [p.strip() for p in re.split(r"[;,/]", s) if p.strip()]
        return parts[:6]

    return {
        "status": status,
        "study_type": study_type,
        "study_design": study_design,
        "sponsor": sponsor,
        "conditions": split_list(condition),
        "interventions": split_list(interventions),
        "secondary_ids": _extract_trial_ids(secondary_text),
    }


def _who_ictrp_search(term: str) -> list[dict]:
    """WHO ICTRP 搜索（ASP.NET postback），返回结果行列表。"""
    s = requests.Session()
    s.headers.update(WHO_HEADERS)
    home = s.get(WHO_ICTRP_URL, timeout=WHO_TIMEOUT)
    home.raise_for_status()

    def field(name: str) -> str:
        m = re.search(r'name="%s"[^>]*value="([^"]*)"' % re.escape(name), home.text)
        return m.group(1) if m else ""

    data = {
        "ToolkitScriptManager_HiddenField": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": field("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": field("__VIEWSTATEGENERATOR"),
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": field("__EVENTVALIDATION"),
        "TextBox1": term,
        "Button1": "Search",
        "TextBoxWatermarkExtender1_ClientState": "",
    }
    resp = s.post(WHO_ICTRP_URL, data=data, timeout=WHO_TIMEOUT)
    resp.raise_for_status()
    return _parse_who_list(resp.text)


def fetch_ictrp(query: dict) -> tuple[bool, list[dict]]:
    """经 WHO ICTRP 检索全注册中心（ChiCTR / EU CTR / CTIS）的抗感染试验（带缓存 + 失败冷却）。

    NCT 记录已由 ClinicalTrials.gov 直连源覆盖，此处跳过以避免重复采集。
    """
    cache_id = "ictrp-" + hashlib.md5(query["term"].encode("utf-8")).hexdigest()[:8]

    if is_failure_cooled_down(cache_id):
        print(f"  [{query['name']}] 跳过（失败冷却期内）")
        return False, []

    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{query['name']}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]

    try:
        rows = _who_ictrp_search(query["term"])
        # 跳过 NCT（已有 ClinicalTrials.gov 直连源），保留 ChiCTR / EU CTR / CTIS
        rows = [r for r in rows if r.get("sourceId") in ("chictr", "euctr", "ctis")]
        if not rows:
            print(f"  [{query['name']}] 无结果（有效空）")
            return True, []

        items = []
        for r in rows[:MAX_ITEMS_PER_FEED]:
            detail: dict = {}
            try:
                detail = _fetch_who_detail(r["trial_id"])
            except Exception as e:
                print(f"    [{r['sourceId']}] 详情抓取失败 {r['trial_id']}: {e}")

            raw_status = detail.get("status") or r.get("status") or ""
            items.append({
                "title": r["title"].strip(),
                "link": WHO_ICTRP_DETAIL_URL.format(r["trial_id"]),
                "pubdate": r["date"],
                "trialId": r["trial_id"],
                "sourceId": r["sourceId"],
                "trialStatus": WHO_STATUS_MAP.get(raw_status, "unknown"),
                "studyDesign": _map_who_study_design(detail.get("study_type", ""), detail.get("study_design", "")),
                "conditions": detail.get("conditions", []),
                "interventions": detail.get("interventions", []),
                "sponsor": detail.get("sponsor", ""),
                "secondaryIds": detail.get("secondary_ids", []),
                "query": query["name"],
            })

        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{query['name']}] 抓取 {len(items)} 条")
        return True, items[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{query['name']}] 抓取失败（已记录冷却）: {e}")
        return False, []


def _fetch_who_detail(trial_id: str) -> dict:
    """抓取单个试验的 WHO ICTRP 详情页。"""
    resp = requests.get(WHO_ICTRP_DETAIL_URL.format(trial_id), headers=WHO_HEADERS, timeout=WHO_TIMEOUT)
    resp.raise_for_status()
    return _parse_who_detail(resp.text)


# ============================================================
# 文本清洗
# ============================================================
def clean_html(html: str) -> str:
    """去除 HTML 标签，返回纯文本"""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_id(prefix: str, text: str) -> str:
    """生成稳定 ID"""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{h}"


def parse_date(date_str: str) -> str:
    """解析多种日期格式，返回 ISO 字符串（默认当前时间）"""
    if not date_str:
        return datetime.now(TZ_CN).isoformat()
    # 尝试常见格式
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ_CN)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now(TZ_CN).isoformat()


def parse_date_or_none(date_str: str) -> str | None:
    """严格解析日期，失败返回 None（绝不伪造发布时间）。"""
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%Y %b %d",
        "%Y %b",
        "%Y",
    ):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ_CN)
            return dt.isoformat()
        except ValueError:
            continue
    return None


def resolve_link(link: str, feed: dict) -> str:
    """将相对链接解析为绝对 URL（以来源 base_url/url 为依据，不猜测域名）。"""
    if not link:
        return feed.get("url", "")
    if link.startswith(("http://", "https://")):
        return link
    base = feed.get("base_url") or feed.get("url", "")
    if base:
        return urljoin(base, link)
    return link


# ============================================================
# 关键词打分与标签提取
# ============================================================
def score_relevance(text: str) -> tuple[int, dict[str, int], list[str]]:
    """
    计算关键词相关性得分。
    返回：(总分, 各分组得分, 命中的标签列表)
    """
    group_scores: dict[str, int] = {}
    matched_tags: list[str] = []

    for group_id, group in KEYWORD_GROUPS.items():
        hits = 0
        for pattern in group["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                hits += 1
        if hits > 0:
            group_scores[group_id] = hits
            matched_tags.append(group["label"])

    total = sum(group_scores.values())

    # 提取细粒度标签（ASCII 缩写用词边界，避免 "CT" 误命中 "infection"、"AI" 误命中 "detail"）
    fine_tags: list[str] = []
    for kw, tag in TAG_KEYWORDS.items():
        if kw.isascii() and kw.isalnum():
            pattern = r"\b" + re.escape(kw) + r"\b"
        else:
            pattern = re.escape(kw)
        if re.search(pattern, text, re.IGNORECASE) and tag not in fine_tags:
            fine_tags.append(tag)

    return total, group_scores, fine_tags


def detect_study_type(text: str) -> str:
    """识别研究类型"""
    for stype, patterns in STUDY_TYPE_PATTERNS.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return stype
    return "other"


def determine_category(text: str, group_scores: dict, feed: dict) -> str:
    """确定行业资讯分类"""
    if "fungal" in group_scores and "amr" in group_scores:
        return "真菌与耐药"
    if "fungal" in group_scores:
        return "真菌与耐药"
    if "amr" in group_scores:
        return "AMR"
    if "imaging" in group_scores:
        return "感染影像"
    if "ai_clinical" in group_scores:
        return "AI临床"
    return feed.get("default_category", "其他")


# ============================================================
# 评分逻辑（五轴，1-10）
# ============================================================
def clamp(v: float, lo: float = 1, hi: float = 10) -> int:
    return max(lo, min(hi, round(v)))


def score_industry(text: str, group_scores: dict, authority: int) -> dict:
    """行业资讯五轴评分"""
    rel = sum(group_scores.values())
    has_fungal = "fungal" in group_scores
    has_amr = "amr" in group_scores
    has_imaging = "imaging" in group_scores
    has_ai = "ai_clinical" in group_scores

    policy_impact = clamp(4 + (has_amr or has_fungal) * 3 + authority * 0.3)
    market_impact = clamp(3 + has_amr * 3 + has_fungal * 2 + authority * 0.2)
    breakthrough = clamp(3 + has_ai * 3 + has_imaging * 2 + (rel > 3) * 2)
    competitive = clamp(3 + has_amr * 3 + has_fungal * 2 + authority * 0.2)
    timeliness = clamp(authority + (rel > 2) * 1)

    scores = {
        "policyImpact": policy_impact,
        "marketImpact": market_impact,
        "breakthrough": breakthrough,
        "competitiveImpact": competitive,
        "timelinessAuthority": timeliness,
    }
    scores["totalScore"] = sum(scores.values())
    return scores


def score_research(text: str, group_scores: dict, authority: int, study_type: str) -> dict:
    """科研资讯五轴评分"""
    rel = sum(group_scores.values())
    has_fungal = "fungal" in group_scores
    has_amr = "amr" in group_scores
    has_imaging = "imaging" in group_scores
    has_ai = "ai_clinical" in group_scores

    ev_base = {"RCT": 9, "meta-analysis": 9, "cohort": 7, "real-world": 7,
               "review": 6, "preprint": 4, "other": 5}.get(study_type, 5)

    topic_insp = clamp(5 + has_fungal * 2 + has_amr * 2 + has_ai * 2 + has_imaging * 1)
    clinical_app = clamp(4 + has_fungal * 2 + has_amr * 3 + has_imaging * 2 + authority * 0.3)
    evidence = clamp(ev_base + (rel > 2) * 1)
    specialty = clamp(5 + has_fungal * 1 + has_amr * 1 + has_imaging * 1)
    research_val = clamp(5 + has_ai * 3 + has_fungal * 2 + has_amr * 2 + (rel > 3) * 1)

    scores = {
        "topicInspiration": topic_insp,
        "clinicalApplicability": clinical_app,
        "evidenceLevel": evidence,
        "specialtyUniversality": specialty,
        "researchValue": research_val,
    }
    scores["totalScore"] = sum(scores.values())
    return scores


# ============================================================
# 统一 Schema 字段补充与轻量合并
# ============================================================
def resolve_content_type(feed: dict, item: dict, kind: str) -> str | None:
    """contentType 优先级：单条记录 > 源级默认值 > 未分类。

    严格区分四概念：
    - kind：现有 news/research 业务分区（决定写入哪个文件）
    - sourceType：信息来源性质（journal/database/society/enterprise/...）
    - contentType：内容业务类型（policy/approval/safety/surveillance/...）
    - studyDesign：研究设计类型（rct/cohort/metaAnalysis/...）
    """
    ct = item.get("content_type") or feed.get("content_type")
    if ct:
        return ct
    # 无法可靠判断时不强行归类；research 模型天然为 research 作为最后回退
    if kind == "research":
        return "research"
    return None


def _fill_default(entry: dict, field: str, default) -> None:
    """字段缺失、为 None 或空字符串时回填默认值；否则保留已有合法值。"""
    val = entry.get(field)
    if val is None or val == "":
        entry[field] = default


def apply_schema_fields(entry: dict, feed: dict, item: dict, kind: str) -> dict:
    """补充统一 Schema 字段（camelCase，与 content.ts 一致）。
    仅补缺失/空字段，绝不覆盖已有合法值。"""
    now = datetime.now(TZ_CN).isoformat()

    ct = resolve_content_type(feed, item, kind)
    if ct:
        if ct not in CONTENT_TYPES:
            print(f"  [警告] 非法 contentType={ct!r}，回退为 other", file=sys.stderr)
            ct = "other"
        entry.setdefault("contentType", ct)

    st = entry.get("sourceType") or feed.get("source_type") or "other"
    if st not in SOURCE_TYPES:
        print(f"  [警告] 非法 sourceType={st!r}，回退为 other", file=sys.stderr)
        st = "other"
    entry["sourceType"] = st
    if feed.get("id"):
        entry.setdefault("sourceId", feed["id"])
    if feed.get("language"):
        entry.setdefault("language", feed["language"])
    if feed.get("geographic_scope"):
        entry.setdefault("geographicScope", feed["geographic_scope"])

    # 状态机 / 版权：缺失或空值才回填默认，绝不覆盖已有合法值
    _fill_default(entry, "recordStatus", "active")
    _fill_default(entry, "verificationStatus", "pending")
    _fill_default(entry, "reviewStatus", "autoProcessed")
    _fill_default(entry, "licenseStatus", "unknown")
    if not isinstance(entry.get("licensePermissions"), list):
        entry["licensePermissions"] = []

    # 时间戳：ingestedAt/lastCheckedAt 为系统采集时间；sourceUpdatedAt 仅在来源明确提供时设置（不伪造）
    entry.setdefault("ingestedAt", now)
    entry.setdefault("lastCheckedAt", now)
    if not entry.get("sourceUpdatedAt"):
        entry.pop("sourceUpdatedAt", None)

    # 外部 ID / 元数据（仅当来源提供）
    if item.get("pmid"):
        entry.setdefault("externalId", item["pmid"])
        entry.setdefault("pmid", item["pmid"])
    if item.get("nctId"):
        entry.setdefault("externalId", item["nctId"])
        entry.setdefault("trialId", item["nctId"])
    if item.get("trialStatus"):
        entry.setdefault("trialStatus", item["trialStatus"])
    if item.get("doi"):
        entry.setdefault("doi", item["doi"])
    if item.get("authors"):
        entry.setdefault("authors", item["authors"])
    if item.get("abstract"):
        entry.setdefault("abstract", item["abstract"])
    if item.get("query"):
        entry.setdefault("sourceQuery", item["query"])

    return entry


class CorruptDataError(Exception):
    """旧数据文件损坏：禁止覆盖写入，必须保留原文件。"""


def _build_source_name_map() -> dict[str, str]:
    """sourceName → sourceId 映射（用于旧记录回退匹配，旧数据可能无 sourceId）。"""
    m: dict[str, str] = {}
    for feed in RSS_FEEDS:
        m[feed["name"]] = feed["id"]
    for src in CURATED_SOURCES:
        m[src["name"]] = src["id"]
    return m


def _infer_source_id(record: dict, name_map: dict[str, str]) -> str | None:
    """推断旧记录的 sourceId：优先 record['sourceId']，否则按 sourceName 匹配；
    PubMed / ClinicalTrials / WHO ICTRP / FDA / EMA / NMPA 旧记录按名称前缀分别归入对应 sourceId。"""
    sid = record.get("sourceId")
    if sid:
        return sid
    name = record.get("sourceName", "")
    if name in name_map:
        return name_map[name]
    if name.startswith("PubMed ("):
        return "pubmed"
    if name.startswith("ClinicalTrials ("):
        return "clinicaltrials"
    if name.startswith("ChiCTR ("):
        return "chictr"
    if name.startswith("EU Clinical Trials Register"):
        return "euctr"
    if name.startswith("EU Clinical Trials Information System"):
        return "ctis"
    if name.startswith("FDA "):
        return "fda"
    if name.startswith("EMA "):
        return "ema"
    if name.startswith("NMPA "):
        return "nmpa"
    if name.startswith("WHO GLASS"):
        return "glass"
    return None


_LEGACY_PUBMED_KEY = "pubmed:__legacy__"  # 旧 PubMed 记录（无 sourceQuery）的哨兵键
_LEGACY_CLINICALTRIALS_KEY = "clinicaltrials:__legacy__"  # 旧 ClinicalTrials 记录（无 sourceQuery）的哨兵键
_LEGACY_CHICTR_KEY = "chictr:__legacy__"  # 旧 ChiCTR 记录（无 sourceQuery）的哨兵键


def _task_key(record: dict, name_map: dict[str, str]) -> str | None:
    """计算旧记录所属的采集任务键（用于失败保护）。

    - 普通源：sourceId（如 cidrap / idcm / gardp）。
    - PubMed / ClinicalTrials / WHO ICTRP(ChiCTR / EU CTR / CTIS)：sourceId + 查询名（如
      `pubmed::PubMed (CRAB / CRE 耐药)`、`clinicaltrials::ClinicalTrials (侵袭性真菌感染)`、
      `chictr::WHO ICTRP (侵袭性真菌感染)`），按实际查询任务追踪成功状态，避免部分查询成功掩盖其他查询失败。
    - 旧记录缺少 sourceQuery 时返回哨兵键（`_LEGACY_PUBMED_KEY` / `_LEGACY_CLINICALTRIALS_KEY` /
      `<sourceId>:__legacy__`），由 main() 依据「该来源是否整体成功」决定去留，避免全部成功后仍残留旧记录。
    """
    sid = record.get("sourceId") or _infer_source_id(record, name_map)
    if sid is None:
        return None
    if sid == "pubmed":
        q = record.get("sourceQuery")
        return f"pubmed::{q}" if q else _LEGACY_PUBMED_KEY
    if sid == "clinicaltrials":
        q = record.get("sourceQuery")
        return f"clinicaltrials::{q}" if q else _LEGACY_CLINICALTRIALS_KEY
    if sid in ("chictr", "euctr", "ctis", "fda", "ema", "nmpa", "glass"):
        q = record.get("sourceQuery")
        return f"{sid}::{q}" if q else f"{sid}:__legacy__"
    return sid


def merge_preserving_manual(path: Path, new_entries: list[dict], successful_task_keys: set[str] | None = None) -> list[dict]:
    """轻量合并（方案 B）：按稳定 id 读旧文件，保留旧数据中的人工字段。

    - 自动采集字段（标题/摘要/时间等）以最新来源为准。
    - 人工字段（核验/审核/版权/证据质量等）旧值非默认时优先保留。
    - 本次成功采集的来源/查询任务：按快照更新（无法匹配的旧记录丢弃）。
    - 本次采集失败的来源/查询任务：保留该来源原有记录，不因本次无返回而删除历史数据。
    - 旧文件不存在：允许首次创建。
    - 旧文件存在但解析失败：抛 CorruptDataError 中止写入，保留原文件。
    """
    if not path.exists():
        return new_entries
    try:
        old_list = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise CorruptDataError(
            f"数据文件解析失败，已停止写入并保留原文件：{path}（{e}）"
        )
    if not isinstance(old_list, list):
        raise CorruptDataError(
            f"数据文件结构异常（非 JSON 数组），已停止写入并保留原文件：{path}"
        )

    successful_task_keys = successful_task_keys or set()
    name_map = _build_source_name_map()

    old_by_id = {}
    for e in old_list:
        if isinstance(e, dict) and e.get("id"):
            old_by_id[e["id"]] = e

    new_ids = {e["id"] for e in new_entries}

    # 1) 逐条合并人工字段
    for new_entry in new_entries:
        old = old_by_id.get(new_entry.get("id"))
        if not old:
            continue
        # 重点人工字段：旧值非默认 → 覆盖新值（防止新采集默认值覆盖人工确认）
        for field, default in MANUAL_FIELDS.items():
            old_val = old.get(field, default)
            if old_val != default:
                new_entry[field] = old_val
        # 其他人工补充字段：旧数据中存在且不在自动字段集合 → 保留旧值
        for k, v in old.items():
            if k in AUTO_FIELDS or k in MANUAL_FIELDS:
                continue
            if v not in (None, "", []):
                new_entry.setdefault(k, v)

    # 2) 保留「本次未成功采集」来源/查询任务的旧记录（防网络异常导致历史数据丢失）
    for old in old_list:
        if not isinstance(old, dict) or not old.get("id"):
            continue
        if old["id"] in new_ids:
            continue
        key = _task_key(old, name_map)
        if key is None or key not in successful_task_keys:
            new_entries.append(old)

    new_entries.sort(key=lambda x: x.get("publishTime") or "", reverse=True)
    return new_entries


# ============================================================
# 试验注册记录与论文关联 / 去重（B2.3 后处理）
# ============================================================
def _source_kind(source_id: str | None) -> str:
    """判定记录类型：pubmed=研究论文；clinicaltrials/chictr/euctr/ctis=试验注册记录。"""
    if source_id == "pubmed":
        return "paper"
    if source_id in ("clinicaltrials", "chictr", "euctr", "ctis"):
        return "trial"
    return "other"


def link_and_dedup_research(entries: list[dict]) -> list[dict]:
    """建立试验注册记录↔研究论文的关联，并识别跨注册平台重复试验。

    原则（B2.3 硬约束）：
    - 仅凭显式标识精确匹配（NCT/ChiCTR/PMID），绝不按标题/文本模糊匹配。
    - 严格区分「试验注册记录」与「研究论文」，二者只做 relatedRecords 双向关联，绝不合并/覆盖。
    - 跨平台重复（ChiCTR 的 Secondary ID 命中 ClinicalTrials 的 NCT）→ 保守标记
      recordStatus='duplicate' + supersedesId 指向主记录，绝不删除任何记录。
    - 关联不确定时保留原始记录，不强行匹配。
    纯后处理：只增补 relatedRecords / supersedesId / recordStatus，不修改其他字段。
    """
    # 1) 索引：试验注册记录（trialId + secondaryIds）与论文（pmid/doi）
    trial_by_id: dict[str, list[str]] = {}   # 归一化注册号 -> [记录 id]
    paper_by_pmid: dict[str, list[str]] = {}  # pmid -> [论文记录 id]
    paper_by_doi: dict[str, list[str]] = {}   # doi(小写) -> [论文记录 id]

    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        eid = e["id"]
        kind = _source_kind(e.get("sourceId"))
        if kind == "trial":
            for tid in [e.get("trialId")] + list(e.get("secondaryIds") or []):
                k = _norm_trial_id(tid)
                if k:
                    trial_by_id.setdefault(k, []).append(eid)
        elif kind == "paper":
            if e.get("pmid"):
                paper_by_pmid.setdefault(e["pmid"], []).append(eid)
            if e.get("doi"):
                paper_by_doi.setdefault(e["doi"].strip().lower(), []).append(eid)

    related: dict[str, set[str]] = {e["id"]: set() for e in entries if isinstance(e, dict) and e.get("id")}

    def add_link(a: str, b: str) -> None:
        if a and b and a != b:
            related.setdefault(a, set()).add(b)
            related.setdefault(b, set()).add(a)

    # 2) 论文 → 试验：论文标题/摘要中显式提及的 NCT/ChiCTR 号命中试验注册记录
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        if _source_kind(e.get("sourceId")) != "paper":
            continue
        text = f"{e.get('title') or ''} {e.get('abstract') or ''}"
        for tid in _extract_trial_ids(text):
            for teid in trial_by_id.get(tid, []):
                add_link(e["id"], teid)

    # 3) 试验 → 论文：试验 referencesModule 捕获的首选 PMID 命中论文
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        if _source_kind(e.get("sourceId")) != "trial":
            continue
        pmid = e.get("pmid")
        if pmid:
            for peid in paper_by_pmid.get(pmid, []):
                add_link(e["id"], peid)

    # 4) 试验 → 论文：试验记录若带 DOI（结果已发表为论文时可能提供），按 DOI 命中论文
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        if _source_kind(e.get("sourceId")) != "trial":
            continue
        doi = (e.get("doi") or "").strip().lower()
        if not doi:
            continue
        for peid in paper_by_doi.get(doi, []):
            add_link(e["id"], peid)

    # 5) 跨平台重复：ChiCTR / EU CTR / CTIS 的 Secondary ID 命中 ClinicalTrials 的 NCT（同一试验）
    supersedes: dict[str, str] = {}
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        if e.get("sourceId") not in ("chictr", "euctr", "ctis"):
            continue
        for tid in list(e.get("secondaryIds") or []):
            k = _norm_trial_id(tid)
            for teid in trial_by_id.get(k, []):
                # 仅当命中记录本身是 ClinicalTrials 记录（而非另一个 ICTRP 记录）时才判重
                if teid == e["id"]:
                    continue
                target = next((x for x in entries if x.get("id") == teid), None)
                if target and target.get("sourceId") == "clinicaltrials":
                    supersedes[e["id"]] = teid
                    break
            if e["id"] in supersedes:
                break

    # 6) 落回：relatedRecords 双向 + 重复标记（recordStatus 仅当仍为 active/空时才改，尊重人工状态）
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        eid = e["id"]
        rr = sorted(related.get(eid, set()))
        if rr:
            e["relatedRecords"] = rr
        else:
            e.pop("relatedRecords", None)
        if eid in supersedes:
            e["supersedesId"] = supersedes[eid]
            if e.get("recordStatus") in (None, "", "active"):
                e["recordStatus"] = "duplicate"

    return entries


# ============================================================
# 条目构建
# ============================================================
def build_industry_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    title = item.get("title", "").strip()
    desc = clean_html(item.get("description", ""))
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))  # 严格解析，不可得为 None（不伪造）
    eid = make_id("ind", title + link)

    summary = desc[:200] if desc else title
    impact = f"来自{feed['name']}的抗感染领域动态，"
    if "fungal" in group_scores:
        impact += "涉及深部真菌感染诊疗进展，"
    if "amr" in group_scores:
        impact += "关注耐药菌（含 CRAB/CRE）流行病学与治疗策略，"
    if "imaging" in group_scores:
        impact += "包含感染影像学新方法，"
    if "ai_clinical" in group_scores:
        impact += "涉及 AI 辅助临床决策，"
    impact += "建议结合临床指南综合判断。"

    scores = score_industry(title + " " + desc, group_scores, feed["authority"])

    entry = {
        "id": eid,
        "title": title,
        "eventTime": pub[:10] if pub else None,
        "publishTime": pub,
        "sourceName": feed["name"],
        "sourceUrl": resolve_link(link, feed),
        "category": determine_category(title + " " + desc, group_scores, feed),
        "tags": tags[:6],
        "summary": summary,
        "impact": impact,
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isCluster": False,
        "factType": "fact",
    }
    # 原文摘要（RSS description 即来源提供的摘要；为空则不写，避免编造）
    if desc:
        entry["abstract"] = desc
    return apply_schema_fields(entry, feed, item, "news")


def _is_preprint(item: dict, text: str) -> bool:
    """判定预印本：仅根据来源平台（期刊名/来源名）判断，不做标题/摘要关键词猜测。"""
    journal = (item.get("journal") or item.get("source") or "").lower()
    return any(h in journal for h in PREPRINT_SOURCE_HINTS)


def build_research_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    title = item.get("title", "").strip()
    desc = clean_html(item.get("description", ""))
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))  # 严格解析，不可得为 None（不伪造）
    eid = make_id("res", title + link)

    # 来源名称：PubMed 用真实期刊名；期刊名缺失时退化为平台名 PubMed（绝不用查询词组冒充期刊）
    source_name = item.get("journal") or ("PubMed" if item.get("pmid") else feed.get("name"))

    study_type = detect_study_type(title + " " + desc)
    is_preprint = _is_preprint(item, title + " " + desc)

    core = desc[:300] if desc else title
    limitations = "本条目为自动采集摘要，研究设计与统计方法细节请查阅原文。"
    inspiration = "建议进一步阅读原文以评估证据质量与临床适用性。"

    if "fungal" in group_scores:
        inspiration = "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。"
    if "amr" in group_scores:
        inspiration = "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。"
    if "ai_clinical" in group_scores:
        inspiration = "AI 辅助诊断/决策方向，可探索多中心验证与临床落地路径。"

    # 证据等级：停用自动推断，统一「原文未评估」（不根据 studyType 生成 1a/2b）
    study_design = STUDY_DESIGN_MAP.get(study_type, "other")
    publication_status = "preprint" if is_preprint else PUBLICATION_STATUS_MAP.get("published", "published")

    scores = score_research(title + " " + desc, group_scores, feed["authority"], study_type)

    entry = {
        "id": eid,
        "title": title,
        "sourceName": source_name,
        "sourceUrl": resolve_link(link, feed),
        "studyType": study_type,
        "publishStatus": "preprint" if is_preprint else "published",
        "sampleSize": None,
        "publishTime": pub,
        "coreFindings": core,
        "limitations": limitations,
        "inspiration": inspiration,
        "evidenceLevel": UNASSESSED,
        "evidenceQuality": UNASSESSED,
        "studyDesign": study_design,
        "publicationStatus": publication_status,
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isPreprint": is_preprint,
        "tags": tags[:6],
    }
    # 原文摘要：RSS description 可作来源摘要；PubMed 摘要由 efetch 写入 item["abstract"]
    if desc and not item.get("pmid"):
        entry["abstract"] = desc
    return apply_schema_fields(entry, feed, item, "research")


def build_clinicaltrial_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    """构建 ClinicalTrials 临床试验注册记录（归属科研前沿 research 分区）。"""
    title = item.get("title", "").strip()
    desc = clean_html(item.get("description", ""))
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))  # 严格解析，不可得为 None（不伪造）
    nct_id = item.get("nctId", "")

    # 以 NCT 编号作为稳定 id 基础，确保同一试验重复采集时去重
    eid = make_id("res", f"nct:{nct_id}") if nct_id else make_id("res", title + link)

    # 来源名称：优先申办方组织名；缺失时退化为查询任务名（不伪装）
    source_name = item.get("sponsor") or feed.get("name", "ClinicalTrials.gov")

    core = desc[:300] if desc else title
    limitations = "本条目为临床试验注册信息自动采集，研究设计、入排标准与统计方法细节请查阅 ClinicalTrials.gov 原始记录。"
    inspiration = "可结合本项目抗感染（真菌 / 耐药菌）主题，跟踪该试验的注册状态与后续结果发布。"

    scores = score_research(title + " " + desc, group_scores, feed["authority"], "other")

    entry = {
        "id": eid,
        "title": title,
        "sourceName": source_name,
        "sourceUrl": link,
        "studyType": "other",
        "publishStatus": "published",
        "sampleSize": item.get("sampleSize"),
        "publishTime": pub,
        "coreFindings": core,
        "limitations": limitations,
        "inspiration": inspiration,
        "evidenceLevel": UNASSESSED,
        "evidenceQuality": UNASSESSED,
        "studyDesign": item.get("studyDesign", "other"),
        "publicationStatus": "registered",
        "trialId": nct_id,
        "trialStatus": item.get("trialStatus", "unknown"),
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isPreprint": False,
        "tags": tags[:6],
    }
    if desc:
        entry["abstract"] = desc
    if item.get("conditions"):
        entry["diseases"] = item["conditions"][:6]
    if item.get("interventions"):
        entry["drugs"] = item["interventions"][:6]
    # 关联参考文献 PMID（用于试验↔论文关联；仅记录首选 PMID，不改变本记录「试验注册」性质）
    pmids = item.get("pmids") or []
    if pmids:
        entry["pmid"] = pmids[0]
    return apply_schema_fields(entry, feed, item, "research")


def build_ictrp_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    """构建 WHO ICTRP 临床试验注册记录（ChiCTR / EU CTR / CTIS，归属科研前沿 research 分区）。"""
    title = item.get("title", "").strip()
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))  # 严格解析，不可得为 None（不伪造）
    trial_id = item.get("trialId", "")

    # 按注册中心识别 sourceId，缺失时回退为 chictr（保持旧记录 id 兼容）
    source_id = item.get("sourceId") or _classify_who_trial(trial_id) or "chictr"
    meta = WHO_REGISTRY_META.get(source_id, WHO_REGISTRY_META["chictr"])

    # 以注册中心 + 注册号作为稳定 id 基础，确保同一试验重复采集时去重（chictr 与历史 id 保持一致）
    eid = make_id("res", f"{source_id}:{trial_id}") if trial_id else make_id("res", title + link)

    # 来源名称：优先申办方（如医院）；缺失时退化为注册中心官方名（不伪装）
    source_name = item.get("sponsor") or meta["sourceName"]

    core = title
    limitations = "本条目为临床试验注册信息自动采集，研究设计、入排标准与统计方法细节请查阅 WHO ICTRP 原始记录。"
    inspiration = "可结合本项目抗感染（真菌 / 耐药菌）主题，跟踪该试验的注册状态与后续结果发布。"

    scores = score_research(title, group_scores, feed["authority"], "other")

    entry = {
        "id": eid,
        "title": title,
        "sourceName": source_name,
        "sourceUrl": link,
        "studyType": "other",
        "publishStatus": "published",
        "publishTime": pub,
        "coreFindings": core,
        "limitations": limitations,
        "inspiration": inspiration,
        "evidenceLevel": UNASSESSED,
        "evidenceQuality": UNASSESSED,
        "studyDesign": item.get("studyDesign", "other"),
        "publicationStatus": "registered",
        "externalId": trial_id,
        "trialId": trial_id,
        "trialStatus": item.get("trialStatus", "unknown"),
        "sourceId": source_id,
        "language": meta["language"],
        "geographicScope": meta["geographicScope"],
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isPreprint": False,
        "tags": tags[:6],
    }
    if item.get("conditions"):
        entry["diseases"] = item["conditions"][:6]
    if item.get("interventions"):
        entry["drugs"] = item["interventions"][:6]
    # Secondary ID(s)：跨平台注册号（如 NCT），仅用于识别重复记录；缺失则不写，避免覆盖历史值
    secondary = item.get("secondaryIds") or []
    if secondary:
        entry["secondaryIds"] = secondary
    return apply_schema_fields(entry, feed, item, "research")


# ============================================================
# B4：官方药品审批/监管数据源（FDA / EMA / NMPA）
# ============================================================
def _is_anti_infective(text: str) -> bool:
    """判断文本是否属于本项目聚焦的抗感染领域（深部真菌 + 耐药菌抗菌药）。"""
    if not text:
        return False
    for p in ANTI_INFECTIVE_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def _fmt_fda_date(d: str) -> str:
    """openFDA 日期 YYYYMMDD → YYYY-MM-DD（非 8 位数字则原样返回）。"""
    d = (d or "").strip()
    if re.fullmatch(r"\d{8}", d):
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d


def _fmt_ema_date(d: str) -> str:
    """EMA 日期 DD/MM/YYYY → YYYY-MM-DD（兼容已是 YYYY-MM-DD 或空）。"""
    d = (d or "").strip()
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", d)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return d


def _request_json(url: str, params: dict, name: str) -> dict | None:
    """GET 并解析 JSON，失败返回 None（调用方决定是否记录冷却）。"""
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"    [{name}] 请求/解析失败: {e}")
        return None


def _fetch_regulatory_rss(cache_id: str, name: str, url: str,
                          market_access_type: str, content_type: str) -> tuple[bool, list[dict]]:
    """抓取官方 RSS 并过滤抗感染，返回 (ok, items)。"""
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        ok, raw = parse_rss(r.text)
        if not ok:
            record_failure(cache_id, f"解析失败（非 XML），URL={url}", url)
            print(f"  [{name}] 解析失败（已记录冷却）")
            return False, []
        items = []
        for it in raw:
            title = it.get("title", "")
            desc = clean_html(it.get("description", ""))
            if not _is_anti_infective(f"{title} {desc}"):
                continue
            items.append({
                "title": title,
                "link": it.get("link", ""),
                "description": desc,
                "pubdate": it.get("pubdate", ""),
                "contentType": content_type,
                "marketAccessType": market_access_type,
                "query": name,
            })
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(items)} 条（过滤后）")
        return True, items[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e), url)
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


def fetch_fda_approvals() -> tuple[bool, list[dict]]:
    """openFDA Drugs@FDA：最近抗感染药品原始批准（ORIG）记录。"""
    cache_id = "fda-approvals"
    name = "FDA 药品批准"
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        data = _request_json(FDA_DRUGSFDA_URL, {
            "sort": "submissions.submission_status_date:desc",
            "limit": 100,
        }, name)
        if not data:
            raise RuntimeError("openFDA 返回空")
        items = []
        for rec in data.get("results", []):
            of = rec.get("openfda", {}) or {}
            brand = (of.get("brand_name") or [""])[0]
            generic = (of.get("generic_name") or [""])[0]
            substances = of.get("substance_name") or []
            pharm = of.get("pharm_class_epc") or []
            text = " ".join([brand, generic] + substances + pharm)
            if not _is_anti_infective(text):
                continue
            app_no = rec.get("application_number", "")
            # 原始批准（ORIG）提交作为批准日期与状态来源
            orig = next((s for s in rec.get("submissions", [])
                         if s.get("submission_type") == "ORIG"), None)
            if not orig:
                continue
            orig_date = _fmt_fda_date(orig.get("submission_status_date", ""))
            if not orig_date:
                continue
            label = brand or generic or (substances[0] if substances else app_no)
            items.append({
                "title": f"{label} 获 FDA 批准",
                "link": f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={app_no}",
                "description": "；".join(substances[:3]),
                "pubdate": orig_date,
                "contentType": "approval",
                "marketAccessType": "fda",
                "approvalStatus": "approved" if orig.get("submission_status") == "AP" else None,
                "externalId": app_no,
                "drugs": substances,
                "query": name,
            })
        items.sort(key=lambda x: x["pubdate"], reverse=True)
        items = items[:MAX_ITEMS_PER_FEED]
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(items)} 条")
        return True, items
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


def fetch_fda_enforcement() -> tuple[bool, list[dict]]:
    """openFDA Drug Enforcement：最近抗感染相关药品召回/执法报告。"""
    cache_id = "fda-enforcement"
    name = "FDA 药品召回"
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        data = _request_json(FDA_ENFORCEMENT_URL, {
            "sort": "report_date:desc",
            "limit": 100,
        }, name)
        if not data:
            raise RuntimeError("openFDA enforcement 返回空")
        items = []
        for rec in data.get("results", []):
            desc = rec.get("product_description", "")
            reason = rec.get("reason_for_recall", "")
            if not _is_anti_infective(f"{desc} {reason}"):
                continue
            report_date = _fmt_fda_date(rec.get("report_date", ""))
            if not report_date:
                continue
            recall_no = rec.get("recall_number", "")
            items.append({
                "title": f"{rec.get('recalling_firm', '').strip()} 药品召回",
                "link": (
                    f"https://api.fda.gov/drug/enforcement.json?search=recall_number:%22{recall_no}%22"
                    if recall_no else "https://api.fda.gov/drug/enforcement.json"
                ),
                "description": (desc + ("；" + reason if reason else ""))[:500],
                "pubdate": report_date,
                "contentType": "safety",
                "marketAccessType": "fda",
                "externalId": recall_no,
                "query": name,
            })
        items.sort(key=lambda x: x["pubdate"], reverse=True)
        items = items[:MAX_ITEMS_PER_FEED]
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(items)} 条")
        return True, items
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


def fetch_ema_medicines() -> tuple[bool, list[dict]]:
    """EMA medicines JSON：最近抗感染（ATC J01/J02）上市许可。"""
    cache_id = "ema-medicines"
    name = "EMA 药品上市许可"
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        r = requests.get(EMA_MEDICINES_URL, headers=HEADERS, timeout=60)
        r.raise_for_status()
        data = r.json()
        items = []
        for rec in data.get("data", []):
            atc = rec.get("atc_code_human") or ""
            if not (atc.startswith("J01") or atc.startswith("J02")):
                continue
            if (rec.get("medicine_status") or "").strip().lower() != "authorised":
                continue
            name_med = rec.get("name_of_medicine", "")
            substance = rec.get("active_substance", "")
            decision = _fmt_ema_date(
                rec.get("marketing_authorisation_date")
                or rec.get("european_commission_decision_date")
                or rec.get("first_published_date")
                or ""
            )
            items.append({
                "title": f"{name_med}（{substance}）欧盟上市许可",
                "link": rec.get("medicine_url") or "https://www.ema.europa.eu/en/medicines",
                "description": clean_html(rec.get("therapeutic_indication", "")),
                "pubdate": decision,
                "contentType": "approval",
                "marketAccessType": "ema",
                "approvalStatus": "approved",
                "externalId": rec.get("ema_product_number", ""),
                "drugs": [substance] if substance else [],
                "query": name,
            })
        items.sort(key=lambda x: x["pubdate"] or "", reverse=True)
        items = items[:MAX_ITEMS_PER_FEED]
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(items)} 条")
        return True, items
    except Exception as e:
        record_failure(cache_id, str(e))
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


def _parse_nmpa_list(html: str) -> list[dict]:
    """解析 NMPA 静态列表页，返回 [{title, link, pubdate}]（相对链接，日期 YYYY-MM-DD）。"""
    results = []
    for li in re.findall(r"<li[\s\S]*?</li>", html, flags=re.I):
        a = re.search(r"<a\s+[^>]*href=\"([^\"]+)\"[^>]*>([\s\S]*?)</a>", li, flags=re.I)
        if not a:
            continue
        href, title = a.group(1), clean_html(a.group(2))
        if not title or not href.lower().endswith(".html"):
            continue
        m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", li)
        if not m:
            continue  # 顶部导航/菜单项无发布日期，非公告条目
        results.append({"title": title, "link": href, "pubdate": m.group(1)})
    return results


def fetch_nmpa_column(name: str, url: str, content_type: str) -> tuple[bool, list[dict]]:
    """抓取单个 NMPA 栏目（静态 HTML），过滤抗感染。"""
    cache_id = "nmpa-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        r.encoding = "utf-8"
        # 瑞数 JS 反爬挑战页（与 CDE 同款）：返回 200 但无真实列表，需如实记录失败而非「成功但 0 条」
        # 注意：真实列表页也可能含 "$_ts" 字符串，须用挑战页专有标记 "$_ts.nsd=" 精确判别
        if "$_ts.nsd=" in r.text:
            record_failure(cache_id, "触发瑞数 JS 反爬挑战", url)
            print(f"  [{name}] 触发反爬挑战（已记录冷却）")
            return False, []
        items = []
        for row in _parse_nmpa_list(r.text):
            title = row["title"]
            if not _is_anti_infective(title):
                continue
            # 按标题关键词区分批准 vs 政策（内容类型分类，不据此推断审批状态）
            ct = "approval" if re.search(r"批准|上市许可|批件|注册证|获批", title) else "policy"
            items.append({
                "title": title,
                "link": row["link"],
                "description": "",
                "pubdate": row["pubdate"],
                "contentType": ct,
                "marketAccessType": "nmpa",
                "policyStatus": "published" if ct == "policy" else None,
                "query": name,
            })
        save_cached_feed(cache_id, items)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(items)} 条（过滤后）")
        return True, items[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e), url)
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


def build_regulatory_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    """构建官方药品审批/监管行业资讯条目（映射 approvalStatus/policyStatus/marketAccessType）。"""
    title = item.get("title", "").strip()
    desc = clean_html(item.get("description", ""))
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))
    external_id = item.get("externalId", "")
    eid = make_id("ind", f"{feed['id']}:{external_id}") if external_id else make_id("ind", title + link)

    summary = desc[:200] if desc else title
    impact = f"来自{feed['name']}的官方动态，"
    ct = item.get("contentType")
    if ct == "approval":
        impact += "涉及药品上市许可/审批动态，"
    elif ct == "safety":
        impact += "涉及药品安全警示/召回，"
    else:
        impact += "涉及监管政策/公告，"
    impact += "建议结合官方原文与临床指南综合判断。"

    scores = score_industry(title + " " + desc, group_scores, feed["authority"])

    entry = {
        "id": eid,
        "title": title,
        "eventTime": pub[:10] if pub else None,
        "publishTime": pub,
        "sourceName": feed["name"],
        "sourceUrl": resolve_link(link, feed),
        "category": determine_category(title + " " + desc, group_scores, feed),
        "tags": tags[:6],
        "summary": summary,
        "impact": impact,
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isCluster": False,
        "factType": "fact",
        "contentType": ct or "policy",
        "marketAccessType": item.get("marketAccessType") or feed.get("market_access_type"),
    }
    if item.get("approvalStatus"):
        entry["approvalStatus"] = item["approvalStatus"]
    if item.get("policyStatus"):
        entry["policyStatus"] = item["policyStatus"]
    if external_id:
        entry["externalId"] = external_id
    if item.get("drugs"):
        entry["drugs"] = [d for d in item["drugs"] if d][:6]
    if desc:
        entry["abstract"] = desc
    return apply_schema_fields(entry, feed, item, "news")


# ============================================================
# B5：WHO GLASS 全球耐药监测数据
# ============================================================
_GLASS_MONTHS = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12",
}


def _strip_zw(text: str) -> str:
    """去除零宽字符（U+200B/U+200E/U+200F/U+2060），WHO 页面标题中夹带这类字符。"""
    return re.sub(r"[\u200b\u200e\u200f\u2060]", "", text or "")


def _fmt_glass_date(d: str) -> str:
    """WHO 页面日期 "13 October 2025" → YYYY-MM-DD（非此格式则原样返回，不伪造）。"""
    d = (d or "").strip()
    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", d)
    if m:
        day, mon, year = m.group(1), m.group(2).capitalize(), m.group(3)
        if mon in _GLASS_MONTHS:
            return f"{year}-{_GLASS_MONTHS[mon]}-{int(day):02d}"
    return d


def _glass_year_info(title: str) -> tuple[str | None, str | None]:
    """从 GLASS 报告标题提取 (监测年份[用于 eventTime], 年份标签)。

    GLASS 报告标题中的年份即监测/报告年份（如 "report 2025" / "2022" / "2017-2018"），
    与报告发布日期严格区分，避免混淆二者。
    """
    if not title:
        return None, None
    years: list[str] = []
    for m in re.finditer(r"\b(20\d{2})\b", title):
        y = m.group(1)
        if y not in years:
            years.append(y)
    if not years:
        return None, None
    if len(years) == 1:
        return years[0], years[0]
    # 连续年份（如 2017-2018）→ 区间；否则按出现顺序用连字符连接
    if len(years) == 2 and int(years[1]) == int(years[0]) + 1:
        return years[0], f"{years[0]}-{years[1]}"
    return years[0], "-".join(years)


def _parse_glass_reports(html: str) -> list[dict]:
    """解析 WHO GLASS 页面「GLASS Reports」区块，返回 [{title, link, pubdate, description, download}]。

    标题取图片 alt（完整标题，含监测年份），回退到 h3（可能被页面截断）。
    """
    results = []
    # 仅按顶层条目 div（class="sf-publications-item list-item..."）切分；
    # 用 \b 避免误匹配嵌套的 sf-publications-item__container / __body 等子元素。
    for chunk in re.split(r'<div class="sf-publications-item\b', html)[1:]:
        alt_m = re.search(r'<img\s+[^>]*alt="([^"]*)"', chunk, re.I)
        title = _strip_zw(clean_html(alt_m.group(1))) if alt_m else ""
        if not title:
            h3_m = re.search(r'<h3 class="sf-publications-item__title">(.*?)</h3>', chunk, re.I | re.S)
            title = _strip_zw(clean_html(h3_m.group(1))) if h3_m else ""
        if not title:
            continue
        link_m = re.search(r'<a href="([^"]+)"[^>]*>\s*<h3 class="sf-publications-item__title"', chunk, re.I | re.S)
        date_m = re.search(r'<div class="sf-publications-item__date">\s*<span>(.*?)</span>', chunk, re.I | re.S)
        desc_m = re.search(r'<div class="sf-publications-item__description">\s*<p>(.*?)</p>', chunk, re.I | re.S)
        dl_m = re.search(r'class="download-url[^"]*"\s*href="([^"]+)"', chunk, re.I)
        results.append({
            "title": title,
            "link": link_m.group(1) if link_m else "",
            "pubdate": _fmt_glass_date(clean_html(date_m.group(1))) if date_m else "",
            "description": clean_html(desc_m.group(1)) if desc_m else "",
            "download": dl_m.group(1) if dl_m else "",
        })
    return results


def fetch_glass_reports() -> tuple[bool, list[dict]]:
    """抓取 WHO GLASS 官方 AMR/AMU 监测报告列表（静态 HTML，带缓存 + 失败冷却）。"""
    cache_id = "glass-reports"
    name = "WHO GLASS 监测报告"
    if is_failure_cooled_down(cache_id):
        print(f"  [{name}] 跳过（失败冷却期内）")
        return False, []
    cached = get_cached_feed(cache_id)
    if cached is not None:
        print(f"  [{name}] 使用本地缓存 {len(cached)} 条")
        return True, cached[:MAX_ITEMS_PER_FEED]
    try:
        r = requests.get(GLASS_PAGE_URL, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        r.encoding = "utf-8"
        items = _parse_glass_reports(r.text)
        # 领域过滤：仅保留抗感染（AMR/AMU/耐药菌/真菌）监测报告；
        # 「GLASS Manual」为实施方法手册，非监测报告/数据，予以排除。
        filtered = []
        for it in items:
            text = f"{it['title']} {it['description']}"
            if not _is_anti_infective(text):
                continue
            if re.search(r"\bmanual\b", it["title"], re.I):
                continue
            it["contentType"] = "surveillance"
            it["query"] = name
            filtered.append(it)
        save_cached_feed(cache_id, filtered)
        clear_failure(cache_id)
        print(f"  [{name}] 抓取 {len(filtered)} 条（过滤后）")
        return True, filtered[:MAX_ITEMS_PER_FEED]
    except Exception as e:
        record_failure(cache_id, str(e), GLASS_PAGE_URL)
        print(f"  [{name}] 抓取失败（已记录冷却）: {e}")
        return False, []


# WHO GLASS 2025 摘要报告（B09585）Table 1 结构化耐药数据（全球 2023，百分比 + 95% CrI）。
# 来源：Global antibiotic resistance surveillance report 2025: summary，Table 1（p.16-18）。
# 原文仅提供全球百分比与 95% 可信区间（CrI），未列原始样本量/分母（样本量见完整报告），故不补充分母。
GLASS_SUMMARY_TABLE1 = (
    "监测年份 2023（Table 1，p.16-18），全球耐药率（%）与趋势（2018-2023）：\n"
    "1. 碳青霉烯耐药鲍曼不动杆菌·亚胺培南·血流感染 54.3%（95% CrI 49.3-59.2），最高东地中海区 66.5%，趋势 +5.3%/年；\n"
    "2. 三代头孢菌素耐药大肠埃希菌·三代头孢·血流感染 44.8%（39.3-50.4），最高非洲区 70.7%；头孢噻肟·尿路感染 39.8%（33.9-46.0）；\n"
    "3. 碳青霉烯耐药大肠埃希菌·亚胺培南·血流感染 2.4%（1.8-3.3）、尿路感染 2.6%（2.0-3.5），趋势 +12.5%/年；\n"
    "4. 三代头孢菌素耐药肺炎克雷伯菌·头孢噻肟·血流感染 55.2%（48.5-61.7），最高非洲区 77.8%；尿路感染 45.5%（38.6-52.5）；\n"
    "5. 碳青霉烯耐药肺炎克雷伯菌·亚胺培南·血流感染 16.7%（13.9-19.9），最高东南亚区 41.2%，趋势 +15.3%/年；尿路感染 10.9%（8.7-13.6）；\n"
    "6. 耐甲氧西林金黄色葡萄球菌（MRSA）·甲氧西林·血流感染 27.1%（23.5-31.0），最高东地中海区 50.3%；\n"
    "7. 氟喹诺酮耐药非伤寒沙门菌·环丙沙星·血流感染 18.0%（13.9-22.9）；\n"
    "8. 氟喹诺酮耐药志贺菌·环丙沙星·胃肠道感染 29.7%（22.9-37.5）；\n"
    "9. 淋病奈瑟菌·环丙沙星 75.0%（70.9-78.8）、头孢曲松 0.3%（0.1-0.6）。"
)
GLASS_SUMMARY_PATHOGENS = ["鲍曼不动杆菌", "大肠埃希菌", "肺炎克雷伯菌", "金黄色葡萄球菌(MRSA)", "非伤寒沙门菌", "志贺菌属", "淋病奈瑟菌"]
GLASS_SUMMARY_DRUGS = ["亚胺培南", "第三代头孢菌素", "头孢噻肟", "环丙沙星", "甲氧西林", "头孢曲松"]
GLASS_SUMMARY_TAGS = ["CRE", "CRKP", "CRAB", "ESBL", "MRSA", "耐药监测"]


def build_surveillance_entry(item: dict, feed: dict, group_scores: dict, tags: list[str]) -> dict:
    """构建 WHO GLASS 监测行业资讯条目。

    - contentType=surveillance
    - eventTime=监测年份（标题中的报告/监测年份）
    - publishTime=报告发布日期（页面发布日期）
    二者严格分离，避免混淆。
    """
    title = item.get("title", "").strip()
    desc = clean_html(item.get("description", ""))
    link = item.get("link", "")
    pub = parse_date_or_none(item.get("pubdate", ""))
    event_year, year_label = _glass_year_info(title)
    event_time = f"{event_year}-01-01" if event_year else None

    # 以官方出版物 ID（链接末段）作为稳定 id 基础，确保跨次采集去重
    pub_id = ""
    m = re.search(r"/item/([^/?#]+)", link)
    if m:
        pub_id = m.group(1)
    eid = make_id("ind", f"glass:{pub_id}") if pub_id else make_id("ind", title + link)

    summary = desc[:200] if desc else title
    parts = []
    if year_label:
        parts.append(f"监测年份 {year_label}")
    if pub:
        parts.append(f"发布日期 {pub[:10]}")
    if parts:
        summary = "；".join(parts) + "。" + summary

    impact = f"来自{feed['name']}的耐药监测动态，"
    if "amr" in group_scores:
        impact += "关注革兰阴性菌及 CRE 等耐药菌的耐药变迁，"
    if "fungal" in group_scores:
        impact += "涉及侵袭性真菌感染监测，"
    impact += "建议结合官方报告原文与临床药敏数据综合判断。"

    scores = score_industry(title + " " + desc, group_scores, feed["authority"])

    # 结构化数据：2025 摘要报告（B09585）已按原文提取 Table 1（全球 2023 耐药率）。
    # 其余报告仅保留元数据与官方 PDF 链接，不自行推算耐药率。
    pdf_url = item.get("download", "")
    structured = GLASS_SUMMARY_TABLE1 if pub_id == "B09585" else ""

    # 标签 / 病原体 / 药物：仅在原文明确列出时填充（B09585 Table 1）
    merged_tags = list(tags)
    extra_pathogens = []
    extra_drugs = []
    if structured:
        merged_tags = list(dict.fromkeys(merged_tags + GLASS_SUMMARY_TAGS))
        extra_pathogens = GLASS_SUMMARY_PATHOGENS
        extra_drugs = GLASS_SUMMARY_DRUGS

    # abstract：优先结构化数据；附官方 PDF 链接与原文页面，保留单位/口径/页码位置
    abstract_parts = []
    if structured:
        abstract_parts.append(structured)
    if pdf_url:
        abstract_parts.append(f"官方 PDF: {pdf_url}")
    abstract = "\n".join(abstract_parts) if abstract_parts else (desc or None)

    entry = {
        "id": eid,
        "title": title,
        "eventTime": event_time,
        "publishTime": pub,
        "sourceName": feed["name"],
        "sourceUrl": link,
        "category": determine_category(title + " " + desc, group_scores, feed),
        "tags": merged_tags[:8],
        "summary": summary,
        "impact": impact,
        "abstract": abstract,
        "scores": scores,
        "totalScore": scores["totalScore"],
        "isCluster": False,
        "factType": "fact",
        "contentType": item.get("contentType") or "surveillance",
    }
    if pub_id:
        entry["externalId"] = pub_id
    if extra_pathogens:
        entry["pathogens"] = extra_pathogens
    if extra_drugs:
        entry["drugs"] = extra_drugs
    return apply_schema_fields(entry, feed, item, "news")


# ============================================================
# 主流程
# ============================================================
def main(argv: list[str] | None = None) -> None:
    # 受控输出目录：--output-dir DIR（B1.1.2 验证用，不覆盖 src/data/auto/ 生产数据）
    global OUTPUT_DIR, INDUSTRY_PATH, RESEARCH_PATH
    if argv is None:
        argv = sys.argv[1:]
    if "--output-dir" in argv:
        i = argv.index("--output-dir")
        out = argv[i + 1] if i + 1 < len(argv) else ""
        if out:
            OUTPUT_DIR = Path(out)
            INDUSTRY_PATH = OUTPUT_DIR / "industry.json"
            RESEARCH_PATH = OUTPUT_DIR / "research.json"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    industry_entries: list[dict] = []
    research_entries: list[dict] = []

    print("=" * 60)
    print("MedAI Hub 资讯采集启动")
    print("=" * 60)

    # ---- 1. 抓取 RSS 源 ----
    print("\n[1/3] 抓取 RSS 源...")
    successful_task_keys: set[str] = set()  # 本次实际采集成功的来源/查询任务
    for feed in RSS_FEEDS:
        ok, items = fetch_feed(feed)
        if ok:
            successful_task_keys.add(feed["id"])
        for item in items:
            title = item.get("title", "")
            desc = clean_html(item.get("description", ""))
            text = f"{title} {desc}"

            total, group_scores, tags = score_relevance(text)
            if total < RELEVANCE_THRESHOLD:
                continue  # 不相关，跳过

            if feed["kind"] == "research":
                entry = build_research_entry(item, feed, group_scores, tags)
                if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                    research_entries.append(entry)
            else:
                entry = build_industry_entry(item, feed, group_scores, tags)
                if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                    industry_entries.append(entry)

    # ---- 1b. 抓取 PubMed（E-utilities API）----
    print("\n[1b/3] 抓取 PubMed 文献...")
    pubmed_all_ok = True  # 全部查询成功时，旧 PubMed 记录（无 sourceQuery）才允许按快照丢弃
    for query in PUBMED_QUERIES:
        feed_meta = {
            "id": "pubmed",  # 统一 sourceId，用于合并时识别 PubMed 来源（失败保护）
            "name": query["name"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/",
            "authority": query["authority"],
            "default_category": "真菌与耐药",
            "content_type": "research",
            "source_type": "database",
            "language": "en",
            "geographic_scope": "global",
        }
        ok, items = fetch_pubmed(query)
        if ok:
            successful_task_keys.add(f"pubmed::{query['name']}")
        else:
            pubmed_all_ok = False
        for item in items:
            title = item.get("title", "")
            desc = clean_html(item.get("description", ""))
            text = f"{title} {desc}"

            total, group_scores, tags = score_relevance(text)
            # PubMed 文献本身就是高价值来源，降低相关性门槛
            if total < 1 and not any(kw in text.lower() for kw in ["fungal", "aspergill", "candida", "acinetobacter", "carbapenem", "imaging"]):
                continue

            entry = build_research_entry(item, feed_meta, group_scores, tags)
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                research_entries.append(entry)

    # 全部 PubMed 查询成功时，旧 PubMed 记录（无 sourceQuery）按快照丢弃，避免残留旧数据
    if pubmed_all_ok:
        successful_task_keys.add(_LEGACY_PUBMED_KEY)

    # ---- 1c. 抓取 ClinicalTrials.gov 临床试验注册 ----
    print("\n[1c/3] 抓取 ClinicalTrials.gov 临床试验注册信息...")
    clinicaltrials_all_ok = True  # 全部查询成功时，旧 ClinicalTrials 记录才允许按快照丢弃
    for query in CLINICALTRIALS_QUERIES:
        feed_meta = {
            "id": "clinicaltrials",  # 统一 sourceId，用于合并时识别 ClinicalTrials 来源（失败保护）
            "name": query["name"],
            "url": "https://clinicaltrials.gov/",
            "authority": query["authority"],
            "default_category": "真菌与耐药",
            "content_type": "research",
            "source_type": "database",
            "language": "en",
            "geographic_scope": "global",
        }
        ok, items = fetch_clinicaltrials(query)
        if ok:
            successful_task_keys.add(f"clinicaltrials::{query['name']}")
        else:
            clinicaltrials_all_ok = False
        for item in items:
            title = item.get("title", "")
            desc = clean_html(item.get("description", ""))
            text = f"{title} {desc}"

            total, group_scores, tags = score_relevance(text)
            # 临床试验注册信息按疾病（query.cond）匹配，本身即高价值抗感染来源
            if total < 1:
                continue

            entry = build_clinicaltrial_entry(item, feed_meta, group_scores, tags)
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                research_entries.append(entry)

    # 全部 ClinicalTrials 查询成功时，旧 ClinicalTrials 记录（无 sourceQuery）按快照丢弃
    if clinicaltrials_all_ok:
        successful_task_keys.add(_LEGACY_CLINICALTRIALS_KEY)

    # ---- 1d. 抓取 WHO ICTRP 全注册中心（ChiCTR / EU CTR / CTIS） ----
    print("\n[1d/3] 抓取 WHO ICTRP 全注册中心临床试验注册信息...")
    ictrp_all_ok = True  # 全部查询成功时，旧 ICTRP 记录（无 sourceQuery）才允许按快照丢弃
    for query in ICTRP_QUERIES:
        feed_meta = {
            "id": "ictrp",  # 占位 sourceId；实际按注册号模式在条目层回填 chictr/euctr/ctis
            "name": query["name"],
            "url": "https://trialsearch.who.int/",
            "authority": query["authority"],
            "default_category": "真菌与耐药",
            "content_type": "research",
            "source_type": "database",
            "language": "en",
            "geographic_scope": "global",
        }
        ok, items = fetch_ictrp(query)
        if ok:
            # 同一查询可能命中多个注册中心，按实际出现的 sourceId 分别标记成功（失败保护）
            for sid in {it.get("sourceId") for it in items if it.get("sourceId")}:
                successful_task_keys.add(f"{sid}::{query['name']}")
        else:
            ictrp_all_ok = False
        for item in items:
            title = item.get("title", "")
            text = title

            total, group_scores, tags = score_relevance(text)
            # WHO ICTRP 检索按疾病关键词匹配，本身即高价值抗感染来源
            if total < 1:
                continue

            entry = build_ictrp_entry(item, feed_meta, group_scores, tags)
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                research_entries.append(entry)

    # 全部 WHO ICTRP 查询成功时，旧 ChiCTR 记录（无 sourceQuery）按快照丢弃
    if ictrp_all_ok:
        successful_task_keys.add(_LEGACY_CHICTR_KEY)

    # ---- 1e. 抓取 FDA 官方药品审批与监管数据（批准 / 安全警示 / 召回） ----
    print("\n[1e/3] 抓取 FDA 官方药品审批与监管数据...")
    fda_feed_meta = {
        "id": "fda",
        "name": "FDA",
        "url": "https://www.fda.gov/",
        "authority": 9,
        "default_category": "真菌与耐药",
        "source_type": "regulatory",
        "language": "en",
        "geographic_scope": "us",
    }
    ok, fda_items = fetch_fda_approvals()
    if ok:
        successful_task_keys.add("fda::FDA 药品批准")
    for item in fda_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        total, group_scores, tags = score_relevance(text)
        if total < 1:
            continue
        entry = build_regulatory_entry(item, fda_feed_meta, group_scores, tags)
        if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
            industry_entries.append(entry)

    ok, fda_enforcement_items = fetch_fda_enforcement()
    if ok:
        successful_task_keys.add("fda::FDA 药品召回")
    for item in fda_enforcement_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        total, group_scores, tags = score_relevance(text)
        if total < 1:
            continue
        entry = build_regulatory_entry(item, fda_feed_meta, group_scores, tags)
        if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
            industry_entries.append(entry)

    # ---- 1f. 抓取 EMA 官方药品审批与监管数据（上市许可 / 新闻公告） ----
    print("\n[1f/3] 抓取 EMA 官方药品审批与监管数据...")
    ema_feed_meta = {
        "id": "ema",
        "name": "EMA",
        "url": "https://www.ema.europa.eu/",
        "authority": 9,
        "default_category": "真菌与耐药",
        "source_type": "regulatory",
        "language": "en",
        "geographic_scope": "eu",
    }
    ok, ema_items = fetch_ema_medicines()
    if ok:
        successful_task_keys.add("ema::EMA 药品上市许可")
    for item in ema_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        total, group_scores, tags = score_relevance(text)
        if total < 1:
            continue
        entry = build_regulatory_entry(item, ema_feed_meta, group_scores, tags)
        if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
            industry_entries.append(entry)

    ok, ema_news_items = _fetch_regulatory_rss("ema-news", "EMA 新闻与公告", EMA_NEWS_URL, "ema", "policy")
    if ok:
        successful_task_keys.add("ema::EMA 新闻与公告")
    for item in ema_news_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        total, group_scores, tags = score_relevance(text)
        if total < 1:
            continue
        entry = build_regulatory_entry(item, ema_feed_meta, group_scores, tags)
        if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
            industry_entries.append(entry)

    # ---- 1g. 抓取 NMPA 官方药品审批与监管数据（公告通告 / 监管动态 / 批件发布） ----
    print("\n[1g/3] 抓取 NMPA 官方药品审批与监管数据...")
    for name, url, content_type in NMPA_COLUMNS:
        nmpa_feed_meta = {
            "id": "nmpa",
            "name": name,
            "url": url,
            "base_url": url,
            "authority": 9,
            "default_category": "真菌与耐药",
            "source_type": "regulatory",
            "language": "zh",
            "geographic_scope": "china",
        }
        ok, items = fetch_nmpa_column(name, url, content_type)
        if ok:
            successful_task_keys.add(f"nmpa::{name}")
        for item in items:
            text = item.get("title", "")
            total, group_scores, tags = score_relevance(text)
            if total < 1:
                continue
            entry = build_regulatory_entry(item, nmpa_feed_meta, group_scores, tags)
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                industry_entries.append(entry)

    # ---- 1h. 抓取 WHO GLASS 全球耐药监测报告（AMR / AMU） ----
    print("\n[1h/3] 抓取 WHO GLASS 全球耐药监测报告...")
    glass_feed_meta = {
        "id": "glass",
        "name": "WHO GLASS",
        "url": GLASS_PAGE_URL,
        "authority": 9,
        "default_category": "耐药监测",
        "source_type": "database",
        "language": "en",
        "geographic_scope": "global",
    }
    ok, glass_items = fetch_glass_reports()
    if ok:
        successful_task_keys.add("glass::WHO GLASS 监测报告")
    for item in glass_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        total, group_scores, tags = score_relevance(text)
        if total < 1:
            continue
        entry = build_surveillance_entry(item, glass_feed_meta, group_scores, tags)
        if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
            industry_entries.append(entry)

    # ---- 2. 录入无 RSS 的权威源（静态知识库条目） ----
    print("\n[2/3] 录入静态权威源条目...")
    for src in CURATED_SOURCES:
        successful_task_keys.add(src["id"])
        text = f"{src['name']} {src['description']}"
        total, group_scores, tags = score_relevance(text)
        tags = list(dict.fromkeys(tags + [src["category"]]))

        if src["kind"] == "research":
            # 机构资源入口：不是研究论文，不设置 studyType/studyDesign/evidenceLevel 等研究专属字段
            entry = {
                "id": make_id("res", src["id"]),
                "title": f"{src['name']}：{src['description']}",
                "sourceName": src["name"],
                "sourceUrl": src["url"],
                "coreFindings": src["description"],
                "limitations": "本条目为权威机构资源入口，具体内容请访问原网站。",
                "inspiration": f"{src['name']}是{src['category']}领域权威来源，建议定期跟踪其指南更新与监测数据。",
                "scores": score_research(text, group_scores, src["authority"], "other"),
                "totalScore": 0,
                "tags": tags[:6],
            }
            entry["totalScore"] = entry["scores"]["totalScore"]
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                research_entries.append(apply_schema_fields(entry, src, {}, "research"))
        else:
            entry = {
                "id": make_id("ind", src["id"]),
                "title": f"{src['name']}：{src['description']}",
                "sourceName": src["name"],
                "sourceUrl": src["url"],
                "category": src["category"],
                "tags": tags[:6],
                "summary": src["description"],
                "abstract": src["description"],
                "impact": f"{src['name']}是{src['category']}领域权威数据来源，建议持续关注其最新发布。",
                "scores": score_industry(text, group_scores, src["authority"]),
                "totalScore": 0,
                "isCluster": False,
                "factType": "fact",
            }
            entry["totalScore"] = entry["scores"]["totalScore"]
            if entry["totalScore"] >= TOTAL_SCORE_THRESHOLD:
                industry_entries.append(apply_schema_fields(entry, src, {}, "news"))

    # ---- 3. 去重、排序、写出 ----
    print("\n[3/3] 去重排序并写出...")

    def dedup(entries: list[dict]) -> list[dict]:
        seen = set()
        result = []
        for e in entries:
            if e["id"] in seen:
                continue
            seen.add(e["id"])
            result.append(e)
        return result

    industry_entries = dedup(industry_entries)
    research_entries = dedup(research_entries)

    # 按时间倒序（publishTime 可能为 None/缺失，安全排序）
    industry_entries.sort(key=lambda x: x.get("publishTime") or "", reverse=True)
    research_entries.sort(key=lambda x: x.get("publishTime") or "", reverse=True)

    # 本次实际采集成功的来源/查询任务：这些按快照更新；失败来源保留旧记录，防数据丢失
    # （successful_task_keys 基于采集执行结果，而非是否产出记录）

    # 轻量合并：按 id 保留旧数据中的人工字段（方案 B）
    # 旧文件损坏时抛 CorruptDataError 中止，绝不覆盖原文件
    try:
        industry_entries = merge_preserving_manual(INDUSTRY_PATH, industry_entries, successful_task_keys)
        research_entries = merge_preserving_manual(RESEARCH_PATH, research_entries, successful_task_keys)
    except CorruptDataError as e:
        print(f"\n[采集中止] {e}", file=sys.stderr)
        print("[采集中止] 已保留原始数据文件，本次不写入任何内容。", file=sys.stderr)
        raise SystemExit(1)

    # B2.3：试验注册记录与论文关联 / 跨平台去重（纯后处理，不合并/覆盖记录）
    research_entries = link_and_dedup_research(research_entries)

    INDUSTRY_PATH.write_text(json.dumps(industry_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    RESEARCH_PATH.write_text(json.dumps(research_entries, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n===== 采集完成 =====")
    print(f"行业资讯: {len(industry_entries)} 条 → {INDUSTRY_PATH.name}")
    print(f"科研资讯: {len(research_entries)} 条 → {RESEARCH_PATH.name}")

    # 分类统计
    from collections import Counter
    ind_cats = Counter(e.get("category", "未分类") for e in industry_entries)
    res_types = Counter(e.get("studyType", "未设置") for e in research_entries)
    print(f"\n行业分类分布: {dict(ind_cats)}")
    print(f"科研类型分布: {dict(res_types)}")


if __name__ == "__main__":
    main()
