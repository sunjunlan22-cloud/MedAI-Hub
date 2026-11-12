#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
raw_materials/ 原始指南/共识解析脚本（本地运行，不依赖云端）
读取 raw_materials/ 下的 PDF / Word 文件，自动提取标题与摘要，
生成符合 guides schema 的 Markdown 到 src/content/guides/。

约束：
- 内容严格 1:1 对齐原始文档，仅做文本抽取，不做 AI 改写/增补。
- 无法提取文本（扫描件）或无法确定年份时，标记 draft: true，前端不发布。
- 仅写入 src/content/guides/（受保护路径 src/content.config.ts、
  src/data/manual 等绝不修改）。
"""
import hashlib
import re
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "raw_materials"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "src" / "content" / "guides"
REVIEW_DATE = "2026-11-09"

try:
    import pdfplumber
except Exception:  # noqa: BLE001
    pdfplumber = None
try:
    import docx as python_docx
except Exception:  # noqa: BLE001
    python_docx = None

# ---- 多维分类关键词规则（严格关键词匹配，杜绝语义猜测）----
PATHOGEN_RULES = [
    ("曲霉", "曲霉"),
    ("毛霉", "毛霉"),
    ("念珠菌", "念珠菌"),
    ("隐球菌", "隐球菌"),
    ("鲍曼不动杆菌", "CRAB"),
    ("碳青霉烯耐药", "CRE/CRKP"),
    ("CRKP", "CRE/CRKP"),
    ("铜绿假单胞菌", "CRPA"),
    ("嗜麦芽窄食单胞菌", "嗜麦芽窄食单胞菌"),
    ("MRSA", "MRSA/VRE"),
    ("VRE", "MRSA/VRE"),
]
SITE_RULES = [
    ("肺", "肺部感染"),
    ("血流", "血流感染"),
    ("中枢神经", "中枢神经系统感染"),
    ("脑膜", "中枢神经系统感染"),
    ("腹腔", "腹腔感染"),
    ("皮肤软组织", "皮肤软组织感染"),
]
IMAGING_RULES = [
    ("治疗药物监测", "TDM"),
    ("血药浓度", "TDM"),
    ("TDM", "TDM"),
    ("CT", "肺部CT影像"),
    ("影像", "真菌/耐药菌影像鉴别"),
]
COMPARISON_RULES = [
    ("伏立康唑", "与伏立康唑/艾沙康唑对比"),
    ("艾沙康唑", "与伏立康唑/艾沙康唑对比"),
    ("多黏菌素", "与多黏菌素对比"),
    ("黏菌素", "与多黏菌素对比"),
    ("依拉环素", "与依拉环素对比"),
    ("舒巴坦", "与舒巴坦/度洛巴坦对比"),
    ("替加环素", "与替加环素对比"),
]
ORG_RULES = [
    "中华医学会", "中国医师协会", "中国医院协会", "中华预防医学会",
    "中国医药教育协会", "中国临床肿瘤学会", "中国抗癌协会",
    "IDSA", "ECMM", "ESCMID", "ISHAM", "MSG", "FUNGINOS", "EORTC",
    "美国感染病学会", "欧洲临床微生物与感染病学会",
]


def extract_text(path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        if pdfplumber is None:
            raise RuntimeError("缺少 pdfplumber，请先安装：pip install pdfplumber")
        parts = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    if ext in (".docx", ".doc"):
        if python_docx is None:
            raise RuntimeError("缺少 python-docx，请先安装：pip install python-docx")
        doc = python_docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def _match(text, rules):
    hit = []
    low = text.lower()
    for kw, label in rules:
        if kw.lower() in low and label not in hit:
            hit.append(label)
    return hit


MONTHS = (
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
    r"January|February|March|April|June|July|August|September|October|November|December)"
)


def detect_year(stem, text):
    head = text[:5000]
    # 1. 文件名中的年份（最强信号）
    m = re.search(r"(19\d{2}|20\d{2})", stem)
    if m:
        return int(m.group(1))
    # 2. 版权标记 © 20xx
    m = re.search(r"©\s*(20\d{2})", head)
    if m:
        return int(m.group(1))
    # 3. 英文月份 + 年份（如 June 2024 / October2020）
    m = re.search(MONTHS + r"\.?,?\s*(20\d{2})", head, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # 4. 中文“20xx年 / 20xx版”
    m = re.search(r"(20\d{2})\s*[年版]", head)
    if m:
        return int(m.group(1))
    # 5. 期刊引用 “, 20xx;” / “, 20xx:”
    m = re.search(r",\s*(20\d{2})\s*[;:]", head)
    if m:
        return int(m.group(1))
    # 6. 括号年份（如（2022））
    m = re.search(r"[（(](19\d{2}|20\d{2})[）)]", head)
    if m:
        return int(m.group(1))
    # 7. 杂志页眉分栏格式：数字 年份 数字 数字（如 “754 2020 10 59”）
    m = re.search(r"\b\d{1,4}\s+(20\d{2})\s+\d{1,2}\s+\d{1,3}\s+\d{1,2}\b", head)
    if m:
        return int(m.group(1))
    return None


def detect_org(text):
    for org in ORG_RULES:
        if org in text[:6000]:
            return org
    return "详见原文"


def detect_doctype(stem, text):
    # 中文：仅依据文件名判断，避免正文引用“指南/共识”造成误判
    if "共识" in stem:
        return ["专家共识"]
    if "指南" in stem:
        return ["指南"]
    if "修订" in stem:
        return ["指南"]
    # 英文：仅查正文标题区域（前 300 字），如 “Guidelines From ... / Consensus ...”
    title_zone = text[:300]
    if re.search(r"consensus", title_zone, re.IGNORECASE):
        return ["专家共识"]
    if re.search(r"\bguidelines?\b", title_zone, re.IGNORECASE):
        return ["指南"]
    return ["推荐依据"]


def clean_title(stem):
    t = re.sub(r"^\d{1,3}\s*[-、._ ]\s*", "", stem)
    t = re.sub(r"^\d{1,3}\s+", "", t)
    return t.strip() or stem


def slugify(stem):
    return "raw-" + hashlib.md5(stem.encode("utf-8")).hexdigest()[:10]


def build_summary(text, limit=260):
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    summary = ""
    for ln in lines:
        if len(ln) < 6:
            continue
        summary += ln + " "
        if len(summary) >= limit:
            break
    return re.sub(r"\s+", " ", summary).strip()[:limit]


def _yaml_quote(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def build_markdown(title, meta, summary):
    fm = {
        "title": title,
        "organization": meta["organization"],
        "year": meta["year"],
        "version": meta["version"],
        "reviewDate": REVIEW_DATE,
        "docType": meta["docType"],
        "pathogens": meta["pathogens"],
        "infectionSites": meta["infectionSites"],
        "imagingDiagnosis": meta["imagingDiagnosis"],
        "comparisons": meta["comparisons"],
        "description": summary,
        "draft": meta["draft"],
    }
    md = "---\n"
    for k, v in fm.items():
        if isinstance(v, bool):
            md += f"{k}: {str(v).lower()}\n"
        elif isinstance(v, list):
            if v:
                md += f"{k}:\n"
                for item in v:
                    md += f'  - "{_yaml_quote(item)}"\n'
            else:
                md += f"{k}: []\n"
        elif isinstance(v, int):
            md += f"{k}: {v}\n"
        else:
            md += f'{k}: "{_yaml_quote(v)}"\n'
    md += "---\n\n"
    if summary:
        md += f"## 摘要\n\n{summary}\n\n"
    else:
        md += "## 摘要\n\n（原始文件无法提取文本摘要，详见原文档。）\n\n"
    md += "---\n\n> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。\n"
    return md


def main():
    if pdfplumber is None and python_docx is None:
        print("错误：缺少 pdfplumber 与 python-docx，请先安装：")
        print("  pip install pdfplumber python-docx")
        return 1

    files = sorted(
        [p for p in RAW_DIR.iterdir()
         if p.suffix.lower() in (".pdf", ".docx", ".doc")]
    )
    if not files:
        print(f"未在 {RAW_DIR} 找到任何 PDF/Word 文件")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for idx, path in enumerate(files, 1):
        stem = path.stem
        title = clean_title(stem)
        slug = slugify(stem)
        out = OUTPUT_DIR / f"{slug}.md"
        print(f"\n[{idx}/{len(files)}] {stem}")

        try:
            text = extract_text(path)
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ 文本提取失败：{e}")
            text = ""

        year = detect_year(stem, text)
        draft = len(text) < 200 or year is None

        meta = {
            "organization": detect_org(text),
            "year": year if year else int(REVIEW_DATE[:4]),
            "version": f"{year}版" if year else "原文（版次待核对）",
            "docType": detect_doctype(stem, text),
            "pathogens": _match(text, PATHOGEN_RULES),
            "infectionSites": _match(text, SITE_RULES),
            "imagingDiagnosis": _match(text, IMAGING_RULES),
            "comparisons": _match(text, COMPARISON_RULES),
            "draft": draft,
        }
        summary = build_summary(text) if text else ""

        out.write_text(build_markdown(title, meta, summary), encoding="utf-8")
        if year is None:
            print("  ⚠ 未能确定年份，已标记 draft")
        if len(text) < 200:
            print(f"  ⚠ 文本过短（{len(text)} 字符），疑似扫描件，已标记 draft")
        status = "draft(草稿不发布)" if draft else "ok"
        print(f"  ✓ {out.name}  year={meta['year']}  文本={len(text)}字符  [{status}]")
        results.append({"name": stem, "slug": slug, "draft": draft})

    print(f"\n===== 汇总：{len(results)} 个文件 =====")
    for r in results:
        print(f"{'✅' if not r['draft'] else '🟡'} {r['slug']}  <-  {r['name']}")
    if any(r["draft"] for r in results):
        print("\n存在 🟡 草稿条目，请人工核对原始文件补全年份/文本后，再将 draft 改为 false。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
