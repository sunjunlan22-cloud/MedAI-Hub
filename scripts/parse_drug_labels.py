#!/usr/bin/env python3
"""
药品说明书 PDF 解析脚本
提取关键字段并生成符合 drug-labels schema 的 Markdown 文件
"""
import pdfplumber
import re
import os
import json
from pathlib import Path

PDF_DIR = Path(__file__).parent.parent / "说明书"
OUTPUT_DIR = Path(__file__).parent.parent / "src" / "content" / "drug-labels"

# 药品元信息映射（从文件名识别）
DRUG_META = {
    "威凡片说明书": {
        "drugName": "伏立康唑片",
        "brandNames": ["威凡"],
        "manufacturer": "辉瑞制药",
        "dosageForm": "片剂",
        "atcCode": "J02AC03",
        "antibioticClass": "三唑类抗真菌药",
        "sourceUrl": "https://www.pfizer.com",
        "slug": "voriconazole-tablet",
    },
    "注射用伏立康唑": {
        "drugName": "注射用伏立康唑",
        "brandNames": ["威凡"],
        "manufacturer": "辉瑞制药",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J02AC03",
        "antibioticClass": "三唑类抗真菌药",
        "sourceUrl": "https://www.pfizer.com",
        "slug": "voriconazole-injection",
    },
    "注射用两性霉素B胆固醇": {
        "drugName": "注射用两性霉素B胆固醇硫酸酯复合物",
        "brandNames": ["ABelcet"],
        "manufacturer": "Enzon Pharmaceuticals",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J02AA01",
        "antibioticClass": "多烯类抗真菌药",
        "sourceUrl": "https://www.abelcet.com",
        "slug": "amphotericin-b-cholesterol",
    },
    "AmBisome": {
        "drugName": "注射用两性霉素B脂质体",
        "brandNames": ["AmBisome"],
        "manufacturer": "Gilead Sciences",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J02AA01",
        "antibioticClass": "多烯类抗真菌药",
        "sourceUrl": "https://www.ambisome.com",
        "slug": "amphotericin-b-liposome",
    },
    "硫酸艾沙康唑胶囊": {
        "drugName": "硫酸艾沙康唑胶囊",
        "brandNames": ["康新博", "Cresemba"],
        "manufacturer": "Basilea Pharmaceutica / 辉瑞",
        "dosageForm": "胶囊剂",
        "atcCode": "J02AC04",
        "antibioticClass": "三唑类抗真菌药",
        "sourceUrl": "https://www.basilea.com",
        "slug": "isavuconazole-capsule",
    },
    "注射用亚胺西瑞": {
        "drugName": "注射用亚胺西瑞",
        "brandNames": ["锐可博®", "RECARBRIO®"],
        "manufacturer": "默沙东",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J01DH56",
        "antibioticClass": "碳青霉烯类/β-内酰胺酶抑制剂复合制剂",
        "sourceUrl": "https://www.msd.com",
        "slug": "imipenem-cilastatin-relebactam",
    },
    "头孢他啶阿维巴坦": {
        "drugName": "注射用头孢他啶阿维巴坦钠",
        "brandNames": ["思福妥"],
        "manufacturer": "百时美施贵宝 / 阿斯利康",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J01DI52",
        "antibioticClass": "β-内酰胺酶抑制剂复合制剂（三代头孢）",
        "sourceUrl": "https://www.astrazeneca.com",
        "slug": "ceftazidime-avibactam",
    },
    "依嘉": {
        "drugName": "注射用盐酸依拉环素",
        "brandNames": ["依嘉®", "XERAVA®"],
        "manufacturer": "云顶新耀（Everest Medicines）/ Tetraphase",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J01AA13",
        "antibioticClass": "四环素类抗菌药物（氟环素）",
        "sourceUrl": "https://www.everestmedicines.com",
        "slug": "eravacycline",
    },
    "双坦": {
        "drugName": "注射用舒巴坦钠/注射用度洛巴坦钠组合包装",
        "brandNames": ["鼎优乐®", "XACDURO®"],
        "manufacturer": "齐鲁制药 / Innoviva",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J01CG51",
        "antibioticClass": "β-内酰胺酶抑制剂复合制剂（舒巴坦/度洛巴坦）",
        "sourceUrl": "https://www.qilu-pharma.com",
        "slug": "sulbactam-durlobactam",
    },
    "鼎优乐": {
        "drugName": "鼎优乐（抗生素类药品）",
        "brandNames": ["鼎优乐"],
        "manufacturer": "未知",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "",
        "antibioticClass": "抗菌药物",
        "sourceUrl": "",
        "slug": "dingyoule",
    },
    "妥布霉素吸入溶液": {
        "drugName": "妥布霉素吸入溶液",
        "brandNames": ["妥布霉素"],
        "manufacturer": "Novartis",
        "dosageForm": "吸入溶液",
        "atcCode": "J01GB01",
        "antibioticClass": "氨基糖苷类",
        "sourceUrl": "https://www.novartis.com",
        "slug": "tobramycin-inhalation",
    },
    "注射用艾沙康唑": {
        "drugName": "注射用硫酸艾沙康唑",
        "brandNames": ["康新博", "Cresemba"],
        "manufacturer": "Basilea Pharmaceutica / 辉瑞",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J02AC04",
        "antibioticClass": "三唑类抗真菌药",
        "sourceUrl": "https://www.basilea.com",
        "slug": "isavuconazole-injection",
    },
    "Emblaveo": {
        "drugName": "注射用氨曲南阿维巴坦钠",
        "brandNames": ["Emblaveo"],
        "manufacturer": "辉瑞 / AbbVie",
        "dosageForm": "注射用无菌粉末",
        "atcCode": "J01DF51",
        "antibioticClass": "单环β-内酰胺/β-内酰胺酶抑制剂复合制剂",
        "sourceUrl": "https://www.pfizer.com",
        "slug": "aztreonam-avibactam",
    },
}

# 需要提取的章节关键词
SECTIONS = {
    "indications": ["【适应症】", "【适应证】"],
    "dosage": ["【用法用量】"],
    "contraindications": ["【禁忌】", "【禁忌症】"],
    "warnings": ["【注意事项】", "【警告】"],
    "renal": ["【肾功能】", "肾功能", "肌酐清除率", "肾损害", "肾功能不全"],
    "hepatic": ["【肝功能】", "肝功能", "肝损害", "肝功能不全"],
    "pregnancy": ["【孕妇及哺乳期妇女用药】", "妊娠", "哺乳期"],
    "children": ["【儿童用药】"],
    "elderly": ["【老年用药】", "【老年患者用药】"],
    "interactions": ["【药物相互作用】"],
    "tdm": ["TDM", "血药浓度", "治疗药物监测", "谷浓度", "峰浓度"],
    "adverse": ["【不良反应】"],
}


def extract_text(pdf_path):
    """提取 PDF 全部文本"""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def find_section(text, keywords):
    """查找并提取指定章节的内容"""
    for kw in keywords:
        idx = text.find(kw)
        if idx == -1:
            continue
        # 从关键词后开始找内容，直到下一个【章节】标记
        start = idx + len(kw)
        # 找下一个章节标记
        next_section = re.search(r"\n【[^】]+】", text[start:])
        if next_section:
            end = start + next_section.start()
        else:
            end = min(start + 3000, len(text))
        content = text[start:end].strip()
        # 清理多余空白
        content = re.sub(r"\n{3,}", "\n\n", content)
        if content:
            return content
    return ""


def clean_text(text):
    """清理文本"""
    # 移除页码水印（多种变体）
    text = re.sub(r"第\s*\d*\s*页\s*，?\s*共\s*\d*\s*页", "", text)
    text = re.sub(r"第\s*\d*\s*页\s*共\s*\d*\s*页", "", text)
    # 移除 "3 / 33" 这类页码
    text = re.sub(r"\n\s*\d+\s*/\s*\d+\s*\n", "\n", text)
    text = re.sub(r"Version No:.*", "", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def parse_indications(text):
    """解析适应症，返回列表"""
    content = find_section(text, SECTIONS["indications"])
    if not content:
        return []
    # 按分号或换行分割
    items = re.split(r"[；;\n]", content)
    items = [i.strip() for i in items if i.strip() and len(i.strip()) > 2]
    # 过滤掉太短的
    items = [i for i in items if len(i) > 3][:10]
    return items


def parse_contraindications(text):
    """解析禁忌"""
    content = find_section(text, SECTIONS["contraindications"])
    if not content:
        return []
    items = re.split(r"[；;\n。]", content)
    items = [i.strip() for i in items if i.strip() and len(i.strip()) > 2]
    return items[:5]


def parse_interactions(text):
    """解析药物相互作用"""
    content = find_section(text, SECTIONS["interactions"])
    if not content:
        return []
    items = re.split(r"\n", content)
    items = [i.strip() for i in items if i.strip() and len(i.strip()) > 5]
    return items[:8]


def parse_adjustments(text, renal=True):
    """解析肾功能/肝功能调整，优先匹配【...】章节标记"""
    # 优先查找带【】的章节标记
    section_keywords = []
    if renal:
        section_keywords = [
            "【肾功能不全患者用药】", "【肾功能损害患者】", "【肾功能不全】",
            "【肾功能】", "【特殊人群（肾功能）】",
        ]
    else:
        section_keywords = [
            "【肝功能不全患者用药】", "【肝功能损害患者】", "【肝功能不全】",
            "【肝功能】", "【特殊人群（肝功能）】",
        ]
    
    for kw in section_keywords:
        idx = text.find(kw)
        if idx != -1:
            start = idx + len(kw)
            next_section = re.search(r"\n【[^】]+】", text[start:])
            if next_section:
                end = start + next_section.start()
            else:
                end = min(start + 1500, len(text))
            content = text[start:end].strip()
            if content:
                return clean_text(content)
    
    # 回退：查找 "肾功能损害" / "肝功能损害" 这类小标题（不在【】内）
    fallback_keywords = ["肾功能损害", "肝功能损害"] if renal else ["肝功能损害"]
    for kw in fallback_keywords:
        idx = text.find(kw)
        if idx == -1:
            continue
        start = idx
        next_section = re.search(r"\n【[^】]+】", text[start:])
        if next_section:
            end = start + next_section.start()
        else:
            end = min(start + 800, len(text))
        content = text[start:end].strip()
        if content:
            return clean_text(content)
    return ""


def parse_dosage(text):
    """解析用法用量"""
    content = find_section(text, SECTIONS["dosage"])
    if not content:
        return ""
    return clean_text(content)[:2000]


def parse_special_populations(text):
    """解析特殊人群"""
    pops = []
    for pop_key in ["pregnancy", "children", "elderly"]:
        content = find_section(text, SECTIONS[pop_key])
        if content:
            label = {"pregnancy": "妊娠/哺乳", "children": "儿童", "elderly": "老年"}[pop_key]
            pops.append(f"{label}：{clean_text(content)[:150]}")
    return pops


def detect_strengths(text):
    """检测规格，优先查找【规格】章节，排除剂量和浓度相关匹配"""
    # 剂量/浓度单位黑名单（不是规格）
    dose_units = ["kg", "m²", "m2", "min", "hour", "h", "day", "d", "hr", "sec"]
    # 浓度/TDM 相关关键词
    concentration_words = ["浓度范围", "浓度", "滴注", "给药", "维持剂量", "负荷剂量", "血药", "谷浓度", "峰浓度"]
    # 剂型单位（规格的常见后缀）
    form_units = ["片", "粒", "支", "袋", "瓶", "包", "枚", "贴", "丸", "板", "盒", "ml", "mL", "g", "mg", "μg", "µg", "IU", "干混悬剂"]
    
    # 1. 优先查找【规格】章节
    spec_section = find_section(text, ["【规格】"])
    if spec_section:
        # 在规格章节中匹配 "数字+单位" 模式
        spec_matches = re.findall(r"\d+(?:\.\d+)?\s*(?:mg|g|μg|µg|IU|万?IU)", spec_section)
        if spec_matches:
            seen = set()
            result = []
            for m in spec_matches:
                key = re.sub(r"\s+", "", m)
                if key not in seen:
                    seen.add(key)
                    result.append(m.strip())
            if result:
                return result[:3]
    
    # 2. 查找 "规格为XXX" 或 "规格:XXX" 模式
    spec_pattern = re.search(r"规格[为:：]?\s*([^\n，。；]+)", text)
    if spec_pattern:
        spec_text = spec_pattern.group(1)
        spec_matches = re.findall(r"\d+(?:\.\d+)?\s*(?:mg|g|μg|µg|IU|万?IU)(?:\s*/\s*[^\s，。、；;]+)?", spec_text)
        if spec_matches:
            return [m.strip() for m in spec_matches[:3]]
    
    # 3. 全文匹配 "数字+单位+/+剂型" 模式，排除剂量和浓度
    strengths = []
    pattern = r"(\d+(?:\.\d+)?\s*(?:mg|g|μg|µg|IU|万?IU)\s*/\s*[^\s，。、；;]+)"
    matches = re.findall(pattern, text)
    for m in matches:
        # 检查是否包含浓度关键词
        if any(cw in m for cw in concentration_words):
            continue
        # 检查 / 后面是否是剂量单位
        after_slash = re.search(r"/\s*([^\s，。、；;]+)", m)
        if after_slash:
            suffix = after_slash.group(1).lower()
            if any(suffix.startswith(du) for du in dose_units):
                continue
        strengths.append(m)
    
    # 去重
    seen = set()
    result = []
    for s in strengths:
        key = re.sub(r"\s+", "", s)
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result[:3] or ["详见说明书原文"]


def detect_renal_adjust(text):
    """检测是否需要肾功能调整"""
    renal_kw = ["肌酐清除率", "肾功能不全", "肾损害", "CrCl", "肌酐", "肾衰", "透析"]
    for kw in renal_kw:
        if text.find(kw) != -1:
            return True
    return False


def detect_hepatic_adjust(text):
    """检测是否需要肝功能调整"""
    hepatic_kw = ["肝功能不全", "肝损害", "肝功能", "Child", "转氨酶", "胆红素"]
    for kw in hepatic_kw:
        if text.find(kw) != -1:
            return True
    return False


def find_tdm_info(text):
    """查找 TDM 相关信息（血药浓度监测、谷浓度目标等）"""
    # 优先查找明确的 TDM/治疗药物监测章节
    tdm_section_keywords = [
        "【治疗药物监测】", "【血药浓度监测】", "【TDM】",
        "【血药浓度】", "【药物浓度监测】",
    ]
    for kw in tdm_section_keywords:
        idx = text.find(kw)
        if idx != -1:
            start = idx + len(kw)
            next_section = re.search(r"\n【[^】]+】", text[start:])
            if next_section:
                end = start + next_section.start()
            else:
                end = min(start + 800, len(text))
            content = text[start:end].strip()
            if content:
                return clean_text(content)
    
    # 回退：在全文中查找 TDM/谷浓度关键词
    tdm_keywords = ["治疗药物监测", "TDM", "谷浓度", "血药浓度监测", "峰浓度"]
    for kw in tdm_keywords:
        idx = text.find(kw)
        if idx != -1:
            start = max(0, idx - 100)
            end = min(idx + 400, len(text))
            content = clean_text(text[start:end])
            # 只保留包含浓度数值的句子
            sentences = re.split(r"[。\n]", content)
            relevant = [s for s in sentences if any(c in s for c in ["浓度", "谷浓度", "峰浓度", "TDM", "监测", "mg/L", "μg/ml", "ng/ml"])]
            if relevant:
                return "。".join(relevant)
            return content
    return ""


def build_markdown(meta, text):
    """构建 Markdown 内容"""
    indications = parse_indications(text)
    contraindications = parse_contraindications(text)
    interactions = parse_interactions(text)
    special_pops = parse_special_populations(text)
    dosage = parse_dosage(text)
    renal_info = parse_adjustments(text, renal=True)
    hepatic_info = parse_adjustments(text, renal=False)
    strengths = detect_strengths(text)
    renal_adj = detect_renal_adjust(text)
    hepatic_adj = detect_hepatic_adjust(text)
    tdm_info = find_tdm_info(text)

    # frontmatter
    fm = {
        "drugName": meta["drugName"],
        "brandNames": meta["brandNames"],
        "manufacturer": meta["manufacturer"],
        "dosageForm": meta["dosageForm"],
        "strengths": strengths,
        "atcCode": meta["atcCode"],
        "antibioticClass": meta["antibioticClass"],
        "indications": indications or ["详见说明书原文"],
        "contraindications": contraindications,
        "specialPopulations": special_pops,
        "renalAdjustment": renal_adj,
        "hepaticAdjustment": hepatic_adj,
        "drugInteractions": interactions,
        "preparation": "详见说明书原文",
        "sourceUrl": meta["sourceUrl"],
        "reviewDate": "2026-11-09",
        "tags": [meta["antibioticClass"]] if meta["antibioticClass"] else [],
        "description": f"{meta['drugName']}，{meta['antibioticClass']}，说明书 PDF 解析生成。",
        "draft": len(text) < 100,  # 扫描件（无法提取文本）标记为草稿
    }

    md = "---\n"
    for k, v in fm.items():
        # 省略空的 sourceUrl（schema 要求 .url() 或省略）
        if k == "sourceUrl" and not v:
            continue
        if isinstance(v, bool):
            # 布尔值直接输出，不加引号
            md += f"{k}: {str(v).lower()}\n"
        elif isinstance(v, list):
            if v:
                md += f"{k}:\n"
                for item in v:
                    # 列表项内换行替换为空格，避免 YAML 格式错乱
                    item_str = str(item).replace("\r", " ").replace("\n", " ").strip()
                    # YAML 双引号字符串转义：先转义反斜杠，再转义双引号
                    safe = item_str.replace("\\", "\\\\").replace('"', '\\"')
                    md += f'  - "{safe}"\n'
            else:
                md += f"{k}: []\n"
        else:
            # YAML 双引号字符串转义：先转义反斜杠，再转义双引号
            safe = str(v).replace("\\", "\\\\").replace('"', '\\"')
            md += f'{k}: "{safe}"\n'
    md += "---\n\n"

    # 正文
    md += f"## 一、药品概述\n\n{meta['drugName']}，{meta['antibioticClass']}。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。\n\n"

    md += "## 二、适应证\n\n"
    for ind in indications:
        md += f"- {ind}\n"
    if not indications:
        md += "详见说明书原文。\n"
    md += "\n"

    md += "## 三、用法用量\n\n"
    md += dosage or "详见说明书原文。"
    md += "\n\n"

    md += "## 四、肾功能调整\n\n"
    if renal_info:
        md += renal_info[:1000] + "\n"
    else:
        md += "说明书中未明确提及肾功能调整。\n"
    md += "\n"

    md += "## 五、肝功能调整\n\n"
    if hepatic_info:
        md += hepatic_info[:1000] + "\n"
    else:
        md += "说明书中未明确提及肝功能调整。\n"
    md += "\n"

    if tdm_info:
        md += "## 六、治疗药物监测（TDM）\n\n"
        md += tdm_info + "\n\n"

    md += "## 七、禁忌\n\n"
    for c in contraindications:
        md += f"- {c}\n"
    if not contraindications:
        md += "详见说明书原文。\n"
    md += "\n"

    md += "## 八、特殊人群\n\n"
    for p in special_pops:
        md += f"- {p}\n"
    if not special_pops:
        md += "详见说明书原文。\n"
    md += "\n"

    md += "## 九、药物相互作用\n\n"
    for i in interactions:
        md += f"- {i}\n"
    if not interactions:
        md += "详见说明书原文。\n"
    md += "\n"

    md += "## 十、注意事项\n\n"
    warnings = find_section(text, SECTIONS["warnings"])
    if warnings:
        md += clean_text(warnings)[:1500] + "\n"
    else:
        md += "详见说明书原文。\n"
    md += "\n"

    md += "---\n\n> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。\n"

    return md


def main():
    pdf_files = sorted(list(PDF_DIR.glob("*.pdf")) + list(PDF_DIR.glob("*.PDF")))
    print(f"找到 {len(pdf_files)} 个 PDF 文件")

    results = []
    for pdf_path in pdf_files:
        name = pdf_path.stem
        print(f"\n处理: {name}")

        # 匹配药品元信息
        meta = None
        for key, m in DRUG_META.items():
            if key in name:
                meta = m
                break
        if not meta:
            # 使用默认元信息
            meta = {
                "drugName": name,
                "brandNames": [name],
                "manufacturer": "未知",
                "dosageForm": "详见说明书",
                "atcCode": "",
                "antibioticClass": "抗菌/抗真菌药物",
                "sourceUrl": "",
                "slug": re.sub(r"[^\w-]", "-", name).lower()[:50],
            }
            print(f"  警告: 未找到匹配的元信息，使用默认值")

        try:
            text = extract_text(str(pdf_path))
            print(f"  提取文本长度: {len(text)} 字符")

            md_content = build_markdown(meta, text)

            out_path = OUTPUT_DIR / f"{meta['slug']}.md"
            out_path.write_text(md_content, encoding="utf-8")
            print(f"  生成: {out_path.name}")
            results.append({"name": name, "slug": meta["slug"], "ok": True})

        except Exception as e:
            print(f"  错误: {e}")
            results.append({"name": name, "ok": False, "error": str(e)})

    # 输出汇总
    ok_count = sum(1 for r in results if r.get("ok"))
    print(f"\n===== 汇总: 成功 {ok_count}/{len(results)} =====")
    for r in results:
        status = "✅" if r.get("ok") else "❌"
        print(f"{status} {r['name']}")


if __name__ == "__main__":
    main()
