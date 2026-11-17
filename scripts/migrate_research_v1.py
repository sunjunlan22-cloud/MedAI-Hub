#!/usr/bin/env python3
"""
MedAI Hub 科研数据一次性迁移 v1（医学文献检索第一版）
======================================================
对 src/data/auto/research.json 做定向离线清理，不重抓数据源：

1. 删除已确认的 CRAB 误收录（螃蟹养殖 / 水产 / 非 AMR 语境）。
2. 清空自动生成的模板化字段：coreFindings / limitations / inspiration。
   （原始摘要仍在 abstract；这些字段原为 desc 截断或模板文案，非真实研究结果/人工解读）
3. 移除已停用的科研五轴评分 scores / totalScore（取消科研自建评分全链路）。

安全机制：
- 写入前自动备份到 scripts/migrations/backups/，保留可恢复副本。
- 记录处理日志到 scripts/migrations/migrate_research_v1.log。
- 幂等：可重复运行，不会二次清理或重复删除。
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESEARCH_PATH = BASE_DIR / "src" / "data" / "auto" / "research.json"
BACKUP_DIR = BASE_DIR / "scripts" / "migrations" / "backups"
LOG_PATH = BASE_DIR / "scripts" / "migrations" / "migrate_research_v1.log"

TZ_CN = timezone(timedelta(hours=8))

# 已确认的 CRAB 误收录（标题含螃蟹/水产/非 AMR 语境，非耐碳青霉烯鲍曼不动杆菌）
FALSE_POSITIVE_IDS = {
    "res-bb5693a1ff": "Aquaculture nutrition 螃蟹类胡萝卜素代谢（非 AMR）",
    "res-9f9ef305a4": "Journal of invertebrate pathology 大理石蟹黑斑病（水产动物疾病）",
    "res-73e949834f": "BMC surgery 颈动脉分叉外科 crab technique（外科术式，非 AMR）",
}

# 自动生成、需清空的模板字段
CLEARED_FIELDS = ["coreFindings", "limitations", "inspiration"]
# 已停用的科研五轴评分字段
REMOVED_FIELDS = ["scores", "totalScore"]


def log(msg: str) -> None:
    line = f"[{datetime.now(TZ_CN).isoformat(timespec='seconds')}] {msg}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    if not RESEARCH_PATH.exists():
        log(f"未找到数据文件：{RESEARCH_PATH}，跳过")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        log("research.json 不是 JSON 数组，中止")
        return 1

    # 备份（写入前）
    stamp = datetime.now(TZ_CN).strftime("%Y%m%dT%H%M%S")
    backup_path = BACKUP_DIR / f"research.json.{stamp}.bak"
    backup_path.write_text(RESEARCH_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    log(f"已备份原数据 → {backup_path.relative_to(BASE_DIR)}（{len(data)} 条）")

    removed: list[str] = []
    cleared: dict[str, int] = {k: 0 for k in CLEARED_FIELDS}
    score_removed = 0
    kept: list[dict] = []

    for e in data:
        eid = e.get("id", "")
        if eid in FALSE_POSITIVE_IDS:
            removed.append(f"{eid} | {FALSE_POSITIVE_IDS[eid]} | {e.get('title', '')[:60]}")
            continue
        for field in CLEARED_FIELDS:
            old = e.get(field)
            if old not in (None, ""):
                cleared[field] += 1
            e[field] = ""
        for field in REMOVED_FIELDS:
            if field in e:
                e.pop(field)
                score_removed += 1
        kept.append(e)

    log(f"删除误收录 {len(removed)} 条：")
    for r in removed:
        log(f"  - {r}")
    for field, n in cleared.items():
        log(f"清空 {field}：{n} 条")
    log(f"移除评分字段 scores/totalScore：{score_removed} 条")
    log(f"迁移后保留 {len(kept)} 条")

    RESEARCH_PATH.write_text(
        json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log("迁移完成，已写回 research.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
