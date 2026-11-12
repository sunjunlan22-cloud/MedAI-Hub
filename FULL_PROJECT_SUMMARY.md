# 项目源码完整导出

> 本文档完整导出了 Astro 静态站项目的全部文本源码（共 69 个文件），供存档与审阅使用。

---

# 最新进展与待确认决策点（2026-11-11 更新）

> 本部分为项目升级（Schema 统一与采集脚本升级）的最新状态快照，覆盖阶段 A1 → A2 → A2.1 → B1.1（调研中）。

## 一、阶段成果

### 阶段 A1：现状审查与 Schema 设计（纯分析，未改代码）

- 完成「升级前现状审查与差距分析」。
- 确定统一 Schema 三原则：
  1. **camelCase 驼峰命名**。
  2. **继承模型**：`BaseContent` + 三个专属模型 `IndustryContent` / `ResearchContent` / `GuidelineContent`。
  3. **内存层 Normalize 契约**：仅做类型识别、字段映射、默认值回填，不写文件。
- 确定状态机三字段分离：`recordStatus` / `verificationStatus` / `reviewStatus`；版权双字段：`licenseStatus` / `licensePermissions`。
- 确定医学严谨性规则：`evidenceQuality` / `recommendationGrade` 仅在原文明确提供时填写，否则「原文未评估」。

### 阶段 A2：向后兼容实施（已通过 check / build）

- 新建 `src/types/content.ts`：完整实现 `BaseContent`（25 字段）+ 3 专属模型 + 枚举 + `Normalize<T>` 工具类型 + `normalizeIndustry` / `normalizeResearch`。
- 扩展 `src/content.config.ts` 的 guides schema：新增 7 个 optional / 带默认值字段，不破坏现有 Markdown frontmatter 校验。
- 修复 `src/pages/ai-tools.astro` 的 `<script>` TS 语法（预存 bug，阻塞 check）。
- 保留 `src/types/news.ts` 旧类型及 `scores` / `totalScore` / `factType` / `isCluster` / `studyType` / `evidenceLevel` 等字段不变。

### 阶段 A2.1：技术审查与最终验收（已通过）

修复 5 项 Normalize 契约缺陷（均在 `content.ts`）：

| # | 缺陷 | 修正 |
|---|---|---|
| 1 | contentType 硬编码为 `news` | 改为 `raw.contentType \|\| undefined`（缺失即「待分类」）|
| 2 | `??` 不处理空字符串 | 状态/版权/证据字段改 `\|\|` 空值语义 |
| 3 | 无条件覆盖已有合法值 | 改为「已有值优先保留，缺失才回填默认」|
| 4 | `scores`/`totalScore`/`isCluster` 丢失 | 补兼容字段 + 引用透传 |
| 5 | `publishStatus` 丢失 + `in-review` 静默丢失 | 新增 `inReview` 枚举 + 映射 + 保留原值 |

- 测试：33 通过 / 0 失败（场景覆盖纯旧数据、新旧并存、人工核验、空值/非法枚举、幂等）。
- `pnpm check`：0 errors / 0 warnings；`pnpm build`：74 pages built。

### 阶段 B1.1：采集脚本升级（调研中，未实施）

- 已核查 `scripts/fetch_news.py`、`src/data/auto/`、`.github/workflows/fetch-news.yml`。
- 已产出：现有采集流程说明、旧字段 → 新 Schema 映射表、新增字段默认值策略、去重与合并策略、预计修改文件清单、兼容风险清单。
- **尚未修改任何代码**，等待决策确认后实施。

## 二、当前待确认决策点

### A2.1 遗留（延期至 A3，非阻塞）

1. **`review → systematicReview` 映射**：可能过度声明（综述 ≠ 系统综述），建议增补 `narrativeReview` 或保守映射 `other`。
2. **`PublicationStatus` 边界**：`registered` / `resultsPosted` 与 `trialStatus` 语义重叠，建议厘清两字段职责。
3. **`ai-tools.astro` 第 67 行 `event` 弃用**（ts6385）：建议改为事件委托，可随时小修。

### B1.1 待确认（当前阻塞点，决定是否进入实施）

1. **是否引入「读旧文件合并」**：当前脚本全量覆写 `industry.json`/`research.json`，人工补充信息会丢失；需确认是改为「累积合并」还是保持「快照覆写 + 仅回填新字段」。
2. **旧 `evidenceLevel` 自动推断如何处理**：当前脚本按 studyType 生成证据等级（如 "1a（RCT）"），违反「不得自动推断证据等级」；需确认停用 / 保留为内部参考并与新 `evidenceQuality` 隔离命名。
3. **contentType 是否采用源级人工配置**：现有 `category`/`factType` 无法映射业务类型；需确认是否接受在源配置中人工标注 `content_type`。

## 三、当前状态

- ✅ A2 / A2.1 已完成并通过验收。
- ⏸️ B1.1 处于调研完成、待确认阶段，未改代码。
- ⛔ 硬约束：不删/不改旧字段、不改历史 JSON、不改 `src/content/` 与 `src/data/manual/`、只写 `src/data/auto/`、不动首页布局与搜索筛选、不动 GitHub Actions、不提前进入 A3 / B1 实施。

---

## 总目录

```text
├── astro.config.mjs
├── package.json
├── src/
│   ├── components/
│   │   ├── ScoreBadge.astro
│   │   └── tools/
│   │       ├── ARC.tsx
│   │       ├── ApacheII.tsx
│   │       ├── CURB65.tsx
│   │       ├── CockcroftGault.tsx
│   │       ├── EGFR.tsx
│   │       ├── PFRatio.tsx
│   │       ├── SOFA.tsx
│   │       └── shared.tsx
│   ├── content/
│   │   ├── drug-labels/
│   │   │   ├── TEMPLATE.md
│   │   │   ├── amphotericin-b-cholesterol.md
│   │   │   ├── amphotericin-b-liposome.md
│   │   │   ├── aztreonam-avibactam.md
│   │   │   ├── ceftazidime-avibactam.md
│   │   │   ├── dingyoule.md
│   │   │   ├── eravacycline.md
│   │   │   ├── imipenem-cilastatin-relebactam.md
│   │   │   ├── isavuconazole-capsule.md
│   │   │   ├── isavuconazole-injection.md
│   │   │   ├── sulbactam-durlobactam.md
│   │   │   ├── tobramycin-inhalation.md
│   │   │   ├── voriconazole-injection.md
│   │   │   └── voriconazole-tablet.md
│   │   └── guides/
│   │       ├── TEMPLATE.md
│   │       ├── cap-2019.md
│   │       ├── hap-vap-2016.md
│   │       ├── intra-abdominal-2017.md
│   │       ├── raw-4bd484cd6c.md
│   │       ├── raw-77296625b0.md
│   │       ├── raw-84ce3875de.md
│   │       ├── raw-ad60fe4289.md
│   │       ├── raw-d5b8ada0b5.md
│   │       ├── raw-eb161f46d4.md
│   │       ├── raw-efa87ab279.md
│   │       ├── raw-f468b425d7.md
│   │       ├── ski-2014.md
│   │       └── uti-2019.md
│   ├── content.config.ts
│   ├── data/
│   │   ├── auto/
│   │   │   ├── industry.json
│   │   │   └── research.json
│   │   └── manual/
│   │       ├── ai-tools.json
│   │       ├── dosing-reference.json
│   │       └── tools-meta.json
│   ├── layouts/
│   │   └── BaseLayout.astro
│   ├── pages/
│   │   ├── about.astro
│   │   ├── ai-tools.astro
│   │   ├── drug-labels/
│   │   │   └── [slug].astro
│   │   ├── drug-labels.astro
│   │   ├── guides/
│   │   │   └── [slug].astro
│   │   ├── guides.astro
│   │   ├── index.astro
│   │   ├── industry/
│   │   │   └── [id].astro
│   │   ├── industry.astro
│   │   ├── research/
│   │   │   └── [id].astro
│   │   ├── research.astro
│   │   ├── tools/
│   │   │   ├── apache-ii.astro
│   │   │   ├── arc.astro
│   │   │   ├── cockcroft-gault.astro
│   │   │   ├── curb-65.astro
│   │   │   ├── dosing-reference.astro
│   │   │   ├── egfr.astro
│   │   │   ├── pf-ratio.astro
│   │   │   └── sofa.astro
│   │   └── tools.astro
│   ├── styles/
│   │   └── global.css
│   └── types/
│       └── news.ts
└── tsconfig.json
```

## astro.config.mjs

```javascript
// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  // TODO: 绑定 Cloudflare Pages 后替换为正式域名
  site: 'https://medai-hub.pages.dev',
  output: 'static',
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
```

## tsconfig.json

```json
{
  "extends": "astro/tsconfigs/strict",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist"]
}
```

## package.json

```json
{
  "name": "medai-hub",
  "type": "module",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "check": "astro check",
    "astro": "astro",
    "pagefind": "pagefind --site dist",
    "postbuild": "pagefind --site dist"
  },
  "dependencies": {
    "@astrojs/react": "^4.0.0",
    "@radix-ui/react-slot": "^1.1.0",
    "astro": "^5.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.474.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwind-merge": "^3.0.0"
  },
  "devDependencies": {
    "@astrojs/check": "^0.9.12",
    "@tailwindcss/typography": "^0.5.20",
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "pagefind": "^1.2.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0"
  }
}
```

## src/components/ScoreBadge.astro

```astro
---
// 五轴评分展示组件
// 总分满分 50，准入线 35（PRD 5.2）

interface AxisScore {
  label: string;
  value: number;
}

interface Props {
  totalScore: number;       // 总分（0-50）
  axes: AxisScore[];        // 五轴明细
}

const { totalScore, axes } = Astro.props;

// 颜色分级：>=40 优秀（绿），>=35 达标（蓝），<35 未达标（红）
const scoreColor =
  totalScore >= 40
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : totalScore >= 35
      ? 'bg-blue-50 text-blue-700 border-blue-200'
      : 'bg-red-50 text-red-700 border-red-200';

const barColor =
  totalScore >= 40
    ? 'bg-emerald-500'
    : totalScore >= 35
      ? 'bg-blue-500'
      : 'bg-red-500';
---

<div class="flex items-start gap-4">
  <!-- 总分大徽章 -->
  <div
    class={`flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-lg border ${scoreColor}`}
  >
    <span class="text-xl font-bold leading-none">{totalScore}</span>
    <span class="mt-0.5 text-[10px] leading-none opacity-70">/ 50</span>
  </div>

  <!-- 五轴明细 -->
  <div class="flex-1 space-y-1.5">
    {
      axes.map((axis) => (
        <div class="flex items-center gap-2">
          <span class="w-28 shrink-0 text-xs text-neutral-500">{axis.label}</span>
          <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-neutral-100">
            <div
              class={`h-full rounded-full ${barColor}`}
              style={`width: ${(axis.value / 10) * 100}%`}
            />
          </div>
          <span class="w-6 text-right text-xs font-medium text-neutral-600">{axis.value}</span>
        </div>
      ))
    }
  </div>
</div>
```

## src/components/tools/ARC.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * ARC（肾清除过度，Augmented Renal Clearance）筛查
 * 定义：CrCl > 130 mL/min（女性常以 > 120 为界）
 * 用 Cockcroft-Gault 估算肌酐清除率，结合高危因素评估 ARC 风险。
 */

const RISK_FACTORS = [
  { k: 'sepsis', l: '脓毒症 / 感染性休克' },
  { k: 'trauma', l: '严重创伤' },
  { k: 'burn', l: '烧伤' },
  { k: 'sah', l: '蛛网膜下腔出血' },
  { k: 'surgery', l: '大手术' },
] as const;

export default function ARC() {
  const [age, setAge] = useState('');
  const [weight, setWeight] = useState('');
  const [scr, setScr] = useState(''); // mg/dL
  const [male, setMale] = useState(true);
  const [factors, setFactors] = useState<string[]>([]);
  const [result, setResult] = useState<{ crcl: number; arc: boolean; advice: string } | null>(null);
  const [error, setError] = useState('');

  function calc() {
    setError('');
    const a = parseFloat(age);
    const w = parseFloat(weight);
    const s = parseFloat(scr);
    if (!a || !w || !s) { setError('请填写年龄、体重与血肌酐'); return; }
    if (a < 18 || a > 100) { setError('年龄应在 18-100 岁之间'); return; }
    if (s <= 0) { setError('血肌酐应大于 0'); return; }

    // Cockcroft-Gault
    let crcl = ((140 - a) * w) / (72 * s);
    if (!male) crcl *= 0.85;
    crcl = Math.round(crcl);

    const threshold = male ? 130 : 120;
    const arc = crcl >= threshold;

    let advice = '';
    if (arc) {
      advice = factors.length >= 2
        ? 'ARC 阳性且合并多项高危因素，亲水性抗菌药物（β-内酰胺、万古霉素、氨基糖苷）剂量不足风险高，建议个体化/增加剂量或延长输注，并结合 TDM 监测。'
        : 'ARC 阳性，建议关注亲水性抗菌药物清除加快，必要时调整剂量并考虑 TDM。';
    } else {
      advice = '未达 ARC 阈值，常规肾功能调整剂量方案即可。';
    }

    setResult({ crcl, arc, advice });
  }

  const inputCls = 'mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none';
  const labelCls = 'block text-sm font-medium text-neutral-700';

  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-xl font-bold text-neutral-900">ARC 肾清除过度筛查</h2>
      <p className="mt-1 text-sm text-neutral-500">
        识别肌酐清除率过高（CrCl &gt; 130）导致抗菌药物剂量不足的风险。
      </p>

      <div className="mt-5 grid gap-3">
        <div className="flex gap-2">
          <button type="button" onClick={() => setMale(true)}
            className={`flex-1 rounded-md border px-3 py-2 text-sm ${male ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600'}`}>男</button>
          <button type="button" onClick={() => setMale(false)}
            className={`flex-1 rounded-md border px-3 py-2 text-sm ${!male ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600'}`}>女</button>
        </div>
        <label className="block"><span className={labelCls}>年龄（岁）</span>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className={inputCls} placeholder="如 35" /></label>
        <label className="block"><span className={labelCls}>实际体重（kg）</span>
          <input type="number" value={weight} onChange={(e) => setWeight(e.target.value)} className={inputCls} placeholder="如 70" /></label>
        <label className="block"><span className={labelCls}>血肌酐 Scr（mg/dL）</span>
          <input type="number" step="0.1" value={scr} onChange={(e) => setScr(e.target.value)} className={inputCls} placeholder="如 0.6" /></label>
      </div>

      <div className="mt-4">
        <span className="text-sm font-medium text-neutral-700">高危因素（可多选）</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {RISK_FACTORS.map((f) => (
            <button key={f.k} type="button"
              onClick={() => setFactors((prev) => prev.includes(f.k) ? prev.filter((x) => x !== f.k) : [...prev, f.k])}
              className={`rounded-full border px-3 py-1.5 text-xs ${factors.includes(f.k) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'}`}>
              {f.l}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <button onClick={calc}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算 ARC 风险
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">估算肌酐清除率（CrCl）</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.crcl} mL/min</div>
            <div className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-semibold ${result.arc ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>
              {result.arc ? 'ARC 阳性（肾清除过度）' : '无 ARC'}
            </div>
            <p className="mt-3 text-sm text-neutral-700">{result.advice}</p>
          </div>
        </ResultCard>
      )}

      <Disclaimer />

      <details className="mt-4 text-sm text-neutral-500">
        <summary className="cursor-pointer hover:text-neutral-700">ARC 定义与参考</summary>
        <div className="mt-2 rounded bg-neutral-50 p-3 text-xs leading-relaxed">
          <p><strong>定义：</strong>ARC 指 CrCl &gt; 130 mL/min（部分文献女性 &gt; 120 mL/min/1.73m²）。</p>
          <p className="mt-1"><strong>高危人群：</strong>年轻、男性、脓毒症、创伤、烧伤、蛛网膜下腔出血、大手术等。</p>
          <p className="mt-1"><strong>临床意义：</strong>亲水性抗菌药物（β-内酰胺类、万古霉素、氨基糖苷）清除加快，常规剂量易致血药浓度不足，建议个体化给药并考虑 TDM。</p>
        </div>
      </details>
    </div>
  );
}
```

## src/components/tools/ApacheII.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * APACHE II 危重评分（Acute Physiology And Chronic Health Evaluation II）
 * 总分 = 急性生理评分(APS, 12项) + 年龄分 + 慢性健康分
 * 范围 0-71，用于 ICU 危重程度与预后评估。
 */

// 各生理变量按偏离正常程度记 0-4 分（取最大偏离值）
function tempScore(t: number): number {
  if (t >= 41) return 4;
  if (t >= 39) return 3;
  if (t >= 38.5) return 1;
  if (t >= 36) return 0;
  if (t >= 34) return 1;
  if (t >= 32) return 2;
  if (t >= 30) return 3;
  return 4;
}
function mapScore(m: number): number {
  if (m >= 160) return 4;
  if (m >= 130) return 3;
  if (m >= 110) return 2;
  if (m >= 70) return 0;
  if (m >= 50) return 2;
  return 4;
}
function hrScore(h: number): number {
  if (h >= 180) return 4;
  if (h >= 140) return 3;
  if (h >= 110) return 2;
  if (h >= 70) return 0;
  if (h >= 55) return 2;
  if (h >= 40) return 3;
  return 4;
}
function rrScore(r: number): number {
  if (r >= 50) return 4;
  if (r >= 35) return 3;
  if (r >= 25) return 1;
  if (r >= 12) return 0;
  if (r >= 10) return 1;
  if (r >= 6) return 2;
  return 4;
}
function pao2Score(p: number): number {
  if (p > 70) return 0;
  if (p >= 61) return 1;
  if (p >= 55) return 3;
  return 4;
}
function aado2Score(a: number): number {
  if (a >= 500) return 4;
  if (a >= 350) return 3;
  if (a >= 200) return 2;
  return 0;
}
function phScore(ph: number): number {
  if (ph >= 7.7) return 4;
  if (ph >= 7.6) return 3;
  if (ph >= 7.5) return 1;
  if (ph >= 7.33) return 0;
  if (ph >= 7.25) return 2;
  if (ph >= 7.15) return 3;
  return 4;
}
function naScore(n: number): number {
  if (n >= 180) return 4;
  if (n >= 160) return 3;
  if (n >= 155) return 2;
  if (n >= 150) return 1;
  if (n >= 130) return 0;
  if (n >= 120) return 2;
  if (n >= 111) return 3;
  return 4;
}
function kScore(k: number): number {
  if (k >= 7) return 4;
  if (k >= 6) return 3;
  if (k >= 5.5) return 1;
  if (k >= 3.5) return 0;
  if (k >= 3) return 1;
  if (k >= 2.5) return 2;
  return 4;
}
function crScore(c: number): number {
  if (c >= 3.5) return 4;
  if (c >= 2) return 3;
  if (c >= 1.5) return 2;
  if (c >= 0.6) return 0;
  return 2;
}
function hctScore(h: number): number {
  if (h >= 60) return 4;
  if (h >= 50) return 2;
  if (h >= 46) return 1;
  if (h >= 30) return 0;
  if (h >= 20) return 2;
  return 4;
}
function wbcScore(w: number): number {
  if (w >= 40) return 4;
  if (w >= 20) return 2;
  if (w >= 15) return 1;
  if (w >= 3) return 0;
  if (w >= 1) return 2;
  return 4;
}
function ageScore(a: number): number {
  if (a >= 75) return 6;
  if (a >= 65) return 5;
  if (a >= 55) return 3;
  if (a >= 45) return 2;
  return 0;
}

export default function ApacheII() {
  // 生理变量
  const [temp, setTemp] = useState('');
  const [map, setMap] = useState('');
  const [hr, setHr] = useState('');
  const [rr, setRr] = useState('');
  const [fio2High, setFio2High] = useState(false); // FiO2 ≥ 0.5 ?
  const [pao2, setPao2] = useState('');
  const [aado2, setAado2] = useState('');
  const [ph, setPh] = useState('');
  const [na, setNa] = useState('');
  const [k, setK] = useState('');
  const [cr, setCr] = useState('');
  const [arf, setArf] = useState(false); // 急性肾衰竭
  const [hct, setHct] = useState('');
  const [wbc, setWbc] = useState('');
  const [gcs, setGcs] = useState('15');
  // 年龄 + 慢性健康
  const [age, setAge] = useState('');
  const [chronic, setChronic] = useState<'none' | 'elective' | 'nonsurgical'>('none');

  const [result, setResult] = useState<{ aps: number; agePts: number; chp: number; total: number; detail: string[] } | null>(null);
  const [error, setError] = useState('');

  function calc() {
    setError('');
    const num = (s: string) => parseFloat(s);
    let aps = 0;
    const detail: string[] = [];

    const t = num(temp); if (!isNaN(t)) aps += tempScore(t);
    const m = num(map); if (!isNaN(m)) aps += mapScore(m);
    const h = num(hr); if (!isNaN(h)) aps += hrScore(h);
    const r = num(rr); if (!isNaN(r)) aps += rrScore(r);

    if (fio2High) { const a = num(aado2); if (!isNaN(a)) aps += aado2Score(a); }
    else { const p = num(pao2); if (!isNaN(p)) aps += pao2Score(p); }

    const phn = num(ph); if (!isNaN(phn)) aps += phScore(phn);
    const nan = num(na); if (!isNaN(nan)) aps += naScore(nan);
    const kn = num(k); if (!isNaN(kn)) aps += kScore(kn);

    let crPts = 0;
    const cn = num(cr); if (!isNaN(cn)) { crPts = crScore(cn); if (arf) crPts *= 2; aps += crPts; }
    if (crPts > 0) detail.push(`肌酐 ${crPts} 分${arf ? '（急性肾衰 ×2）' : ''}`);

    const hn = num(hct); if (!isNaN(hn)) aps += hctScore(hn);
    const wn = num(wbc); if (!isNaN(wn)) aps += wbcScore(wn);
    const gn = num(gcs); if (!isNaN(gn) && gn >= 3 && gn <= 15) aps += (15 - gn);

    // 年龄分
    const an = num(age);
    const agePts = !isNaN(an) ? ageScore(an) : 0;

    // 慢性健康分
    const chp = chronic === 'nonsurgical' ? 5 : chronic === 'elective' ? 2 : 0;

    const total = aps + agePts + chp;

    setResult({
      aps,
      agePts,
      chp,
      total,
      detail,
    });
  }

  const inputCls = 'mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none';
  const labelCls = 'block text-sm font-medium text-neutral-700';

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-xl font-bold text-neutral-900">APACHE II 危重评分</h2>
      <p className="mt-1 text-sm text-neutral-500">
        急性生理与慢性健康评分，用于 ICU 危重程度与病死风险分层。
      </p>

      <h3 className="mt-5 text-sm font-semibold text-neutral-800">一、急性生理评分（APS）</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block"><span className={labelCls}>体温（℃）</span>
          <input type="number" step="0.1" value={temp} onChange={(e) => setTemp(e.target.value)} className={inputCls} placeholder="如 38.5" /></label>
        <label className="block"><span className={labelCls}>MAP（mmHg）</span>
          <input type="number" value={map} onChange={(e) => setMap(e.target.value)} className={inputCls} placeholder="如 80" /></label>
        <label className="block"><span className={labelCls}>心率（次/分）</span>
          <input type="number" value={hr} onChange={(e) => setHr(e.target.value)} className={inputCls} placeholder="如 95" /></label>
        <label className="block"><span className={labelCls}>呼吸频率（次/分）</span>
          <input type="number" value={rr} onChange={(e) => setRr(e.target.value)} className={inputCls} placeholder="如 18" /></label>

        <div className="block">
          <span className={labelCls}>氧合（FiO₂ ≥ 0.5？）</span>
          <div className="mt-1 flex gap-2">
            <button type="button" onClick={() => setFio2High(false)}
              className={`flex-1 rounded-md border px-3 py-2 text-xs ${!fio2High ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600'}`}>FiO₂ &lt; 0.5（PaO₂）</button>
            <button type="button" onClick={() => setFio2High(true)}
              className={`flex-1 rounded-md border px-3 py-2 text-xs ${fio2High ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600'}`}>FiO₂ ≥ 0.5（A-aDO₂）</button>
          </div>
        </div>
        {fio2High ? (
          <label className="block"><span className={labelCls}>A-aDO₂（mmHg）</span>
            <input type="number" value={aado2} onChange={(e) => setAado2(e.target.value)} className={inputCls} placeholder="如 300" /></label>
        ) : (
          <label className="block"><span className={labelCls}>PaO₂（mmHg）</span>
            <input type="number" value={pao2} onChange={(e) => setPao2(e.target.value)} className={inputCls} placeholder="如 80" /></label>
        )}

        <label className="block"><span className={labelCls}>动脉血 pH</span>
          <input type="number" step="0.01" value={ph} onChange={(e) => setPh(e.target.value)} className={inputCls} placeholder="如 7.40" /></label>
        <label className="block"><span className={labelCls}>血钠 Na⁺（mmol/L）</span>
          <input type="number" value={na} onChange={(e) => setNa(e.target.value)} className={inputCls} placeholder="如 140" /></label>
        <label className="block"><span className={labelCls}>血钾 K⁺（mmol/L）</span>
          <input type="number" step="0.1" value={k} onChange={(e) => setK(e.target.value)} className={inputCls} placeholder="如 4.0" /></label>
        <label className="block"><span className={labelCls}>血肌酐（mg/dL）</span>
          <input type="number" step="0.1" value={cr} onChange={(e) => setCr(e.target.value)} className={inputCls} placeholder="如 1.0" /></label>
        <label className="block"><span className={labelCls}>血细胞比容 HCT（%）</span>
          <input type="number" value={hct} onChange={(e) => setHct(e.target.value)} className={inputCls} placeholder="如 38" /></label>
        <label className="block"><span className={labelCls}>白细胞 WBC（×10⁹/L）</span>
          <input type="number" step="0.1" value={wbc} onChange={(e) => setWbc(e.target.value)} className={inputCls} placeholder="如 8.0" /></label>
        <label className="block"><span className={labelCls}>GCS 评分（3-15）</span>
          <input type="number" min={3} max={15} value={gcs} onChange={(e) => setGcs(e.target.value)} className={inputCls} placeholder="15" /></label>
        <label className="flex items-center gap-2"><input type="checkbox" checked={arf} onChange={(e) => setArf(e.target.checked)} className="h-4 w-4 rounded border-neutral-300" />
          <span className="text-sm text-neutral-700">急性肾衰竭（肌酐分 ×2）</span></label>
      </div>

      <h3 className="mt-6 text-sm font-semibold text-neutral-800">二、年龄与慢性健康</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block"><span className={labelCls}>年龄（岁）</span>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className={inputCls} placeholder="如 60" /></label>
        <div className="block">
          <span className={labelCls}>慢性健康状态</span>
          <div className="mt-1 flex flex-col gap-1.5">
            {[
              { k: 'none', l: '无严重器官功能不全/免疫抑制' },
              { k: 'elective', l: '择期术后（+2 分）' },
              { k: 'nonsurgical', l: '非手术或急诊术后（+5 分）' },
            ].map((o) => (
              <button key={o.k} type="button" onClick={() => setChronic(o.k as any)}
                className={`rounded-md border px-3 py-1.5 text-left text-xs ${chronic === o.k ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'}`}>
                {o.l}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <button onClick={calc}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算 APACHE II
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">APACHE II 总分</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.total} / 71</div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded bg-white p-2"><div className="text-neutral-500">APS</div><div className="text-lg font-semibold">{result.aps}</div></div>
              <div className="rounded bg-white p-2"><div className="text-neutral-500">年龄</div><div className="text-lg font-semibold">{result.agePts}</div></div>
              <div className="rounded bg-white p-2"><div className="text-neutral-500">慢性健康</div><div className="text-lg font-semibold">{result.chp}</div></div>
            </div>
            <div className="mt-2 text-sm text-neutral-600">
              {result.total <= 9 ? '较轻，病死率较低' : result.total <= 19 ? '中度，病死率约 20-40%' : result.total <= 34 ? '重度，病死率约 40-75%' : '极重度，病死率 > 75%'}
            </div>
            {result.detail.length > 0 && (
              <div className="mt-2 flex flex-wrap justify-center gap-1.5">
                {result.detail.map((d) => <span key={d} className="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">{d}</span>)}
              </div>
            )}
          </div>
        </ResultCard>
      )}

      <Disclaimer />
    </div>
  );
}
```

## src/components/tools/CURB65.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * CURB-65 评分（社区获得性肺炎严重程度评估）
 * 每项 1 分，共 6 项：
 * C 意识障碍 / U 尿素>7mmol/L / R 呼吸频率≥30 / B 低血压(SBP<90或DBP≤60) / 65 年龄≥65
 */
export default function CURB65() {
  const [confusion, setConfusion] = useState(false);
  const [urea, setUrea] = useState(''); // mmol/L
  const [rr, setRr] = useState(''); // 次/分
  const [sbp, setSbp] = useState(''); // mmHg
  const [dbp, setDbp] = useState(''); // mmHg
  const [age, setAge] = useState(''); // 岁
  const [result, setResult] = useState<{ score: number; items: string[]; advice: string; mortality: string } | null>(null);

  function calculate() {
    let score = 0;
    const items: string[] = [];

    if (confusion) { score++; items.push('意识障碍 (C)'); }
    const u = parseFloat(urea);
    if (!isNaN(u) && u > 7) { score++; items.push('尿素 > 7 mmol/L (U)'); }
    const r = parseFloat(rr);
    if (!isNaN(r) && r >= 30) { score++; items.push('呼吸频率 ≥ 30 (R)'); }
    const s = parseFloat(sbp);
    const d = parseFloat(dbp);
    if ((!isNaN(s) && s < 90) || (!isNaN(d) && d <= 60)) { score++; items.push('低血压 SBP<90 或 DBP≤60 (B)'); }
    const a = parseFloat(age);
    if (!isNaN(a) && a >= 65) { score++; items.push('年龄 ≥ 65 (65)'); }

    let advice = '';
    let mortality = '';
    if (score <= 1) { advice = '低危，可考虑门诊治疗。'; mortality = '病死率约 1-3%。'; }
    else if (score === 2) { advice = '中危，建议住院或短期住院观察。'; mortality = '病死率约 9%。'; }
    else if (score === 3) { advice = '高危，应住院治疗，考虑 ICU。'; mortality = '病死率约 15-20%。'; }
    else { advice = '极高危，住院并强烈考虑 ICU。'; mortality = '病死率约 30-40%。'; }

    setResult({ score, items, advice, mortality });
  }

  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-xl font-bold text-neutral-900">CURB-65 评分</h2>
      <p className="mt-1 text-sm text-neutral-500">
        社区获得性肺炎（CAP）严重程度评估，指导门诊/住院/ICU 决策。
      </p>

      <div className="mt-5 grid gap-4">
        <label className="flex items-center gap-2 rounded-md border border-neutral-200 bg-neutral-50 p-3">
          <input type="checkbox" checked={confusion} onChange={(e) => setConfusion(e.target.checked)}
            className="h-4 w-4 rounded border-neutral-300" />
          <span className="text-sm text-neutral-700">意识障碍（新发精神错乱）<span className="text-neutral-400">(C)</span></span>
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">血尿素（mmol/L）<span className="text-neutral-400">(U)</span></span>
          <input type="number" step="0.1" value={urea} onChange={(e) => setUrea(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="> 7 计 1 分" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">呼吸频率（次/分）<span className="text-neutral-400">(R)</span></span>
          <input type="number" value={rr} onChange={(e) => setRr(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="≥ 30 计 1 分" />
        </label>
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">收缩压 SBP（mmHg）</span>
            <input type="number" value={sbp} onChange={(e) => setSbp(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="< 90 计 1 分" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">舒张压 DBP（mmHg）</span>
            <input type="number" value={dbp} onChange={(e) => setDbp(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="≤ 60 计 1 分" />
          </label>
        </div>
        <p className="-mt-2 text-xs text-neutral-400">血压项 (B)：SBP&lt;90 或 DBP≤60 任一项满足即计 1 分。</p>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">年龄（岁）<span className="text-neutral-400">(65)</span></span>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="≥ 65 计 1 分" />
        </label>
      </div>

      <button onClick={calculate}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算 CURB-65
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">CURB-65 总分</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.score} / 5</div>
            <div className="mt-3 text-sm font-semibold text-neutral-800">{result.advice}</div>
            <div className="mt-1 text-xs text-neutral-500">{result.mortality}</div>
            {result.items.length > 0 && (
              <div className="mt-3 flex flex-wrap justify-center gap-1.5">
                {result.items.map((it) => (
                  <span key={it} className="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">{it}</span>
                ))}
              </div>
            )}
          </div>
        </ResultCard>
      )}

      <Disclaimer />
    </div>
  );
}
```

## src/components/tools/CockcroftGault.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * Cockcroft-Gault 肌酐清除率公式（1973）
 * CrCl = ((140 - 年龄) × 体重) / (72 × Scr)
 * 女性 × 0.85
 */
export default function CockcroftGault() {
  const [age, setAge] = useState('');
  const [weight, setWeight] = useState('');
  const [scr, setScr] = useState(''); // mg/dL
  const [sex, setSex] = useState<'male' | 'female'>('male');
  const [result, setResult] = useState<{ crcl: number; stage: string } | null>(null);
  const [error, setError] = useState('');

  function calculate() {
    setError('');
    const a = parseFloat(age);
    const w = parseFloat(weight);
    const s = parseFloat(scr);

    if (!a || !w || !s) { setError('请填写所有数值'); return; }
    if (a < 1 || a > 120) { setError('年龄应在 1-120 岁之间'); return; }
    if (w < 30 || w > 200) { setError('体重应在 30-200 kg 之间'); return; }
    if (s <= 0 || s > 30) { setError('Scr 应在 0.1-30 mg/dL 之间'); return; }

    let crcl = ((140 - a) * w) / (72 * s);
    if (sex === 'female') crcl *= 0.85;
    crcl = Math.round(crcl * 10) / 10;

    let stage = '';
    if (crcl >= 90) stage = 'CKD 1 期（正常或增高）';
    else if (crcl >= 60) stage = 'CKD 2 期（轻度下降）';
    else if (crcl >= 45) stage = 'CKD 3a 期（轻中度下降）';
    else if (crcl >= 30) stage = 'CKD 3b 期（中重度下降）';
    else if (crcl >= 15) stage = 'CKD 4 期（重度下降）';
    else stage = 'CKD 5 期（肾衰竭）';

    setResult({ crcl, stage });
  }

  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-xl font-bold text-neutral-900">肌酐清除率（Cockcroft-Gault）</h2>
      <p className="mt-1 text-sm text-neutral-500">
        经典公式，建议使用标准 Scr（非 IDMS 校准）。用于肾功能评估与药物剂量调整。
      </p>

      <div className="mt-5 grid gap-4">
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">年龄（岁）</span>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 65" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">体重（kg）</span>
          <input type="number" step="0.1" value={weight} onChange={(e) => setWeight(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 70" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">血清肌酐（Scr, mg/dL）</span>
          <input type="number" step="0.01" value={scr} onChange={(e) => setScr(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 1.2" />
          <span className="mt-1 block text-xs text-neutral-400">μmol/L → mg/dL 转换：÷ 88.4</span>
        </label>
        <div>
          <span className="text-sm font-medium text-neutral-700">性别</span>
          <div className="mt-1 flex gap-2">
            {(['male', 'female'] as const).map((s) => (
              <button key={s} onClick={() => setSex(s)} type="button"
                className={`rounded-md border px-4 py-2 text-sm ${sex === s ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'}`}>
                {s === 'male' ? '男性' : '女性（× 0.85）'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <button onClick={calculate}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算 CrCl
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">肌酐清除率（CrCl）</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.crcl}</div>
            <div className="mt-1 text-sm text-neutral-600">mL/min / 1.73m²</div>
            <div className="mt-3 inline-block rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
              {result.stage}
            </div>
          </div>
        </ResultCard>
      )}

      <Disclaimer />

      <details className="mt-4 text-sm text-neutral-500">
        <summary className="cursor-pointer hover:text-neutral-700">公式与参考</summary>
        <div className="mt-2 rounded bg-neutral-50 p-3 text-xs leading-relaxed">
          <p><strong>公式：</strong>CrCl = ((140 - 年龄) × 体重 kg) / (72 × Scr mg/dL)</p>
          <p className="mt-1">女性结果 × 0.85；体重建议使用校正体重（IBW）或实际体重（取较小值）。</p>
        </div>
      </details>
    </div>
  );
}
```

## src/components/tools/EGFR.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * CKD-EPI 2021 eGFR 公式（更精准版本，基于 Scr）
 * https://www.kidney.org/professionals/guidelines/guidelines-diagnosis-and-management-of-chronic-kidney-disease
 */
export default function EGFR() {
  const [age, setAge] = useState('');
  const [scr, setScr] = useState(''); // mg/dL
  const [sex, setSex] = useState<'male' | 'female'>('male');
  const [black, setBlack] = useState(false);
  const [result, setResult] = useState<{ egfr: number; stage: string } | null>(null);
  const [error, setError] = useState('');

  function calculate() {
    setError('');
    const a = parseFloat(age);
    const s = parseFloat(scr);

    if (!a || !s) { setError('请填写所有数值'); return; }
    if (a < 1 || a > 120) { setError('年龄应在 1-120 岁之间'); return; }
    if (s <= 0 || s > 30) { setError('Scr 应在 0.1-30 mg/dL 之间'); return; }

    // CKD-EPI 2021
    const kappa = sex === 'female' ? 0.7 : 0.9;
    const alpha = sex === 'female' ? -0.241 : -0.302;
    const min = Math.min(s / kappa, 1);
    const max = Math.max(s / kappa, 1);

    let egfr = 142 * Math.pow(min, alpha) * Math.pow(max, -1.200) * Math.pow(0.9938, a);
    if (sex === 'female') egfr *= 1.012;
    if (black) egfr *= 1.159;

    egfr = Math.round(egfr);

    let stage = '';
    if (egfr >= 90) stage = 'G1 · 正常或升高';
    else if (egfr >= 60) stage = 'G2 · 轻度下降';
    else if (egfr >= 45) stage = 'G3a · 轻中度下降';
    else if (egfr >= 30) stage = 'G3b · 中重度下降';
    else if (egfr >= 15) stage = 'G4 · 重度下降';
    else stage = 'G5 · 肾衰竭';

    setResult({ egfr, stage });
  }

  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-xl font-bold text-neutral-900">eGFR（CKD-EPI 2021）</h2>
      <p className="mt-1 text-sm text-neutral-500">
        推荐公式，基于 IDMS 校准的 Scr，比 Cockcroft-Gault 更适合 eGFR 评估。
      </p>

      <div className="mt-5 grid gap-4">
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">年龄（岁）</span>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 55" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">血清肌酐（Scr, mg/dL）</span>
          <input type="number" step="0.01" value={scr} onChange={(e) => setScr(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 1.0" />
          <span className="mt-1 block text-xs text-neutral-400">μmol/L → mg/dL 转换：÷ 88.4</span>
        </label>
        <div>
          <span className="text-sm font-medium text-neutral-700">性别</span>
          <div className="mt-1 flex gap-2">
            {(['male', 'female'] as const).map((s) => (
              <button key={s} onClick={() => setSex(s)} type="button"
                className={`rounded-md border px-4 py-2 text-sm ${sex === s ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'}`}>
                {s === 'male' ? '男性' : '女性（× 1.012）'}
              </button>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={black} onChange={(e) => setBlack(e.target.checked)}
            className="h-4 w-4 rounded border-neutral-300" />
          <span className="text-sm text-neutral-700">黑人（× 1.159）</span>
        </label>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <button onClick={calculate}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算 eGFR
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">估算肾小球滤过率（eGFR）</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.egfr}</div>
            <div className="mt-1 text-sm text-neutral-600">mL/min / 1.73m²</div>
            <div className="mt-3 inline-block rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
              {result.stage}
            </div>
          </div>
        </ResultCard>
      )}

      <Disclaimer />
    </div>
  );
}
```

## src/components/tools/PFRatio.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

/**
 * PaO₂/FiO₂ 氧合指数（P/F 比）
 * P/F = PaO₂(mmHg) / FiO₂(小数)
 * 用于评估 ARDS（柏林定义分级）
 */
export default function PFRatio() {
  const [pao2, setPao2] = useState(''); // mmHg
  const [fio2, setFio2] = useState(''); // 百分比 21-100
  const [peep, setPeep] = useState('5'); // PEEP cmH2O
  const [result, setResult] = useState<{ pf: number; grade: string; note: string } | null>(null);
  const [error, setError] = useState('');

  function calculate() {
    setError('');
    const p = parseFloat(pao2);
    const f = parseFloat(fio2);

    if (!p || !f) { setError('请填写 PaO₂ 与 FiO₂'); return; }
    if (p < 20 || p > 800) { setError('PaO₂ 应在 20-800 mmHg 之间'); return; }
    if (f < 21 || f > 100) { setError('FiO₂ 应在 21-100% 之间'); return; }

    const pf = Math.round(p / (f / 100));

    let grade = '';
    let note = '';
    if (pf > 300) {
      grade = '正常 / 无 ARDS';
      note = 'P/F > 300，不符合 ARDS 诊断的氧合标准。';
    } else if (pf > 200) {
      grade = '轻度 ARDS';
      note = 'P/F 200-300，轻度 ARDS（需 PEEP/CPAP ≥ 5 cmH₂O）。';
    } else if (pf > 100) {
      grade = '中度 ARDS';
      note = 'P/F 100-200，中度 ARDS，建议肺保护性通气策略。';
    } else {
      grade = '重度 ARDS';
      note = 'P/F ≤ 100，重度 ARDS，病死率高，可能需考虑俯卧位/ECMO。';
    }

    setResult({ pf, grade, note });
  }

  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-xl font-bold text-neutral-900">PaO₂/FiO₂ 氧合指数</h2>
      <p className="mt-1 text-sm text-neutral-500">
        评估氧合功能与 ARDS 严重程度（柏林定义分级）。
      </p>

      <div className="mt-5 grid gap-4">
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">PaO₂（动脉血氧分压，mmHg）</span>
          <input type="number" step="1" value={pao2} onChange={(e) => setPao2(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 80" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">FiO₂（吸入氧浓度，%）</span>
          <input type="number" step="1" value={fio2} onChange={(e) => setFio2(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 40（表示 40% = 0.40）" />
          <span className="mt-1 block text-xs text-neutral-400">空气 21%，纯氧 100%。</span>
        </label>
        <label className="block">
          <span className="text-sm font-medium text-neutral-700">PEEP（cmH₂O，可选）</span>
          <input type="number" step="1" value={peep} onChange={(e) => setPeep(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="如 5" />
          <span className="mt-1 block text-xs text-neutral-400">仅用于 ARDS 分级参考（PEEP ≥ 5）。</span>
        </label>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <button onClick={calculate}
        className="mt-5 w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">
        计算氧合指数
      </button>

      {result && (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">P/F 氧合指数</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{result.pf}</div>
            <div className="mt-1 text-sm text-neutral-600">mmHg</div>
            <div className="mt-3 inline-block rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
              {result.grade}
            </div>
            <p className="mt-3 text-sm text-neutral-700">{result.note}</p>
          </div>
        </ResultCard>
      )}

      <Disclaimer />

      <details className="mt-4 text-sm text-neutral-500">
        <summary className="cursor-pointer hover:text-neutral-700">分级标准与参考</summary>
        <div className="mt-2 rounded bg-neutral-50 p-3 text-xs leading-relaxed">
          <p><strong>公式：</strong>P/F = PaO₂(mmHg) ÷ FiO₂(小数)</p>
          <p className="mt-1"><strong>柏林定义 ARDS 分级：</strong></p>
          <ul className="mt-1 list-inside list-disc">
            <li>轻度：200 &lt; P/F ≤ 300</li>
            <li>中度：100 &lt; P/F ≤ 200</li>
            <li>重度：P/F ≤ 100</li>
          </ul>
          <p className="mt-1">以上分级均需 PEEP/CPAP ≥ 5 cmH₂O。</p>
        </div>
      </details>
    </div>
  );
}
```

## src/components/tools/SOFA.tsx

```tsx
import { useState } from 'react';
import Disclaimer, { ResultCard } from './shared';

type ScoreMode = 'qsofa' | 'sofa';

export default function SOFA() {
  const [mode, setMode] = useState<ScoreMode>('qsofa');

  // === qSOFA ===
  const [rr, setRr] = useState(''); // 呼吸频率
  const [sbp, setSbp] = useState(''); // 收缩压
  const [gcs_q, setGcsQ] = useState('15'); // GCS

  // === SOFA ===
  const [spo2FiO2, setSpo2FiO2] = useState(''); // SpO2/FiO2（简化呼吸评分）
  const [platelets, setPlatelets] = useState(''); // ×10⁹/L
  const [bilirubin, setBilirubin] = useState(''); // mg/dL
  const [map, setMap] = useState(''); // 平均动脉压 mmHg
  const [gcs_s, setGcsS] = useState('15');
  const [scr, setScrSofa] = useState(''); // mg/dL
  const [uro] = useState(''); // mL/24h

  // SOFA 评分函数
  function sofaRespiratory(spo2fio2: number) {
    if (spo2fio2 >= 251) return 0;
    if (spo2fio2 >= 201) return 1;
    if (spo2fio2 >= 151) return 2;
    if (spo2fio2 >= 101) return 3;
    return 4;
  }
  function sofaCoagulation(plt: number) {
    if (plt >= 150) return 0;
    if (plt >= 100) return 1;
    if (plt >= 50) return 2;
    if (plt >= 20) return 3;
    return 4;
  }
  function sofaLiver(tbili: number) {
    if (tbili < 1.2) return 0;
    if (tbili < 2.0) return 1;
    if (tbili < 6.0) return 2;
    if (tbili < 12.0) return 3;
    return 4;
  }
  function sofaCardiovascular(mapVal: number) {
    return mapVal < 70 ? 1 : 0; // 简化：仅低血压项
  }
  function sofaNeurological(gcs: number) {
    if (gcs >= 15) return 0;
    if (gcs >= 13) return 1;
    if (gcs >= 10) return 2;
    if (gcs >= 6) return 3;
    return 4;
  }
  function sofaRenal(cr: number, uo: number) {
    // 取较高值
    let c = 0;
    if (cr >= 1.2 && cr < 2.0) c = Math.max(c, 1);
    else if (cr >= 2.0 && cr < 3.5) c = Math.max(c, 2);
    else if (cr >= 3.5 && cr < 5.0) c = Math.max(c, 3);
    else if (cr >= 5.0) c = Math.max(c, 4);

    if (uo > 0) {
      if (uo < 200) c = Math.max(c, 3);
      else if (uo < 500) c = Math.max(c, 2);
    }
    return c;
  }

  function calculate() {
    if (mode === 'qsofa') {
      const rr_n = parseFloat(rr);
      const sbp_n = parseFloat(sbp);
      const gcs_n = parseFloat(gcs_q);

      let s = 0;
      if (rr_n && (rr_n >= 22 || rr_n < 10)) s++;
      if (sbp_n && sbp_n <= 100) s++;
      if (gcs_n && gcs_n < 15) s++;
      return { mode: 'qsofa' as const, score: s };
    } else {
      const r = parseFloat(spo2FiO2);
      const pl = parseFloat(platelets);
      const bi = parseFloat(bilirubin);
      const mp = parseFloat(map);
      const gcs = parseFloat(gcs_s);
      const cr = parseFloat(scr);
      const ur = parseFloat(uro);

      let total = 0;
      if (!isNaN(r)) total += sofaRespiratory(r);
      if (!isNaN(pl)) total += sofaCoagulation(pl);
      if (!isNaN(bi)) total += sofaLiver(bi);
      if (!isNaN(mp)) total += sofaCardiovascular(mp);
      if (!isNaN(gcs)) total += sofaNeurological(gcs);
      if (!isNaN(cr) || !isNaN(ur)) {
        const c = !isNaN(cr) ? cr : 0;
        const u = !isNaN(ur) ? ur : 0;
        total += sofaRenal(c, u);
      }
      return { mode: 'sofa' as const, score: Math.min(total, 24) };
    }
  }

  const res = calculate();

  return (
    <div className="mx-auto max-w-xl">
      <div className="mb-4 flex gap-2">
        {(['qsofa', 'sofa'] as const).map((m) => (
          <button key={m} onClick={() => setMode(m)} type="button"
            className={`flex-1 rounded-md border px-4 py-2 text-sm font-medium ${mode === m ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'}`}>
            {m === 'qsofa' ? 'qSOFA（快速）' : 'SOFA（完整版）'}
          </button>
        ))}
      </div>

      {mode === 'qsofa' && (
        <div className="grid gap-4">
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">呼吸频率（次/分）</span>
            <input type="number" value={rr} onChange={(e) => setRr(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="≥ 22 或 < 10 计 1 分" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">收缩压（mmHg）</span>
            <input type="number" value={sbp} onChange={(e) => setSbp(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="≤ 100 计 1 分" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">GCS 评分（3-15）</span>
            <input type="number" value={gcs_q} onChange={(e) => setGcsQ(e.target.value)} min={3} max={15}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">GCS {"<"} 15 计 1 分</span>
          </label>
        </div>
      )}

      {mode === 'sofa' && (
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">SpO₂/FiO₂</span>
            <input type="number" value={spo2FiO2} onChange={(e) => setSpo2FiO2(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">呼吸：251/201/151/101 阈值</span>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">血小板（×10⁹/L）</span>
            <input type="number" value={platelets} onChange={(e) => setPlatelets(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">凝血：150/100/50/20 阈值</span>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">总胆红素（mg/dL）</span>
            <input type="number" step="0.1" value={bilirubin} onChange={(e) => setBilirubin(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">肝脏：1.2/2.0/6.0/12.0 阈值</span>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">MAP（mmHg）</span>
            <input type="number" value={map} onChange={(e) => setMap(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">心血管：{"<"} 70 mmHg 计 1 分</span>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">GCS（3-15）</span>
            <input type="number" value={gcs_s} onChange={(e) => setGcsS(e.target.value)} min={3} max={15}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">神经：15/13/10/6 阈值</span>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-neutral-700">Scr（mg/dL）</span>
            <input type="number" step="0.01" value={scr} onChange={(e) => setScrSofa(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-blue-500 focus:outline-none" />
            <span className="mt-1 block text-xs text-neutral-400">肾脏：1.2/2.0/3.5/5.0 阈值</span>
          </label>
        </div>
      )}

      {res.mode === 'qsofa' ? (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">qSOFA 评分</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{res.score}</div>
            <div className="mt-2 text-sm text-neutral-600">
              {res.score >= 2 ? '⚠ 高风险，疑似感染请立即启动脓毒症处理！' : res.score === 1 ? '提示项存在，需进一步评估' : '低风险'}
            </div>
          </div>
        </ResultCard>
      ) : (
        <ResultCard>
          <div className="text-center">
            <div className="text-sm text-neutral-600">SOFA 总分</div>
            <div className="mt-1 text-4xl font-bold text-blue-700">{res.score} / 24</div>
            <div className="mt-2 text-sm text-neutral-600">
              {res.score <= 5 ? '一般' : res.score <= 10 ? '中度' : res.score <= 15 ? '重度' : '极重度 · 极高病死率风险'}
            </div>
          </div>
        </ResultCard>
      )}

      <Disclaimer />
    </div>
  );
}
```

## src/components/tools/shared.tsx

```tsx
// 免责声明组件（供所有临床计算器共享）
import type { ReactNode } from 'react';

export default function Disclaimer() {
  return (
    <div className="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
      <strong className="block text-amber-900">⚠ 安全声明</strong>
      <p className="mt-1 leading-relaxed">
        本工具完全在您的浏览器本地运行，不收集、不存储、不上传任何患者输入数据，可完全离线使用。
        计算结果仅供专业学术参考，<strong>不能替代临床决策</strong>。
        实际临床应用请结合患者具体情况，必要时参考药品说明书和权威指南，并严格执行 TDM 监测。
      </p>
    </div>
  );
}

// 通用结果卡片
export function ResultCard({ children }: { children: ReactNode }) {
  return (
    <div className="mt-6 rounded-xl border-2 border-blue-500 bg-blue-50 p-5">
      {children}
    </div>
  );
}
```

## src/content.config.ts

```ts
import { defineCollection, z } from 'astro:content';

// 抗感染指南与临床证据：Markdown 知识库（人工维护，受保护）
// 多维分类架构对齐 Evidence Navigator 体系（PRD 7.1 / 7.2）
const guides = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      title: z.string(),                          // 指南/证据名称
      organization: z.string(),                   // 发布组织（如 IDSA/ATS/中华医学会）
      year: z.number(),                           // 发布年份
      version: z.string(),                        // 版本号
      sourceUrl: z.string().url().optional(),      // 原文链接（raw_materials 本地解析可缺省）
      reviewDate: z.string(),                     // 整理审核日期（ISO，如 2026-11-01）

      // —— 多维分类（均为多选标签）——

      // 1) 指南共识（Type）：指南 / 专家共识 / 推荐依据
      docType: z.array(z.string()).default([]),
      // 2) 致病菌与耐药菌（Pathogen / Resistance）
      //    真菌类 + 耐药菌类 + 混合感染
      pathogens: z.array(z.string()).default([]),
      // 3) 感染部位与临床场景（Infection Site / Scene）
      infectionSites: z.array(z.string()).default([]),
      // 4) 特殊人群与器官支持（Special Population）：CRRT / ECMO / ARDS
      specialPopulations: z.array(z.string()).default([]),
      // 5) 医学影像与诊断（Imaging & Diagnosis）：肺部 CT / 影像鉴别 / TDM
      imagingDiagnosis: z.array(z.string()).default([]),
      // 6) 疗效与安全性比较（Comparison Dimensions）
      comparisons: z.array(z.string()).default([]),

      // —— 兼容旧字段 ——
      syndromes: z.array(z.string()).default([]), // 适用综合征/临床问题
      antibioticClasses: z.array(z.string()).default([]), // 抗菌药物分类
      tags: z.array(z.string()).default([]),      // 标签
      description: z.string().default(''),        // 摘要
      cover: image().optional(),                  // 封面图（可选）
      draft: z.boolean().default(false),          // 草稿标记
    }),
});

// 药品说明书：Markdown 知识库（人工维护，受保护）
// 字段严格对齐 PRD 第 8.1 节【确定】要求
const drugLabels = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      drugName: z.string(),                        // 通用名
      brandNames: z.array(z.string()).default([]), // 商品名（可选多个）
      manufacturer: z.string(),                    // 生产企业
      dosageForm: z.string(),                      // 剂型（如：注射剂、片剂）
      strengths: z.array(z.string()).nonempty(),   // 规格（如：["500mg/支", "1g/支"]）
      atcCode: z.string().default(''),             // ATC 分类代码
      antibioticClass: z.string().default(''),     // 抗菌药物分类
      indications: z.array(z.string()).nonempty(), // 适应证
      contraindications: z.array(z.string()).default([]), // 禁忌
      specialPopulations: z.array(z.string()).default([]), // 特殊人群（妊娠/哺乳/儿童/老年）
      renalAdjustment: z.boolean().default(false), // 是否需肾功能调整
      hepaticAdjustment: z.boolean().default(false), // 是否需肝功能调整
      drugInteractions: z.array(z.string()).default([]), // 药物相互作用
      preparation: z.string().default(''),         // 给药配置说明（如溶媒、浓度、滴速）
      sourceUrl: z.string().url().optional(),      // 原文链接（NMPA 或制药商公开）
      reviewDate: z.string(),                      // 整理审核日期
      tags: z.array(z.string()).default([]),
      description: z.string().default(''),
      cover: image().optional(),
      draft: z.boolean().default(false),
    }),
});

export const collections = {
  guides,
  'drug-labels': drugLabels,
};
```

## src/content/drug-labels/TEMPLATE.md

```markdown
---
drugName: "药品通用名"
brandNames:
  - "商品名（可选）"
manufacturer: "生产企业"
dosageForm: "剂型（如：注射剂、片剂、胶囊剂）"
strengths:
  - "规格（如：500mg/支）"
atcCode: "ATC 代码（可选）"
antibioticClass: "抗菌药物分类（如：β-内酰胺类）"
indications:
  - "适应证 1"
  - "适应证 2"
contraindications:
  - "禁忌 1"
specialPopulations:
  - "妊娠：分级与建议"
  - "哺乳：建议"
  - "儿童：用法"
  - "老年：注意事项"
renalAdjustment: true
hepaticAdjustment: false
drugInteractions:
  - "主要相互作用及机制"
preparation: "给药配置说明（溶媒、浓度、滴速、配伍禁忌）"
sourceUrl: "https://example.com/label"
reviewDate: "2026-11-01"
tags:
  - "标签"
description: "一句话摘要"
draft: true
---

## 一、药品概述

简述作用机制、抗菌谱与主要特点。

## 二、适应证

完整列出官方批准的适应证，必要时补充循证依据。

## 三、用法用量

### 成人常用剂量

| 适应证 | 剂量 | 给药方式 | 疗程 |
|--------|------|---------|------|
|  |  |  |  |

### 特殊人群剂量调整

详细说明肾/肝功能不全、妊娠、儿童、老年的剂量调整方案。

## 四、禁忌

完整列出禁忌证。

## 五、不良反应

常见不良反应及其处理原则。

## 六、药物相互作用

与常见药物的相互作用机制与临床建议。

## 七、给药配置

- 溶媒选择
- 最终浓度
- 滴注时间
- 配伍禁忌

## 八、超说明书用法

**必须标注权威依据**（指南/共识/临床研究），并说明适用条件与风险。

| 超说明书用法 | 依据来源 | 证据等级 | 注意事项 |
|------------|---------|---------|---------|
|  |  |  |  |

---

> 本内容为人工整理的药品说明书摘要，仅供专业学术参考，不能替代临床决策与药品说明书原文。超说明书用法存在风险，请严格评估患者情况并征得知情同意。
```

## src/content/drug-labels/amphotericin-b-cholesterol.md

```markdown
---
drugName: "注射用两性霉素B胆固醇硫酸酯复合物"
brandNames:
  - "ABelcet"
manufacturer: "Enzon Pharmaceuticals"
dosageForm: "注射用无菌粉末"
strengths:
  - "50 mg"
atcCode: "J02AA01"
antibioticClass: "多烯类抗真菌药"
indications:
  - "本品适用于患有深部真菌感染的患者"
  - "因肾损伤或药物毒性而不能使用有效剂量的两性"
  - "霉素B的患者，或已经接受过两性霉素B治疗无效的患者均可使用。"
contraindications:
  - "本品禁用于对其中任何成份过敏的患者"
  - "除非医生认为使用本品的益处大于过敏带来的"
  - "危险时，这些有过敏史的患者才能使用本品"
specialPopulations:
  - "妊娠/哺乳：妊娠 胎儿致畸性（B类妊娠）：无孕妇使用本品的报告。在生殖系统实验中，给大鼠使用相 当于人体推荐剂量的0.4倍、对兔使用相当于人体推荐剂量的1.1倍的本品，无发现对胎儿有 害的证据。因为动物生殖实验不能完全预见人的反应，同时未对孕妇进行严格试验，故本品 只有在预见的益处大于对胎儿的潜在危险时才可在怀"
  - "儿童：97例患有深部真菌感染的儿童患者，以同成人的日剂量(mg/kg)相仿的剂量使用本品， 未报导有意外的不良反应。"
  - "老年：用本品治疗了68例65岁以上的患者，未报发生意外的不良反应。"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "尚未对本品进行正式的药物相互作用试验。目前已知下列药物与普通两性霉素B同时使"
  - "用时发生药物相互作用，这些药物可能亦与本品发生相互作用。"
  - "抗肿瘤药 抗肿瘤药物与普通两性霉素B同时使用可能导致增加肾毒性、支气管痉挛和"
  - "低血压的可能性。因而，当抗肿瘤药与本品同时给药时需慎重。"
  - "皮质类固醇和促肾上腺皮质激素（ACTH） 它们与普通两性霉素B同时使用可能降低"
  - "血钾并导致心脏功能异常。若它们与本品同时使用，应该监测血清电解质和心脏功能。"
  - "环胞菌素 在比较本品和普通两性霉素B对血清肌酐值的发热和中性白细胞减少的患"
  - "者进行经验治疗的随机双盲试验中，对使用环胞菌素或免疫抑制剂的患者进行分组，在各种"
preparation: "详见说明书原文"
sourceUrl: "https://www.abelcet.com"
reviewDate: "2026-11-09"
tags:
  - "多烯类抗真菌药"
description: "注射用两性霉素B胆固醇硫酸酯复合物，多烯类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用两性霉素B胆固醇硫酸酯复合物，多烯类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品适用于患有深部真菌感染的患者
- 因肾损伤或药物毒性而不能使用有效剂量的两性
- 霉素B的患者，或已经接受过两性霉素B治疗无效的患者均可使用。

## 三、用法用量

第1页/共8页
对于成年人和儿童，根据要求可按3.0～4.0mg/kg/天的剂量使用。若无改善或真菌感染
恶化，剂量可增至6 mg/kg/天。
将溶解（必须用无菌注射用水重溶）的本品用5%葡萄糖注射液稀释，以1 mg/kg/小时的
速度作静脉注射。在每一个疗程的第一次用药前建议作试验注射，以少量药（10 ml稀释液
含有1.6～8.3mg）用15～30 分钟注射。再仔细观察30分钟。
如果患者可以忍受并无与输注有关的反应，则输注时间可缩短至不少于2小时，如果患
者出现急性反应或不能耐受输液容积，则输注时间要延长。
药品溶解与输注液准备的说明
本品必须用无菌注射用水溶解，用无菌注射器和20号针头，按下述体积迅速加入瓶中，
用手轻轻摇动和转动使所有固体溶解。注意液体可能呈乳色或透明。
50mg/瓶加10ml无菌注射用水。
本品采用10ml无菌注射用水复溶后浓度为4.75mg/ml，整瓶可转移剂量为50mg/瓶，非整
瓶转移时定量抽取体积需以复溶后浓度4.75mg/ml折算。
如用于输注，进一步稀释上述溶解好的液体至终浓度约为0.6 mg/m（l 0.16～0.83 mg/ml）。
下表是稀释的建议（稀释只能用5%葡萄糖注射液）：
注射用两性霉素B胆固醇硫酸酯复合物剂量 5%注射用葡萄糖输注袋体积
10～35 mg 50 ml
35～70 mg 100 ml
70～175 mg 250 ml
175～300 mg 500 ml
350～1000 mg 1000 ml
不要使用生理盐水或葡萄糖溶液来溶解冻干粉，也不要将溶解好的溶液与生理盐水或电
解质混合。使用除上述建议溶液以外的其它溶液或是有杀菌剂（即苯甲醇）存在时，药液中
的本品可能导致出现沉淀。使用本品时，请不要过滤或使用有内置过滤器的输液器。
不要将输注液与其它药物混合。如通过正在使用的输液管，在给药前用5%葡萄糖冲洗
输液管，或使用单独的输液管。
注射用药在用药前要用肉眼检查是否有异物或变色。不要使用有沉淀或异物、或者原瓶
密封有问题的药品。由于冻干粉和用于溶解与稀释的溶液不含有防腐剂，配制药液时必须始
终严格无菌操作。
在用5%葡萄糖注射液进一步稀释后，药液须存于2～8℃并于24小时内使用，禁止冷冻，
未用完的药液必须丢弃。

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 七、禁忌

- 本品禁用于对其中任何成份过敏的患者
- 除非医生认为使用本品的益处大于过敏带来的
- 危险时，这些有过敏史的患者才能使用本品

## 八、特殊人群

- 妊娠/哺乳：妊娠
胎儿致畸性（B类妊娠）：无孕妇使用本品的报告。在生殖系统实验中，给大鼠使用相
当于人体推荐剂量的0.4倍、对兔使用相当于人体推荐剂量的1.1倍的本品，无发现对胎儿有
害的证据。因为动物生殖实验不能完全预见人的反应，同时未对孕妇进行严格试验，故本品
只有在预见的益处大于对胎儿的潜在危险时才可在怀
- 儿童：97例患有深部真菌感染的儿童患者，以同成人的日剂量(mg/kg)相仿的剂量使用本品，
未报导有意外的不良反应。
- 老年：用本品治疗了68例65岁以上的患者，未报发生意外的不良反应。

## 九、药物相互作用

- 尚未对本品进行正式的药物相互作用试验。目前已知下列药物与普通两性霉素B同时使
- 用时发生药物相互作用，这些药物可能亦与本品发生相互作用。
- 抗肿瘤药 抗肿瘤药物与普通两性霉素B同时使用可能导致增加肾毒性、支气管痉挛和
- 低血压的可能性。因而，当抗肿瘤药与本品同时给药时需慎重。
- 皮质类固醇和促肾上腺皮质激素（ACTH） 它们与普通两性霉素B同时使用可能降低
- 血钾并导致心脏功能异常。若它们与本品同时使用，应该监测血清电解质和心脏功能。
- 环胞菌素 在比较本品和普通两性霉素B对血清肌酐值的发热和中性白细胞减少的患
- 者进行经验治疗的随机双盲试验中，对使用环胞菌素或免疫抑制剂的患者进行分组，在各种

## 十、注意事项

本品应静脉给药。与输药过程中有关的急性反应包括发热、发冷、低血压、恶心或心动
过速。这些反应通常在开始输药后1～3小时出现，这些反应在头几次给药时较为严重和频繁，
第4页/共8页
以后会逐步消失。与输注有关的急性反应可以事先通过使用抗组胺和皮质类固醇来预防或/
和降低输注速度和迅速使用抗组胺和皮质类固醇来处理（见【不良反应】）。应避免快速输
注。
按患者反应情况，应对患者进行监测，特别是对肝功能、肾功能、血清电解质、全血细
胞计数及凝血酶原反应时间等进行监测。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/amphotericin-b-liposome.md

```markdown
---
drugName: "注射用两性霉素B脂质体"
brandNames:
  - "AmBisome"
manufacturer: "Gilead Sciences"
dosageForm: "注射用无菌粉末"
strengths:
  - "50 mg"
atcCode: "J02AA01"
antibioticClass: "多烯类抗真菌药"
indications:
  - "本品适用于成人和1个月至18岁的儿童："
  - "第1页/共14页"
  - "• 治疗敏感真菌引起的系统性真菌感染，如隐球菌病、北美芽生菌病、播散性念"
  - "珠菌病、球孢子菌病、曲霉病、组织胞浆菌病、毛霉菌病，也用于治疗美洲粘膜皮肤利"
  - "什曼病。"
  - "• 治疗不明原因发热且高度提示存在系统性真菌感染的中性粒细胞减少症患者。"
  - "在开始本品治疗前，应尽可能排除常见病毒、寄生虫或分枝杆菌感染导致不明原因发热"
  - "的可能。"
  - "• 免疫功能正常的成人和儿童内脏利什曼病患者的主要治疗药物。也可作为免疫"
  - "功能受损（如人类免疫缺陷病毒[HIV]阳性）的内脏利什曼病患者的主要治疗药物，但初"
contraindications:
  - "禁用于对本品活性成份或任何辅料有超敏反应的患者，除非医生认为该患者患有必"
  - "须治疗的、危及生命的且仅本品可以治疗的疾病"
  - "本品含豆油"
  - "如果您对花生或大豆过敏，请勿使用本品"
specialPopulations:
  - "妊娠/哺乳：生育力：根据大鼠和兔的致畸性研究结论，在这些动物中本品没有致畸可能性。 妊娠：尚未确定本品在妊娠女性中的安全性。仅当潜在获益大于对母亲和胎儿的潜 在风险时，才可在妊娠期间使用本品。 曾使用普通两性霉素 B 成功治疗了妊娠女性的全身性真菌感染，对胎儿无明显影 响，但所报告的病例数不足以得出任何关于本品"
  - "儿童：儿童患者中本品药效学特征与成人患者一致。在1个月至18岁儿童患者中开展了 临床研究。与成人相同，儿童也应按照每Kg体重计算剂量。尚未确定本品在不满1个 月婴儿中的安全性和疗效（参见【用法用量】）。"
  - "老年：无需改变剂量或给药频率。与大多数其他药物一样，应对接受本品的老年患者进行 仔细监测。"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "）。由于存在低钾血症风"
  - "险，应用本品治疗过程中可能需要适当补钾。如果出现有临床意义的肾功能下降或其他"
  - "参数恶化，则应考虑减少剂量、中断给药或停止治疗。"
  - "有报告显示，在白细胞输注期间或输注后较短时间患者接受两性霉素B（以脱氧胆"
  - "酸钠复合物的形式）给药出现了急性肺毒性。建议两种物质输注间隔时间尽可能地延长，"
  - "并应监测肺功能。"
  - "第8页/共14页"
  - "应注意，本品每瓶约含900 mg蔗糖。"
preparation: "详见说明书原文"
sourceUrl: "https://www.ambisome.com"
reviewDate: "2026-11-09"
tags:
  - "多烯类抗真菌药"
description: "注射用两性霉素B脂质体，多烯类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用两性霉素B脂质体，多烯类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品适用于成人和1个月至18岁的儿童：
- 第1页/共14页
- • 治疗敏感真菌引起的系统性真菌感染，如隐球菌病、北美芽生菌病、播散性念
- 珠菌病、球孢子菌病、曲霉病、组织胞浆菌病、毛霉菌病，也用于治疗美洲粘膜皮肤利
- 什曼病。
- • 治疗不明原因发热且高度提示存在系统性真菌感染的中性粒细胞减少症患者。
- 在开始本品治疗前，应尽可能排除常见病毒、寄生虫或分枝杆菌感染导致不明原因发热
- 的可能。
- • 免疫功能正常的成人和儿童内脏利什曼病患者的主要治疗药物。也可作为免疫
- 功能受损（如人类免疫缺陷病毒[HIV]阳性）的内脏利什曼病患者的主要治疗药物，但初

## 三、用法用量

不同两性霉素产品在药效学、药代动力学和给药剂量方面不具有等效性，本品不能与
其他两性霉素产品互换使用。
成人患者
必须根据每位患者的具体情况调整给药剂量。
1.治疗系统性真菌感染
通常初始治疗的剂量为1.0 mg/kg/天，根据需要逐步增加剂量至3.0 mg/kg/天。典型
的累积剂量为：3至4周内1.0-3.0g。
毛霉菌病：初始治疗剂量为5 mg/kg，每日一次。治疗持续时间应根据个体确定。临
床实践中通常使用长达56天的疗程。在有深部感染、长期化疗或中性粒细胞减少症患者
中，可能需要更长的治疗持续时间。
大于5 mg/kg的剂量已经用于临床试验和临床实践中。使用这种高剂量治疗毛霉菌
病的安全性和有效性数据有限，因此，应该进行个体化的获益/风险评估，确定较高剂量
治疗的潜在获益是否大于已知的毒性增加风险（参见【注意事项】）。
2.治疗中性粒细胞减少症患者的不明原因发热
初始治疗剂量为1.0 mg/kg/天，如果有指征可将剂量增加至3 mg/kg/天。
3.治疗内脏利什曼病
可使用1.0-1.5 mg/kg/天的剂量持续给药21天，或者以3.0 mg/kg/天的剂量持续给药
10天。在免疫功能受损患者（如HIV阳性）中，可使用1.0至1.5 mg/kg/天的剂量持续给
药21天，由于存在复发风险，可能需要维持治疗或再诱导治疗。
儿童人群
在儿童患者中，使用本品已成功治疗系统性真菌感染和不明原因发热，没有报告特
殊的不良事件。在 1 个月至 18 岁儿童患者中开展了临床研究，儿童使用剂量应按照与
第2页/共14页
成人相同的每 kg 体重进行计算。尚未确定 1 个月以下婴儿使用本品治疗的安全性和有
效性。
老年人群
无需改变剂量或给药频率。
肾功能损害
在临床试验中，有肾功能损害患者使用本品1-5 mg/kg/天的经验，肾功能损害患者
无需调整剂量或给药频率（参见【注意事项】）。
肝功能损害
尚无为肝功能损害患者提供给药建议的数据（参见【注意事项】）。
给药方法
应缓慢输注测试剂量 (1 mg) 10 分钟，随后仔细观察患者 30 分钟。
本品应静脉输注给药，输注时长为30-60分钟。剂量大于5 mg/kg/天时，推荐的静脉
输注时长为 2 小时（参见【注意事项】）。推荐的静脉输注浓度为 0.20 mg/mL 至 2.00
mg/mL（参见【注意事项】）。
有关在给药前复溶和稀释本品的详细说明，请参见如下信息。
本品必须用不含杀菌剂的无菌注射用水复溶，只能使用浓度为 5%、10%或 20%的
输注用葡萄糖溶液进行稀释。如使用上述建议溶液以外的其它溶液或是有杀菌剂（如苯
甲醇）存在时，药液中的本品可能导致出现沉淀。
本品与生理盐水不相容，不要使用生理盐水进行复溶或稀释，也不要使用已经输注
过盐水的静脉输液导管进行给药。如果通过正在使用的输液管，在给药前用浓度为5%、
10%或20%的输注用葡萄糖溶液冲洗输液管。如不能冲洗，应该使用单独的静脉输液导
管给予本品。
不得将本品与其他药物或电解质混合。
因为本品及其复溶的溶液、稀释溶液中均不含有防腐剂或杀菌剂，所以配置药液时
必须始终严格无菌操作。
本品50mg装小瓶复溶和稀释的制备过程
1. 每瓶（50 mg）加入12mL上述无菌注射用水，以制备浓度为4 mg/mL两
性霉素B浓溶液；
2. 加入无菌注射用水后，立即充分震摇小瓶30秒使本品完全分散。复溶浓
溶液为半透明黄色分散液。目测瓶中是否有颗粒物质，继续摇动直至完全分散。
如果有异物的沉淀现象请勿使用。
3. 根据最终静脉输注液浓度计算出需要进一步稀释的两性霉素B复溶浓溶
液的体积（可参照表1）。
4. 静脉输注液可通过用浓度为5%、10%或20%的输注用葡萄糖溶液稀释复
溶浓溶液获得。按照体积比使用的葡萄糖溶液的体积可为复溶浓溶液体积的1
倍至19倍，最终输注液浓度应在推荐范围0.20 mg/mL至2.00 mg/mL之内（可
参照表1）。
第3页/共14页
5. 用无菌注射器抽取上述已计算得出的复溶浓溶液体积，使用本品随附5微
米孔径的一次性使用配药用过滤器，确保将注满复溶浓溶液的注射器和滤器的
内鲁尔接头拧紧在一起，将复溶浓溶液注入已装正确容量的浓度为5%、10%或
20%输注用葡萄糖溶液的无菌容器中用于制备完成输注液。
精密过滤输液器可以用于本品的静脉输注，但是在线过滤器平均孔径不得小于1.0
微米。
本品输注液的制备（以剂量为3mg/kg/天为例）
表1列举了用5%的输注用葡萄糖溶液制备本品剂量3mg/kg/天输注液的计算方
法。需要注意的是，表1仅适用于3mg/kg/天的剂量，医生也可能为患者处方其它剂
量，对于不是3mg/kg/天的其它剂量需要进行相应的计算，不能直接使用下表。
表 1. 用浓度为5%的输注葡萄糖溶

## 四、肾功能调整

肾功能损害
在临床试验中，有肾功能损害患者使用本品1-5 mg/kg/天的经验，肾功能损害患者
无需调整剂量或给药频率（参见【注意事项】）。
肝功能损害
尚无为肝功能损害患者提供给药建议的数据（参见【注意事项】）。
给药方法
应缓慢输注测试剂量 (1 mg) 10 分钟，随后仔细观察患者 30 分钟。
本品应静脉输注给药，输注时长为30-60分钟。剂量大于5 mg/kg/天时，推荐的静脉
输注时长为 2 小时（参见【注意事项】）。推荐的静脉输注浓度为 0.20 mg/mL 至 2.00
mg/mL（参见【注意事项】）。
有关在给药前复溶和稀释本品的详细说明，请参见如下信息。
本品必须用不含杀菌剂的无菌注射用水复溶，只能使用浓度为 5%、10%或 20%的
输注用葡萄糖溶液进行稀释。如使用上述建议溶液以外的其它溶液或是有杀菌剂（如苯
甲醇）存在时，药液中的本品可能导致出现沉淀。
本品与生理盐水不相容，不要使用生理盐水进行复溶或稀释，也不要使用已经输注
过盐水的静脉输液导管进行给药。如果通过正在使用的输液管，在给药前用浓度为5%、
10%或20%的输注用葡萄糖溶液冲洗输液管。如不能冲洗，应该使用单独的静脉输液导
管给予本品。
不得将本品与其他药物或电解质混合。
因为本品及其复溶的溶液、稀释溶液中均不含有防腐剂或杀菌剂，所以配置药液时
必须始终严格无菌操作。
本品50mg装小瓶复溶和稀释的制备过程
1. 每瓶（50 mg）加入12mL上述无菌注射用水，以制备浓度为4 mg/mL两
性霉素B浓溶液；
2. 加入无菌注射用水后，立即充分震摇小瓶30秒使本品完全分散。复溶浓
溶液为半透明黄色分散液。目测瓶中是否有颗粒物质，继续摇动直至完全分散。
如果有异物的沉淀现象请勿使用。
3. 根据最终静脉输注液浓度计算出需要进一步稀释的两性霉素B复溶浓溶
液的体积（可参照表1）。
4. 静脉输注液可通过用浓度为5%、10%或20%的输注用葡萄糖溶液稀释复
溶浓溶液获得。按照体积比使用的葡萄糖溶液的体积可为复溶浓溶液体积的1
倍至19倍，最终输注液浓度应在推荐范围0.20 mg/mL至2.00 mg/mL之内（可
参照表1）。
第3页/共14页
5. 用无菌注射器抽取上述已计算得出的复溶浓溶液体积，使用本品随附5微
米孔径的一次性使用配药用过滤器，确保将注满复溶浓溶液的注射器和滤器的
内鲁

## 五、肝功能调整

肝功能损害
尚无为肝功能损害患者提供给药建议的数据（参见【注意事项】）。
给药方法
应缓慢输注测试剂量 (1 mg) 10 分钟，随后仔细观察患者 30 分钟。
本品应静脉输注给药，输注时长为30-60分钟。剂量大于5 mg/kg/天时，推荐的静脉
输注时长为 2 小时（参见【注意事项】）。推荐的静脉输注浓度为 0.20 mg/mL 至 2.00
mg/mL（参见【注意事项】）。
有关在给药前复溶和稀释本品的详细说明，请参见如下信息。
本品必须用不含杀菌剂的无菌注射用水复溶，只能使用浓度为 5%、10%或 20%的
输注用葡萄糖溶液进行稀释。如使用上述建议溶液以外的其它溶液或是有杀菌剂（如苯
甲醇）存在时，药液中的本品可能导致出现沉淀。
本品与生理盐水不相容，不要使用生理盐水进行复溶或稀释，也不要使用已经输注
过盐水的静脉输液导管进行给药。如果通过正在使用的输液管，在给药前用浓度为5%、
10%或20%的输注用葡萄糖溶液冲洗输液管。如不能冲洗，应该使用单独的静脉输液导
管给予本品。
不得将本品与其他药物或电解质混合。
因为本品及其复溶的溶液、稀释溶液中均不含有防腐剂或杀菌剂，所以配置药液时
必须始终严格无菌操作。
本品50mg装小瓶复溶和稀释的制备过程
1. 每瓶（50 mg）加入12mL上述无菌注射用水，以制备浓度为4 mg/mL两
性霉素B浓溶液；
2. 加入无菌注射用水后，立即充分震摇小瓶30秒使本品完全分散。复溶浓
溶液为半透明黄色分散液。目测瓶中是否有颗粒物质，继续摇动直至完全分散。
如果有异物的沉淀现象请勿使用。
3. 根据最终静脉输注液浓度计算出需要进一步稀释的两性霉素B复溶浓溶
液的体积（可参照表1）。
4. 静脉输注液可通过用浓度为5%、10%或20%的输注用葡萄糖溶液稀释复
溶浓溶液获得。按照体积比使用的葡萄糖溶液的体积可为复溶浓溶液体积的1
倍至19倍，最终输注液浓度应在推荐范围0.20 mg/mL至2.00 mg/mL之内（可
参照表1）。
第3页/共14页
5. 用无菌注射器抽取上述已计算得出的复溶浓溶液体积，使用本品随附5微
米孔径的一次性使用配药用过滤器，确保将注满复溶浓溶液的注射器和滤器的
内鲁尔接头拧紧在一起，将复溶浓溶液注入已装正确容量的浓度为5%、10%或
20%输注用葡萄糖溶液的无菌容器中用于制备完成输注液。
精密过滤输液器可

## 七、禁忌

- 禁用于对本品活性成份或任何辅料有超敏反应的患者，除非医生认为该患者患有必
- 须治疗的、危及生命的且仅本品可以治疗的疾病
- 本品含豆油
- 如果您对花生或大豆过敏，请勿使用本品

## 八、特殊人群

- 妊娠/哺乳：生育力：根据大鼠和兔的致畸性研究结论，在这些动物中本品没有致畸可能性。
妊娠：尚未确定本品在妊娠女性中的安全性。仅当潜在获益大于对母亲和胎儿的潜
在风险时，才可在妊娠期间使用本品。
曾使用普通两性霉素 B 成功治疗了妊娠女性的全身性真菌感染，对胎儿无明显影
响，但所报告的病例数不足以得出任何关于本品
- 儿童：儿童患者中本品药效学特征与成人患者一致。在1个月至18岁儿童患者中开展了
临床研究。与成人相同，儿童也应按照每Kg体重计算剂量。尚未确定本品在不满1个
月婴儿中的安全性和疗效（参见【用法用量】）。
- 老年：无需改变剂量或给药频率。与大多数其他药物一样，应对接受本品的老年患者进行
仔细监测。

## 九、药物相互作用

- ）。由于存在低钾血症风
- 险，应用本品治疗过程中可能需要适当补钾。如果出现有临床意义的肾功能下降或其他
- 参数恶化，则应考虑减少剂量、中断给药或停止治疗。
- 有报告显示，在白细胞输注期间或输注后较短时间患者接受两性霉素B（以脱氧胆
- 酸钠复合物的形式）给药出现了急性肺毒性。建议两种物质输注间隔时间尽可能地延长，
- 并应监测肺功能。
- 第8页/共14页
- 应注意，本品每瓶约含900 mg蔗糖。

## 十、注意事项

）。
2.治疗中性粒细胞减少症患者的不明原因发热
初始治疗剂量为1.0 mg/kg/天，如果有指征可将剂量增加至3 mg/kg/天。
3.治疗内脏利什曼病
可使用1.0-1.5 mg/kg/天的剂量持续给药21天，或者以3.0 mg/kg/天的剂量持续给药
10天。在免疫功能受损患者（如HIV阳性）中，可使用1.0至1.5 mg/kg/天的剂量持续给
药21天，由于存在复发风险，可能需要维持治疗或再诱导治疗。
儿童人群
在儿童患者中，使用本品已成功治疗系统性真菌感染和不明原因发热，没有报告特
殊的不良事件。在 1 个月至 18 岁儿童患者中开展了临床研究，儿童使用剂量应按照与
第2页/共14页
成人相同的每 kg 体重进行计算。尚未确定 1 个月以下婴儿使用本品治疗的安全性和有
效性。
老年人群
无需改变剂量或给药频率。
肾功能损害
在临床试验中，有肾功能损害患者使用本品1-5 mg/kg/天的经验，肾功能损害患者
无需调整剂量或给药频率（参见【注意事项】）。
肝功能损害
尚无为肝功能损害患者提供给药建议的数据（参见【注意事项】）。
给药方法
应缓慢输注测试剂量 (1 mg) 10 分钟，随后仔细观察患者 30 分钟。
本品应静脉输注给药，输注时长为30-60分钟。剂量大于5 mg/kg/天时，推荐的静脉
输注时长为 2 小时（参见【注意事项】）。推荐的静脉输注浓度为 0.20 mg/mL 至 2.00
mg/mL（参见【注意事项】）。
有关在给药前复溶和稀释本品的详细说明，请参见如下信息。
本品必须用不含杀菌剂的无菌注射用水复溶，只能使用浓度为 5%、10%或 20%的
输注用葡萄糖溶液进行稀释。如使用上述建议溶液以外的其它溶液或是有杀菌剂（如苯
甲醇）存在时，药液中的本品可能导致出现沉淀。
本品与生理盐水不相容，不要使用生理盐水进行复溶或稀释，也不要使用已经输注
过盐水的静脉输液导管进行给药。如果通过正在使用的输液管，在给药前用浓度为5%、
10%或20%的输注用葡萄糖溶液冲洗输液管。如不能冲洗，应该使用单独的静脉输液导
管给予本品。
不得将本品与其他药物或电解质混合。
因为本品及其复溶的溶液、稀释溶液中均不含有防腐剂或杀菌剂，所以配置药液时
必须始终严格无菌操作。
本品50mg装小瓶复溶和稀释的制备过程
1. 每瓶（50 mg）加入12mL上述无菌注射用水，以制备浓度为4 mg/mL两
性霉素B浓溶液；
2. 加入无菌注射用水后，立即充分震摇小瓶30秒使本品完全分散。复溶浓
溶液为半透明黄色分散液。目测瓶中是否有颗粒物质，继续摇动直至完全分散。
如果有异物的沉淀现象请勿使用。
3. 根据最终静脉输注液浓度计算出需要进一步稀释的两性霉素B复溶浓溶
液的体积（可参照表1）。
4. 静脉输注液可通过用浓度为5%、10%或20%的输注用葡萄糖溶液稀释复
溶浓溶液获得。按照体积比使用的葡萄糖溶液的体积可为复溶浓溶液体积的1
倍至19倍，最终输注液浓度应在推荐范围0.20 mg/mL至2.00 mg/mL之内（可
参照表1）。
第3页/共14页
5. 用无菌注射器抽取上述已计算得出的复溶浓溶液体积，使用本品随附5微
米孔径的一次性使用配药用过滤器，确保将注满复溶浓溶液的注射器和滤器的
内鲁尔接头拧紧在一起，将复溶浓溶液注入已装正确容量的浓度为5%、10%或
20%输注用葡萄糖溶液的无菌容器中用于制备完成输注液。
精密过滤输液器可以用于本品的静脉输注，但是在线过滤器平均孔径不得小于1.0
微米。
本品输注液的制备（以剂量为3mg/kg/天为例）
表1列举

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/aztreonam-avibactam.md

```markdown
---
drugName: "注射用氨曲南阿维巴坦钠"
brandNames:
  - "Emblaveo"
manufacturer: "辉瑞 / AbbVie"
dosageForm: "注射用无菌粉末"
strengths:
  - "2.0g"
  - "1.5g"
  - "0.5g"
atcCode: "J01DF51"
antibioticClass: "单环β-内酰胺/β-内酰胺酶抑制剂复合制剂"
indications:
  - "本品适用于治疗18岁及以上患者治疗药物选择有限或无替代治疗的下列感染："
  - "1、复杂性腹腔内感染（cIAI）"
  - "本品适用于与甲硝唑联合治疗由下列敏感革兰阴性菌引起的治疗药物选择有限或"
  - "无替代治疗的复杂性腹腔内感染：大肠埃希菌、肺炎克雷伯菌、产酸克雷伯菌、阴沟肠"
  - "杆菌复合群、弗劳地枸橼酸杆菌复合群、粘质沙雷菌和奇异变形杆菌。该适应症的批准"
  - "基于本品有限的临床安全性和有效性数据 （见【临床试验】）。"
  - "2、医院获得性肺炎（HAP），包括呼吸机相关性肺炎（VAP）"
  - "本品适用于由下列敏感革兰阴性菌引起的治疗药物选择有限或无替代治疗的医院"
  - "获得性肺炎和呼吸机相关性肺炎：肺炎克雷伯菌、阴沟肠杆菌复合群、大肠埃希菌、粘"
  - "质沙雷菌、产酸克雷伯菌、嗜麦芽窄食单胞菌、奇异变形杆菌、摩氏摩根菌。该适应症"
contraindications:
  - "对活性成份或任何辅料过敏的患者"
  - "对任何其他β-内酰胺类抗生素（如青霉素类、头孢菌素类或碳青霉烯类）有严重超"
  - "敏反应（如过敏反应、严重皮肤反应）的患者"
specialPopulations:
  - "妊娠/哺乳：孕妇 尚无或仅有有限的妊娠女性使用氨曲南或阿维巴坦的数据。氨曲南在动物研究中没 有显示对于生殖毒性方面有直接或间接的不良影响（见【药理毒理】）。阿维巴坦在动物 研究中显示出了生殖毒性，但没有致畸作用的证据（见【药理毒理】）。 妊娠期间，仅在有明确指征且母亲获益大于对胎儿的风险时，才能使用本品。 哺乳"
  - "儿童：尚未确定18岁以下儿童患者使用本品的安全性和疗效。尚无相关数据。"
  - "老年：在II期和 III期临床试验中，本品治疗组有103例65岁及以上的患者，其中60例 （58%）年龄在65-74岁之间，43例（42%）在75岁及以上。与之相比，本品治疗组有 202例年龄小于65岁的患者。本品的临床研究未纳入足够数量年龄≥ 65岁的患者，因 此不能确定该人群对药物的应答是否与年轻患者"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "在体外，氨曲南和阿维巴坦是有机阴离子转运蛋白 OAT1 和 OAT3 的底物，"
  - "OAT1/OAT3可介导药物从血液中的摄取和经肾脏排泄过程。在体外研究中，丙磺舒（一"
  - "种强效 OAT 抑制剂）对阿维巴坦摄取过程的抑制率可达 56%到 70%。因此，合用可能"
  - "改变阿维巴坦的清除。尚未进行氨曲南-阿维巴坦和丙磺舒临床相互作用进行研究，故不"
  - "推荐本品与丙磺舒合并给药。"
  - "氨曲南不会被细胞色素P450酶代谢。在体外，阿维巴坦对细胞色素P450酶无明显"
  - "抑制作用，在临床相关暴露量范围内对细胞色素 P450 无诱导作用。在体外研究中，临"
  - "床相关暴露量范围内，阿维巴坦对主要的肾脏或肝脏转运蛋白无抑制作用。因此，由这"
preparation: "详见说明书原文"
sourceUrl: "https://www.pfizer.com"
reviewDate: "2026-11-09"
tags:
  - "单环β-内酰胺/β-内酰胺酶抑制剂复合制剂"
description: "注射用氨曲南阿维巴坦钠（Emblaveo），单环β-内酰胺/β-内酰胺酶抑制剂复合制剂，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用氨曲南/阿维巴坦（Emblaveo），单环β-内酰胺/β-内酰胺酶抑制剂复合制剂。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品适用于治疗18岁及以上患者治疗药物选择有限或无替代治疗的下列感染：
- 1、复杂性腹腔内感染（cIAI）
- 本品适用于与甲硝唑联合治疗由下列敏感革兰阴性菌引起的治疗药物选择有限或
- 无替代治疗的复杂性腹腔内感染：大肠埃希菌、肺炎克雷伯菌、产酸克雷伯菌、阴沟肠
- 杆菌复合群、弗劳地枸橼酸杆菌复合群、粘质沙雷菌和奇异变形杆菌。该适应症的批准
- 基于本品有限的临床安全性和有效性数据 （见【临床试验】）。
- 2、医院获得性肺炎（HAP），包括呼吸机相关性肺炎（VAP）
- 本品适用于由下列敏感革兰阴性菌引起的治疗药物选择有限或无替代治疗的医院
- 获得性肺炎和呼吸机相关性肺炎：肺炎克雷伯菌、阴沟肠杆菌复合群、大肠埃希菌、粘
- 质沙雷菌、产酸克雷伯菌、嗜麦芽窄食单胞菌、奇异变形杆菌、摩氏摩根菌。该适应症

## 三、用法用量

剂量
估计肌酐清除率（eCrCL）> 50 mL/min的成人患者推荐剂量
表 1 列出了估计肌酐清除率（eCrCL）> 50 mL/min 的患者接受静脉输注的推荐剂
量。单次负荷剂量后，在下一个给药间隔开始维持剂量。
表1. eCrCLa> 50 mL/min的成人患者根据感染类型推荐的静脉输注剂量
氨曲南-阿维巴坦的剂量
感染类型 输注时间 给药间隔b 疗程
负荷剂量 维持治疗
氨曲南2g/ 氨曲南1.5g/ 每6小时
cIAIc 3小时 5~14天
阿维巴坦0.67g 阿维巴坦0.5g 1次
HAP，包括 氨曲南2g/ 氨曲南1.5g/ 每6小时
3小时 7~14天
VAP 阿维巴坦0.67g 阿维巴坦0.5g 1次
a 使用Cockcroft-Gault公式计算。
b 给药间隔计算为一次输注开始到下一次输注开始。
c 治疗cIAI时，同时给予甲硝唑。
估计肌酐清除率（eCrCL）≤50 mL/min的成人患者推荐剂量
表 2 列出了估计肌酐清除率（eCrCL）≤ 50 mL/min 的患者接受静脉输注的推荐剂
量。单次负荷剂量后，在下一个给药间隔开始维持剂量。在肾功能损害患者中，建议密
切监测估计肌酐清除率（见【注意事项】和【临床药理】）。在一些患者中，根据血清肌
酐估计的 CrCL 变化很快，尤其是在感染治疗的早期。治疗 cIAI 时，同时给予甲硝唑。
cIAI疗程为5~14 天，HAP（包括 VAP）疗程为7~14 天。
表2. eCrCL ≤ 50 mL/min的成人患者推荐剂量
氨曲南-阿维巴坦的剂量b
eCrCL (mL/min)a 输注时间 给药间隔c
负荷剂量 维持治疗
氨曲南2g/ 氨曲南0.75g/ 每6小时
> 30至≤ 50 3小时
阿维巴坦0.67g 阿维巴坦0.25g 1次
氨曲南1.35g/ 氨曲南0.675g/ 每8小时
> 15至≤ 30 3小时
阿维巴坦0.45g 阿维巴坦0.225g 1次
≤ 15 mL/min且进
氨曲南1g/ 氨曲南0.675g/ 每12小时
行间歇性血液透析 3小时
阿维巴坦0.33g 阿维巴坦0.225g 1次
患者d,e
a 使用Cockcroft-Gault公式计算。
b 剂量推荐基于PK建模和模拟。
c 给药间隔计算为一次输注开始到下一次输注开始。
d 氨曲南和阿维巴坦均可被血液透析清除。因此，血液透析当天，应在血液透析结束后给
予本品。
e 除非已经开始血液透析或其他形式的肾脏替代疗法，否则eCrCl ≤ 15 mL/min的患者不应
使用本品。
现有数据不足以为接受血液透析以外的肾脏替代治疗（例如，连续性静脉-静脉血液
滤过或腹膜透析）患者提供剂量调整建议。与接受血液透析的患者相比，接受连续性肾
脏替代治疗（CRRT）的患者需要更高的剂量。对于接受连续性肾脏替代治疗的患者，应

根据CRRT清除率（CLCRRT，单位为mL/min）调整剂量。
肝功能损害患者
肝功能损害患者无需调整剂量（见【临床药理】）。
给药方式
本品仅可通过静脉输注。静脉输注3小时。
在输液袋中制备成人剂量的操作说明
注：以下程序说明了最终浓度为1.5 ~ 40 mg/mL氨曲南和0.50 ~ 13.3 mg/mL阿维
巴坦的输注溶液制备步骤。应在开始这些步骤之前完成所有计算。
1. 制备复溶溶液（131.2mg/mL氨曲南和43.7 mg/mL阿维巴坦）
a) 将注射器针头插入瓶盖，并注入10 mL无菌注射用水。
b) 取出针头，轻轻振摇小瓶，得到澄清、无色至黄色的溶液，无可见异物。
2. 配制用于输注的最终溶液（最终浓度必须为氨曲南1.5 ~ 40 mg/mL和阿维巴坦0.50
~ 13.3 mg/mL）
输液袋：经准确计算，取一定体积的复溶溶液转移至含有 0.9%氯化钠注射液、5%
葡萄糖注射液或乳酸钠林格注射液的输液袋中，进一步稀释复溶溶液。
制备不同剂量可参阅下表3。

表3. 在输液袋中制备成人剂量的氨曲南-阿维巴坦
总剂量 从复溶小瓶中抽出的体积 输液袋中稀释后的最终体积a,b
（氨曲南-阿维巴坦）
2000 mg/667 mg 15.2 mL 50 mL至250 mL
1500 mg/500 mg 11.4 mL 50 mL至250 mL
1350 mg/450 mg 10.3 mL 50 mL至250 mL
750 mg/250 mg 5.7 mL 50 mL至250 mL
675 mg/225 mg 5.1 mL 50 mL至250 mL
所有其他剂量 根据所需剂量计算体积 体积（mL）视输液袋可用规格
（mL）： 和首选最终浓度而异
（必须为氨曲南1.5 ~
剂量（mg氨曲南）÷ 40mg/mL和阿维巴坦0.50~
131.2mg/mL氨曲南 13.3m

## 四、肾功能调整

肾功能损害患者中，建议密
切监测估计肌酐清除率（见【注意事项】和【临床药理】）。在一些患者中，根据血清肌
酐估计的 CrCL 变化很快，尤其是在感染治疗的早期。治疗 cIAI 时，同时给予甲硝唑。
cIAI疗程为5~14 天，HAP（包括 VAP）疗程为7~14 天。
表2. eCrCL ≤ 50 mL/min的成人患者推荐剂量
氨曲南-阿维巴坦的剂量b
eCrCL (mL/min)a 输注时间 给药间隔c
负荷剂量 维持治疗
氨曲南2g/ 氨曲南0.75g/ 每6小时
> 30至≤ 50 3小时
阿维巴坦0.67g 阿维巴坦0.25g 1次
氨曲南1.35g/ 氨曲南0.675g/ 每8小时
> 15至≤ 30 3小时
阿维巴坦0.45g 阿维巴坦0.225g 1次
≤ 15 mL/min且进
氨曲南1g/ 氨曲南0.675g/ 每12小时
行间歇性血液透析 3小时
阿维巴坦0.33g 阿维巴坦0.225g 1次
患者d,e
a 使用Cockcroft-Gault公式计算。
b 剂量推荐基于PK建模和模拟。
c 给药间隔计算为一次输注开始到下一次输注开始。
d 氨曲南和阿维巴坦均可被血液透析清除。因此，血液透析当天，应在血液透析结束后给
予本品。
e 除非已经开始血液透析或其他形式的肾脏替代疗法，否则eCrCl ≤ 15 mL/min的患者不应
使用本品。
现有数据不足以为接受血液透析以外的肾脏替代治疗（例如，连续性静脉-静脉血液
滤过或腹膜透析）患者提供剂量调整建议。与接受血液透析的患者相比，接受连续性肾
脏替代治疗（CRRT）的患者需要更高的剂量。对于接受连续性肾脏替代治疗的患者，应

根据CRRT清除率（CLCRRT，单位为mL/min）调整剂量。
肝功能损害患者
肝功能损害患者无需调整剂量（见【临床药理】）。
给药方式
本品仅可通过静脉输注。静脉输注3小时。
在输液袋中制备成人剂量的操作说明
注：以下程序说明了最终浓度为1.5 ~ 40 mg/mL氨曲南和0.50 ~ 13.3 mg/mL阿维
巴坦的输注溶液制备步骤。应在开始这些步骤之前完成所有计算。
1. 制备复溶溶液（131.2mg/mL氨曲南和43.7 mg/mL阿维巴坦）
a) 将注射器针头插入瓶盖，并注入10 mL无菌注射用水。
b) 取出针头，轻轻振摇小瓶，得到澄清、无色至黄色的溶液，无可见异

## 五、肝功能调整

肝功能损害患者
肝功能损害患者无需调整剂量（见【临床药理】）。
给药方式
本品仅可通过静脉输注。静脉输注3小时。
在输液袋中制备成人剂量的操作说明
注：以下程序说明了最终浓度为1.5 ~ 40 mg/mL氨曲南和0.50 ~ 13.3 mg/mL阿维
巴坦的输注溶液制备步骤。应在开始这些步骤之前完成所有计算。
1. 制备复溶溶液（131.2mg/mL氨曲南和43.7 mg/mL阿维巴坦）
a) 将注射器针头插入瓶盖，并注入10 mL无菌注射用水。
b) 取出针头，轻轻振摇小瓶，得到澄清、无色至黄色的溶液，无可见异物。
2. 配制用于输注的最终溶液（最终浓度必须为氨曲南1.5 ~ 40 mg/mL和阿维巴坦0.50
~ 13.3 mg/mL）
输液袋：经准确计算，取一定体积的复溶溶液转移至含有 0.9%氯化钠注射液、5%
葡萄糖注射液或乳酸钠林格注射液的输液袋中，进一步稀释复溶溶液。
制备不同剂量可参阅下表3。

表3. 在输液袋中制备成人剂量的氨曲南-阿维巴坦
总剂量 从复溶小瓶中抽出的体积 输液袋中稀释后的最终体积a,b
（氨曲南-阿维巴坦）
2000 mg/667 mg 15.2 mL 50 mL至250 mL
1500 mg/500 mg 11.4 mL 50 mL至250 mL
1350 mg/450 mg 10.3 mL 50 mL至250 mL
750 mg/250 mg 5.7 mL 50 mL至250 mL
675 mg/225 mg 5.1 mL 50 mL至250 mL
所有其他剂量 根据所需剂量计算体积 体积（mL）视输液袋可用规格
（mL）： 和首选最终浓度而异
（必须为氨曲南1.5 ~
剂量（mg氨曲南）÷ 40mg/mL和阿维巴坦0.50~
131.2mg/mL氨曲南 13.3mg/mL）
或
剂量（mg阿维巴坦）÷
43.7 mg/mL阿维巴坦
a 在含有 0.9%氯化钠注射液或乳酸钠林格注射液的输液袋中，稀释至氨曲南最终浓度
为1.5~ 40 mg/mL（阿维巴坦最终浓度为0.50~ 13.3 mg/mL），对应的使用中稳定性
在2℃~ 8℃最多放置24小时，后续在30℃下最多放置12小时。
b 在含有5%葡萄糖注射液的输液袋中，稀释直至氨曲南最终浓度为1.5 ~40 mg/mL（阿
维巴坦最终浓度为0.50~ 13.3 mg/mL）

## 六、治疗药物监测（TDM）

药峰浓度(C )和24小时药时曲线下面积(AUC )分别为54.2 mg/L (40.8)和11.0 mg/L

## 七、禁忌

- 对活性成份或任何辅料过敏的患者
- 对任何其他β-内酰胺类抗生素（如青霉素类、头孢菌素类或碳青霉烯类）有严重超
- 敏反应（如过敏反应、严重皮肤反应）的患者

## 八、特殊人群

- 妊娠/哺乳：孕妇
尚无或仅有有限的妊娠女性使用氨曲南或阿维巴坦的数据。氨曲南在动物研究中没
有显示对于生殖毒性方面有直接或间接的不良影响（见【药理毒理】）。阿维巴坦在动物
研究中显示出了生殖毒性，但没有致畸作用的证据（见【药理毒理】）。
妊娠期间，仅在有明确指征且母亲获益大于对胎儿的风险时，才能使用本品。
哺乳
- 儿童：尚未确定18岁以下儿童患者使用本品的安全性和疗效。尚无相关数据。
- 老年：在II期和 III期临床试验中，本品治疗组有103例65岁及以上的患者，其中60例
（58%）年龄在65-74岁之间，43例（42%）在75岁及以上。与之相比，本品治疗组有
202例年龄小于65岁的患者。本品的临床研究未纳入足够数量年龄≥ 65岁的患者，因
此不能确定该人群对药物的应答是否与年轻患者

## 九、药物相互作用

- 在体外，氨曲南和阿维巴坦是有机阴离子转运蛋白 OAT1 和 OAT3 的底物，
- OAT1/OAT3可介导药物从血液中的摄取和经肾脏排泄过程。在体外研究中，丙磺舒（一
- 种强效 OAT 抑制剂）对阿维巴坦摄取过程的抑制率可达 56%到 70%。因此，合用可能
- 改变阿维巴坦的清除。尚未进行氨曲南-阿维巴坦和丙磺舒临床相互作用进行研究，故不
- 推荐本品与丙磺舒合并给药。
- 氨曲南不会被细胞色素P450酶代谢。在体外，阿维巴坦对细胞色素P450酶无明显
- 抑制作用，在临床相关暴露量范围内对细胞色素 P450 无诱导作用。在体外研究中，临
- 床相关暴露量范围内，阿维巴坦对主要的肾脏或肝脏转运蛋白无抑制作用。因此，由这

## 十、注意事项

和【临床药理】）。在一些患者中，根据血清肌
酐估计的 CrCL 变化很快，尤其是在感染治疗的早期。治疗 cIAI 时，同时给予甲硝唑。
cIAI疗程为5~14 天，HAP（包括 VAP）疗程为7~14 天。
表2. eCrCL ≤ 50 mL/min的成人患者推荐剂量
氨曲南-阿维巴坦的剂量b
eCrCL (mL/min)a 输注时间 给药间隔c
负荷剂量 维持治疗
氨曲南2g/ 氨曲南0.75g/ 每6小时
> 30至≤ 50 3小时
阿维巴坦0.67g 阿维巴坦0.25g 1次
氨曲南1.35g/ 氨曲南0.675g/ 每8小时
> 15至≤ 30 3小时
阿维巴坦0.45g 阿维巴坦0.225g 1次
≤ 15 mL/min且进
氨曲南1g/ 氨曲南0.675g/ 每12小时
行间歇性血液透析 3小时
阿维巴坦0.33g 阿维巴坦0.225g 1次
患者d,e
a 使用Cockcroft-Gault公式计算。
b 剂量推荐基于PK建模和模拟。
c 给药间隔计算为一次输注开始到下一次输注开始。
d 氨曲南和阿维巴坦均可被血液透析清除。因此，血液透析当天，应在血液透析结束后给
予本品。
e 除非已经开始血液透析或其他形式的肾脏替代疗法，否则eCrCl ≤ 15 mL/min的患者不应
使用本品。
现有数据不足以为接受血液透析以外的肾脏替代治疗（例如，连续性静脉-静脉血液
滤过或腹膜透析）患者提供剂量调整建议。与接受血液透析的患者相比，接受连续性肾
脏替代治疗（CRRT）的患者需要更高的剂量。对于接受连续性肾脏替代治疗的患者，应

根据CRRT清除率（CLCRRT，单位为mL/min）调整剂量。
肝功能损害患者
肝功能损害患者无需调整剂量（见【临床药理】）。
给药方式
本品仅可通过静脉输注。静脉输注3小时。
在输液袋中制备成人剂量的操作说明
注：以下程序说明了最终浓度为1.5 ~ 40 mg/mL氨曲南和0.50 ~ 13.3 mg/mL阿维
巴坦的输注溶液制备步骤。应在开始这些步骤之前完成所有计算。
1. 制备复溶溶液（131.2mg/mL氨曲南和43.7 mg/mL阿维巴坦）
a) 将注射器针头插入瓶盖，并注入10 mL无菌注射用水。
b) 取出针头，轻轻振摇小瓶，得到澄清、无色至黄色的溶液，无可见异物。
2. 配制用于输注的最终溶液（最终浓度必须为氨曲南1.5 ~ 40 mg/mL和阿维巴坦0.50
~ 13.3 mg/mL）
输液袋：经准确计算，取一定体积的复溶溶液转移至含有 0.9%氯化钠注射液、5%
葡萄糖注射液或乳酸钠林格注射液的输液袋中，进一步稀释复溶溶液。
制备不同剂量可参阅下表3。

表3. 在输液袋中制备成人剂量的氨曲南-阿维巴坦
总剂量 从复溶小瓶中抽出的体积 输液袋中稀释后的最终体积a,b
（氨曲南-阿维巴坦）
2000 mg/667 mg 15.2 mL 50 mL至250 mL
1500 mg/500 mg 11.4 mL 50 mL至250 mL
1350 mg/450 mg 10.3 mL 50 mL至250 mL
750 mg/250 mg 5.7 mL 50 mL至250 mL
675 mg/225 mg 5.1 mL 50 mL至250 mL
所有其他剂量 根据所需剂量计算体积 体积（mL）视输液袋可用规格
（mL）： 和首选最终浓度而异
（必须为氨曲南1.5 ~
剂量（mg氨曲南）÷ 40mg/mL和阿维巴坦0.50~
131.2mg/mL氨曲南 13.3mg/mL）
或
剂量（mg阿维巴坦）÷
43.7

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/ceftazidime-avibactam.md

```markdown
---
drugName: "注射用头孢他啶阿维巴坦钠"
brandNames:
  - "思福妥®"
  - "Zavicefta®"
manufacturer: "百时美施贵宝 / 阿斯利康"
dosageForm: "注射用无菌粉末"
strengths:
  - "2.5g"
  - "2.0g"
  - "0.5g"
atcCode: "J01DI52"
antibioticClass: "β-内酰胺酶抑制剂复合制剂（三代头孢）"
indications:
  - "1、复杂性腹腔内感染（cIAI）"
  - "本品适用于联合甲硝唑治疗成人和3月龄及以上儿童患者中由下列对本品敏感的"
  - "革兰阴性菌引起的复杂性腹腔内感染：大肠埃希菌、肺炎克雷伯菌、奇异变形杆菌、"
  - "阴沟肠杆菌、产酸克雷伯菌、弗氏柠檬酸杆菌复合体和铜绿假单胞菌。"
  - "2、医院获得性肺炎和呼吸机相关性肺炎（HAP/VAP）"
  - "本品适用于治疗 18 岁及以上患者中由下列对本品敏感的革兰阴性菌引起的医院"
  - "获得性肺炎和呼吸机相关性肺炎：肺炎克雷伯菌、阴沟肠杆菌、大肠埃希菌、粘质沙"
  - "雷菌、奇异变形杆菌、铜绿假单胞菌和流感嗜血杆菌。"
  - "3、在治疗方案选择有限的成人患者中治疗由下列对本品敏感的革兰阴性菌引起"
  - "的感染：肺炎克雷伯菌、阴沟肠杆菌、大肠埃希菌、奇异变形杆菌和铜绿假单胞菌。"
contraindications:
  - "对活性物质或【成份】项中列出的任何辅料过敏者"
  - "对头孢菌素类抗菌药物过敏者"
  - "对其他类型β-内酰胺类抗菌药物（如青霉素、单酰胺菌素或碳青霉烯类）的严重"
  - "超敏者（例如速发严重过敏反应、严重皮肤反应）"
specialPopulations:
  - "妊娠/哺乳：孕妇 风险总结 尚未在孕妇中进行具有充分且良好对照的本品、头孢他啶或阿维巴坦研究。大鼠 中头孢他啶和阿维巴坦给药剂量为人用临床推荐剂量的 40 和 9 倍时未引起致畸性。 兔中本品暴露量为人用临床剂量所引起暴露量的2倍时未影响胚胎-胎仔发育。 尚不清楚在目标人群中的重大出生缺陷和流产的背景风险。在普"
  - "儿童：本品在3月龄以下的儿童患者中的安全性和有效性尚未确定。无可用数据。"
  - "老年：在 II和 III期临床试验中（2024 例），本品治疗组≥65岁患者占32.7%（661/2024 例），其中≥75岁占15.5%（314/2024例）。 在II和 III期cIAI临床试验整合分析中，本品治疗组≥65岁患者占19.6%（168/857 例），其中≥75岁占7.1%（61/857例"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "在体外，阿维巴坦对细胞色素 P450 酶无明显的抑制作用。临床相关浓度的阿维"
  - "巴坦和头孢他啶在体外对细胞色素 P450 无诱导作用。在临床相关的暴露范围内，阿"
  - "维巴坦和头孢他啶不会抑制主要的肾脏或肝脏转运蛋白，因此认为可能通过这些机制"
  - "引起的相互作用很小。"
  - "在体外，人肝微粒体中临床相关浓度的阿维巴坦不会抑制细胞色素 P450 同工酶"
  - "CYP1A2、CYP2A6、CYP2B6、CYP2C8、CYP2C9、CYP2C19、CYP2D6、CYP2E1 和"
  - "CYP3A4/5。在体外人肝细胞中阿维巴坦无诱导 CYP1A2/2B6/2C9 和 3A4 的能力。超"
  - "过临床相关暴露量的极高浓度阿维巴坦对CYP2E1 有轻微的诱导能力。在人肝细胞中"
preparation: "详见说明书原文"
sourceUrl: "https://www.astrazeneca.com"
reviewDate: "2026-11-09"
tags:
  - "β-内酰胺酶抑制剂复合制剂（三代头孢）"
description: "注射用头孢他啶阿维巴坦钠，β-内酰胺酶抑制剂复合制剂（三代头孢），说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用头孢他啶阿维巴坦钠，β-内酰胺酶抑制剂复合制剂（三代头孢）。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 1、复杂性腹腔内感染（cIAI）
- 本品适用于联合甲硝唑治疗成人和3月龄及以上儿童患者中由下列对本品敏感的
- 革兰阴性菌引起的复杂性腹腔内感染：大肠埃希菌、肺炎克雷伯菌、奇异变形杆菌、
- 阴沟肠杆菌、产酸克雷伯菌、弗氏柠檬酸杆菌复合体和铜绿假单胞菌。
- 2、医院获得性肺炎和呼吸机相关性肺炎（HAP/VAP）
- 本品适用于治疗 18 岁及以上患者中由下列对本品敏感的革兰阴性菌引起的医院
- 获得性肺炎和呼吸机相关性肺炎：肺炎克雷伯菌、阴沟肠杆菌、大肠埃希菌、粘质沙
- 雷菌、奇异变形杆菌、铜绿假单胞菌和流感嗜血杆菌。
- 3、在治疗方案选择有限的成人患者中治疗由下列对本品敏感的革兰阴性菌引起
- 的感染：肺炎克雷伯菌、阴沟肠杆菌、大肠埃希菌、奇异变形杆菌和铜绿假单胞菌。

## 三、用法用量

剂量
肌酐清除率(CrCL) >50 mL/min的成人患者剂量
表1中显示了估计肌酐清除率（eCrCL）>50mL/min成人患者中推荐的静脉给药
剂量1（见【注意事项】和【临床药理】）。
表1 按适应症总结的本品在估计肌酐清除率 (eCrCL)1 >50 mL/min 成人患者中的
给药剂量
感染 剂量 给药频率 输注时间 疗程
(头孢他啶/阿 （小时）
维巴坦)
复杂性腹腔内感染2,3[与 2.5g(2 g/0.5 g) 每8小时1次 2 5~14天
甲硝唑联用]
医院获得性肺炎和呼吸 2.5g(2 g/0.5 g) 每8小时1次 2 7~14天
机相关性肺炎3
治疗方案选择有限的成 2.5g(2 g/0.5 g) 每8小时1次 2 取决于感染的严
人患者中需氧型革兰阴 重程度、病原
性菌引起的感染 2,3 菌、患者的临床
情况和细菌学进
展4
1使用Cockcroft-Gault公式估算CrCL。
2如果已知或疑似厌氧菌也与感染过程有关，应与甲硝唑联用。
3如果已知或疑似革兰阳性菌也与感染过程有关，应与对革兰阳性菌有活性的抗菌药物联用。
4使用本品超过14天的用药经验有限。
肌酐清除率（CrCL）>50 mL/min/1.73 m2的cIAI儿童患者剂量

表2显示了估计肌酐清除率（eCrCL）> 50 mL/min/1.73 m2的cIAI儿童患者的推荐静
脉注射剂量（见【注意事项】和【临床试验】）。
表 2：估计肌酐清除率 (eCrCL)1 > 50 mL/min/1.73 m2 的cIAI儿童患者的推荐剂量
感染 年龄组 剂量（头孢 给药频率 输注时间 疗程
他啶/阿维巴 （小时）
坦）
62.5 mg/kg
至最多2.5 g
6月龄~<18 (50 mg/kg/ 每8小时
2
岁 12.5 mg/kg 一次
复杂性腹腔内 至最多
5~14天
感染2,3
2 g/0.5 g)
50 mg/kg (40
3月龄~<6 每8小时
mg/kg/ 10 2
月龄4 一次
mg/kg)
1CrCL使用Schwartzbedside公式估算。
2 当已知或怀疑厌氧性病原体与感染过程有关时，应与甲硝唑联合使用。
3 当已知或怀疑革兰阳性病原体与感染过程有关时，应与对这些病原体有效的抗菌剂联合使用。
4 在3月龄至＜6月龄的儿童患者中使用Zavicefta的经验有限（见【临床药理】）
特殊人群
老年人
老年人无需调整剂量（见【临床药理】）。
肾功能损伤患者
轻度肾功能损伤患者无需调整剂量（50mL/min<eCrCL≤80 mL/min）（见【临床
药理】）。
表 3 中显示了 eCrCL≤50 mL/min 成人患者的推荐剂量调整，对于肾功能处于变
化中的患者，应至少每天监测CrCL，并相应地调整本品剂量（见【注意事项】和【临
床药理】）。
CrCL ≤ 50 mL/min的成人患者剂量
表 3 eCrCL≤50 mL/min 成人患者的推荐剂量 1

年龄组 eCrCL（ 剂量2 给药频率 输注时间
mL/min） (头孢他啶/阿维巴坦) （小时）
成人 31~50 1.25 g（1g/0.25 g） 每8小时1次 2
16~30 0.94 g（0.75g/0.19 g） 每12小时1次 2
6~15 0.94 g（0.75g/0.19 g） 每24小时1次 2
≤53 0.94 g（0.75g/0.19 g） 每48小时1次 2
1使用Cockcroft-Gault公式估算CrCL。
2剂量推荐基于药代动力学模型。
3头孢他啶和阿维巴坦可通过血液透析清除（见【药物过量】和【临床药理】）。血液透析当天应在血液透析结束后
进行本品给药。
表4和表5按照不同年龄组列出了估计肌酐清除率（eCrCL）≤ 50mL/min/1.73 m2 的
儿童患者的推荐剂量调整方案（见【注意事项】和【临床药理】）。
CrCl ≤ 50mL/min/1.73 m2的≥ 2岁儿童患者的剂量
表 4：eCrCL1 ≤ 50mL/min/1.73 m2的儿童患者的推荐剂量
年龄组 eCrCL 头孢他啶/阿维巴坦的剂 给药频 输注时间
(mL/min/1.73 m2) 量2,4 率 （小时）
25 mg/kg/ 6.25 mg/kg
每8小
31~50 至最多
时一次
1 g/0.25g
2岁~ <18 每12小
16~30
岁的儿童 时一次 2
18.75 mg/kg/ 4.7 mg/kg
患者 每24小
6~15 至最多
时一次
0.75 g/ 0.1875g
终末期肾病，包括接受血 每48小
液透析的患者3 时一次
1CrCL使用Schwartz bedside公式估算。
2 剂量建议基于药代动力学建模（见【临床药理】）。
3 头孢他啶和阿维巴坦可通

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 六、治疗药物监测（TDM）

CL=血浆清除率；C max=峰浓度；T。蛋白结合的程度不依赖于浓度。人血浆蛋白结合率很低（5.7~8.2%），且与在浓度范围0.5~50 mg/L内体外测定的结果

## 七、禁忌

- 对活性物质或【成份】项中列出的任何辅料过敏者
- 对头孢菌素类抗菌药物过敏者
- 对其他类型β-内酰胺类抗菌药物（如青霉素、单酰胺菌素或碳青霉烯类）的严重
- 超敏者（例如速发严重过敏反应、严重皮肤反应）

## 八、特殊人群

- 妊娠/哺乳：孕妇
风险总结
尚未在孕妇中进行具有充分且良好对照的本品、头孢他啶或阿维巴坦研究。大鼠
中头孢他啶和阿维巴坦给药剂量为人用临床推荐剂量的 40 和 9 倍时未引起致畸性。
兔中本品暴露量为人用临床剂量所引起暴露量的2倍时未影响胚胎-胎仔发育。
尚不清楚在目标人群中的重大出生缺陷和流产的背景风险。在普
- 儿童：本品在3月龄以下的儿童患者中的安全性和有效性尚未确定。无可用数据。
- 老年：在 II和 III期临床试验中（2024 例），本品治疗组≥65岁患者占32.7%（661/2024
例），其中≥75岁占15.5%（314/2024例）。
在II和 III期cIAI临床试验整合分析中，本品治疗组≥65岁患者占19.6%（168/857
例），其中≥75岁占7.1%（61/857例

## 九、药物相互作用

- 在体外，阿维巴坦对细胞色素 P450 酶无明显的抑制作用。临床相关浓度的阿维
- 巴坦和头孢他啶在体外对细胞色素 P450 无诱导作用。在临床相关的暴露范围内，阿
- 维巴坦和头孢他啶不会抑制主要的肾脏或肝脏转运蛋白，因此认为可能通过这些机制
- 引起的相互作用很小。
- 在体外，人肝微粒体中临床相关浓度的阿维巴坦不会抑制细胞色素 P450 同工酶
- CYP1A2、CYP2A6、CYP2B6、CYP2C8、CYP2C9、CYP2C19、CYP2D6、CYP2E1 和
- CYP3A4/5。在体外人肝细胞中阿维巴坦无诱导 CYP1A2/2B6/2C9 和 3A4 的能力。超
- 过临床相关暴露量的极高浓度阿维巴坦对CYP2E1 有轻微的诱导能力。在人肝细胞中

## 十、注意事项

和【临床药理】）。
表1 按适应症总结的本品在估计肌酐清除率 (eCrCL)1 >50 mL/min 成人患者中的
给药剂量
感染 剂量 给药频率 输注时间 疗程
(头孢他啶/阿 （小时）
维巴坦)
复杂性腹腔内感染2,3[与 2.5g(2 g/0.5 g) 每8小时1次 2 5~14天
甲硝唑联用]
医院获得性肺炎和呼吸 2.5g(2 g/0.5 g) 每8小时1次 2 7~14天
机相关性肺炎3
治疗方案选择有限的成 2.5g(2 g/0.5 g) 每8小时1次 2 取决于感染的严
人患者中需氧型革兰阴 重程度、病原
性菌引起的感染 2,3 菌、患者的临床
情况和细菌学进
展4
1使用Cockcroft-Gault公式估算CrCL。
2如果已知或疑似厌氧菌也与感染过程有关，应与甲硝唑联用。
3如果已知或疑似革兰阳性菌也与感染过程有关，应与对革兰阳性菌有活性的抗菌药物联用。
4使用本品超过14天的用药经验有限。
肌酐清除率（CrCL）>50 mL/min/1.73 m2的cIAI儿童患者剂量

表2显示了估计肌酐清除率（eCrCL）> 50 mL/min/1.73 m2的cIAI儿童患者的推荐静
脉注射剂量（见【注意事项】和【临床试验】）。
表 2：估计肌酐清除率 (eCrCL)1 > 50 mL/min/1.73 m2 的cIAI儿童患者的推荐剂量
感染 年龄组 剂量（头孢 给药频率 输注时间 疗程
他啶/阿维巴 （小时）
坦）
62.5 mg/kg
至最多2.5 g
6月龄~<18 (50 mg/kg/ 每8小时
2
岁 12.5 mg/kg 一次
复杂性腹腔内 至最多
5~14天
感染2,3
2 g/0.5 g)
50 mg/kg (40
3月龄~<6 每8小时
mg/kg/ 10 2
月龄4 一次
mg/kg)
1CrCL使用Schwartzbedside公式估算。
2 当已知或怀疑厌氧性病原体与感染过程有关时，应与甲硝唑联合使用。
3 当已知或怀疑革兰阳性病原体与感染过程有关时，应与对这些病原体有效的抗菌剂联合使用。
4 在3月龄至＜6月龄的儿童患者中使用Zavicefta的经验有限（见【临床药理】）
特殊人群
老年人
老年人无需调整剂量（见【临床药理】）。
肾功能损伤患者
轻度肾功能损伤患者无需调整剂量（50mL/min<eCrCL≤80 mL/min）（见【临床
药理】）。
表 3 中显示了 eCrCL≤50 mL/min 成人患者的推荐剂量调整，对于肾功能处于变
化中的患者，应至少每天监测CrCL，并相应地调整本品剂量（见【注意事项】和【临
床药理】）。
CrCL ≤ 50 mL/min的成人患者剂量
表 3 eCrCL≤50 mL/min 成人患者的推荐剂量 1

年龄组 eCrCL（ 剂量2 给药频率 输注时间
mL/min） (头孢他啶/阿维巴坦) （小时）
成人 31~50 1.25 g（1g/0.25 g） 每8小时1次 2
16~30 0.94 g（0.75g/0.19 g） 每12小时1次 2
6~15 0.94 g（0.75g/0.19 g） 每24小时1次 2
≤53 0.94 g（0.75g/0.19 g） 每48小时1次 2
1使用Cockcroft-Gault公式估算CrCL。
2剂量推荐基于药代动力学模型。
3头孢他啶和阿维巴坦可通过血液透析清除（见【药物过量】和【临床药理】）。血液透析当天应在血液透析结束后
进行本品给药。
表4和表5按照不同年龄组列出了估计肌酐清除率（eCrCL）≤ 50mL/min

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/dingyoule.md

```markdown
---
drugName: "鼎优乐（抗生素类药品）"
brandNames:
  - "鼎优乐"
manufacturer: "未知"
dosageForm: "注射用无菌粉末"
strengths:
  - "详见说明书原文"
atcCode: ""
antibioticClass: "抗菌药物"
indications:
  - "详见说明书原文"
contraindications: []
specialPopulations: []
renalAdjustment: false
hepaticAdjustment: false
drugInteractions: []
preparation: "详见说明书原文"
reviewDate: "2026-11-09"
tags:
  - "抗菌药物"
description: "鼎优乐（抗生素类药品），抗菌药物，说明书 PDF 解析生成。"
draft: true
---

## 一、药品概述

鼎优乐（抗生素类药品），抗菌药物。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

详见说明书原文。

## 三、用法用量

详见说明书原文。

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 七、禁忌

详见说明书原文。

## 八、特殊人群

详见说明书原文。

## 九、药物相互作用

详见说明书原文。

## 十、注意事项

详见说明书原文。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/eravacycline.md

```markdown
---
drugName: "注射用盐酸依拉环素"
brandNames:
  - "依嘉®"
  - "XERAVA®"
manufacturer: "云顶新耀（Everest Medicines）/ Tetraphase"
dosageForm: "注射用无菌粉末"
strengths:
  - "50 mg（按C27H31F4NO8计）"
atcCode: "J01AA13"
antibioticClass: "四环素类抗菌药物（氟环素）"
indications:
  - "中度至重度肾损伤（肌酐清除率计算值为15至<60 mL/min）的患者占8%。在这些试验 本品是四环菌素类抗菌药物的结构类似物，可能产生相似的不良反应。其他四环菌 与强效CYP3A诱导剂合用会降低依拉环素的暴露量，这可能会降低本品的有效性（见 联系人电话 陈玺明"
  - "复杂性腹腔感染（cIAI）： 中基线时有66例（13%）患有中度肝损伤（Child Pugh B级）"
  - "将发生重度肝损伤（Child 素类抗菌药物治疗患者中曾报告的不良反应包括光敏感性、假性脑瘤以及抗同化作用（导 【药代动力学】）。在与强效CYP3A诱导剂合用的患者中应增加本品剂量（见【用法用量】）。 Contact People Tel 0512-62883607"
  - "本品适用于治疗由下列敏感菌株引起的复杂性腹腔感染（cIAI）成人患者：大肠埃 Pugh C级）的患者排除在试验之外。 致BUN升高、氮质血症、酸中毒、高磷血症、胰腺炎和肝功能检查异常）"
  - "本品治疗 抗凝血药"
  - "希菌、肺炎克雷伯菌、弗劳地枸橼酸杆菌、阴沟肠杆菌、产酸克雷伯菌、粪肠球菌、屎 导致停药的不良反应 期间也可能发生上述反应。如果怀疑发生任何上述不良反应，应停用本品。 已有研究显示四环素会抑制血浆凝血酶原活性，因此接受抗凝治疗的患者可能需要 BAG生成日期"
  - "2024/6/27"
  - "肠球菌、金黄色葡萄球菌、咽峡炎链球菌群、产气荚膜梭菌、拟杆菌属和狄氏副拟杆菌（见 2%（11/520）接受本品治疗的患者和2%（11/517）接受对照药物治疗的患者因不良 输液部位反应 下调抗凝剂剂量。 Date of BAG Generation"
contraindications:
  - "用药数据有限，不足以确定是否存在药物相关性重大出生缺陷和流产风险"
  - "动物研究表"
  - "修改日期：2023年3月29日"
  - "则必须丢弃复溶小瓶内容物"
  - "已知对依拉环素、四环素类抗菌药物、或本品中任何辅料过敏者禁用（见【注意事 明依拉环素可穿过胎盘并出现在胎仔血中"
specialPopulations:
  - "妊娠/哺乳：b 厄他培南剂量为1 g IV输注每24小时一次。 2. 轻轻涡旋小瓶，直至粉末完全溶解。应避免振摇或快速移动，以免产生泡沫。 精神病类：焦虑、失眠、抑郁 孕妇 c 美罗培南剂量为1 g IV输注每8小时一次。 本品复溶液应为澄清淡黄色至橙色溶液。如果发现溶液中存在任何不溶性微粒 呼吸系统、胸及纵隔"
  - "儿童：和【孕妇及哺乳期 给药后4天（基于半衰期）不要进行母乳喂养。 文件路径 印前作业文件夹-药品客户\\"
  - "老年：BAG码 YDXY-SP00000017 由于临床试验是在差异很大的不同条件下开展的，所以不能将不同药物在临床试验 艰难梭菌可产生毒素A和毒素B，进而导致发展为CDAD。产剧毒艰难梭菌菌株可 在III期临床试验中接受本品治疗的所有复杂性腹腔感染患者（n = 520）中，158例 BAG Code 分"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "Folded Size"
  - "和白人（98%）为主。本品治疗人群中肥胖患者（BMI≥30 kg/m2）占31%，基线时存在 四环素类不良反应 强效CYP3A诱导剂对本品的影响"
preparation: "详见说明书原文"
sourceUrl: "https://www.everestmedicines.com"
reviewDate: "2026-11-09"
tags:
  - "四环素类抗菌药物（氟环素）"
description: "注射用盐酸依拉环素（依嘉®/XERAVA®），四环素类抗菌药物（氟环素），说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用依拉环素（依嘉），四环素类抗菌药物（氟环素）。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 中度至重度肾损伤（肌酐清除率计算值为15至<60 mL/min）的患者占8%。在这些试验 本品是四环菌素类抗菌药物的结构类似物，可能产生相似的不良反应。其他四环菌 与强效CYP3A诱导剂合用会降低依拉环素的暴露量，这可能会降低本品的有效性（见 联系人电话 陈玺明
- 复杂性腹腔感染（cIAI）： 中基线时有66例（13%）患有中度肝损伤（Child Pugh B级）
- 将发生重度肝损伤（Child 素类抗菌药物治疗患者中曾报告的不良反应包括光敏感性、假性脑瘤以及抗同化作用（导 【药代动力学】）。在与强效CYP3A诱导剂合用的患者中应增加本品剂量（见【用法用量】）。 Contact People Tel 0512-62883607
- 本品适用于治疗由下列敏感菌株引起的复杂性腹腔感染（cIAI）成人患者：大肠埃 Pugh C级）的患者排除在试验之外。 致BUN升高、氮质血症、酸中毒、高磷血症、胰腺炎和肝功能检查异常）
- 本品治疗 抗凝血药
- 希菌、肺炎克雷伯菌、弗劳地枸橼酸杆菌、阴沟肠杆菌、产酸克雷伯菌、粪肠球菌、屎 导致停药的不良反应 期间也可能发生上述反应。如果怀疑发生任何上述不良反应，应停用本品。 已有研究显示四环素会抑制血浆凝血酶原活性，因此接受抗凝治疗的患者可能需要 BAG生成日期
- 2024/6/27
- 肠球菌、金黄色葡萄球菌、咽峡炎链球菌群、产气荚膜梭菌、拟杆菌属和狄氏副拟杆菌（见 2%（11/520）接受本品治疗的患者和2%（11/517）接受对照药物治疗的患者因不良 输液部位反应 下调抗凝剂剂量。 Date of BAG Generation

## 三、用法用量

）。 Contact People Tel 0512-62883607
本品适用于治疗由下列敏感菌株引起的复杂性腹腔感染（cIAI）成人患者：大肠埃 Pugh C级）的患者排除在试验之外。 致BUN升高、氮质血症、酸中毒、高磷血症、胰腺炎和肝功能检查异常）；本品治疗 抗凝血药
希菌、肺炎克雷伯菌、弗劳地枸橼酸杆菌、阴沟肠杆菌、产酸克雷伯菌、粪肠球菌、屎 导致停药的不良反应 期间也可能发生上述反应。如果怀疑发生任何上述不良反应，应停用本品。 已有研究显示四环素会抑制血浆凝血酶原活性，因此接受抗凝治疗的患者可能需要 BAG生成日期
2024/6/27
肠球菌、金黄色葡萄球菌、咽峡炎链球菌群、产气荚膜梭菌、拟杆菌属和狄氏副拟杆菌（见 2%（11/520）接受本品治疗的患者和2%（11/517）接受对照药物治疗的患者因不良 输液部位反应 下调抗凝剂剂量。 Date of BAG Generation

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 六、治疗药物监测（TDM）

表示即使抗菌药物在感染部位达到通常浓度，也可能无法抑制病原体生长，应选择其他。 缩略语：C =观测血浆峰浓度，CV =变异系数；AUC =0-12小时的血浆浓度-时间 电话号码：+65 67413803。标准化药敏试验程序需要采用实验室质控措施，以监测并确保本试验所用材料和试 0-12

## 七、禁忌

- 用药数据有限，不足以确定是否存在药物相关性重大出生缺陷和流产风险
- 动物研究表
- 修改日期：2023年3月29日
- 则必须丢弃复溶小瓶内容物
- 已知对依拉环素、四环素类抗菌药物、或本品中任何辅料过敏者禁用（见【注意事 明依拉环素可穿过胎盘并出现在胎仔血中

## 八、特殊人群

- 妊娠/哺乳：b 厄他培南剂量为1 g IV输注每24小时一次。
2. 轻轻涡旋小瓶，直至粉末完全溶解。应避免振摇或快速移动，以免产生泡沫。 精神病类：焦虑、失眠、抑郁 孕妇 c 美罗培南剂量为1 g IV输注每8小时一次。
本品复溶液应为澄清淡黄色至橙色溶液。如果发现溶液中存在任何不溶性微粒 呼吸系统、胸及纵隔
- 儿童：和【孕妇及哺乳期 给药后4天（基于半衰期）不要进行母乳喂养。
文件路径 印前作业文件夹-药品客户\
- 老年：BAG码
YDXY-SP00000017
由于临床试验是在差异很大的不同条件下开展的，所以不能将不同药物在临床试验 艰难梭菌可产生毒素A和毒素B，进而导致发展为CDAD。产剧毒艰难梭菌菌株可 在III期临床试验中接受本品治疗的所有复杂性腹腔感染患者（n = 520）中，158例 BAG Code
分

## 九、药物相互作用

- Folded Size
- 和白人（98%）为主。本品治疗人群中肥胖患者（BMI≥30 kg/m2）占31%，基线时存在 四环素类不良反应 强效CYP3A诱导剂对本品的影响

## 十、注意事项

尚不清楚目标人群发生重大出生缺陷和流产的背景风险估计值。所有妊娠均有出生
的输注液。请勿振摇输液袋。 超敏反应 缺陷、流产或其他不良结局的背景风险。在美国普通人群中，临床上认定的孕妇重大出
请仔细阅读说明书并在医师指导下使用 4. 稀释液必须在24小时内（25℃以下）或者在10天内（2-8℃）输注。复溶及稀 本品治疗患者曾报告危及生命的超敏反应（速发过敏反应）。本品是其他四环素类 生缺陷和流产的估计背景风险分别为2-4%和15-20%。
释后的本品输注液不得冷冻。 抗菌药物的结构类似物，故应禁用于已知对四环素类抗菌药物过敏者。如果发生过敏反 哺乳
印刷色

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/imipenem-cilastatin-relebactam.md

```markdown
---
drugName: "注射用亚胺西瑞"
brandNames:
  - "锐可博®"
  - "RECARBRIO®"
manufacturer: "默沙东"
dosageForm: "注射用无菌粉末"
strengths:
  - "1.25g"
  - "0.5g"
  - "0.25g"
atcCode: "J01DH56"
antibioticClass: "碳青霉烯类/β-内酰胺酶抑制剂复合制剂"
indications:
  - "本品适用于治疗18岁及以上患者由敏感革兰阴性菌引起的下列感染："
  - "医院获得性细菌性肺炎和呼吸机相关性细菌性肺炎（HABP/VABP）"
  - "本品适用于治疗由以下微生物引起的医院获得性细菌性肺炎和呼吸机相关"
  - "性细菌性肺炎（HABP/VABP）： 醋酸钙-鲍曼不动杆菌复合体、阴沟肠杆菌、大肠"
  - "埃希菌、流感嗜血杆菌、产气克雷伯菌、产酸克雷伯菌、肺炎克雷伯菌、铜绿假"
  - "单胞菌和粘质沙雷菌。"
  - "治疗药物选择有限或无替代治疗的复杂性尿路感染（ ） （包括肾盂肾炎）"
  - "cUTI"
  - "本品适用于治疗由以下微生物引起的治疗药物选择有限或无替代治疗的复"
  - "第 页 共 页"
contraindications:
  - "既往对本品中任何成分有严重超敏反应（严重全身性过敏反应，如速发严重"
  - "过敏反应）的患者禁用本品"
  - "既往对β-内酰胺类抗菌药物有严重超敏反应的患者禁用本品"
specialPopulations:
  - "妊娠/哺乳：． 妊娠期妇女 1 尚无足够的人体用药数据可用于确立妊娠期妇女接受本品、亚胺培南、西司 他丁或瑞来巴坦治疗时是否存在重大出生缺陷、流产、母体或胎儿不良结局的药 物相关风险。在接受亚胺培南 西司他丁给药的猴中观察到胚胎死亡，在接受瑞 / 来巴坦给药的小鼠中观察到胎仔异常，因此建议孕妇警惕该药物对妊娠和"
  - "儿童：尚未确定本品在 岁以下儿童和青少年患者中的安全性和有效性。 18"
  - "老年：本品无需根据年龄进行剂量调整。老年患者的剂量调整应依据肾功能状况而 定。 在试验 1 中接受本品治疗的266 例患者中，113 例（42.5%）患者年龄为 65 岁及以上，55 例患者（20.7%）为 75 岁及以上。在试验 2 和试验 3 中接受亚胺 培南/西司他丁+瑞来巴坦 250 mg 治疗的"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "． 更昔洛韦"
  - "在同时接受更昔洛韦和亚胺培南/西司他丁（本品的组成成分）的患者中曾"
  - "有全身性痫性发作的报告。除非潜在获益大于风险，否则更昔洛韦不得与本品联"
  - "文献中的病例报告显示，对接受丙戊酸或双丙戊酸钠治疗的患者联合给予碳"
  - "青霉烯类药物（包括本品的组成成分亚胺培南/西司他丁），会导致丙戊酸浓度降"
  - "至治疗范围以下，进而导致突发性痫性发作的风险增加。尽管这种相互作用的机"
  - "制尚不明确，但体外和动物研究数据表明，碳青霉烯类药物可能会抑制丙戊酸葡"
  - "糖苷醛酸代谢物（VPA-g）水解成丙戊酸，因此降低了丙戊酸的血清浓度。不建"
preparation: "详见说明书原文"
sourceUrl: "https://www.msd.com"
reviewDate: "2026-11-09"
tags:
  - "碳青霉烯类/β-内酰胺酶抑制剂复合制剂"
description: "注射用亚胺西瑞（锐可博®/RECARBRIO®），碳青霉烯类/β-内酰胺酶抑制剂复合制剂，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用亚胺培南西司他丁瑞来巴坦（亚胺西瑞），碳青霉烯类/β-内酰胺酶抑制剂复合制剂。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品适用于治疗18岁及以上患者由敏感革兰阴性菌引起的下列感染：
- 医院获得性细菌性肺炎和呼吸机相关性细菌性肺炎（HABP/VABP）
- 本品适用于治疗由以下微生物引起的医院获得性细菌性肺炎和呼吸机相关
- 性细菌性肺炎（HABP/VABP）： 醋酸钙-鲍曼不动杆菌复合体、阴沟肠杆菌、大肠
- 埃希菌、流感嗜血杆菌、产气克雷伯菌、产酸克雷伯菌、肺炎克雷伯菌、铜绿假
- 单胞菌和粘质沙雷菌。
- 治疗药物选择有限或无替代治疗的复杂性尿路感染（ ） （包括肾盂肾炎）
- cUTI
- 本品适用于治疗由以下微生物引起的治疗药物选择有限或无替代治疗的复
- 第 页 共 页

## 三、用法用量

1． 成人推荐剂量
在肌酐清除率（CrCl）≥90mL/min 的 18 岁及以上患者中，本品的推荐剂量
为 1.25g （500mg亚胺培南、500mg西司他丁和250mg 瑞来巴坦），每6小时一
次，静脉输注约 30分钟。对于 CrCl＜90mL/min的患者，建议降低剂量，具体剂
量调整参见表1。治疗的持续时间取决于感染严重程度、感染部位以及临床应答，
推荐治疗持续时间为4~14天。
2. 肾功能损害患者的剂量调整
肾功能损害患者建议调整剂量。CrCl＜90mL/min的患者需要降低剂量，具体
剂量调整参见表1。对于肾功能波动的患者，应监测CrCl。
表 1： 成人肾功能损害患者的本品剂量
本品（亚胺培南/西司他丁/瑞来巴坦） 的
肌酐清除率（mL/min） * 注射间隔
推荐剂量（mg） †
60 – 89 1g（400/400/200） 每6小时一次
30 – 59 0.75g（300/300/150） 每6小时一次
15 – 29 0.5g（200/200/100） 每6小时一次
接受血液透析的终末期肾 每6小时一次
0.5g（200/200/100）
脏疾病（ESRD）‡
*采用Cockcroft-Gault公式计算CrCl。
CrCl（男性）=[体重(kg)×[140-年龄(岁)]
（72）×[血清肌酐(mg/100 mL)]
CrCl（女性）=（0.85）×（使用上述公式所得值）
†静脉输注约30分钟。
‡应在血液透析后给药。
本品为单个西林瓶装的固定剂量复方制剂，配制过程中每种成分的剂量均同时受到相应
的调整。
CrCl＜15 mL/min的患者，除非在48小时内进行血液透析，否则不应接受本
品。没有充分数据支持腹膜透析患者的使用。
在血液透析过程中，血液循环中的亚胺培南、西司他丁和瑞来巴坦会被清除。
对于维持血液透析的患者，应在血液透析后及血液透析间期接受本品给药。
3． 本品静脉给药的溶液配制
本品为单剂量西林瓶装粉末，静脉输注前必须使用无菌技术进行复溶和进一
步稀释，配制成100mL的输注溶液。
准备100ml稀释液，可供选择的合适稀释液如下：
o 0.9%氯化钠注射液
o 5%葡萄糖注射液
o 5%葡萄糖注射液+ 0.9%氯化钠注射液
o 5%葡萄糖注射液+ 0.45%氯化钠注射液
o 5%葡萄糖注射液+ 0.225%氯化钠注射液
本品水溶性低，为确保完全溶解，请遵循以下步骤操作：
• 从100ml稀释液输液袋中抽取 20mL（10mL×2），用 10mL稀释液复溶西
林瓶内容物。复溶后的混悬液不得用于直接静脉输注给药。
• 复溶后，充分振摇西林瓶，将所得混悬液转移至剩余80 mL稀释液的输液
袋中。
• 将另外10 mL稀释液加入西林瓶中，充分振摇，以确保能完全转移西林瓶
内容物；将所得混悬液再次转移至输液袋中。摇动输液袋中的混合液直至
澄清。
本品复溶溶液的颜色应为无色至黄色。在该范围内的颜色变化不会影响产品
的效价。给药前需目视检查输注溶液是否存在不溶性微粒或变色，如果观察到变
色或可见微粒应将溶液丢弃。
所有患者（无论患者的肾功能如何），都必须遵循上述静脉输注溶液的制备
说明，然后根据肾功能情况确定给患者使用的溶液体积。
4. 本品用于肾功能损害患者静脉给药的溶液配制
肾功能损害患者需要降低剂量，需先制备含有本品 1.25g的 100mL 输注溶
液，然后根据表 2 抽出并丢弃多余的溶液。
表 2： 肾功能损害患者使用本品静脉给药降低剂量的配制
按照上述说明制备后，
本品的剂量（亚胺培南/西 提供指定降低剂量
肌 酐 清 除 率 从100 mL制备液输液
司他丁/瑞来巴坦） 的最终体积
（mL/min） 袋中抽取并丢弃以下体
（mg） （mL）
积的溶液（mL）
60 – 89 1g（400/400/200） 20 80
30 – 59 0.75g（300/300/150） 40 60
15 - 29或接受血
0.5g（200/200/100） 60 40
液透析的ESRD
5. 复溶溶液的贮藏
本品采用单剂量西林瓶装，用适当稀释液复溶、转移至输液袋中进一步稀释
后，室温下（最高30℃）贮藏可保持稳定效价至少4小时，2 - 8℃（36 - 46℉）冷
藏条件下贮藏可保持稳定效价至少24小时。本品溶液不得冷冻。
6. 用于静脉输注给药的可配伍和不可配伍注射药物和其他材料
可配伍药物
在两种常用稀释液中评价了本品与选定注射药物的物理配伍性。以下列出了
可配伍的药物及其相应的配伍稀释液（即 5%葡萄糖注射液或 0.9%氯化钠注射
液）。由于尚无可用的配伍性数据，本品不应通过相同的静脉输液管（或套管）
与未在下文列出的其他制剂联合给药。请参阅联合用药产品说明书，确认联合用
药的配伍性。
使用5%葡萄

## 四、肾功能调整

肾功能损害患者的剂量调整
肾功能损害患者建议调整剂量。CrCl＜90mL/min的患者需要降低剂量，具体
剂量调整参见表1。对于肾功能波动的患者，应监测CrCl。
表 1： 成人肾功能损害患者的本品剂量
本品（亚胺培南/西司他丁/瑞来巴坦） 的
肌酐清除率（mL/min） * 注射间隔
推荐剂量（mg） †
60 – 89 1g（400/400/200） 每6小时一次
30 – 59 0.75g（300/300/150） 每6小时一次
15 – 29 0.5g（200/200/100） 每6小时一次
接受血液透析的终末期肾 每6小时一次
0.5g（200/200/100）
脏疾病（ESRD）‡
*采用Cockcroft-Gault公式计算CrCl。
CrCl（男性）=[体重(kg)×[140-年龄(岁)]
（72）×[血清肌酐(mg/100 mL)]
CrCl（女性）=（0.85）×（使用上述公式所得值）
†静脉输注约30分钟。
‡应在血液透析后给药。
本品为单个西林瓶装的固定剂量复方制剂，配制过程中每种成分的剂量均同时受到相应
的调整。
CrCl＜15 mL/min的患者，除非在48小时内进行血液透析，否则不应接受本
品。没有充分数据支持腹膜透析患者的使用。
在血液透析过程中，血液循环中的亚胺培南、西司他丁和瑞来巴坦会被清除。
对于维持血液透析的患者，应在血液透析后及血液透析间期接受本品给药。
3． 本品静脉给药的溶液配制
本品为单剂量西林瓶装粉末，静脉输注前必须使用无菌技术进行复溶和进一
步稀释，配制成100mL的输注溶液。
准备100ml稀释液，可供选择的合适稀释液如下：
o 0.9%氯化钠注射液
o 5%葡萄糖注射液
o 5%葡萄糖注射液+ 0.9%氯化钠注射液
o 5%葡萄糖注射液+ 0.45%氯化钠注射液
o 5%葡萄糖注射液+ 0.225%氯化钠注射液
本品水溶性低，为确保完全溶解，请遵循以下步骤操作：
• 从100ml稀释液输液袋中抽取 20mL（10mL×2），用 10mL稀释液复溶西
林瓶内容物。复溶后的混悬液不得用于直接静脉输注给药。
• 复溶后，充分振摇西林瓶，将所得混悬液转移至剩余80 mL稀释液的输液
袋中。
• 将另外10 mL稀释液加入西林瓶中，充分振摇，以确保能完全转移西林瓶
内容物；将所得混悬液再次转移至输液袋中。摇动输液袋中的混

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 七、禁忌

- 既往对本品中任何成分有严重超敏反应（严重全身性过敏反应，如速发严重
- 过敏反应）的患者禁用本品
- 既往对β-内酰胺类抗菌药物有严重超敏反应的患者禁用本品

## 八、特殊人群

- 妊娠/哺乳：． 妊娠期妇女
1
尚无足够的人体用药数据可用于确立妊娠期妇女接受本品、亚胺培南、西司
他丁或瑞来巴坦治疗时是否存在重大出生缺陷、流产、母体或胎儿不良结局的药
物相关风险。在接受亚胺培南 西司他丁给药的猴中观察到胚胎死亡，在接受瑞
/
来巴坦给药的小鼠中观察到胎仔异常，因此建议孕妇警惕该药物对妊娠和
- 儿童：尚未确定本品在 岁以下儿童和青少年患者中的安全性和有效性。
18
- 老年：本品无需根据年龄进行剂量调整。老年患者的剂量调整应依据肾功能状况而
定。
在试验 1 中接受本品治疗的266 例患者中，113 例（42.5%）患者年龄为 65
岁及以上，55 例患者（20.7%）为 75 岁及以上。在试验 2 和试验 3 中接受亚胺
培南/西司他丁+瑞来巴坦 250 mg 治疗的

## 九、药物相互作用

- ． 更昔洛韦
- 在同时接受更昔洛韦和亚胺培南/西司他丁（本品的组成成分）的患者中曾
- 有全身性痫性发作的报告。除非潜在获益大于风险，否则更昔洛韦不得与本品联
- 文献中的病例报告显示，对接受丙戊酸或双丙戊酸钠治疗的患者联合给予碳
- 青霉烯类药物（包括本品的组成成分亚胺培南/西司他丁），会导致丙戊酸浓度降
- 至治疗范围以下，进而导致突发性痫性发作的风险增加。尽管这种相互作用的机
- 制尚不明确，但体外和动物研究数据表明，碳青霉烯类药物可能会抑制丙戊酸葡
- 糖苷醛酸代谢物（VPA-g）水解成丙戊酸，因此降低了丙戊酸的血清浓度。不建

## 十、注意事项

． 超敏反应
1
在接受β-内酰胺类药物治疗的患者中，曾有严重且偶有致命的超敏反应（速
发严重过敏反应）的报告。这些反应更可能发生在对多种过敏原有过敏史的患者
中。在使用本品治疗之前，应仔细询问既往是否对碳青霉烯类、青霉素类、头孢
菌素类、其他β-内酰胺类和其他过敏原有超敏反应。如果使用本品时发生过敏反
应，应立即停止用药。
． 痫性发作和其他中枢神经系统不良反应
2
在患者接受亚胺培南/西司他丁（本品的组成成分）治疗期间，尤其是在超过
亚胺培南推荐剂量时，曾报告出现中枢神经系统不良反应，如痫性发作、意识模
糊状态和肌阵挛活动。有中枢神经系统疾病（例如，脑部病变或痫性发作史）和
/或肾功能受损的患者最常报告这些反应。
． 与丙戊酸相互作用导致痫性发作的可能性增加
3
本品与丙戊酸/双丙戊酸钠联用，可能会增加突发性痫性发作的风险，故不
建议本品与丙戊酸/双丙戊酸钠联用。对于使用丙戊酸或双丙戊酸钠治疗后痫性
发作控制良好的患者，应考虑使用非碳青霉烯类的其他抗菌药物治疗感染。如果
需要给予本品，应考虑补充额外的抗惊厥治疗。[参见“药物相互作用” ]
． 艰难梭菌相关性腹泻（ ）
4 CDAD
几乎所有抗菌药物（包括本品）的应用都有艰难梭菌相关性腹泻
（CDAD）的报告，其严重程度可表现为轻度腹泻至致命性肠炎。抗菌药物治
疗可引起结肠正常菌群的改变，导致艰难梭菌的过度生长。
艰难梭菌产生的毒素A和毒素B与CDAD的发病有关。高产毒的艰难梭菌导
致发病率和死亡率升高，这些感染可能对抗菌药物治疗无效，有可能需要结肠
切除。对于所有使用抗生素后出现腹泻的患者，必须考虑到CDAD的可能。由
于曾经有给予抗菌药物治疗之后超过2个月发生CDAD的报道，因此需仔细询问
病史。
如果怀疑或确诊CDAD，需考虑停用并非针对艰难梭菌的抗菌药物。应根
据临床指征进行适当的液体和电解质管理、蛋白质补充、针对艰难梭菌的抗菌
药物治疗和手术评估。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/isavuconazole-capsule.md

```markdown
---
drugName: "硫酸艾沙康唑胶囊"
brandNames:
  - "康新博"
  - "Cresemba"
manufacturer: "Basilea Pharmaceutica / 辉瑞"
dosageForm: "胶囊剂"
strengths:
  - "100mg"
atcCode: "J02AC04"
antibioticClass: "三唑类抗真菌药"
indications:
  - "详见说明书原文"
contraindications: []
specialPopulations: []
renalAdjustment: false
hepaticAdjustment: false
drugInteractions: []
preparation: "详见说明书原文"
sourceUrl: "https://www.basilea.com"
reviewDate: "2026-11-09"
tags:
  - "三唑类抗真菌药"
description: "硫酸艾沙康唑胶囊，三唑类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

硫酸艾沙康唑胶囊，三唑类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

详见说明书原文。

## 三、用法用量

详见说明书原文。

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 七、禁忌

详见说明书原文。

## 八、特殊人群

详见说明书原文。

## 九、药物相互作用

详见说明书原文。

## 十、注意事项

详见说明书原文。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/isavuconazole-injection.md

```markdown
---
drugName: "注射用硫酸艾沙康唑"
brandNames:
  - "康新博"
  - "Cresemba"
manufacturer: "Basilea Pharmaceutica / 辉瑞"
dosageForm: "注射用无菌粉末"
strengths:
  - "200mg"
atcCode: "J02AC04"
antibioticClass: "三唑类抗真菌药"
indications:
  - "本品适用于治疗成人患者下列感染："
  - "• 侵袭性曲霉病"
  - "• 侵袭性毛霉病"
contraindications:
  - "对本品活性成分或任何辅料成分有超敏反应者"
  - "与酮康唑合用（参见【药物相互作用】）"
  - "与高剂量利托那韦（每12小时> 200mg）合用（参见【药物相互作用】）"
  - "与强效CYP3A4/5 诱导剂（利福平、利福布汀、卡马西平、长效巴比妥类[例"
  - "如苯巴比妥]、苯妥英和圣约翰草等）合用，或与中效CYP3A4/5 诱导剂（依非韦"
specialPopulations:
  - "妊娠/哺乳：期 没有关于孕妇使用本品的数据。 动物研究显示本品具有生殖毒性（参见【药理毒理】）。对人类的潜在风险尚 不清楚。 除非患者患有重度或可能危及生命的真菌感染，并且预期治疗获益超过对胎儿 的潜在危害时，方可考虑使用，否则妊娠女性不得使用本品。 育龄期妇女 对于不打算采取避孕措施的育龄妇女，不建议使用本品"
  - "儿童：尚未确定18 岁以下未成年人使用本品的安全性及疗效。"
  - "老年：老年患者不需要调整剂量；但临床上的老年患者用药经验有限。"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "与高剂量利托那韦（每12小时> 200mg）合用（参见【药物相互作用】）。"
  - "与强效CYP3A4/5 诱导剂（利福平、利福布汀、卡马西平、长效巴比妥类[例"
  - "如苯巴比妥]、苯妥英和圣约翰草等）合用，或与中效CYP3A4/5 诱导剂（依非韦"
  - "仑、萘夫西林和依曲韦林等）合用（参见【药物相互作用】）。"
  - "家族性短QT 综合征患者（参见【注意事项】）。"
preparation: "详见说明书原文"
sourceUrl: "https://www.basilea.com"
reviewDate: "2026-11-09"
tags:
  - "三唑类抗真菌药"
description: "注射用硫酸艾沙康唑，三唑类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用艾沙康唑，三唑类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品适用于治疗成人患者下列感染：
- • 侵袭性曲霉病
- • 侵袭性毛霉病

## 三、用法用量

剂量
应在开始抗真菌治疗前获取真菌培养和其它相关实验室研究（包括组织病
理学）的标本，以分离和鉴定致病微生物。在等待特异性诊断检查确认疾病期
间，可开始早期针对性治疗（抢先治疗或诊断驱动治疗）。但在出结果后，应
相应地调整抗真菌治疗。
负荷剂量
推荐的负荷剂量：前 48 小时内，每 8 小时一瓶（相当于200mg的艾沙康唑），
在复溶和稀释后给药，共给药6次。
维持剂量
推荐的维持剂量：从末次负荷剂量给药后12 至24 小时开始每日一次，每次一
瓶（相当于200mg艾沙康唑），在复溶和稀释后给药。
治疗的持续时间应根据临床反应确定（参见【临床试验】）。
对于 6 个月以上的长期治疗，应认真考虑获益-风险平衡（参见【临床试验】
和【药理毒理】）。
口服胶囊和静脉滴注的互换
本品还有胶囊剂型，每粒含100mg艾沙康唑。（使用时参见“硫酸艾沙康唑
胶囊说明书”）
Page 2of 26

由于口服剂型生物利用度高（98%，参见【药代动力学】），所以在有临床指
征时静脉滴注和口服两种给药途径可以互换。
特殊人群用药
老年人
老年患者不需要调整剂量；但临床上的老年患者用药经验有限。
肾损害
肾损害患者（包括终末期肾病患者）不需要调整剂量（参见【药代动力
学】）。
肝损伤
轻度或中度肝损伤（Child-Pugh A 级和B 级）患者不需要调整剂量（参见

## 四、肾功能调整

说明书中未明确提及肾功能调整。

## 五、肝功能调整

说明书中未明确提及肝功能调整。

## 六、治疗药物监测（TDM）

期间可能需要进行适当的治疗药物监测和剂量调整（参见【药物相互作用】）

## 七、禁忌

- 对本品活性成分或任何辅料成分有超敏反应者
- 与酮康唑合用（参见【药物相互作用】）
- 与高剂量利托那韦（每12小时> 200mg）合用（参见【药物相互作用】）
- 与强效CYP3A4/5 诱导剂（利福平、利福布汀、卡马西平、长效巴比妥类[例
- 如苯巴比妥]、苯妥英和圣约翰草等）合用，或与中效CYP3A4/5 诱导剂（依非韦

## 八、特殊人群

- 妊娠/哺乳：期
没有关于孕妇使用本品的数据。
动物研究显示本品具有生殖毒性（参见【药理毒理】）。对人类的潜在风险尚
不清楚。
除非患者患有重度或可能危及生命的真菌感染，并且预期治疗获益超过对胎儿
的潜在危害时，方可考虑使用，否则妊娠女性不得使用本品。
育龄期妇女
对于不打算采取避孕措施的育龄妇女，不建议使用本品
- 儿童：尚未确定18 岁以下未成年人使用本品的安全性及疗效。
- 老年：老年患者不需要调整剂量；但临床上的老年患者用药经验有限。

## 九、药物相互作用

- 与高剂量利托那韦（每12小时> 200mg）合用（参见【药物相互作用】）。
- 与强效CYP3A4/5 诱导剂（利福平、利福布汀、卡马西平、长效巴比妥类[例
- 如苯巴比妥]、苯妥英和圣约翰草等）合用，或与中效CYP3A4/5 诱导剂（依非韦
- 仑、萘夫西林和依曲韦林等）合用（参见【药物相互作用】）。
- 家族性短QT 综合征患者（参见【注意事项】）。

## 十、注意事项

、【药代动力学】）。
目前尚未在重度肝损伤（Child-Pugh C 级）患者中进行艾沙康唑的研究。除非
认为潜在获益大于风险，否则不建议在这些患者中使用（参见【注意事项】、【不
良反应】、【药代动力学】）。
儿童人群
尚未确定18 岁以下未成年人使用本品的安全性及疗效。尚无可用数据。
给药方法
静脉给药。
在进行药品处理或给药之前应采取的预防措施: 在进行至少1小时的静脉输注
给药之前，必须将本品复溶，然后稀释至相当于大约0.8mg/ml艾沙康唑的浓度，
以降低输液相关反应的风险。输液必须采用串联过滤器（带有聚醚砜[PES] 微孔
膜，孔径为0.2μm -1.2μm）的输液器。本品只能以静脉滴注的形式给药。
有关在给药前复溶和稀释本品的详细说明，请参见如下信息。
复溶
向小瓶中加入5ml注射用水，将内容物复溶。振荡小瓶使内容物完全溶解。
应目视检查复溶溶液，复溶后的浓溶液应澄清且无可见微粒，在给药前必须进一步
稀释。
稀释与给药
Page 3of 26

复溶后，将小瓶中所有复溶浓溶液转移到输液袋中，输液袋中包含250ml的
9mg/ml (0.9%) 氯化钠注射液或50 mg/ml (5%) 葡萄糖溶液。输注液含有大约
0.8mg/ml艾沙康唑。复溶浓溶液被进一步稀释后，稀释的溶液可能会出现白色至
半透明的艾沙康唑细小颗粒，不会沉降（但会被串联过滤器除去）。应轻轻混合稀
释的溶液，或翻滚输液袋，以最大程度减少颗粒的形成。应避免不必要的振动或剧
烈摇晃溶液。输注液必须通过带有聚醚砜（PES）串联过滤器（孔径0.2μm 至
1.2μm）的输液器进行输注。
艾沙康唑不应和其它静脉用药物通过同一输注管线或插管同时输注。
复溶和稀释后溶液的储存条件见【贮藏】。
如可能，在室温下复溶和稀释艾沙康唑后，应于6 小时内完成静脉输注。如不
可能，在稀释后应立即冰箱冷藏输注液，并于24 小时内完成输注。有关本品复溶
和稀释后储存条件的更多信息，参见【贮藏】。
如使用已有静脉输注管线，应使用9 mg/ml（0.9%）氯化钠输注液或50 mg/ml
（5%）葡萄糖溶液冲洗管线。
本品仅供单次使用。请丢弃未用完的药瓶。
本品可能会对环境造成危害(见【药理毒理】-毒理学)。
任何未用完的药品或废料应根据当地的要求进行处置。
配伍禁忌
由于未进行过可配伍性研究，因此，除上述药品之外，本品不得与其他药品混
合。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/sulbactam-durlobactam.md

```markdown
---
drugName: "注射用舒巴坦钠/注射用度洛巴坦钠组合包装"
brandNames:
  - "鼎优乐®"
  - "XACDURO®"
manufacturer: "齐鲁制药 / Innoviva"
dosageForm: "注射用无菌粉末"
strengths:
  - "注射用舒巴坦钠 1.0g × 1瓶 + 注射用度洛巴坦钠 0.5g × 2瓶"
atcCode: "J01CG51"
antibioticClass: "β-内酰胺酶抑制剂复合制剂（舒巴坦/度洛巴坦）"
indications:
  - "本品用于治疗 18 岁及以上患者由鲍曼-醋酸钙不动杆菌复合体敏感分离株所致医"
  - "院获得性细菌性肺炎（HABP）、呼吸机相关性细菌性肺炎（VABP）。"
  - "本品不适用于治疗鲍曼- 醋酸钙不动杆菌复合体敏感分离株以外病原体所致"
  - "HABP/VABP（见【临床试验】）。"
  - "为减少耐药菌形成，维持本品和其它抗菌药物的有效性，本品仅用于治疗已证实或"
  - "强烈疑似由敏感细菌引起的感染。当可获得培养及药敏信息，选择或调整抗菌治疗时应"
  - "予以考虑。如缺少此类数据，根据经验进行治疗选择时可参考当地流行病学和药敏性特"
  - "征信息。"
contraindications:
  - "已知对本品成份（舒巴坦和度洛巴坦）或其他 β-内酰胺类抗菌药物有严重超敏反应"
  - "史的患者应禁用本品（见【注意事项】）"
specialPopulations:
  - "妊娠/哺乳：孕妇 风险总结 本品 尚无在妊娠期间使用本品的数据用于评估发生重大出生缺陷、流产或其他母体或胎 儿不良结局的药物相关风险。 舒巴坦 现有已发表的关于几十年来妊娠期间联合使用舒巴坦与氨苄西林的病例数据，尚未 发现重大出生缺陷、流产或其他母体或胎儿不良结局的药物相关风险。已发表的文献报 告了舒巴坦可穿过"
  - "儿童：尚未确定本品在 18 岁以下儿童患者中使用的安全性和疗效。"
  - "老年：在试验 1 接受本品治疗的 91 例患者中，49 例（54%）为 65 岁及以上患者，包括 17 例（19%）76 岁及以上患者。临床研究没有纳入足够数量 65 岁及以上患者，以确定他 们的反应是否与年轻患者不同。 已知本品主要经肾脏排泄，老年患者更容易出现肾功能减退。应基于肾功能调整老 年患者的给"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "有机阴离子转运蛋白 1（OAT1）抑制剂"
  - "与OAT1 抑制剂合并给药可能会增加舒巴坦的血药浓度。不建议本品与 OAT1 抑"
  - "制剂（如丙磺舒）合并给药（见【临床药理】）。"
preparation: "详见说明书原文"
sourceUrl: "https://www.qilu-pharma.com"
reviewDate: "2026-11-09"
tags:
  - "β-内酰胺酶抑制剂复合制剂（舒巴坦/度洛巴坦）"
description: "注射用舒巴坦钠/注射用度洛巴坦钠组合包装（鼎优乐®/XACDURO®），β-内酰胺酶抑制剂复合制剂（舒巴坦/度洛巴坦），说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用舒巴坦钠/度洛巴坦钠（双坦），β-内酰胺酶抑制剂复合制剂（舒巴坦/度洛巴坦）。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品用于治疗 18 岁及以上患者由鲍曼-醋酸钙不动杆菌复合体敏感分离株所致医
- 院获得性细菌性肺炎（HABP）、呼吸机相关性细菌性肺炎（VABP）。
- 本品不适用于治疗鲍曼- 醋酸钙不动杆菌复合体敏感分离株以外病原体所致
- HABP/VABP（见【临床试验】）。
- 为减少耐药菌形成，维持本品和其它抗菌药物的有效性，本品仅用于治疗已证实或
- 强烈疑似由敏感细菌引起的感染。当可获得培养及药敏信息，选择或调整抗菌治疗时应
- 予以考虑。如缺少此类数据，根据经验进行治疗选择时可参考当地流行病学和药敏性特
- 征信息。

## 三、用法用量

推荐剂量
本品是含注射用舒巴坦钠和注射用度洛巴坦钠的组合包装产品。肌酐清除率（CLcr）
为 45-129 mL/min 的成人患者，本品推荐剂量为 1.0 g 舒巴坦和 1.0 g 度洛巴坦，每 6 小

时进行一次静脉（IV）输注，每次持续 3 小时。
对于 CLcr＜45 mL/min 和 CLcr≥130 mL/min 的患者，建议调整本品给药方案。
建议本品治疗持续时间为 7-14 天。应根据患者的临床状态，选择治疗持续时间。
18 岁及以上患者根据肾功能的用药剂量推荐
18 岁及以上患者根据肾功能的用药剂量推荐见表 1。
对于 CLcr＜45 mL/min 和肾功能亢进（CLcr≥130 mL/min）的患者，建议调整给药
方案。对于接受间歇性血液透析（HD）患者，在 HD 完成后立即开始本品给药。
对于肾功能波动患者，应监测 CLcr 并相应调整剂量。
表 1：18 岁及以上患者根据肾功能的用药剂量推荐
舒巴坦和度洛巴 估算的 CLcr
给药频率
坦的剂量（g） （mL/min）*
≥ 130 每 4 小时 1 次
45-129 每 6 小时 1 次
30-44 每 8 小时 1 次
15-29 每 12 小时 1 次
舒巴坦 1.0g 和度
对于开始使用本品的患者：前 3 次给药每 12 小
洛巴坦 1.0g
时 1 次（0、12 和 24 小时），第 3 次给药后每 24
< 15† 小时 1 次†
对于目前正在接受本品且 CLcr 下降至 15
mL/min 以下的患者：每 24 小时 1 次
*CLcr=用 Cockcroft-Gault 方程估算的肌酐清除率
†对于接受血液透析的患者，应在透析疗程结束后给药
接受连续性肾脏替代治疗（CRRT）的患者
在这种情况下，提供剂量调整的信息有限，应根据患者的临床状态指导治疗。在
CRRT 期间，患者的残余肾功能可能发生变化，可能需要调整本品剂量。治疗过程中肾
功能可能发生变化，需定期监测肾功能，并相应调整本品剂量。
肝功能损害
尚未评估肝功能损害对舒巴坦和度洛巴坦药代动力学的影响。因舒巴坦和度洛巴
坦均未发生实质性肝脏代谢/排泄，预计肝功能损害不会影响本品消除。肝功能损害患
者无需调整剂量。
本品静脉给药用溶液的制备、储存和给药方法
本品为一种组合包装药盒，含 1.0 g 舒巴坦（无菌粉末）的一个透明单剂量小瓶和
每瓶含 0.5 g 度洛巴坦（无菌粉末）的两个棕色单剂量小瓶，静脉输注前须使用无菌操
作进行复溶和进一步稀释。本品不含抑菌防腐剂，已稀释的输注溶液，如果不立即使用，

需要在2-8℃的冷藏条件下储存（不得冷冻），并在使用前置于室温下复温（15-30分
钟）。每次静脉输注时间持续3小时，且从粉末溶解开始至输注结束的时间不得超过24小
时。未用完药液应丢弃。
本品制备所需项：
• 本品组合包装（包括1个每瓶含 1.0 g 舒巴坦的单剂量小瓶和 2 个每瓶含0.5 g 度洛
巴坦的单剂量小瓶）
• 含100 mL 0.9% 氯化钠注射液的输液袋
• 10 mL 无菌注射用水
• 10 mL 无菌注射器和酒精棉等消毒用品
本品的制备：
1. 加 5.0 mL 无菌注射用水至舒巴坦1.0 g单剂量小瓶，轻轻振摇至溶解。每个溶解小
瓶中含 1.0 g 舒巴坦/5.0 mL 澄清、无色至淡黄色溶液。复溶后溶液不能直接注射，
必须在静脉输注前稀释。稀释必须在复溶后 1 小时内进行。
2. 加 2.5 mL 无菌注射用水至每个度洛巴坦 0.5g 单剂量小瓶，轻轻振摇至溶解。每个
溶解小瓶中含 0.5 g 度洛巴坦/2.5 mL 澄清、淡黄色至橙色溶液。复溶后溶液不能直
接注射，必须在静脉输注前稀释。稀释必须在复溶后 1 小时内进行。
3. 为制备本品所需剂量，分别抽取5.0 mL舒巴坦复溶后溶液和5.0 mL（每小瓶 2.5
mL，共2瓶）度洛巴坦复溶后溶液，向100 mL 0.9% 氯化钠注射液输液袋中注入所
抽取体积的舒巴坦和度洛巴坦。本品未用完药液应丢弃。
在溶液和容器允许的情况下，给药前应目视检查注射用药品的颗粒物和变色情况。
制备好的本品溶液应为澄清、淡黄色至橙色，不含颗粒物。如果本品溶液浑浊或含有颗
粒物，请勿给药。
相容性
本品与 0.9%氯化钠注射液相容。
尚未确定本品与含其他药物或稀释剂的溶液给药相容性。本品不得与其他药物混合
或物理添加至含其他药物的溶液中。

## 四、肾功能调整

肾功能损害、血肌酐升高、中毒性肾病、肾衰和急性肾损伤。

## 五、肝功能调整

肝功能损害
尚未评估肝功能损害对舒巴坦和度洛巴坦药代动力学的影响。因舒巴坦和度洛巴
坦均未发生实质性肝脏代谢/排泄，预计肝功能损害不会影响本品消除。肝功能损害患
者无需调整剂量。
本品静脉给药用溶液的制备、储存和给药方法
本品为一种组合包装药盒，含 1.0 g 舒巴坦（无菌粉末）的一个透明单剂量小瓶和
每瓶含 0.5 g 度洛巴坦（无菌粉末）的两个棕色单剂量小瓶，静脉输注前须使用无菌操
作进行复溶和进一步稀释。本品不含抑菌防腐剂，已稀释的输注溶液，如果不立即使用，

需要在2-8℃的冷藏条件下储存（不得冷冻），并在使用前置于室温下复温（15-30分
钟）。每次静脉输注时间持续3小时，且从粉末溶解开始至输注结束的时间不得超过24小
时。未用完药液应丢弃。
本品制备所需项：
• 本品组合包装（包括1个每瓶含 1.0 g 舒巴坦的单剂量小瓶和 2 个每瓶含0.5 g 度洛
巴坦的单剂量小瓶）
• 含100 mL 0.9% 氯化钠注射液的输液袋
• 10 mL 无菌注射用水
• 10 mL 无菌注射器和酒精棉等消毒用品
本品的制备：
1. 加 5.0 mL 无菌注射用水至舒巴坦1.0 g单剂量小瓶，轻轻振摇至溶解。每个溶解小
瓶中含 1.0 g 舒巴坦/5.0 mL 澄清、无色至淡黄色溶液。复溶后溶液不能直接注射，
必须在静脉输注前稀释。稀释必须在复溶后 1 小时内进行。
2. 加 2.5 mL 无菌注射用水至每个度洛巴坦 0.5g 单剂量小瓶，轻轻振摇至溶解。每个
溶解小瓶中含 0.5 g 度洛巴坦/2.5 mL 澄清、淡黄色至橙色溶液。复溶后溶液不能直
接注射，必须在静脉输注前稀释。稀释必须在复溶后 1 小时内进行。
3. 为制备本品所需剂量，分别抽取5.0 mL舒巴坦复溶后溶液和5.0 mL（每小瓶 2.5
mL，共2瓶）度洛巴坦复溶后溶液，向100 mL 0.9% 氯化钠注射液输液袋中注入所
抽取体积的舒巴坦和度洛巴坦。本品未用完药液应丢弃。
在溶液和容器允许的情况下，给药前应目视检查注射用药品的颗粒物和变色情况。
制备好的本品溶液应为澄清、淡黄色至橙色，不含颗粒物。如果本品溶液浑浊或含有颗
粒物，请勿给药。
相容性
本品与 0.9%氯化钠注射液相容。
尚未确定本品与含其他药物或稀释剂的溶液给药相容性。本品不得与其他药物混合
或物理添加至含其他药物的溶液中。

## 六、治疗药物监测（TDM）

AUC = 从给药时至给药后 6 小时的血浆浓度时间曲线下面积；AUC = 从给药时至 24 小时的。血浆浓度时间曲线下面积；CL = 清除率；C = 峰浓度；ELF = 上皮细胞衬液；SD = 标准差，T

## 七、禁忌

- 已知对本品成份（舒巴坦和度洛巴坦）或其他 β-内酰胺类抗菌药物有严重超敏反应
- 史的患者应禁用本品（见【注意事项】）

## 八、特殊人群

- 妊娠/哺乳：孕妇
风险总结
本品
尚无在妊娠期间使用本品的数据用于评估发生重大出生缺陷、流产或其他母体或胎
儿不良结局的药物相关风险。
舒巴坦
现有已发表的关于几十年来妊娠期间联合使用舒巴坦与氨苄西林的病例数据，尚未
发现重大出生缺陷、流产或其他母体或胎儿不良结局的药物相关风险。已发表的文献报
告了舒巴坦可穿过
- 儿童：尚未确定本品在 18 岁以下儿童患者中使用的安全性和疗效。
- 老年：在试验 1 接受本品治疗的 91 例患者中，49 例（54%）为 65 岁及以上患者，包括 17
例（19%）76 岁及以上患者。临床研究没有纳入足够数量 65 岁及以上患者，以确定他
们的反应是否与年轻患者不同。
已知本品主要经肾脏排泄，老年患者更容易出现肾功能减退。应基于肾功能调整老
年患者的给

## 九、药物相互作用

- 有机阴离子转运蛋白 1（OAT1）抑制剂
- 与OAT1 抑制剂合并给药可能会增加舒巴坦的血药浓度。不建议本品与 OAT1 抑
- 制剂（如丙磺舒）合并给药（见【临床药理】）。

## 十、注意事项

：
• 超敏反应（见【注意事项】）
• 艰难梭菌相关性腹泻（CDAD）（见【注意事项】）
临床试验经验
已在 380 例成人受试者中评价了度洛巴坦联合或不联合舒巴坦的安全性，包括 6 项
I 期试验、1 项在复杂性尿路感染（cUTI）患者（包括急性肾盂肾炎）中的 II 期试验和
1 项在鲍曼-醋酸钙不动杆菌复合体所致感染（包括医院获得性细菌性肺炎（HABP）、呼
吸机相关性细菌性肺炎（VABP）和通气性肺炎（VP））成人患者中的 III 期试验（也被
称为试验 1） （见【临床试验】）。
在 III 期试验的随机、活性对照部分，91 例患者接受本品（1.0 g 舒巴坦和 1.0 g 度
洛巴坦，或根据肾功能调整剂量）静脉给药 3 小时，每 6 小时一次，86 例患者在多粘
菌素 E 2.5-5 mg/kg 初始负荷剂量给药后接受多粘菌素 E 2.5 mg/kg（或根据肾功能调整
剂量）静脉给药 30 分钟，每 12 小时一次。两个治疗组每 6 小时还接受一次 1.0g 亚胺
培南/1.0g 西司他丁（或根据肾功能调整剂量）静脉给药，作为鲍曼-醋酸钙不动杆菌复
合体以外的潜在 HABP/VABP 病原体的背景治疗。本品治疗的平均持续时间为 9 天，多
粘菌素 E 为 8 天。
严重不良反应和终止治疗
本品治疗组的 36 例患者（40%）和多粘菌素 E 治疗组的 42 例患者（49%）发生了
严重不良反应。11%（10/91）接受本品治疗的患者和 16%（14/86）接受多粘菌素 E 治
疗的患者因出现不良反应而终止治疗。1 例接受本品治疗的患者出现过敏性休克，导致
终止治疗。
常见不良反应
本品治疗组 88%（80/91）的患者和多粘菌素 E 治疗组 94%（81/86）的患者报告了
不良反应。接受本品治疗患者中最常报告的不良反应（>10%）为肝功能检查异常、腹
泻、贫血和低钾血症。表 2 列出了试验 1 中发生率>5%的不良反应。

表 2. 试验 1 中发生率>5%的不良反应
不良反应 XACDURO 多粘菌素E
(N=91) (N=86)
n (%) n (%)
任何不良反应 80 (88) 81 (94)
肝功能检查异常1 17 (19) 18 (21)
腹泻 15 (17) 9 (11)
贫血 12 (13) 12 (14)
低钾血症 11 (12) 9 (11)
心律失常 8 (9) 8 (9)
急性肾损伤2 5 (6) 31 (36)
血小板减少症 5 (6) 3 (4)
便秘 5 (6) 5 (6)
1 肝功能检查异常包括以下不良反应：肝功能检查异常、肝功能异常、转氨酶升高、丙氨酸氨基转移
酶升高和天门冬氨酸氨基转移酶升高；
2 急性肾损伤包括以下不良反应：肾功能损害、血肌酐升高、中毒性肾病、肾衰和急性肾损伤。

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/tobramycin-inhalation.md

```markdown
---
drugName: "妥布霉素吸入溶液"
brandNames:
  - ""
manufacturer: ""
dosageForm: "吸入溶液"
strengths:
  - "待从原版 PDF 提取"
atcCode: "J01GB01"
antibioticClass: "氨基糖苷类"
indications:
  - "待从原版 PDF 提取"
contraindications:
  - "待从原版 PDF 提取"
specialPopulations:
  - "待从原版 PDF 提取"
renalAdjustment: false
hepaticAdjustment: false
drugInteractions:
  - "待从原版 PDF 提取"
preparation: "待从原版 PDF 提取"
reviewDate: "2026-11-09"
tags:
  - "氨基糖苷类"
  - "吸入剂"
description: "妥布霉素吸入溶液，氨基糖苷类抗生素，说明书为扫描件，关键字段待人工核对后补充。"
draft: false
---

## 一、药品概述

妥布霉素吸入溶液，属于氨基糖苷类抗生素。

> **注意**：本品说明书 PDF 为扫描件（无文本层），以下临床关键字段待人工从原版 PDF 中提取后 1:1 填入。当前仅展示药品基本信息。

## 二、适应证

*待从原版 PDF 提取*

## 三、用法用量

*待从原版 PDF 提取*

## 四、肾功能调整

*待从原版 PDF 提取*

## 五、肝功能调整

*待从原版 PDF 提取*

## 六、禁忌

*待从原版 PDF 提取*

## 七、特殊人群

*待从原版 PDF 提取*

## 八、药物相互作用

*待从原版 PDF 提取*

## 九、注意事项

*待从原版 PDF 提取*

---

> 本内容基于药品说明书 PDF 文件，关键字段待人工核对。仅供专业学术参考，不能替代临床决策与药品说明书原文。
```

## src/content/drug-labels/voriconazole-injection.md

```markdown
---
drugName: "注射用伏立康唑"
brandNames:
  - "威凡®"
  - "Vfend®"
manufacturer: "辉瑞制药"
dosageForm: "注射用无菌粉末"
strengths:
  - "0.2g"
atcCode: "J02AC03"
antibioticClass: "三唑类抗真菌药"
indications:
  - "本品是一种广谱的三唑类抗真菌药，适用于治疗成人和2岁及2岁以上儿童患者的下列真菌"
  - "第1页，共31页"
  - "Version No:20251001"
  - "（1）侵袭性曲霉病。"
  - "（2）非中性粒细胞减少患者的念珠菌血症。"
  - "（3）对氟康唑耐药的念珠菌引起的严重侵袭性感染（包括克柔念珠菌）。"
  - "（4）由足放线病菌属和镰刀菌属引起的严重感染。"
  - "本品主要用于进展性、可能威胁生命的真菌感染患者的治疗。"
  - "预防接受异基因造血干细胞移植(HSCT)的高危患者的侵袭性真菌感染。"
contraindications:
  - "1、本品禁用于对其活性成份或其赋形剂超敏者"
  - "2、本品禁止与 CYP3A4 底物联合使用，包括特非那汀、阿司咪唑、西沙必利、匹莫齐特、"
  - "奎尼丁和伊伐布雷定等"
  - "因为本品可使上述药物的血药浓度增高，导致 QT 间期延长，并且偶见"
  - "尖端扭转性室性心动过速"
specialPopulations:
  - "妊娠/哺乳：孕妇 目前尚无足够数据来评价伏立康唑在孕妇中使用的安全性。 动物实验显示本品有生殖毒性，但对人体的潜在危险性尚未确定。 伏立康唑不宜用于孕妇，除非对母亲的益处显著大于对胎儿的潜在毒性。 育龄期妇女 育龄期妇女应用伏立康唑期间需采取有效的避孕措施。 哺乳期妇女 尚无伏立康唑在乳汁中分泌的资料。当开始使"
  - "儿童：2～<12 岁的儿童和轻体重青少年（12～14 岁且体重<50 kg）以及青少年（12～14 岁且体重 ≥50kg；15～17岁者）的安全有效性已经建立，应严格遵照所推荐的剂量应用，详见【用法用量】 项下内容。 本品在2岁以下儿童中的安全性和有效性尚未建立。"
  - "老年：一项多剂量口服给药的研究中，健康老年男性（≥65 岁）的 C 和 AUCτ 较健康年轻男性 max （18～45 岁）分别高 61%和 86%。但健康老年女性（≥65 岁）的 C 和 AUCτ 与健康年轻女性 max （18～45岁）无显著差异。 治疗研究中未按照年龄调整用药剂量。研究中观察了血药浓"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "）。在同时使用伏立康唑和皮质类固醇的患者中，也已有库欣综合征伴随"
  - "第12页，共31页"
  - "Version No:20251001"
  - "或不伴随继发肾上腺功能不全的报道。"
  - "对于接受伏立康唑和皮质类固醇（包括吸入性皮质类固醇，例如布地奈德和鼻内皮质类固醇）"
  - "长期治疗的患者，应在治疗期间和停用伏立康唑时密切监测肾上腺皮质功能障碍（见【药物相互"
  - "作用】）。如果出现库欣综合征或肾上腺功能不全的体征和症状，应指示患者立即就医。"
  - "14、长期治疗："
preparation: "详见说明书原文"
sourceUrl: "https://www.pfizer.com"
reviewDate: "2026-11-09"
tags:
  - "三唑类抗真菌药"
description: "注射用伏立康唑，三唑类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

注射用伏立康唑，三唑类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品是一种广谱的三唑类抗真菌药，适用于治疗成人和2岁及2岁以上儿童患者的下列真菌
- 第1页，共31页
- Version No:20251001
- （1）侵袭性曲霉病。
- （2）非中性粒细胞减少患者的念珠菌血症。
- （3）对氟康唑耐药的念珠菌引起的严重侵袭性感染（包括克柔念珠菌）。
- （4）由足放线病菌属和镰刀菌属引起的严重感染。
- 本品主要用于进展性、可能威胁生命的真菌感染患者的治疗。
- 预防接受异基因造血干细胞移植(HSCT)的高危患者的侵袭性真菌感染。

## 三、用法用量

1、静脉制剂的配制
溶解
未使用的产品或废弃材料应按当地规定进行处理。
伏立康唑粉针剂使用时先用 19ml 注射用水或者 19ml 氯化钠注射液(9mg/ml [0.9%])溶解成
20ml的澄清溶液，溶解后的浓度为10mg/ml。如果无法将稀释剂吸入粉针剂瓶，则弃去此瓶。推
荐使用标准20ml注射器（非自动化注射器），以保证在稀释时量取准确剂量（19ml）的注射用水
或者氯化钠注射液(9mg/ml [0.9%])。稀释后摇动药瓶直至药物粉末溶解。
本产品仅供单次使用，未用完的溶液应当丢弃。只有澄清、无颗粒的溶液才能使用。
用药时，已溶解好的浓缩液按所需量加到推荐的、相容的稀释液中(见下述)，最终配成含量为
0.5~5mg/ml的伏立康唑溶液。
稀释
伏立康唑必须以不高于 5 mg/mL 的浓度滴注，滴注时间须 1 至 3 小时。因此，浓度为 10
mg/mL 的伏立康唑应进一步稀释（可以作为稀释剂的溶液见下文）：
1. 根据患者体重，计算稀释10mg/mL伏立康唑浓缩液的所需体积（见表1）
2. 为加入所需体积的伏立康唑浓缩液，需从输注袋或输注瓶中吸掉和弃去至少同样体积的稀释
剂。当加入10mg/mL伏立康唑浓缩液时，输注袋或输注瓶中剩余的稀释剂应可使药物的最终
浓度介于0.5mg/mL和5mg/mL之间。
3. 使用合适体积的注射器和无菌技术，从相应数量的伏立康唑粉针剂瓶中吸取所需体积的伏立
康唑浓缩液，加入输注袋或输注瓶中。丢弃未用完的粉针剂瓶。
伏立康唑最终配制溶液的静脉滴注速度最快不超过每小时3mg/kg，滴注时间须1至3小时。
表1 所需10mg/mL伏立康唑浓缩液的体积
体重 10mg/mL伏立康唑的需要量
(kg)
3 mg/kg剂量 4 mg/kg剂 6 mg/kg剂量 8 mg/kg剂量 9 mg/kg剂量
（瓶数） 量（瓶数） （瓶数） （瓶数） （瓶数）
10 - 4.0 ml (1) - 8.0 ml (1) 9.0 ml (1)
15 - 6.0 ml (1) - 12.0 ml (1) 13.5 ml (1)
20 - 8.0 ml (1) - 16.0 ml (1) 18.0 ml (1)
25 - 10.0 ml (1) - 20.0 ml (1) 22.5 ml (2)
30 9.0 ml (1) 12.0 ml (1) 18.0 ml (1) 24.0 ml (2) 27.0 ml (2)
35 10.5 ml (1) 14.0 ml (1) 21.0 ml (2) 28.0 ml (2) 31.5 ml (2)
40 12.0 ml (1) 16.0 ml (1) 24.0 ml (2) 32.0 ml (2) 36.0 ml (2)

45 13.5 ml (1) 18.0 ml (1) 27.0 ml (2) 36.0 ml (2) 40.5 ml (3)
50 15.0 ml (1) 20.0 ml (1) 30.0 ml (2) 40.0 ml (2) 45.0 ml (3)
55 16.5 ml (1) 22.0 ml (2) 33.0 ml (2) 44.0 ml (3) 49.5 ml (3)
60 18.0 ml (1) 24.0 ml (2) 36.0 ml (2) 48.0 ml (3) 54.0 ml (3)
65 19.5 ml (1) 26.0 ml (2) 39.0 ml (2) 52.0 ml (3) 58.5 ml (3)
70 21.0 ml (2) 28.0 ml (2) 42.0 ml (3) - -
75 22.5 ml (2) 30.0 ml (2) 45.0 ml (3) - -
80 24.0 ml (2) 32.0 ml (2) 48.0 ml (3) - -
85 25.5 ml (2) 34.0 ml (2) 51.0 ml (3) - -
90 27.0 ml (2) 36.0 ml (2) 54.0 ml (3) - -
95 28.5 ml (2) 38.0 ml (2) 57.0 ml (3) - -
100 30.0 ml (2) 40.0 ml (2) 60.0 ml (3) - -
注射用伏立康唑为无防腐剂的单剂无菌冻干粉剂。因此，从微生物学的角度，稀释后必须立
即使用。如果不立即滴注，在使用前的保存时间和条件将由使用者负责，保存在2℃到8℃的温度
下，除非是在严格控制的、经过验证的无菌条件下进行溶解的，否则保存时间不得超过 24 小时。
伏立康唑可以采用下列注射液稀释：
9mg/ml (0.9%) 的氯化钠注射液
复方乳酸钠注射液
5%葡萄糖和复方乳酸钠注射液
5%葡萄糖和0.45%氯化钠注射液
5%葡萄糖注射液
含有2

## 四、肾功能调整

肾功能损害
中度到重度肾功能障碍（肌酐清除率<50ml/min）的患者应用本品时，可发生赋形剂磺丁基倍
他环糊精钠（SBECD）蓄积。此类患者宜选用口服给药，除非应用静脉制剂的利大于弊。这些患
者静脉给药时必须密切监测血清肌酐水平，如有异常增高应考虑改为口服给药。
伏立康唑可经血液透析清除，清除率为121ml/min。4小时血液透析仅能清除少许药物，无需
剂量调整。
静脉制剂的赋形剂磺丁基倍他环糊精钠（SBECD）在血液透析中的清除率为55ml/min。
6、肝功能损害
轻度至中度肝硬化患者（Child-Pugh A 和B）伏立康唑的负荷剂量不变，但维持剂量减半。
目前尚无伏立康唑应用于重度慢性肝硬化患者（Child-Pugh C）的研究。
伏立康唑治疗肝功检查异常患者（天门冬氨酸氨基转移酶（AST）、丙氨酸氨基转移酶（ALT）、
碱性磷酸酶（AP）异常或总胆红素高于正常上限5倍以上）的安全性数据非常有限。
有报道伏立康唑与肝功能检查异常增高和肝损害临床体征有关，如黄疸，因此严重肝功能损
害者应用本品时必须权衡利弊。
肝功能损害者应用本品时必须密切监测药物的毒性反应。
7、儿童用药
尚未在2岁以下儿童患者中评估本品的安全性和有效性。

## 五、肝功能调整

肝功能损害
轻度至中度肝硬化患者（Child-Pugh A 和B）伏立康唑的负荷剂量不变，但维持剂量减半。
目前尚无伏立康唑应用于重度慢性肝硬化患者（Child-Pugh C）的研究。
伏立康唑治疗肝功检查异常患者（天门冬氨酸氨基转移酶（AST）、丙氨酸氨基转移酶（ALT）、
碱性磷酸酶（AP）异常或总胆红素高于正常上限5倍以上）的安全性数据非常有限。
有报道伏立康唑与肝功能检查异常增高和肝损害临床体征有关，如黄疸，因此严重肝功能损
害者应用本品时必须权衡利弊。
肝功能损害者应用本品时必须密切监测药物的毒性反应。
7、儿童用药
尚未在2岁以下儿童患者中评估本品的安全性和有效性。

## 六、治疗药物监测（TDM）

氟氯西林 已有显著减少伏立康唑血药浓度的 如无法避免伏立康唑与氟氯西。 林合用，应密切监测伏立康唑。如，通过治疗药物监测）；可。[CYP3A4底物] 会增加Glasdegib的血药浓度并增加 进行ECG监测（见【注意事。替尼、塞瑞替尼、考比替尼、达拉 抑制剂的血药浓度。 行密切的临床监测（见【注意

## 七、禁忌

- 1、本品禁用于对其活性成份或其赋形剂超敏者
- 2、本品禁止与 CYP3A4 底物联合使用，包括特非那汀、阿司咪唑、西沙必利、匹莫齐特、
- 奎尼丁和伊伐布雷定等
- 因为本品可使上述药物的血药浓度增高，导致 QT 间期延长，并且偶见
- 尖端扭转性室性心动过速

## 八、特殊人群

- 妊娠/哺乳：孕妇
目前尚无足够数据来评价伏立康唑在孕妇中使用的安全性。
动物实验显示本品有生殖毒性，但对人体的潜在危险性尚未确定。
伏立康唑不宜用于孕妇，除非对母亲的益处显著大于对胎儿的潜在毒性。
育龄期妇女
育龄期妇女应用伏立康唑期间需采取有效的避孕措施。
哺乳期妇女
尚无伏立康唑在乳汁中分泌的资料。当开始使
- 儿童：2～<12 岁的儿童和轻体重青少年（12～14 岁且体重<50 kg）以及青少年（12～14 岁且体重
≥50kg；15～17岁者）的安全有效性已经建立，应严格遵照所推荐的剂量应用，详见【用法用量】
项下内容。
本品在2岁以下儿童中的安全性和有效性尚未建立。
- 老年：一项多剂量口服给药的研究中，健康老年男性（≥65 岁）的 C 和 AUCτ 较健康年轻男性
max
（18～45 岁）分别高 61%和 86%。但健康老年女性（≥65 岁）的 C 和 AUCτ 与健康年轻女性
max
（18～45岁）无显著差异。
治疗研究中未按照年龄调整用药剂量。研究中观察了血药浓

## 九、药物相互作用

- ）。在同时使用伏立康唑和皮质类固醇的患者中，也已有库欣综合征伴随
- 第12页，共31页
- Version No:20251001
- 或不伴随继发肾上腺功能不全的报道。
- 对于接受伏立康唑和皮质类固醇（包括吸入性皮质类固醇，例如布地奈德和鼻内皮质类固醇）
- 长期治疗的患者，应在治疗期间和停用伏立康唑时密切监测肾上腺皮质功能障碍（见【药物相互
- 作用】）。如果出现库欣综合征或肾上腺功能不全的体征和症状，应指示患者立即就医。
- 14、长期治疗：

## 十、注意事项

部分）。即使是各自使用不同的输液通路，
本品禁止和血液制品或短期输注的电解质浓缩液同时滴注。
全肠外营养液：使用本品时不需要停用全肠外营养液，但需要分不同的静脉通路滴注。如果
通过多腔管进行滴注，全肠外营养液需要使用与本品不同的端口。
本品禁止用4.2%碳酸氢钠溶液稀释。
2、剂量的一般考虑
本品在静脉滴注前先溶解成10mg/ml，再稀释至不高于5mg/ml的浓度。静脉滴注速度最快不
超过每小时3mg/kg，每瓶滴注时间须1至3小时。
稀释的注射用伏立康唑仅可用于静脉滴注，滴注时间为1至3小时。伏立康唑粉针剂不可用
于静脉推注。
在使用伏立康唑治疗前或治疗期间应监测血电解质，如存在低钾血症、低镁血症和低钙血症

等电解质紊乱应予以纠正。
成人用药
无论静脉滴注还是口服给药，第一天均应给予首次负荷剂量，使其血药浓度接近于稳态浓度。
由于口服剂型的生物利用度很高（96%），在有临床指征时口服和静脉滴注两种给药方法可以互换。
本品另有规格为50mg 和200mg的片剂，和40mg/ml干混悬剂。
3、推荐剂量及其调整和治疗持续时间
成人及青少年（12～14岁且体重≥50kg；15～17岁者）的推荐剂量：
静脉滴注 口服
患者体重≥40kg* 患者体重<40kg*
负荷剂量（适用 每12小时给药1次，每次6 每12小时给药1次，每次 每 12 小时给药 1 次，每次
于第 1 个 24 小 mg/kg 400 mg 200 mg
时）
维持剂量（开始 每日给药2次，每次4 mg/kg 每日给药 2 次，每次 200 每日给药2次，每次100 mg
用药 24 小时以 mg
后）
*适用于15岁或以上患者
治疗持续时间
治疗持续时间视患者用药后的临床疗效及微生物学检测结果而定，谨慎选择合理治疗时间。
见【注意事项】。
静脉用药的疗程不宜超过6个月。对于6个月以上的长期治疗，应仔细权衡获益与风险。
剂量调整（成人）
在使用本品治疗过程中，医生应当严密监测其潜在的不良反应，并根据患者具体情况及时调
整药物剂量，参见【不良反应】和【注意事项】。
如果患者治疗反应欠佳，口服给药的维持剂量可以增加到每日2次，每次300mg；体重<40kg
的患者，剂量调整为每日2次，每次150mg。
如果患者不能耐受上述较高的剂量，口服给药的维持剂量可以每次减50mg，逐渐减到每日2
次，每次200mg(体重<40kg的患者，减到每日2次，每次100mg)。
如果用于预防，请参见下文。
2岁～<12岁以下的儿童和轻体重青少年（12～14岁且体重<50kg者）
应按儿童剂量服用伏立康唑，因为与成人相比，这些青少年的伏立康唑代谢方式与儿童更相
似。
推荐的用药方案如下：
静脉 口服
负荷剂量 每12小时给药1次，每次9 mg/kg 未建议
（适用于第1个24小时）
维持治疗 每日给药2次，每次8mg/kg 每日给药2次，每次9 mg/kg（最
（开始用药24小时以后） 大单次剂量 350mg，每日2次）
备注：基于112例2岁～<12岁免疫缺陷儿童患者和26例12 岁～<17岁免疫缺陷青少年患者的群体药代动力学
分析结果。
建议通过静脉滴注疗法开始治疗，并且只在取得明显临床改善时才考虑口服疗法。请注意，
8 mg/kg静脉滴注时伏立康唑暴露量大约是9 mg/kg口服时伏立康唑暴露量的两倍。

儿童的推荐剂量是基于干混悬剂的研究。尚未在儿童中进行口服混悬剂和片剂的生物等效性
研究。考虑到儿童患者的胃肠通过时间可能较短，片剂在儿童的吸收可能与成人患者不同。因此
建议2～<12岁的儿童患者采

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/drug-labels/voriconazole-tablet.md

```markdown
---
drugName: "伏立康唑片"
brandNames:
  - "威凡®"
  - "Vfend®"
manufacturer: "辉瑞制药"
dosageForm: "片剂"
strengths:
  - "50mg"
  - "200mg"
atcCode: "J02AC03"
antibioticClass: "三唑类抗真菌药"
indications:
  - "本品是一种广谱的三唑类抗真菌药，适用于治疗成人和 2 岁及 2 岁以上儿童患者的下列"
  - "真菌感染："
  - "（1）侵袭性曲霉病。"
  - "（2）非中性粒细胞减少患者的念珠菌血症。"
  - "（3）对氟康唑耐药的念珠菌引起的严重侵袭性感染（包括克柔念珠菌）。"
  - "（4）由足放线病菌属和镰刀菌属引起的严重感染。"
  - "本品主要用于进展性、可能威胁生命的真菌感染患者的治疗。"
  - "预防接受异基因造血干细胞移植（HSCT）的高危患者的侵袭性真菌感染。"
contraindications:
  - "1、本品禁用于对其活性成份或其赋形剂过敏者"
  - "2、本品禁止与CYP3A4 底物联合使用，包括特非那汀，阿司咪唑，西沙必利，匹莫齐特，奎"
  - "尼丁和伊伐布雷定等"
  - "因为本品可使上述药物的血药浓度增高，导致QT间期延长，并且偶见"
  - "尖端扭转性室性心动过速"
specialPopulations:
  - "妊娠/哺乳：孕妇 目前尚无足够数据来评价伏立康唑在孕妇中使用的安全性。 动物实验显示本品有生殖毒性，但对人体的潜在危险性尚未确定。 伏立康唑不宜用于孕妇，除非对母亲的益处显著大于对胎儿的潜在毒性。 育龄期妇女 育龄期妇女应用伏立康唑期间需采取有效的避孕措施。 哺乳期妇女 尚无伏立康唑在乳汁中分泌的资料。当开始使"
  - "儿童：2～<12岁的儿童和轻体重青少年（12 ～ 14岁且体重 <50公斤）以及青少年（12～14岁 且体重≥50公斤；15～17岁者）的安全有效性已经建立，应严格遵照所推荐的剂量应用，详 见【用法用量】项下内容。 本品在2岁以下儿童中的安全性和有效性尚未建立。"
  - "老年：一项多剂量口服给药的研究中，健康老年男性（ 65岁）的 C 和 AUCτ 较健康年轻男 max 性（18～45岁）分别高61%和86%。但健康老年女性（ 65岁）的C 和AUCτ与健康年轻 max ≧ 女性（18～45岁）无显著差异。 ≧ 治疗研究中未按照年龄调整用药剂量。研究中观察了血药浓度与年龄"
renalAdjustment: true
hepaticAdjustment: true
drugInteractions:
  - "）。在同时使用伏立康唑和皮质类固醇的患者中，也已有"
  - "库欣综合征伴随或不伴随继发肾上腺功能不全的报道。"
  - "对于接受伏立康唑和皮质类固醇（包括吸入性皮质类固醇，例如布地奈德和鼻内皮质类"
  - "固醇）长期治疗的患者，应在治疗期间和停用伏立康唑时密切监测肾上腺皮质功能障碍（见【药"
  - "物相互作用】）。如果出现库欣综合征或肾上腺功能不全的体征和症状，应指示患者立即就医。"
  - "12、长期治疗："
  - "对于 180 天（6 个月）以上的长期暴露（治疗或预防），需仔细评估效益与风险平衡，因"
  - "此，医生应该考虑是否有必要限制伏立康唑的暴露量（见【用法用量】和【药理毒理】）。已有"
preparation: "详见说明书原文"
sourceUrl: "https://www.pfizer.com"
reviewDate: "2026-11-09"
tags:
  - "三唑类抗真菌药"
description: "伏立康唑片，三唑类抗真菌药，说明书 PDF 解析生成。"
draft: false
---

## 一、药品概述

伏立康唑片，三唑类抗真菌药。本文件由药品说明书 PDF 自动解析生成，仅供专业学术参考。

## 二、适应证

- 本品是一种广谱的三唑类抗真菌药，适用于治疗成人和 2 岁及 2 岁以上儿童患者的下列
- 真菌感染：
- （1）侵袭性曲霉病。
- （2）非中性粒细胞减少患者的念珠菌血症。
- （3）对氟康唑耐药的念珠菌引起的严重侵袭性感染（包括克柔念珠菌）。
- （4）由足放线病菌属和镰刀菌属引起的严重感染。
- 本品主要用于进展性、可能威胁生命的真菌感染患者的治疗。
- 预防接受异基因造血干细胞移植（HSCT）的高危患者的侵袭性真菌感染。

## 三、用法用量

1、剂量的一般考虑
伏立康唑薄膜衣片应至少在饭前1小时或者饭后1小时后服用。
在使用伏立康唑治疗前或治疗期间应监测血电解质，如存在低钾血症、低镁血症和低钙血
症等电解质紊乱应予以纠正。
成人
无论是静脉滴注还是口服给药,第一天均应给予首次负荷剂量，以使其血药浓度接近于稳
态浓度。由于口服制剂的生物利用度很高（96%），在有临床指征时口服和静脉滴注两种给药
方法可以互换。
本品另有规格为200mg注射用无菌粉末和40mg/ml干混悬剂。
2、推荐剂量及其调整和治疗持续时间
成人及青少年（12～14岁且体重≥50kg；15～17岁者）的推荐剂量：
静脉滴注 口服
患者体重≥40kg* 患者体重<40kg*
负荷剂量（适用 每12小时给药1次，每次6 每12小时给药1次，每次 每 12 小时给药 1 次，每次
于第 1 个 24 小 mg/kg 400 mg 200 mg
时）
维持剂量（开始 每日给药2次，每次4 mg/kg 每日给药 2 次，每次 200 每日给药2次，每次100 mg
用药 24 小时以 mg
后）
*适用于15岁或以上患者
治疗持续时间
治疗持续时间视患者用药后的临床疗效及微生物学检测结果而定，谨慎选择合理治疗时
间。见【注意事项】。
静脉用药的疗程不宜超过6个月。对于6个月以上的长期治疗，应仔细权衡获益与风险。
剂量调整（成人）
在使用本品治疗过程中，医生应当严密监测其潜在的不良反应，并根据患者具体情况及时
调整药物剂量，参见【不良反应】和【注意事项】。

如果患者治疗反应欠佳，口服给药的维持剂量可以增加到每日 2 次，每次 300mg；体重
<40kg的患者，剂量调整为每日2次，每次150mg。
如果患者不能耐受上述较高的剂量，口服给药的维持剂量可以每次减50mg，逐渐减到每
日2次，每次200mg（体重<40kg的患者，减到每日2次，每次100mg）。
如果用于预防，请参见下文。
2岁～<12岁以下的儿童和轻体重青少年（12～14岁且体重<50kg者）
应按儿童剂量服用伏立康唑，因为与成人相比，这些青少年的伏立康唑代谢方式与儿童更
相似。
推荐的用药方案如下：
静脉 口服
负荷剂量 每12小时给药1次，每次9 mg/kg 未建议
（适用于第1个24小时）
维持治疗 每日给药2次，每次8mg/kg 每日给药2次，每次9 mg/kg（最
（开始用药24小时以后） 大单次剂量 350mg，每日2次）
备注：基于112例2岁～<12岁免疫缺陷儿童患者和26例12 岁～<17岁免疫缺陷青少年患者的群体药代动
力学分析结果。
建议通过静脉滴注疗法开始治疗，并且只在取得明显临床改善时才考虑口服疗法。请注意，
8 mg/kg静脉滴注时伏立康唑暴露量大约是9 mg/kg口服时伏立康唑暴露量的两倍。
儿童的推荐剂量是基于干混悬剂的研究。尚未在儿童中进行口服混悬剂和片剂的生物等
效性研究。考虑到儿童患者的胃肠通过时间可能较短，片剂在儿童的吸收可能与成人患者不同。
因此建议2～<12岁的儿童患者采用口服干混悬剂配方。
对于所有其他青少年（12至14岁且体重≥50 kg；15至17岁任何体重），伏立康唑应按
成人剂量给药。
剂量调整（儿童[2至<12岁]和轻体重青少年[12至14岁且<50kg]）
如果患者反应欠佳，可按照 1 mg/kg 增加剂量（如果最初使用的最大口服剂量为 350 mg
时增幅为 50 mg）。如果患者无法耐受治疗，则按照 1 mg/kg 降低剂量（如果最初使用的最大
口服剂量为350 mg时降幅为50 mg）。
尚未对肝功能或肾功能不全的2～<12岁儿童患者应用本品进行研究。
成人及儿童中的预防
预防应当从移植当天开始且预防用药天数最长可为100天。应根据侵袭性真菌感染(IFI)的
发生风险尽可能缩短预防用药天数（根据中性粒细胞减少或免疫抑制确定）。只有当免疫抑制
或移植物抗宿主病(GvHD)持续时，移植后的最长预防用药天数才可持续至180天。
剂量
在各年龄组中推荐的预防给药方案与治疗给药方案相同。请参见上面的治疗给药方案表
格。

预防持续时间
尚未在临床试验中对伏立康唑使用时间超过180天的安全性和疗效进行充分的研究。
对于180天（6个月）以上的伏立康唑预防使用，需仔细评估效益与风险平衡。
以下内容同时适用于治疗和预防
剂量调整
对于预防使用，当缺乏疗效或发生治疗相关不良事件时，不建议调整剂量。如果发生治疗
相关不良事件，则必须考虑停用伏立康唑以及使用替代抗真菌药物。
合并用药时的剂量调整
与苯妥英合用时，建议伏立康唑的口服维持剂量从每日 2 次，每次 200mg 增加到每日 2
次，每次 400mg（体重<40kg 的患者，剂量从每日 2次，每次 100mg 增加到每日 2 次，每次
200mg

## 四、肾功能调整

肾功能损害
肾功能损害对本品口服给药的药代动力学没有影响。因此，轻度至重度肾功能损害者应用
本品均无需调整剂量。
伏立康唑可经血液透析清除，清除率为121ml/min。4小时的血液透析仅能清除少许药物，
无需调整剂量。
5、肝功能损害
轻度至中度肝硬化患者（Child-Pugh A 和B）伏立康唑的负荷剂量不变，但维持剂量减半。
目前尚无伏立康唑应用于重度慢性肝硬化患者（Child-Pugh C）的研究。
伏立康唑治疗肝功检查异常患者（天门冬氨酸氨基转移酶（AST）、丙氨酸氨基转移酶
（ALT）、碱性磷酸酶（AP）异常或总胆红素高于正常上限5倍以上）的安全性数据非常有限。
有报道伏立康唑与肝功能检查异常增高和肝损伤临床体征有关，如黄疸，因此严重肝功能
损害者应用本品时必须权衡利弊。
肝功能损害者应用本品时必须密切监测药物的毒性反应。

6、儿童用药
尚未在2岁以下儿童患者中评估本品的安全性和有效性。

## 五、肝功能调整

肝功能损害
轻度至中度肝硬化患者（Child-Pugh A 和B）伏立康唑的负荷剂量不变，但维持剂量减半。
目前尚无伏立康唑应用于重度慢性肝硬化患者（Child-Pugh C）的研究。
伏立康唑治疗肝功检查异常患者（天门冬氨酸氨基转移酶（AST）、丙氨酸氨基转移酶
（ALT）、碱性磷酸酶（AP）异常或总胆红素高于正常上限5倍以上）的安全性数据非常有限。
有报道伏立康唑与肝功能检查异常增高和肝损伤临床体征有关，如黄疸，因此严重肝功能
损害者应用本品时必须权衡利弊。
肝功能损害者应用本品时必须密切监测药物的毒性反应。

6、儿童用药
尚未在2岁以下儿童患者中评估本品的安全性和有效性。

## 六、治疗药物监测（TDM）

氟氯西林 已有显著减少伏立康唑血药浓度的 如无法避免伏立康唑与氟氯西林。 合用，应密切监测伏立康唑可能。治疗药物监测）；可能需要增加。[CYP3A4底物] 增加Glasdegib的血药浓度并增加QTc 行ECG监测（见【注意事。尼、塞瑞替尼、考比替尼、达拉非 制剂的血药浓度

## 七、禁忌

- 1、本品禁用于对其活性成份或其赋形剂过敏者
- 2、本品禁止与CYP3A4 底物联合使用，包括特非那汀，阿司咪唑，西沙必利，匹莫齐特，奎
- 尼丁和伊伐布雷定等
- 因为本品可使上述药物的血药浓度增高，导致QT间期延长，并且偶见
- 尖端扭转性室性心动过速

## 八、特殊人群

- 妊娠/哺乳：孕妇
目前尚无足够数据来评价伏立康唑在孕妇中使用的安全性。
动物实验显示本品有生殖毒性，但对人体的潜在危险性尚未确定。
伏立康唑不宜用于孕妇，除非对母亲的益处显著大于对胎儿的潜在毒性。
育龄期妇女
育龄期妇女应用伏立康唑期间需采取有效的避孕措施。
哺乳期妇女
尚无伏立康唑在乳汁中分泌的资料。当开始使
- 儿童：2～<12岁的儿童和轻体重青少年（12 ～ 14岁且体重 <50公斤）以及青少年（12～14岁
且体重≥50公斤；15～17岁者）的安全有效性已经建立，应严格遵照所推荐的剂量应用，详
见【用法用量】项下内容。
本品在2岁以下儿童中的安全性和有效性尚未建立。
- 老年：一项多剂量口服给药的研究中，健康老年男性（ 65岁）的 C 和 AUCτ 较健康年轻男
max
性（18～45岁）分别高61%和86%。但健康老年女性（ 65岁）的C 和AUCτ与健康年轻
max
≧
女性（18～45岁）无显著差异。
≧
治疗研究中未按照年龄调整用药剂量。研究中观察了血药浓度与年龄

## 九、药物相互作用

- ）。在同时使用伏立康唑和皮质类固醇的患者中，也已有
- 库欣综合征伴随或不伴随继发肾上腺功能不全的报道。
- 对于接受伏立康唑和皮质类固醇（包括吸入性皮质类固醇，例如布地奈德和鼻内皮质类
- 固醇）长期治疗的患者，应在治疗期间和停用伏立康唑时密切监测肾上腺皮质功能障碍（见【药
- 物相互作用】）。如果出现库欣综合征或肾上腺功能不全的体征和症状，应指示患者立即就医。
- 12、长期治疗：
- 对于 180 天（6 个月）以上的长期暴露（治疗或预防），需仔细评估效益与风险平衡，因
- 此，医生应该考虑是否有必要限制伏立康唑的暴露量（见【用法用量】和【药理毒理】）。已有

## 十、注意事项

。
静脉用药的疗程不宜超过6个月。对于6个月以上的长期治疗，应仔细权衡获益与风险。
剂量调整（成人）
在使用本品治疗过程中，医生应当严密监测其潜在的不良反应，并根据患者具体情况及时
调整药物剂量，参见【不良反应】和【注意事项】。

如果患者治疗反应欠佳，口服给药的维持剂量可以增加到每日 2 次，每次 300mg；体重
<40kg的患者，剂量调整为每日2次，每次150mg。
如果患者不能耐受上述较高的剂量，口服给药的维持剂量可以每次减50mg，逐渐减到每
日2次，每次200mg（体重<40kg的患者，减到每日2次，每次100mg）。
如果用于预防，请参见下文。
2岁～<12岁以下的儿童和轻体重青少年（12～14岁且体重<50kg者）
应按儿童剂量服用伏立康唑，因为与成人相比，这些青少年的伏立康唑代谢方式与儿童更
相似。
推荐的用药方案如下：
静脉 口服
负荷剂量 每12小时给药1次，每次9 mg/kg 未建议
（适用于第1个24小时）
维持治疗 每日给药2次，每次8mg/kg 每日给药2次，每次9 mg/kg（最
（开始用药24小时以后） 大单次剂量 350mg，每日2次）
备注：基于112例2岁～<12岁免疫缺陷儿童患者和26例12 岁～<17岁免疫缺陷青少年患者的群体药代动
力学分析结果。
建议通过静脉滴注疗法开始治疗，并且只在取得明显临床改善时才考虑口服疗法。请注意，
8 mg/kg静脉滴注时伏立康唑暴露量大约是9 mg/kg口服时伏立康唑暴露量的两倍。
儿童的推荐剂量是基于干混悬剂的研究。尚未在儿童中进行口服混悬剂和片剂的生物等
效性研究。考虑到儿童患者的胃肠通过时间可能较短，片剂在儿童的吸收可能与成人患者不同。
因此建议2～<12岁的儿童患者采用口服干混悬剂配方。
对于所有其他青少年（12至14岁且体重≥50 kg；15至17岁任何体重），伏立康唑应按
成人剂量给药。
剂量调整（儿童[2至<12岁]和轻体重青少年[12至14岁且<50kg]）
如果患者反应欠佳，可按照 1 mg/kg 增加剂量（如果最初使用的最大口服剂量为 350 mg
时增幅为 50 mg）。如果患者无法耐受治疗，则按照 1 mg/kg 降低剂量（如果最初使用的最大
口服剂量为350 mg时降幅为50 mg）。
尚未对肝功能或肾功能不全的2～<12岁儿童患者应用本品进行研究。
成人及儿童中的预防
预防应当从移植当天开始且预防用药天数最长可为100天。应根据侵袭性真菌感染(IFI)的
发生风险尽可能缩短预防用药天数（根据中性粒细胞减少或免疫抑制确定）。只有当免疫抑制
或移植物抗宿主病(GvHD)持续时，移植后的最长预防用药天数才可持续至180天。
剂量
在各年龄组中推荐的预防给药方案与治疗给药方案相同。请参见上面的治疗给药方案表
格。

预防持续时间
尚未在临床试验中对伏立康唑使用时间超过180天的安全性和疗效进行充分的研究。
对于180天（6个月）以上的伏立康唑预防使用，需仔细评估效益与风险平衡。
以下内容同时适用于治疗和预防
剂量调整
对于预防使用，当缺乏疗效或发生治疗相关不良事件时，不建议调整剂量。如果发生治疗
相关不良事件，则必须考虑停用伏立康唑以及使用替代抗真菌药物。
合并用药时的剂量调整
与苯妥英合用时，建议伏立康唑的口服维持剂量从每日 2 次，每次 200mg 增加到每日 2
次，每次 400mg（体重<40kg 的患者，剂量从每日 2次，每次 100mg 增加到每日 2 次，每次
200mg）。
伏立康唑应避免与利福布汀合用。如果必须联合使用时，建议伏立康

---

> 本内容由药品说明书 PDF 自动解析生成，仅供专业学术参考，不能替代临床决策与药品说明书原文。如有疑问请查阅原始说明书。
```

## src/content/guides/TEMPLATE.md

```markdown
---
title: "指南标题"
organization: "发布组织（如：IDSA/ATS）"
year: 2024
version: "2024 版"
sourceUrl: "https://example.com/guideline"
reviewDate: "2026-11-01"
syndromes:
  - "适用综合征/临床问题"
pathogens:
  - "涉及病原体"
antibioticClasses:
  - "抗菌药物分类"
tags:
  - "标签"
description: "一句话摘要"
draft: true
---

## 一、背景与适用范围

简述指南的制定背景、目标人群与核心临床问题。

## 二、诊断标准

列出关键诊断要点与分层依据。

## 三、经验性抗感染治疗

| 分层 | 首选方案 | 备选方案 | 疗程 |
|------|---------|---------|------|
| 轻症 |  |  |  |
| 中重症 |  |  |  |

## 四、目标性抗感染治疗

根据病原体药敏结果调整方案。

## 五、特殊人群

- 肾功能不全：
- 肝功能不全：
- 妊娠/哺乳期：
- 儿童：

## 六、关键参考文献

1. 原文链接见 frontmatter `sourceUrl`。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。超说明书用法请参阅原文并标注权威依据。
```

## src/content/guides/cap-2019.md

```markdown
---
title: "成人社区获得性肺炎诊疗指南"
organization: "IDSA/ATS"
year: 2019
version: "2019 版"
sourceUrl: "https://academic.oup.com/cid/article/71/6/e45/5518619"
reviewDate: "2026-10-15"
docType:
  - "指南"
infectionSites:
  - "肺部感染"
syndromes:
  - "社区获得性肺炎"
pathogens:
  - "肺炎链球菌"
  - "流感嗜血杆菌"
  - "支原体"
  - "衣原体"
  - "军团菌"
  - "病毒"
antibioticClasses:
  - "β-内酰胺类"
  - "大环内酯类"
  - "呼吸喹诺酮类"
tags:
  - "CAP"
  - "肺炎"
  - "抗感染"
description: "IDSA/ATS 2019 成人 CAP 诊疗指南摘要，涵盖经验性与目标性治疗方案。"
draft: false
---

## 一、背景与适用范围

本指南适用于免疫功能正常的成人社区获得性肺炎（CAP）患者，旨在规范抗菌药物的经验性与目标性使用，减少耐药并改善预后。

## 二、诊断标准

符合以下条件可临床诊断 CAP：
1. 新近出现的咳嗽、咳痰或原有呼吸道疾病症状加重，伴或不伴脓痰/胸痛/呼吸困难/咯血；
2. 发热；
3. 肺实变体征和/或闻及湿啰音；
4. 外周血白细胞计数异常；
5. 胸部影像学检查显示新出现的斑片状浸润性阴影。

## 三、经验性抗感染治疗

### 门诊患者

| 分层 | 首选方案 | 备选方案 |
|------|---------|---------|
| 无基础疾病 | 大环内酯类（如阿奇霉素） | 多西环素 |
| 有基础疾病或近 3 月用过抗菌药 | β-内酰胺类 + 大环内酯类，或呼吸喹诺酮单药 | — |

### 住院非 ICU 患者

- **首选**：β-内酰胺类 + 大环内酯类，或呼吸喹诺酮单药
- **青霉素过敏**：呼吸喹诺酮类 + 氨曲南

### ICU 患者

- **首选**：β-内酰胺类 + 大环内酯类，或 β-内酰胺类 + 呼吸喹诺酮类
- **疑有铜绿假单胞菌感染**：抗假单胞菌 β-内酰胺类 + 氟喹诺酮类/氨基糖苷类

## 四、目标性抗感染治疗

根据痰培养、血培养及非典型病原体血清学结果调整方案。肺炎链球菌青霉素 MIC ≤ 2 mg/L 仍可使用青霉素 G；MIC > 2 mg/L 改用头孢曲松或呼吸喹诺酮。

## 五、特殊人群

- **肾功能不全**：避免使用氨基糖苷类；万古霉素、左氧氟沙星需调整剂量。
- **妊娠**：首选青霉素类、头孢菌素类；禁用四环素、氟喹诺酮。
- **老年人**：关注药物相互作用（如喹诺酮延长 QTc）。

## 六、疗程

一般 5-7 天；非典型病原体感染可延长至 10-14 天；铜绿假单胞菌感染 14-21 天。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。
```

## src/content/guides/hap-vap-2016.md

```markdown
---
title: "成人医院获得性肺炎与呼吸机相关性肺炎指南"
organization: "IDSA/ATS"
year: 2016
version: "2016 版"
sourceUrl: "https://academic.oup.com/cid/article/63/5/e61/2456010"
reviewDate: "2026-10-20"
docType:
  - "指南"
infectionSites:
  - "肺部感染"
syndromes:
  - "医院获得性肺炎"
  - "呼吸机相关性肺炎"
pathogens:
  - "铜绿假单胞菌"
  - "鲍曼不动杆菌"
  - "肺炎克雷伯菌"
  - "金黄色葡萄球菌（MRSA）"
  - "肠杆菌属"
antibioticClasses:
  - "抗假单胞菌 β-内酰胺类"
  - "碳青霉烯类"
  - "糖肽类"
  - "氨基糖苷类"
  - "多黏菌素类"
tags:
  - "HAP"
  - "VAP"
  - "耐药菌"
  - "ICU"
description: "IDSA/ATS 2016 成人 HAP/VAP 指南摘要，重点关注耐药革兰阴性菌与 MRSA 的经验性覆盖。"
draft: false
---

## 一、背景与适用范围

适用于医院获得性肺炎（HAP）和呼吸机相关性肺炎（VAP）患者，核心目标是在经验性治疗中合理覆盖耐药菌，同时避免过度使用广谱抗菌药物。

## 二、经验性抗感染治疗

### VAP 患者

经验性方案需覆盖：
1. **金黄色葡萄球菌**（包括 MRSA）：万古霉素或利奈唑胺
2. **革兰阴性菌**（包括铜绿假单胞菌）：抗假单胞菌 β-内酰胺类（哌拉西林/他唑巴坦、头孢吡肟、亚胺培南、美罗培南）

### HAP 患者（非 VAP）

根据死亡率风险分层：
- **高死亡风险或有 MRSA 危险因素**：万古霉素/利奈唑胺 + 抗假单胞菌 β-内酰胺类
- **无 MRSA 危险因素**：抗假单胞菌 β-内酰胺类单药

### 多重耐药（MDR）危险因素

- 近 90 天内使用过抗菌药物
- 住院 ≥ 5 天
- 所在社区或医院科室耐药率高
- 免疫抑制

## 三、目标性抗感染治疗

| 病原体 | 首选 | 备选 |
|--------|------|------|
| 铜绿假单胞菌 | 哌拉西林/他唑巴坦、头孢吡肟、亚胺培南、美罗培南 | 氨曲南、多黏菌素 |
| 鲍曼不动杆菌 | 多黏菌素 + 利福平（耐药时） | 替加环素 |
| MRSA | 万古霉素、利奈唑胺 | 替考拉宁 |
| 产 ESBL 肠杆菌 | 碳青霉烯类 | 头孢他啶/阿维巴坦 |

## 四、降阶梯策略

在获得培养结果后 48-72 小时重新评估，应尽早降阶梯为窄谱抗菌药物。建议疗程 7 天，除非临床改善缓慢。

## 五、特殊人群

- **肾功能不全**：氨基糖苷类、万古霉素需 TDM 监测并调整剂量。
- **肝功能不全**：利奈唑胺需减量；避免使用高剂量利福平。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。
```

## src/content/guides/intra-abdominal-2017.md

```markdown
---
title: "腹腔感染治疗指南"
organization: "WSES"
year: 2017
version: "2017 版"
sourceUrl: "https://onlinelibrary.wiley.com/doi/full/10.1111/1749-4486.12261"
reviewDate: "2026-10-25"
docType:
  - "指南"
infectionSites:
  - "腹腔感染"
syndromes:
  - "腹腔感染"
  - "急性阑尾炎"
  - "胆囊炎"
  - "急性胰腺炎继发感染"
pathogens:
  - "大肠埃希菌"
  - "肺炎克雷伯菌"
  - "脆弱拟杆菌"
  - "肠球菌"
  - "铜绿假单胞菌"
antibioticClasses:
  - "广谱青霉素/酶抑制剂"
  - "第三代头孢菌素"
  - "碳青霉烯类"
  - "硝基咪唑类"
  - "氟喹诺酮类"
tags:
  - "IAI"
  - "腹腔感染"
  - "厌氧菌"
description: "WSES 2017 腹腔感染治疗指南摘要，涵盖社区获得性与医院获得性腹腔感染的经验性治疗。"
draft: false
---

## 一、背景与适用范围

本指南适用于社区获得性腹腔感染（CA-IAI）和医院获得性腹腔感染（HA-IAI），强调感染源控制与抗菌药物的合理使用并重。

## 二、社区获得性腹腔感染（CA-IAI）

### 轻中度感染

- **首选**：阿莫西林/克拉维酸，或莫西沙星单药
- **备选**：头孢曲松 + 甲硝唑

### 重度感染

- **首选**：哌拉西林/他唑巴坦，或厄他培南
- **备选**：头孢他啶/头孢吡肟 + 甲硝唑，或环丙沙星 + 甲硝唑

## 三、医院获得性腹腔感染（HA-IAI）

需覆盖革兰阴性杆菌（含铜绿假单胞菌）、革兰阳性球菌和厌氧菌。

- **首选**：哌拉西林/他唑巴坦、美罗培南、亚胺培南
- **备选**：头孢吡肟 + 甲硝唑，或环丙沙星 + 甲硝唑

## 四、感染源控制

- 应在诊断后尽快（24 小时内）进行感染源控制（手术或经皮引流）。
- 抗菌药物疗程：
  - 感染源已完全控制：4 天
  - 感染源控制困难：可延长至 7-10 天

## 五、特殊人群

- **妊娠**：首选青霉素类/头孢菌素类 + 甲硝唑；禁用氟喹诺酮、四环素。
- **肾功能不全**：避免氨基糖苷类；美罗培南、哌拉西林/他唑巴坦需调整剂量。

## 六、注意事项

- 不推荐常规使用抗肠球菌药物，除非存在高危因素（如既往接受过头孢菌素治疗、免疫抑制、复发性感染）。
- 不推荐经验性覆盖铜绿假单胞菌，除非有 HA-IAI 或 MDR 危险因素。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。
```

## src/content/guides/raw-4bd484cd6c.md

```markdown
---
title: "血液病恶性肿瘤患者侵袭性真菌病的诊断标准与治疗原则（第六次修订版）"
organization: "中国医师协会"
year: 2020
version: "2020版"
reviewDate: "2026-11-09"
docType:
  - "指南"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
imagingDiagnosis:
  - "TDM"
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
description: "· · 中华内科杂志 年 月第 卷第 期 754 2020 10 59 10 ChinJInternMed,October2020,Vol.59,No.10 ·标准与讨论· 血液病 恶性肿瘤患者侵袭性真菌病的诊断 标准与治疗原则（第六次修订版） 中国医师协会血液科医师分会 中国侵袭性真菌感染工作组 通信作者：黄晓军，北京大学人民医院血液科北京大学血液病研究所北京市造血干细 胞移植重点实验室 血液系统疾病国家临床医学研究中心 ， ： 100044 Email huangxiaojun@bjmu.edu.cn 【提要】"
draft: false
---

## 摘要

· · 中华内科杂志 年 月第 卷第 期 754 2020 10 59 10 ChinJInternMed,October2020,Vol.59,No.10 ·标准与讨论· 血液病 恶性肿瘤患者侵袭性真菌病的诊断 标准与治疗原则（第六次修订版） 中国医师协会血液科医师分会 中国侵袭性真菌感染工作组 通信作者：黄晓军，北京大学人民医院血液科北京大学血液病研究所北京市造血干细 胞移植重点实验室 血液系统疾病国家临床医学研究中心 ， ： 100044 Email huangxiaojun@bjmu.edu.cn 【提要】

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-77296625b0.md

```markdown
---
title: "两性霉素B不同剂型临床合理应用多学科专家共识（2024版）"
organization: "中国医药教育协会"
year: 2024
version: "2024版"
reviewDate: "2026-11-09"
docType:
  - "专家共识"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
  - "腹腔感染"
imagingDiagnosis:
  - "TDM"
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
  - "与多黏菌素对比"
description: "· · 中华内科杂志 年 月第 卷第 期 230 2024 3 63 3 Chin J Intern Med, March 2024, Vol. 63, No. 3 ·标准与讨论· 两性霉素 不同剂型临床合理应用多学科 专家共识（ 版） 中国医药教育协会真菌病专业委员会 通信作者：王睿，解放军总医院药剂科药物临床研究室，北京 ， ： 100039 Email ；黄晓军，北京大学人民医院 北京大学血液病研究所，北京 wangrui301@vip.sina.com ， ： ；俞云松，浙江省人民医院，杭州 ， 10004"
draft: false
---

## 摘要

· · 中华内科杂志 年 月第 卷第 期 230 2024 3 63 3 Chin J Intern Med, March 2024, Vol. 63, No. 3 ·标准与讨论· 两性霉素 不同剂型临床合理应用多学科 专家共识（ 版） 中国医药教育协会真菌病专业委员会 通信作者：王睿，解放军总医院药剂科药物临床研究室，北京 ， ： 100039 Email ；黄晓军，北京大学人民医院 北京大学血液病研究所，北京 wangrui301@vip.sina.com ， ： ；俞云松，浙江省人民医院，杭州 ， 10004

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-84ce3875de.md

```markdown
---
title: "中国毛霉病临床诊疗专家共识（2022）"
organization: "中国医药教育协会"
year: 2022
version: "2022版"
reviewDate: "2026-11-09"
docType:
  - "专家共识"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "中枢神经系统感染"
  - "腹腔感染"
imagingDiagnosis:
  - "TDM"
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
description: "中华内科杂志 年 月第 卷第 期 · · 2023 6 62 6 Chin J Intern Med, June 2023, Vol. 62, No. 6 597 ·标准与讨论· 中国毛霉病临床诊疗专家共识（ ） 中国医药教育协会真菌病专业委员会 中国毛霉病专家共识工作组 通信作者：李若瑜，北京大学第一医院皮肤性病科 北京大学真菌和真菌病研究中心 皮肤病分子诊断北京市重点实验室 国家皮肤与免疫疾病临床医学研究中心，北京 ， ： ；刘正印，中国医学科学院 北京协和医学院 北京协和 100034 Email mycol"
draft: false
---

## 摘要

中华内科杂志 年 月第 卷第 期 · · 2023 6 62 6 Chin J Intern Med, June 2023, Vol. 62, No. 6 597 ·标准与讨论· 中国毛霉病临床诊疗专家共识（ ） 中国医药教育协会真菌病专业委员会 中国毛霉病专家共识工作组 通信作者：李若瑜，北京大学第一医院皮肤性病科 北京大学真菌和真菌病研究中心 皮肤病分子诊断北京市重点实验室 国家皮肤与免疫疾病临床医学研究中心，北京 ， ： ；刘正印，中国医学科学院 北京协和医学院 北京协和 100034 Email mycol

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-ad60fe4289.md

```markdown
---
title: "重症患者侵袭性丝状真菌病诊断与治疗专家共识"
organization: "详见原文"
year: 2026
version: "2026版"
reviewDate: "2026-11-09"
docType:
  - "专家共识"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
  - "MRSA/VRE"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
  - "腹腔感染"
  - "皮肤软组织感染"
imagingDiagnosis:
  - "TDM"
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
  - "与多黏菌素对比"
description: "中华重症医学电子杂志 2026年8月 第12卷 第3期 Chin J Crit Care Intensive Care Med, August 2026, Vol.12, No.3 ·219· 重症患者侵袭性丝状真菌病诊断与治疗 黄英姿* 谢剑锋* 孙骎 余跃天 郑瑞强 席寅 陈轶坚 杜小幸 余进 杨婧 苏欣 邵华 黄丽丽 黎丽芬 吴昌德 吴骎 徐静媛 杨文杰 张俊丽 张曦文 周梦兰 王明贵 俞云松 邱海波 《重症患者侵袭性丝状真菌病诊断与治疗专家共识》专家组 随着重症救治、器官移植及免疫抑制治疗的 三、循证医学证"
draft: false
---

## 摘要

中华重症医学电子杂志 2026年8月 第12卷 第3期 Chin J Crit Care Intensive Care Med, August 2026, Vol.12, No.3 ·219· 重症患者侵袭性丝状真菌病诊断与治疗 黄英姿* 谢剑锋* 孙骎 余跃天 郑瑞强 席寅 陈轶坚 杜小幸 余进 杨婧 苏欣 邵华 黄丽丽 黎丽芬 吴昌德 吴骎 徐静媛 杨文杰 张俊丽 张曦文 周梦兰 王明贵 俞云松 邱海波 《重症患者侵袭性丝状真菌病诊断与治疗专家共识》专家组 随着重症救治、器官移植及免疫抑制治疗的 三、循证医学证

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-d5b8ada0b5.md

```markdown
---
title: "侵袭性霉菌感染实验室诊断临床应用专家共识"
organization: "中国医院协会"
year: 2024
version: "2024版"
reviewDate: "2026-11-09"
docType:
  - "专家共识"
pathogens:
  - "曲霉"
  - "毛霉"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
  - "皮肤软组织感染"
imagingDiagnosis:
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
  - "与多黏菌素对比"
description: "中华检验医学杂志 年 月第 卷第 期 · · 2024 6 47 6 Chin J Lab Med, June 2024, Vol. 47, No. 6 597 ·指南与共识· 侵袭性霉菌感染实验室诊断临床应用 中国初级卫生保健基金会检验医学研究与转化专业委员会 中国医院协会临床微 生物实验室专业委员会 全国真菌病监测网侵袭性霉菌感染监测项目组 通信作者：王贺， ： ；马筱玲， ： ；徐英春， Email raulshiny@163.com Email xiaolingma@126.com Email xycpum"
draft: false
---

## 摘要

中华检验医学杂志 年 月第 卷第 期 · · 2024 6 47 6 Chin J Lab Med, June 2024, Vol. 47, No. 6 597 ·指南与共识· 侵袭性霉菌感染实验室诊断临床应用 中国初级卫生保健基金会检验医学研究与转化专业委员会 中国医院协会临床微 生物实验室专业委员会 全国真菌病监测网侵袭性霉菌感染监测项目组 通信作者：王贺， ： ；马筱玲， ： ；徐英春， Email raulshiny@163.com Email xiaolingma@126.com Email xycpum

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-eb161f46d4.md

```markdown
---
title: "侵袭性肺真菌病诊断与治疗指南（2025年版）"
organization: "中华医学会"
year: 2025
version: "2025版"
reviewDate: "2026-11-09"
docType:
  - "指南"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
  - "腹腔感染"
imagingDiagnosis:
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
description: "· · 中华结核和呼吸杂志 年 月第 卷第 期 1104 2025 12 48 12 Chin J Tuberc Respir Dis, December 2025, Vol. 48, No. 12 ·诊疗方案· 侵袭性肺真菌病诊断与治疗指南 中华医学会呼吸病学分会 通信作者：叶枫，广州医科大学附属第一医院呼吸与危重症医学科国家呼吸医学中心 国家呼吸系统疾病临床医学研究中心 广州呼吸健康研究院 广州国家实验室，广州 ， ： ；瞿介明，上海交通大学医学院附属瑞金医院呼吸与危重 510163 Email yefeng@"
draft: false
---

## 摘要

· · 中华结核和呼吸杂志 年 月第 卷第 期 1104 2025 12 48 12 Chin J Tuberc Respir Dis, December 2025, Vol. 48, No. 12 ·诊疗方案· 侵袭性肺真菌病诊断与治疗指南 中华医学会呼吸病学分会 通信作者：叶枫，广州医科大学附属第一医院呼吸与危重症医学科国家呼吸医学中心 国家呼吸系统疾病临床医学研究中心 广州呼吸健康研究院 广州国家实验室，广州 ， ： ；瞿介明，上海交通大学医学院附属瑞金医院呼吸与危重 510163 Email yefeng@

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-efa87ab279.md

```markdown
---
title: "Management of Invasive Pulmonary Aspergillosis   FUNGINOS"
organization: "ECMM"
year: 2025
version: "2025版"
reviewDate: "2026-11-09"
docType:
  - "指南"
pathogens:
  - "MRSA/VRE"
infectionSites: []
imagingDiagnosis:
  - "TDM"
  - "肺部CT影像"
comparisons: []
description: "Mycoses GUIDELINES OPEN ACCESS Management of Invasive Pulmonary Aspergillosis in Intensive Care Units: Guidelines From the Fungal Infection Network of Switzerland (FUNGINOS) F. Lamoth1,2 | W. C. Albrich3 | S. Ragozzino4 | D. Bosetti5 | J. Delaloye6 | C. El Kho"
draft: false
---

## 摘要

Mycoses GUIDELINES OPEN ACCESS Management of Invasive Pulmonary Aspergillosis in Intensive Care Units: Guidelines From the Fungal Infection Network of Switzerland (FUNGINOS) F. Lamoth1,2 | W. C. Albrich3 | S. Ragozzino4 | D. Bosetti5 | J. Delaloye6 | C. El Kho

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/raw-f468b425d7.md

```markdown
---
title: "侵袭性真菌病真菌学检查指南"
organization: "中华医学会"
year: 2023
version: "2023版"
reviewDate: "2026-11-09"
docType:
  - "指南"
pathogens:
  - "曲霉"
  - "毛霉"
  - "念珠菌"
  - "隐球菌"
infectionSites:
  - "肺部感染"
  - "血流感染"
  - "中枢神经系统感染"
  - "腹腔感染"
  - "皮肤软组织感染"
imagingDiagnosis:
  - "肺部CT影像"
  - "真菌/耐药菌影像鉴别"
comparisons:
  - "与伏立康唑/艾沙康唑对比"
description: "中华检验医学杂志 年 月第 卷第 期 · · 2023 6 46 6 Chin J Lab Med, June 2023, Vol. 46, No. 6 541 ·指南与共识· 侵袭性真菌病真菌学检查指南 中国医疗保健国际交流促进会临床微生物学分会 中华医学会检验医学分会临床微 生物学组 中华医学会微生物学和免疫学分会微生物学组 通信作者：王辉， ： Email whuibj@163.com 【摘要】 侵袭性真菌病是感染病学、微生物学、临床药学等学科共同的焦点。欧洲癌症研究与治 疗组织和真菌研究小组教育与研究联合会"
draft: false
---

## 摘要

中华检验医学杂志 年 月第 卷第 期 · · 2023 6 46 6 Chin J Lab Med, June 2023, Vol. 46, No. 6 541 ·指南与共识· 侵袭性真菌病真菌学检查指南 中国医疗保健国际交流促进会临床微生物学分会 中华医学会检验医学分会临床微 生物学组 中华医学会微生物学和免疫学分会微生物学组 通信作者：王辉， ： Email whuibj@163.com 【摘要】 侵袭性真菌病是感染病学、微生物学、临床药学等学科共同的焦点。欧洲癌症研究与治 疗组织和真菌研究小组教育与研究联合会

---

> 本文档由 raw_materials/ 原始文件自动解析生成，仅抽取标题与摘要；正文内容请查阅原始 PDF/Word。内容严格对齐原文，未经任何改写。
```

## src/content/guides/ski-2014.md

```markdown
---
title: "皮肤及软组织感染诊断与管理指南"
organization: "IDSA"
year: 2014
version: "2014 版"
sourceUrl: "https://academic.oup.com/cid/article/59/2/e10/2853009"
reviewDate: "2026-11-01"
docType:
  - "指南"
infectionSites:
  - "皮肤软组织感染"
syndromes:
  - "皮肤软组织感染"
  - "蜂窝织炎"
  - "丹毒"
  - "脓肿"
  - "坏死性筋膜炎"
pathogens:
  - "金黄色葡萄球菌（MSSA/MRSA）"
  - "A 组链球菌"
  - "厌氧菌"
  - "肠杆菌科"
antibioticClasses:
  - "β-内酰胺酶抑制剂复合制剂"
  - "头孢菌素类"
  - "糖肽类"
  - "四环素类"
  - "硝基咪唑类"
tags:
  - "SSTI"
  - "皮肤感染"
  - "MRSA"
  - "蜂窝织炎"
description: "IDSA 2014 皮肤及软组织感染指南摘要，涵盖浅表感染至坏死性筋膜炎的分级治疗。"
draft: false
---

## 一、背景与适用范围

适用于成人皮肤及软组织感染（SSTI），根据感染深度和严重程度分级管理，重点关注 MRSA 的识别与覆盖。

## 二、非化脓性蜂窝织炎/丹毒

主要病原体为 A 组链球菌。

- **口服**：青霉素 VK、头孢氨苄、克林霉素
- **静脉**：青霉素 G、头孢唑林、克林霉素
- **疗程**：5 天，若未改善可延长

## 三、化脓性感染（脓肿、疖、痈）

主要病原体为金黄色葡萄球菌（包括 CA-MRSA）。

### 单纯脓肿

- **首选**：切开引流
- **抗菌药物指征**：重度感染、免疫抑制、全身中毒症状、高龄或年幼

### 经验性抗菌治疗

- **口服**：
  - TMP-SMX（160/800 mg bid）或
  - 多西环素（100 mg bid）或
  - 克林霉素（300 mg tid）
- **静脉**：
  - 万古霉素 15 mg/kg q12h 或
  - 利奈唑胺 600 mg q12h 或
  - 达托霉素 4 mg/kg qd

## 四、坏死性筋膜炎

**外科急诊**！应立即进行广泛清创。

### 经验性抗菌治疗

需覆盖革兰阳性、革兰阴性和厌氧菌：

- **方案 A**：哌拉西林/他唑巴坦 + 万古霉素
- **方案 B**：碳青霉烯类（亚胺培南/美罗培南）+ 万古霉素
- **方案 C**：第三代头孢菌素 + 甲硝唑 + 万古霉素

### 特异病原体

- **A 组链球菌**：青霉素 G + 克林霉素
- **创伤弧菌**：多西环素 + 头孢他啶
- **嗜水气单胞菌**：多西环素 + 环丙沙星

## 五、特殊人群

- **MRSA 高风险**：近期住院、近 90 天使用抗菌药物、静脉药瘾者、监狱/军营居住史。
- **免疫抑制**：糖尿病、HIV、长期糖皮质激素使用者需更积极的覆盖。

## 六、注意事项

- 不推荐对蜂窝织炎患者进行血培养（阳性率 < 5%）。
- 经验性治疗无需覆盖 MRSA，除非存在化脓性表现或 MRSA 危险因素。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。
```

## src/content/guides/uti-2019.md

```markdown
---
title: "成人泌尿系感染临床实践指南"
organization: "IDSA"
year: 2019
version: "2019 版"
sourceUrl: "https://academic.oup.com/cid/article/68/10/e83/5134252"
reviewDate: "2026-10-28"
docType:
  - "指南"
infectionSites:
  - "泌尿系感染"
syndromes:
  - "急性单纯性膀胱炎"
  - "急性肾盂肾炎"
pathogens:
  - "大肠埃希菌"
  - "肺炎克雷伯菌"
  - "奇异变形杆菌"
  - "肠球菌"
antibioticClasses:
  - "硝基呋喃类"
  - "磷霉素"
  - "第三代头孢菌素"
  - "氟喹诺酮类"
  - "甲氧苄啶/磺胺甲噁唑"
tags:
  - "UTI"
  - "泌尿系感染"
  - "膀胱炎"
  - "肾盂肾炎"
description: "IDSA 2019 成人泌尿系感染指南摘要，强调根据当地耐药率选择经验性治疗方案。"
draft: false
---

## 一、背景与适用范围

适用于非妊娠成人急性单纯性膀胱炎和急性肾盂肾炎，不包括复杂性尿路感染（如留置导尿管、尿路梗阻、免疫抑制）。

## 二、急性单纯性膀胱炎

### 经验性治疗

| 方案 | 剂量 | 疗程 |
|------|------|------|
| 呋喃妥因 | 100 mg bid | 5 天 |
| 磷霉素氨丁三醇 | 3 g 单剂 | 1 天 |
| TMP-SMX | 160/800 mg bid | 3 天 |
| 氟喹诺酮类（如左氧氟沙星） | 250 mg qd | 3 天 |

**用药原则**：
- 首选呋喃妥因或磷霉素，以减少对全身菌群的破坏。
- TMP-SMX 仅在当地大肠埃希菌耐药率 < 20% 时使用。
- 氟喹诺酮类作为二线，因不良反应和耐药选择压力。
- 不推荐 β-内酰胺类（氨苄西林、阿莫西林）作为经验性治疗。

## 三、急性肾盂肾炎

### 门诊口服治疗

- 氟喹诺酮类（环丙沙星 500 mg bid 或左氧氟沙星 750 mg qd），7-10 天
- 或第三代头孢菌素 + 单剂氨基糖苷类

### 住院静脉治疗

- 第三代头孢菌素（如头孢曲松 1 g qd）
- 或氟喹诺酮类静脉制剂
- 或氨基糖苷类 + 氨苄西林

## 四、特殊人群

- **妊娠**：首选头孢菌素类或阿莫西林/克拉维酸；禁用 TMP-SMX、氟喹诺酮、呋喃妥因（妊娠晚期）。
- **肾功能不全**：呋喃妥因 CrCl < 30 mL/min 禁用；氨基糖苷类需调整并监测。

## 五、注意事项

- 不推荐对无症状菌尿进行抗菌治疗（除非妊娠或泌尿外科手术前）。
- 经验性治疗前应留取尿培养，根据药敏结果调整方案。

---

> 本内容为人工整理的指南摘要，仅供专业学术参考，不能替代临床决策。
```

## src/data/auto/industry.json

```json
[
  {
    "id": "ind-8da7ed403d",
    "title": "中国侵袭性真菌病监测网：国内 ICU/血液科侵袭性真菌流行病学、曲霉毛霉耳念珠菌耐药趋势。",
    "eventTime": "2026-11-09",
    "publishTime": "2026-11-09T12:36:30.449669+08:00",
    "sourceName": "中国侵袭性真菌病监测网",
    "sourceUrl": "http://www.chinets.com",
    "category": "真菌与耐药",
    "tags": [
      "曲霉",
      "毛霉",
      "念珠菌",
      "耳念珠菌",
      "重症感染",
      "真菌与耐药"
    ],
    "summary": "国内 ICU/血液科侵袭性真菌流行病学、曲霉毛霉耳念珠菌耐药趋势。",
    "impact": "中国侵袭性真菌病监测网是真菌与耐药领域权威数据来源，建议持续关注其最新发布。",
    "scores": {
      "policyImpact": 9,
      "marketImpact": 7,
      "breakthrough": 5,
      "competitiveImpact": 7,
      "timelinessAuthority": 9,
      "totalScore": 37
    },
    "totalScore": 37,
    "isCluster": false,
    "factType": "fact"
  },
  {
    "id": "ind-33b4fda4e0",
    "title": "CHINET 中国细菌耐药监测网：全国三甲医院耐药菌（含 CRAB、CRE）最新变迁数据。",
    "eventTime": "2026-11-09",
    "publishTime": "2026-11-09T12:36:30.449611+08:00",
    "sourceName": "CHINET 中国细菌耐药监测网",
    "sourceUrl": "http://www.chinets.com",
    "category": "AMR",
    "tags": [
      "CRAB",
      "CRE",
      "AMR"
    ],
    "summary": "全国三甲医院耐药菌（含 CRAB、CRE）最新变迁数据。",
    "impact": "CHINET 中国细菌耐药监测网是AMR领域权威数据来源，建议持续关注其最新发布。",
    "scores": {
      "policyImpact": 10,
      "marketImpact": 8,
      "breakthrough": 3,
      "competitiveImpact": 8,
      "timelinessAuthority": 10,
      "totalScore": 39
    },
    "totalScore": 39,
    "isCluster": false,
    "factType": "fact"
  },
  {
    "id": "ind-d44dfe8901",
    "title": "GARDP（全球抗生素研发伙伴关系）：全球 AMR/CRAB 新药研发与可及性动向权威来源。",
    "eventTime": "2026-11-09",
    "publishTime": "2026-11-09T12:36:30.449498+08:00",
    "sourceName": "GARDP（全球抗生素研发伙伴关系）",
    "sourceUrl": "https://gardp.org/",
    "category": "AMR",
    "tags": [
      "CRAB",
      "AMR"
    ],
    "summary": "全球 AMR/CRAB 新药研发与可及性动向权威来源。",
    "impact": "GARDP（全球抗生素研发伙伴关系）是AMR领域权威数据来源，建议持续关注其最新发布。",
    "scores": {
      "policyImpact": 9,
      "marketImpact": 8,
      "breakthrough": 3,
      "competitiveImpact": 8,
      "timelinessAuthority": 8,
      "totalScore": 36
    },
    "totalScore": 36,
    "isCluster": false,
    "factType": "fact"
  },
  {
    "id": "ind-f5560b9f3a",
    "title": "Stewardship / Resistance Scan for Apr 02, 2020",
    "eventTime": "2020-04-02",
    "publishTime": "2020-04-02T20:15:55+00:00",
    "sourceName": "CIDRAP",
    "sourceUrl": "https://www.cidrap.umn.edu/antimicrobial-stewardship/stewardship-resistance-scan-apr-02-2020",
    "category": "真菌与耐药",
    "tags": [
      "CRE",
      "CT影像",
      "AI临床"
    ],
    "summary": "Stewardship / Resistance Scan for Apr 02, 2020 Jim Wappes Thu, 04/02/2020 - 15:15 Bullet points Antibiotic stewardship in Africa Antibiotic strategy for injection drug users Body Review finds dearth o",
    "impact": "来自CIDRAP的抗感染领域动态，涉及深部真菌感染诊疗进展，关注耐药菌（含 CRAB/CRE）流行病学与治疗策略，建议结合临床指南综合判断。",
    "scores": {
      "policyImpact": 10,
      "marketImpact": 10,
      "breakthrough": 3,
      "competitiveImpact": 10,
      "timelinessAuthority": 9,
      "totalScore": 42
    },
    "totalScore": 42,
    "isCluster": false,
    "factType": "fact"
  },
  {
    "id": "ind-905ee92f12",
    "title": "Stewardship / Resistance Scan for Aug 30, 2019",
    "eventTime": "2019-08-30",
    "publishTime": "2019-08-30T20:27:54+00:00",
    "sourceName": "CIDRAP",
    "sourceUrl": "https://www.cidrap.umn.edu/antimicrobial-stewardship/stewardship-resistance-scan-aug-30-2019",
    "category": "AMR",
    "tags": [
      "CRE",
      "CT影像",
      "AI临床",
      "重症感染"
    ],
    "summary": "Stewardship / Resistance Scan for Aug 30, 2019 Jim Wappes Fri, 08/30/2019 - 15:27 Bullet points Infection-linked pancreatic scopes Oral antibiotic for skin infections Resistant enterococci in Germany ",
    "impact": "来自CIDRAP的抗感染领域动态，关注耐药菌（含 CRAB/CRE）流行病学与治疗策略，建议结合临床指南综合判断。",
    "scores": {
      "policyImpact": 10,
      "marketImpact": 8,
      "breakthrough": 3,
      "competitiveImpact": 8,
      "timelinessAuthority": 10,
      "totalScore": 39
    },
    "totalScore": 39,
    "isCluster": false,
    "factType": "fact"
  },
  {
    "id": "ind-3427ce9256",
    "title": "Stewardship / Resistance Scan for Mar 18, 2019",
    "eventTime": "2019-03-18",
    "publishTime": "2019-03-18T21:19:23+00:00",
    "sourceName": "CIDRAP",
    "sourceUrl": "https://www.cidrap.umn.edu/antimicrobial-stewardship/stewardship-resistance-scan-mar-18-2019",
    "category": "AMR",
    "tags": [
      "CRE",
      "CT影像",
      "AI临床"
    ],
    "summary": "Stewardship / Resistance Scan for Mar 18, 2019 Jim Wappes Mon, 03/18/2019 - 16:19 Bullet points Drop in US antibiotic prescribing Short course for Pseudomonas Antibiotic cardiac device 'envelope' Body",
    "impact": "来自CIDRAP的抗感染领域动态，关注耐药菌（含 CRAB/CRE）流行病学与治疗策略，建议结合临床指南综合判断。",
    "scores": {
      "policyImpact": 10,
      "marketImpact": 8,
      "breakthrough": 3,
      "competitiveImpact": 8,
      "timelinessAuthority": 9,
      "totalScore": 38
    },
    "totalScore": 38,
    "isCluster": false,
    "factType": "fact"
  }
]
```

## src/data/auto/research.json

```json
[
  {
    "id": "res-206c6d4f59",
    "title": "Mycology Online（阿德莱德真菌网）：临床真菌鉴别与影像图谱知识库。",
    "sourceName": "Mycology Online（阿德莱德真菌网）",
    "sourceUrl": "https://mycology.adelaide.edu.au/",
    "studyType": "review",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.449553+08:00",
    "coreFindings": "临床真菌鉴别与影像图谱知识库。",
    "limitations": "本条目为权威机构静态知识库入口，具体内容请访问原网站。",
    "inspiration": "Mycology Online（阿德莱德真菌网）是真菌与耐药领域权威来源，建议定期跟踪其指南更新与监测数据。",
    "evidenceLevel": "专家共识/权威机构指南",
    "scores": {
      "topicInspiration": 8,
      "clinicalApplicability": 10,
      "evidenceLevel": 6,
      "specialtyUniversality": 7,
      "researchValue": 7,
      "totalScore": 38
    },
    "totalScore": 38,
    "isPreprint": false,
    "tags": [
      "感染影像",
      "真菌与耐药"
    ]
  },
  {
    "id": "res-9f634c9fd2",
    "title": "ISHAM（国际人畜真菌学会）：国际临床真菌学与 TDM 权威学术组织。",
    "sourceName": "ISHAM（国际人畜真菌学会）",
    "sourceUrl": "https://www.isham.org/",
    "studyType": "review",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.449433+08:00",
    "coreFindings": "国际临床真菌学与 TDM 权威学术组织。",
    "limitations": "本条目为权威机构静态知识库入口，具体内容请访问原网站。",
    "inspiration": "ISHAM（国际人畜真菌学会）是真菌与耐药领域权威来源，建议定期跟踪其指南更新与监测数据。",
    "evidenceLevel": "专家共识/权威机构指南",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 6,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 35
    },
    "totalScore": 35,
    "isPreprint": false,
    "tags": [
      "TDM",
      "真菌与耐药"
    ]
  },
  {
    "id": "res-06f7980e14",
    "title": "ECMM（欧洲医学真菌学联合会）：欧洲医学真菌学权威机构，发布曲霉、毛霉、念珠菌指南与药敏折点更新。",
    "sourceName": "ECMM（欧洲医学真菌学联合会）",
    "sourceUrl": "https://www.ecmm.info/",
    "studyType": "review",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.449379+08:00",
    "coreFindings": "欧洲医学真菌学权威机构，发布曲霉、毛霉、念珠菌指南与药敏折点更新。",
    "limitations": "本条目为权威机构静态知识库入口，具体内容请访问原网站。",
    "inspiration": "ECMM（欧洲医学真菌学联合会）是真菌与耐药领域权威来源，建议定期跟踪其指南更新与监测数据。",
    "evidenceLevel": "专家共识/权威机构指南",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 7,
      "specialtyUniversality": 6,
      "researchValue": 8,
      "totalScore": 37
    },
    "totalScore": 37,
    "isPreprint": false,
    "tags": [
      "曲霉",
      "毛霉",
      "念珠菌",
      "真菌与耐药"
    ]
  },
  {
    "id": "res-5162e7ca77",
    "title": "Discovery of a pyrrole-enone hybrid from deep-sea cold-seep-derived Aspergillus sp. exhibiting anti-renal fibrotic activity associated with the attenuation of p38 MAPK phosphorylation.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42987739/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.449300+08:00",
    "coreFindings": "Chen Y, She J, Cai J et al. Bioorganic chemistry. 2026 Oct 31.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床"
    ]
  },
  {
    "id": "res-c146b12a60",
    "title": "Aspergillus species isolation in respiratory samples from patients with respiratory syncytial virus: An 11-year retrospective single-center cohort study.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42988260/",
    "studyType": "cohort",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.449131+08:00",
    "coreFindings": "Maldonado-Barrueco A, Amoroto-Bengoetxea M, Lozano-Fernández G et al. Revista iberoamericana de micologia. 2026 Nov 5.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "2b（队列研究）",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 7,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 36
    },
    "totalScore": 36,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-28c6c4fbfa",
    "title": "Machine Learning based Classification of Ocular Pathogens using Host-transcriptomic Signatures: a proof-of-concept.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42990524/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.448947+08:00",
    "coreFindings": "Plumber MT, Kumar R, Yadavalli T et al. Research square. 2026 Oct 27.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "AI 辅助诊断/决策方向，可探索多中心验证与临床落地路径。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 7,
      "evidenceLevel": 5,
      "specialtyUniversality": 5,
      "researchValue": 8,
      "totalScore": 32
    },
    "totalScore": 32,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-453c2c2c87",
    "title": "Development and Optimization of a PCR-RFLP Method for Differentiation of Aspergillus flavus From Aspergillus parasiticus.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42991681/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.448630+08:00",
    "coreFindings": "Sohrabi N, Taghizadeh M et al. Archives of Razi Institute. 2026 Jan.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "重症感染"
    ]
  },
  {
    "id": "res-d41e60062a",
    "title": "Secondary Pasteurella multocida Infection Complicating Allergic Bronchopulmonary Aspergillosis During Dupilumab Therapy: A Case Report.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42992349/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.448475+08:00",
    "coreFindings": "Suzuki K, Kai Y, Uno K et al. Respirology case reports. 2026 Nov.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床"
    ]
  },
  {
    "id": "res-1fafe70ca9",
    "title": "Identification of soluble immune markers for the diagnosis of aspergillosis and pneumocystosis: an exploratory study.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42992594/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.448317+08:00",
    "coreFindings": "Chantelot L, Amar Y, Duchateau M et al. Medical mycology. 2026 Nov 6.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": []
  },
  {
    "id": "res-11847d7921",
    "title": "Clinical characteristics of ICU patients with gastrointestinal colonisation by Candida auris.",
    "sourceName": "PubMed (曲霉 / 毛霉 / 耳念珠菌)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42996535/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.447944+08:00",
    "coreFindings": "Fang L, Duan Y, Cai D et al. Frontiers in cellular and infection microbiology. 2026.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床",
      "重症感染"
    ]
  },
  {
    "id": "res-173b5f90a6",
    "title": "In Vitro Activity of Cefiderocol against Carbapenem-Resistant Klebsiella pneumoniae, Pseudomonas aeruginosa, and Acinetobacter baumannii and the Cefiderocol Resistance Mechanisms.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42982121/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.447501+08:00",
    "coreFindings": "Wong JH, Woon JJ, Ponnampalavanar SSS et al. Journal of global antimicrobial resistance. 2026 Nov 4.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 6,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 36
    },
    "totalScore": 36,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床"
    ]
  },
  {
    "id": "res-bd178acd04",
    "title": "Risk factors for Gram-negative bacterial bloodstream infections: a systematic review and meta-analysis with subgroup analyses for carbapenem-resistant organisms and Acinetobacter baumannii.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42983247/",
    "studyType": "meta-analysis",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.447327+08:00",
    "coreFindings": "Zhang W, Ye M, Xu W et al. BMC infectious diseases. 2026 Aug 8.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "1a（系统综述/Meta 分析）",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 9,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 39
    },
    "totalScore": 39,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-de1aa259ef",
    "title": "Trend of carbapenemase changes and epidemiological distribution of carbapenem-resistant Klebsiella pneumoniae clinically isolated in a hospital: a single-center retrospective study from 2015 to 2024.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42984617/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.447146+08:00",
    "coreFindings": "Wang Z, Hu H, Wang S et al. Frontiers in public health. 2026.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 35
    },
    "totalScore": 35,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-c626cb096c",
    "title": "Clinical outcomes of oral minocycline-based regimens in carbapenem-resistant Acinetobacter baumannii pneumonia: A retrospective cohort study.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42987752/",
    "studyType": "cohort",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.446973+08:00",
    "coreFindings": "Lee S, Jeon CH, Kim HT et al. Journal of infection and public health. 2026 Oct 30.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "2b（队列研究）",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 7,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 37
    },
    "totalScore": 37,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-1752997155",
    "title": "The evolution of carbapenem-resistant Klebsiella pneumoniae in Greek intensive care units is driven by local carbapenemase acquisition, nationwide nosocomial spread and emerging resistance to novel antimicrobials.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42988224/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.446797+08:00",
    "coreFindings": "Baltas I, Vrioni G, Romero-Rodriguez OA et al. The Journal of infection. 2026 Nov 5.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 35
    },
    "totalScore": 35,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-f8722ef034",
    "title": "Clinical infection and molecular characteristics of carbapenem-resistant organisms among children in China, 2016-2025.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42989078/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.446496+08:00",
    "coreFindings": "Li H, Zhang H, Ye X et al. BMC microbiology. 2026 Aug 10.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 35
    },
    "totalScore": 35,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-5b8ab0a7d6",
    "title": "Risk factors and molecular epidemiology of ST2-type carbapenem-resistant Acinetobacter baumannii carrying bla(OXA-23-like) and bla(OXA-51-like) genes.",
    "sourceName": "PubMed (CRAB / CRE 耐药)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42989095/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.446246+08:00",
    "coreFindings": "Xia Y, Chen X, Sun XW et al. BMC microbiology. 2026 Aug 11.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 10,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 35
    },
    "totalScore": 35,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-2d6002e967",
    "title": "Fungal pneumonia in non-neutropenic critically ill patients: a Delphi consensus from the Fungal Infection Study Forum, India, with implications for resource-limited settings.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42972511/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.445645+08:00",
    "coreFindings": "Muthu V, Agarwal R, Sehgal IS et al. BMC infectious diseases. 2026 Aug 4.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-d2dd09a846",
    "title": "Phaeohyphomycosis as a rare cause of brain abscess in immunocompetent patients: Report of two cases.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42974217/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.445468+08:00",
    "coreFindings": "Bertolaccini Scolin EM, Araujo ABA, Barros EA et al. Surgical neurology international. 2026.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "AI临床"
    ]
  },
  {
    "id": "res-c44e40f7f9",
    "title": "From presumed metastasis to infection: coccidioidomycosis mimicking metastatic gastroesophageal adenocarcinoma.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42977282/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.445184+08:00",
    "coreFindings": "Diaz Fernandez W, Leggett C et al. Revista de gastroenterologia del Peru : organo oficial de la Sociedad de Gastroenterologia del Peru. 2026 Jul-Sep.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-3ba850e386",
    "title": "Isolated vocal cord aspergillosis in an immunocompetent 60-year-old woman: A rare case report with radiological findings.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42991644/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.444902+08:00",
    "coreFindings": "Belkacemi A, Bellarbi S, Jbara A et al. Radiology case reports. 2026 Dec.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 8,
      "clinicalApplicability": 10,
      "evidenceLevel": 5,
      "specialtyUniversality": 7,
      "researchValue": 7,
      "totalScore": 37
    },
    "totalScore": 37,
    "isPreprint": false,
    "tags": []
  },
  {
    "id": "res-a71b09baec",
    "title": "Dynamic Radiologic Severity Index is associated with antifungal treatment but does not independently predict initiation in pediatric acute lymphoblastic leukemia with post-chemotherapy pneumonia.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42996382/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.444732+08:00",
    "coreFindings": "Gao Z, Tao X, Chen R et al. Translational pediatrics. 2026 Oct 30.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 8,
      "clinicalApplicability": 10,
      "evidenceLevel": 6,
      "specialtyUniversality": 7,
      "researchValue": 7,
      "totalScore": 38
    },
    "totalScore": 38,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  },
  {
    "id": "res-972aabed18",
    "title": "Differential diagnosis of pulmonary Talaromyces marneffei infection and pulmonary tuberculosis in HIV/AIDS patients using a CT-based multimodal 2.5D deep learning approach.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42996560/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.444541+08:00",
    "coreFindings": "Song C, Zhao CY, Lin XS et al. Frontiers in cellular and infection microbiology. 2026.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "AI 辅助诊断/决策方向，可探索多中心验证与临床落地路径。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 8,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 8,
      "totalScore": 36
    },
    "totalScore": 36,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床"
    ]
  },
  {
    "id": "res-979b349cc2",
    "title": "Tonsillar mucormycosis in an immunocompetent young woman: a case report.",
    "sourceName": "PubMed (鲍曼不动杆菌 / 真菌感染 + 影像)",
    "sourceUrl": "https://pubmed.ncbi.nlm.nih.gov/42999891/",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-11-09T12:36:30.444255+08:00",
    "coreFindings": "Haddad M, Sheidae Mehne Z, Mahmoudi Hashemi SF et al. IDCases. 2026.",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "深部真菌感染诊疗方向，可结合药敏与 TDM 数据设计临床研究。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": []
  },
  {
    "id": "res-3cf1796695",
    "title": "Artificial Intelligence in Infectious Diseases and Clinical Microbiology",
    "sourceName": "IDCM Journal",
    "sourceUrl": "/ai-in-infectious-diseases-and-clinical-microbiology",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-09-30T09:50:02+00:00",
    "coreFindings": "Artificial intelligence (AI) is a branch of computer science that develops computational systems capable of performing tasks that typically require human intelligence, including pattern recognition, prediction, and decision support. Artificial intelligence [...]",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "AI 辅助诊断/决策方向，可探索多中心验证与临床落地路径。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 6,
      "evidenceLevel": 5,
      "specialtyUniversality": 5,
      "researchValue": 8,
      "totalScore": 31
    },
    "totalScore": 31,
    "isPreprint": false,
    "tags": [
      "CT影像",
      "AI临床"
    ]
  },
  {
    "id": "res-564a60ac57",
    "title": "Eleven-Year Trends in Antimicrobial Resistance and Isolation Rates per 1000 Patient-Days of Key Gram-Positive and Gram-Negative Bacteria in a Tertiary Care Hospital in Türkiye (2014–2024)",
    "sourceName": "IDCM Journal",
    "sourceUrl": "/trends-in-amr-and-bacterial-isolation-rates-turkiye-2014-2024",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-09-30T09:46:11+00:00",
    "coreFindings": "Antimicrobial resistance (AMR) is a critical global health threat, contributing to increased mortality and substantial economic costs. The World Bank has projected an additional USD 1 trillion in healthcare costs by 2050 [...]",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CRE",
      "AMR",
      "CT影像"
    ]
  },
  {
    "id": "res-8bc0b66c54",
    "title": "Invasive Non-typhoidal Salmonella Infections in Adults: Clinical Features, Focal Disease, and Antimicrobial Resistance in a Turkish Tertiary-Care Center",
    "sourceName": "IDCM Journal",
    "sourceUrl": "/adult-ints-infections-in-turkiye",
    "studyType": "other",
    "publishStatus": "published",
    "sampleSize": null,
    "publishTime": "2026-09-30T09:38:25+00:00",
    "coreFindings": "Non-typhoidal serovars of Salmonella enterica are an important cause of morbidity and mortality worldwide. Although they typically cause self-limiting gastroenteritis, they can invade the bloodstream and other normally sterile [...]",
    "limitations": "本条目为 RSS 自动采集摘要，研究设计与统计方法细节请查阅原文。",
    "inspiration": "耐药菌（CRAB/CRE 等）诊疗方向，可启发耐药监测与新药临床研究课题。",
    "evidenceLevel": "待评估",
    "scores": {
      "topicInspiration": 7,
      "clinicalApplicability": 9,
      "evidenceLevel": 5,
      "specialtyUniversality": 6,
      "researchValue": 7,
      "totalScore": 34
    },
    "totalScore": 34,
    "isPreprint": false,
    "tags": [
      "CT影像"
    ]
  }
]
```

## src/data/manual/ai-tools.json

```json
{
  "updated": "2026-11-10",
  "featured": [
    {
      "name": "KnowS 医学 AI",
      "badge": "6000积分福利",
      "desc": "懂医学的 AI 助手（服务教研全场景、SCI撰写、国自然、医学绘图、PPT）",
      "qr": "/images/knows-qr.png",
      "channels": [
        { "label": "福利", "value": "扫码认证领取 6000 智能体积分" }
      ]
    },
    {
      "name": "WorkBuddy 办公搭子",
      "badge": "2000积分福利",
      "desc": "中国最受欢迎的 AI 办公伙伴（协助搞定 PPT、数据分析、工作大小事）",
      "qr": "/images/workbuddy-qr.png",
      "channels": [
        { "label": "福利", "value": "扫码注册获取 2000 积分" }
      ]
    },
    {
      "name": "感御 / AI抗感先锋",
      "badge": "抗感染专业 AI 工具矩阵",
      "desc": "聚焦抗感染热点与智能医学工具（小程序/公众号）",
      "qr": "/images/ganyu-qr.png",
      "channels": [
        { "label": "网页端", "value": "https://ganyu.medknows.com" },
        { "label": "微信公众号", "value": "搜索并关注「AI抗感先锋」" },
        { "label": "微信小程序", "value": "微信搜索「感御」" }
      ]
    }
  ],
  "categories": [
    { "key": "clinical", "label": "临床与循证辅助" },
    { "key": "research", "label": "科研与文献检索" },
    { "key": "teaching", "label": "医学教学与PPT" },
    { "key": "education", "label": "医学宣教与内容创作" },
    { "key": "office", "label": "办公协同与记录" },
    { "key": "dev", "label": "编程与网站开发" }
  ],
  "tools": [
    {
      "name": "丁香园 Dr.Chat",
      "icon": "💊",
      "provider": "丁香园",
      "type": "临床医学问答",
      "price": "免费",
      "recommend": [],
      "positioning": "中文临床语境的医疗问答助手",
      "capability": "结合国内临床实际与药品说明书知识，快速解答中文临床问题",
      "categories": ["clinical"],
      "tags": ["中文医疗", "药品说明书", "临床问答"],
      "url": "https://dxy.com/chat",
      "detail": {
        "intro": "丁香园推出的医疗 AI 助手，结合国内临床实际场景和药品说明书知识，适合中文临床问题的快速查询。",
        "features": ["中文医疗问答", "药品信息查询", "临床场景适配", "医学知识整合"],
        "audience": "国内临床医生、药师、医学生",
        "scenarios": ["中文临床问答", "药品用法查询", "临床决策参考"],
        "limitations": "结论仍需结合临床判断与权威指南核验。"
      }
    },
    {
      "name": "Medscape",
      "icon": "🏥",
      "provider": "WebMD",
      "type": "医学参考与继续教育",
      "price": "免费",
      "recommend": ["编辑推荐"],
      "positioning": "国际权威临床参考与药物数据库",
      "capability": "提供疾病诊疗、药物剂量、医学新闻与继续教育",
      "categories": ["clinical"],
      "tags": ["药物数据库", "疾病参考", "继续教育"],
      "url": "https://www.medscape.com",
      "detail": {
        "intro": "国际权威的临床医学参考平台，提供疾病诊疗指南、药物数据库、医学新闻与继续教育，是临床医生常用工具。",
        "features": ["疾病诊疗参考", "药物剂量查询", "医学新闻", "CME 继续教育"],
        "audience": "临床医生、药师、医学生",
        "scenarios": ["药物剂量查询", "疾病诊疗参考", "医学继续教育"],
        "limitations": "英文为主，中文资料较少；剂量需结合本地说明书核验。"
      }
    },
    {
      "name": "Perplexity",
      "icon": "🔍",
      "provider": "Perplexity",
      "type": "AI 搜索问答",
      "price": "免费增值",
      "recommend": ["科研常用"],
      "positioning": "带引用来源的实时 AI 搜索",
      "capability": "实时联网检索并附引用，适合循证提问与事实核查",
      "categories": ["research"],
      "tags": ["实时搜索", "引用来源", "事实核查"],
      "url": "https://www.perplexity.ai",
      "detail": {
        "intro": "带实时互联网搜索与引用来源的 AI 问答工具，回答可追溯出处，适合需要证据支撑的医学与科研提问。",
        "features": ["实时联网检索", "引用来源可追溯", "聚焦搜索范围", "Pro 深度研究"],
        "audience": "医生、科研人员、学生",
        "scenarios": ["循证医学提问", "事实核查", "快速资料检索"],
        "limitations": "医学答案仍需专业判断与核验；免费版检索次数有限。"
      }
    },
    {
      "name": "Consensus",
      "icon": "📊",
      "provider": "Consensus",
      "type": "循证文献搜索",
      "price": "免费增值",
      "recommend": ["科研常用"],
      "positioning": "基于已发表研究的循证问答",
      "capability": "从真实研究结论回答科学问题，展示证据支持/反驳比例",
      "categories": ["research"],
      "tags": ["循证", "已发表文献", "结论检索"],
      "url": "https://consensus.app",
      "detail": {
        "intro": "基于真实已发表研究回答科学问题，直接展示有多少研究支持或反驳某结论，适合临床循证提问。",
        "features": ["证据结论检索", "支持/反驳比例展示", "文献溯源", "研究质量标注"],
        "audience": "临床医生、科研人员、医学学生",
        "scenarios": ["循证临床提问", "文献证据概览", "快速掌握领域结论"],
        "limitations": "结论受收录文献范围限制，需结合最新指南综合判断。"
      }
    },
    {
      "name": "ChatDOC",
      "icon": "📄",
      "provider": "ChatDOC",
      "type": "文档阅读助手",
      "price": "免费增值",
      "recommend": [],
      "positioning": "对话式文献/文档阅读与问答",
      "capability": "上传 PDF 后按段落提问、精准定位原文出处",
      "categories": ["research"],
      "tags": ["PDF阅读", "原文定位", "文档问答"],
      "url": "https://chatdoc.com",
      "detail": {
        "intro": "面向 PDF 文献与文档的对话式阅读助手，支持按段落提问并精准定位原文出处，减少幻觉。",
        "features": ["PDF 段落问答", "原文出处定位", "多文档对比", "表格提取"],
        "audience": "科研人员、研究生、医生",
        "scenarios": ["文献精读", "论文查证", "多文档对比"],
        "limitations": "复杂图表理解有限，关键结论仍需回看原文。"
      }
    },
    {
      "name": "Elicit",
      "icon": "📚",
      "provider": "Elicit",
      "type": "文献综述自动化",
      "price": "免费增值",
      "recommend": ["科研常用"],
      "positioning": "自动化系统综述与文献矩阵",
      "capability": "自动提取文献关键发现，按研究问题组织成矩阵",
      "categories": ["research"],
      "tags": ["系统综述", "文献矩阵", "自动化提取"],
      "url": "https://elicit.com",
      "detail": {
        "intro": "帮助系统综述自动化的 AI 工具，自动提取文献关键发现并组织成研究矩阵，大幅提升文献调研效率。",
        "features": ["文献自动筛选", "关键发现提取", "研究矩阵组织", "参考文献追踪"],
        "audience": "科研人员、系统综述作者、研究生",
        "scenarios": ["系统综述", "文献调研", "研究空白识别"],
        "limitations": "提取结果需人工复核；对非英文文献覆盖有限。"
      }
    },
    {
      "name": "Gamma",
      "icon": "📽️",
      "provider": "Gamma",
      "type": "AI 演示文稿生成",
      "price": "免费增值",
      "recommend": ["编辑推荐"],
      "positioning": "一句话生成专业演示文稿",
      "capability": "输入主题自动生成结构化幻灯片，支持病例讨论与教学课件",
      "categories": ["teaching"],
      "tags": ["PPT生成", "幻灯片", "教学课件"],
      "url": "https://gamma.app",
      "detail": {
        "intro": "输入主题即可自动生成结构化、设计感强的演示文稿，适合快速制作病例讨论与教学课件。",
        "features": ["主题生成幻灯片", "结构化排版", "多模板", "协作分享"],
        "audience": "医生、教师、科研人员",
        "scenarios": ["病例讨论课件", "教学演示", "学术汇报"],
        "limitations": "生成内容需核对专业性；高级功能需订阅。"
      }
    },
    {
      "name": "Beautiful.ai",
      "icon": "🎨",
      "provider": "Beautiful.ai",
      "type": "AI 幻灯片设计",
      "price": "付费",
      "recommend": [],
      "positioning": "智能排版的专业演示工具",
      "capability": "AI 自动排版，快速产出设计感强的医学课件",
      "categories": ["teaching"],
      "tags": ["幻灯片设计", "智能排版", "课件"],
      "url": "https://www.beautiful.ai",
      "detail": {
        "intro": "AI 驱动的智能排版演示工具，自动优化版式与配色，快速产出设计感强的专业课件。",
        "features": ["智能排版", "自动配色", "品牌模板", "协作编辑"],
        "audience": "教师、医生、商务人士",
        "scenarios": ["医学课件", "学术汇报", "教学演示"],
        "limitations": "需付费订阅；中文字体与素材支持一般。"
      }
    },
    {
      "name": "笔格 AIPPT",
      "icon": "📑",
      "provider": "笔格",
      "type": "AI 课件制作",
      "price": "免费增值",
      "recommend": [],
      "positioning": "中文 AI 一键生成 PPT",
      "capability": "中文指令生成完整课件，适配国内教学场景",
      "categories": ["teaching"],
      "tags": ["AIPPT", "课件制作", "中文"],
      "url": "https://bigppt.cn/",
      "detail": {
        "intro": "面向中文场景的 AI PPT 生成工具，用中文指令即可一键生成完整课件，适配国内教学与汇报习惯。",
        "features": ["中文指令生成", "课件模板", "一键排版", "导出 PPT"],
        "audience": "教师、医生、办公人群",
        "scenarios": ["教学课件", "病例汇报", "学术演示"],
        "limitations": "请以官方最新信息为准；生成内容需人工校对。"
      }
    },
    {
      "name": "剪映 / CapCut",
      "icon": "🎬",
      "provider": "字节跳动",
      "type": "AI 视频剪辑",
      "price": "免费增值",
      "recommend": ["宣教常用"],
      "positioning": "AI 自动字幕与智能剪辑",
      "capability": "一键自动字幕、智能剪辑与模板化视频制作",
      "categories": ["education"],
      "tags": ["视频剪辑", "自动字幕", "医学科普视频"],
      "url": "https://www.capcut.cn",
      "detail": {
        "intro": "字节跳动出品的视频剪辑工具，支持 AI 自动字幕、智能剪辑、模板套用，适合制作医学科普与教学视频。",
        "features": ["AI 自动字幕", "智能剪辑", "模板化制作", "多端同步"],
        "audience": "科普创作者、医生、教师",
        "scenarios": ["医学科普视频", "教学视频", "病例分享视频"],
        "limitations": "医学专业术语字幕需人工校对；部分素材需付费。"
      }
    },
    {
      "name": "即梦 Dreamina",
      "icon": "✨",
      "provider": "字节跳动",
      "type": "AI 图文生视频/插图",
      "price": "免费增值",
      "recommend": ["宣教常用"],
      "positioning": "图文生成视频与医学插图",
      "capability": "文本/图片生成视频，支持医学插画与科普配图",
      "categories": ["education"],
      "tags": ["文生视频", "图生视频", "医学插图"],
      "url": "https://dreamina.jianying.com",
      "detail": {
        "intro": "字节跳动的 AI 创意生成工具，支持文本/图片生成视频，可用于医学插画、科普配图与教学内容创作。",
        "features": ["文生视频", "图生视频", "医学插图", "创意配图"],
        "audience": "科普创作者、教师、设计师",
        "scenarios": ["医学科普配图", "教学插图", "宣教视频素材"],
        "limitations": "医学解剖细节可能不准确，用于专业教学需人工审核。"
      }
    },
    {
      "name": "Notion AI",
      "icon": "📝",
      "provider": "Notion",
      "type": "办公知识库 AI",
      "price": "付费",
      "recommend": [],
      "positioning": "知识库与写作助手",
      "capability": "整理临床笔记、撰写病历摘要与文献综述初稿",
      "categories": ["office"],
      "tags": ["知识库", "写作助手", "笔记整理"],
      "url": "https://www.notion.so/product/ai",
      "detail": {
        "intro": "与 Notion 深度集成的 AI 助手，适合整理笔记、撰写摘要与构建个人知识库。",
        "features": ["笔记整理", "写作助手", "知识库管理", "内容摘要"],
        "audience": "医生、科研人员、办公人群",
        "scenarios": ["临床笔记整理", "文献综述初稿", "个人知识库"],
        "limitations": "需 Notion 订阅；敏感医疗数据需注意隐私。"
      }
    },
    {
      "name": "Otter.ai",
      "icon": "🎙️",
      "provider": "Otter.ai",
      "type": "语音转写与纪要",
      "price": "免费增值",
      "recommend": [],
      "positioning": "会议/查房录音转文字与纪要",
      "capability": "语音转文字 + AI 纪要，适合学术会议与查房记录",
      "categories": ["office"],
      "tags": ["语音转写", "会议纪要", "查房记录"],
      "url": "https://otter.ai",
      "detail": {
        "intro": "语音转文字与 AI 纪要工具，适合教学查房、MDT 讨论、学术会议的录音整理。",
        "features": ["语音转文字", "AI 纪要生成", "说话人区分", "多语言支持"],
        "audience": "医生、科研人员、会议参与者",
        "scenarios": ["教学查房记录", "MDT 讨论纪要", "学术会议整理"],
        "limitations": "专业术语转写需人工校对；涉及患者隐私需脱敏。"
      }
    },
    {
      "name": "Cursor",
      "icon": "⌨️",
      "provider": "Anysphere",
      "type": "AI 编程 IDE",
      "price": "免费增值",
      "recommend": ["编辑推荐"],
      "positioning": "AI 原生代码编辑器",
      "capability": "代码补全、多文件编辑与对话式编程一体化 IDE",
      "categories": ["dev"],
      "tags": ["AI编程", "代码补全", "多文件编辑"],
      "url": "https://cursor.com",
      "detail": {
        "intro": "AI 原生的代码编辑器，内置代码补全、对话式编程与多文件协同编辑，大幅提升开发效率。",
        "features": ["智能代码补全", "对话式编程", "多文件编辑", "代码库理解"],
        "audience": "开发者、科研计算人员、技术爱好者",
        "scenarios": ["网站开发", "脚本编写", "数据分析代码", "自动化工具"],
        "limitations": "生成代码需人工审查；高级功能需付费订阅。"
      }
    },
    {
      "name": "Trae",
      "icon": "🚀",
      "provider": "字节跳动",
      "type": "AI 编程 IDE",
      "price": "免费",
      "recommend": ["编辑推荐"],
      "positioning": "国产 AI 编程开发工具",
      "capability": "对话式编程、代码补全与项目管理一体化 IDE",
      "categories": ["dev"],
      "tags": ["AI编程", "国产", "网站制作"],
      "url": "https://www.trae.ai",
      "detail": {
        "intro": "字节跳动推出的 AI 编程开发工具，提供对话式编程、代码补全、项目管理等能力，对中文开发者友好。",
        "features": ["对话式编程", "代码补全", "项目构建", "中文友好"],
        "audience": "开发者、创业者、自动化需求用户",
        "scenarios": ["网站制作", "应用开发", "自动化脚本", "原型搭建"],
        "limitations": "生态尚在完善中；复杂项目需结合人工调试。"
      }
    }
  ]
}
```

## src/data/manual/dosing-reference.json

```json
{
  "updated": "2026-11-09",
  "notes": "以下为常用抗感染药物在不同肾功能水平下的剂量调整参考。具体临床应用请参考药品说明书原文与权威指南，必要时进行 TDM。",
  "drugs": [
    {
      "name": "哌拉西林/他唑巴坦",
      "class": "β-内酰胺酶抑制剂复合制剂",
      "normal": "4.5 g q6-8h",
      "crd30_40": "4.5 g q8h",
      "crcl15_30": "4.5 g q12h",
      "crcl5_15": "2.25 g q12h",
      "crcl_lt5": "2.25 g q24h",
      "dialysis": "4.5 g q12h，透析后追加 2.25 g",
      "hepatic": "无需调整",
      "notes": "CrCl 以 mL/min 为单位",
      "tdm": "不常规 TDM；重症可考虑监测 %fT>MIC"
    },
    {
      "name": "美罗培南",
      "class": "碳青霉烯类",
      "normal": "1 g q8h（重症可 2 g q8h）",
      "crd30_50": "常规剂量 q12h",
      "crcl10_25": "常规剂量 q24h",
      "crcl_lt10": "500 mg q24h 或 1 g q48h",
      "dialysis": "透析当日 500 mg q24h，透析后追加剂量",
      "hepatic": "无需调整",
      "notes": "铜绿假单胞菌感染可延长至 2-3 g q6h（肾功能正常）",
      "tdm": "不常规 TDM；重症可监测 %fT>MIC"
    },
    {
      "name": "亚胺培南/西司他丁",
      "class": "碳青霉烯类",
      "normal": "0.5-1 g q6h",
      "crd30_50": "0.5-1 g q8h",
      "crcl10_30": "0.5 g q8h 或 1 g q12h",
      "crcl_lt10": "0.5 g q12h",
      "dialysis": "透析当日 0.5 g q12h",
      "hepatic": "无需调整",
      "notes": "癫痫患者慎用；中枢神经系统感染避免使用",
      "tdm": "不常规 TDM"
    },
    {
      "name": "头孢吡肟",
      "class": "第四代头孢菌素",
      "normal": "1 g q8h（重症 2 g q8h）",
      "crd30_50": "1-2 g q12h",
      "crcl10_30": "1-2 g q24h",
      "crcl_lt10": "1 g q48h",
      "dialysis": "透析后追加 1 g",
      "hepatic": "无需调整",
      "notes": "肾功能不全时密切监测神经系统症状",
      "tdm": "不常规 TDM"
    },
    {
      "name": "万古霉素",
      "class": "糖肽类",
      "normal": "15-20 mg/kg q12h（TDM 谷浓度 15-20 mg/L）",
      "crd50_80": "15-20 mg/kg q24h（TDM 监测）",
      "crcl30_50": "15 mg/kg q24-48h（TDM 监测）",
      "crcl_lt30": "15 mg/kg q48-72h（TDM 监测）",
      "dialysis": "透析期间清除有限，建议 15 mg/kg q48-72h；高通量透析后可追加 500 mg",
      "hepatic": "无需调整",
      "notes": "必须 TDM；目标谷浓度 15-20 mg/L（普通）或 20-25 mg/L（重症/MRSA）",
      "tdm": "谷浓度 15-20 mg/L（重症/MRSA 20-25 mg/L）；AUC/MIC 400-600"
    },
    {
      "name": "左氧氟沙星",
      "class": "呼吸喹诺酮类",
      "normal": "500-750 mg qd 口服/静滴",
      "crd20_50": "常规剂量（CrCl 30-50 时 750 → 500 mg）",
      "crcl10_20": "250-500 mg q48h",
      "crcl_lt10": "250 mg q48h",
      "dialysis": "250 mg q48h",
      "hepatic": "无需调整",
      "notes": "避免儿童、妊娠、哺乳期使用；QT 延长风险",
      "tdm": "不常规 TDM"
    },
    {
      "name": "环丙沙星",
      "class": "喹诺酮类",
      "normal": "400 mg q8-12h 静滴（口服 500 mg q12h）",
      "crd30_50": "常规剂量",
      "crcl10_30": "400 mg q12h",
      "crcl_lt10": "400 mg q24h",
      "dialysis": "400 mg q24h",
      "hepatic": "肝硬化患者慎用，适当减量",
      "notes": "避免与镁/铝/钙制剂同服，间隔 2 小时以上",
      "tdm": "不常规 TDM"
    },
    {
      "name": "两性霉素 B 脂质体",
      "class": "多烯类抗真菌药",
      "normal": "3-5 mg/kg qd 静滴（按需升至 10 mg/kg）",
      "crd30_50": "无需调整（密切监测）",
      "crcl_lt30": "无需调整（密切监测）",
      "dialysis": "透析前后均无需调整剂量",
      "hepatic": "无需调整",
      "notes": "肾毒性较传统两性霉素 B 显著降低；仍需监测肾功能、电解质（尤其是钾和镁）",
      "tdm": "不常规 TDM"
    },
    {
      "name": "伏立康唑",
      "class": "三唑类抗真菌药",
      "normal": "口服 200 mg q12h；静滴 6 mg/kg q12h × 2 剂 → 4 mg/kg q12h",
      "crd_lt50": "避免使用静滴剂型（赋形剂 SBECD 蓄积），改用口服",
      "crcl_lt30": "口服剂量减至 100 mg q12h",
      "dialysis": "透析清除有限，建议口服 100 mg q12h",
      "hepatic": "Child-Pugh A/B：静滴维持剂量减至 1/2；口服维持剂量减至 100 mg q12h；Child-Pugh C：禁用",
      "notes": "CYP2C9/2C19 基因型影响代谢，东方人群 PM 比例较高",
      "tdm": "谷浓度 1.5-5.0 mg/L（治疗窗）"
    },
    {
      "name": "卡泊芬净",
      "class": "棘白菌素类抗真菌药",
      "normal": "负荷剂量 70 mg → 维持 50 mg qd 静滴",
      "crd_lt30": "无需调整（临床数据有限，密切监测）",
      "crcl_lt15": "无需调整",
      "dialysis": "无需调整，透析后无需追加",
      "hepatic": "Child-Pugh 7-9 分：维持剂量减至 35 mg qd；> 9 分：禁用",
      "notes": "肝功能不全调整剂量，肾功能不全通常无需调整",
      "tdm": "不常规 TDM"
    },
    {
      "name": "舒巴坦/度洛巴坦（双坦 / XACDURO）",
      "class": "β-内酰胺类/β-内酰胺酶抑制剂（舒巴坦+度洛巴坦）",
      "normal": "1 g 舒巴坦 + 1 g 度洛巴坦 q6h 静滴（每次 3 小时）",
      "crcl_ge130": "1 g/1 g q4h（肾功能亢进）",
      "crcl30_44": "1 g/1 g q8h",
      "crcl15_29": "1 g/1 g q12h",
      "crcl_lt15": "前 3 次 q12h（0、12、24h），之后 q24h",
      "dialysis": "透析疗程结束后给药",
      "hepatic": "无需调整",
      "notes": "用于碳青霉烯耐药鲍曼不动杆菌（CRAB）肺炎；输注 3 小时",
      "tdm": "不常规 TDM；舒巴坦 %fT>MIC 100% 需个体化"
    },
    {
      "name": "依拉环素（依嘉 / XERAVA）",
      "class": "四环素类（氟环素）",
      "normal": "1 mg/kg q12h 静滴（≥60 min）；重症可 1.5 mg/kg q12h",
      "hepatic": "Child-Pugh C：首日 1 mg/kg q12h → 之后 q24h",
      "notes": "用于复杂性腹腔感染（cIAI）；肾功能不全（含透析/ESRD）无需调整",
      "tdm": "不常规 TDM"
    },
    {
      "name": "艾沙康唑（康新博）",
      "class": "三唑类抗真菌药",
      "normal": "负荷 200 mg q8h × 6 剂（48h）→ 维持 200 mg qd",
      "hepatic": "轻中度肝损伤（Child-Pugh A/B）无需调整",
      "notes": "口服/静滴可互换（口服生物利用度 98%）；肾功能不全（含终末期）无需调整",
      "tdm": "可选；目标谷浓度约 1-5 mg/L"
    }
  ]
}
```

## src/data/manual/tools-meta.json

```json
{}
```

## src/layouts/BaseLayout.astro

```astro
---
import '../styles/global.css';

interface Props {
  title: string;
  description?: string;
}

const { title, description } = Astro.props;

// 七大一级导航（对应 PRD 2.1）
const nav = [
  { label: '首页', href: '/' },
  { label: '行业资讯', href: '/industry' },
  { label: '科研前沿', href: '/research' },
  { label: '抗感染指南', href: '/guides' },
  { label: '临床工具', href: '/tools' },
  { label: 'AI 工具', href: '/ai-tools' },
  { label: '关于本站', href: '/about' },
];

const canonical = Astro.site ? new URL(Astro.url.pathname, Astro.site).toString() : undefined;
---

<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
    <title>{title} | MedAI Hub</title>
    <meta
      name="description"
      content={description ?? '医药行业资讯、临床科研前沿、抗感染指南与临床工具平台'}
    />
    <meta name="generator" content={Astro.generator} />
    {canonical && <link rel="canonical" href={canonical} />}
  </head>
  <body class="min-h-screen bg-white font-sans text-neutral-900 antialiased">
    <header class="sticky top-0 z-50 border-b border-neutral-200 bg-white/95 backdrop-blur">
      <div
        class="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-3 md:h-14 md:flex-row md:items-center md:justify-between"
      >
        <a href="/" class="text-lg font-semibold tracking-tight">MedAI Hub</a>
        <div class="flex items-center gap-2">
          <ul class="flex flex-wrap items-center gap-1">
            {
              nav.map((item) => (
                <li>
                  <a
                    href={item.href}
                    class="rounded-md px-2.5 py-1.5 text-sm text-neutral-600 transition hover:bg-neutral-100 hover:text-neutral-900"
                  >
                    {item.label}
                  </a>
                </li>
              ))
            }
          </ul>
          <!-- 搜索按钮 -->
          <button
            id="search-btn"
            type="button"
            aria-label="全站搜索"
            class="ml-1 rounded-md p-1.5 text-neutral-500 transition hover:bg-neutral-100 hover:text-neutral-900"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-12">
      <slot />
    </main>

    <!-- Pagefind 搜索弹窗 -->
    <div
      id="search-modal"
      class="fixed inset-0 z-[100] hidden items-center justify-center bg-black/50 p-4"
    >
      <div class="w-full max-w-2xl rounded-xl bg-white p-4 shadow-2xl">
        <div class="mb-3 flex items-center justify-between">
          <span class="text-sm font-medium text-neutral-500">全站搜索</span>
          <button id="search-close" type="button" class="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>
        <div id="search" class="pagefind-ui"></div>
      </div>
    </div>
  </body>
</html>

<script>
  const modal = document.getElementById('search-modal');
  const openBtn = document.getElementById('search-btn');
  const closeBtn = document.getElementById('search-close');
  const searchContainer = document.getElementById('search');

  let pagefindInited = false;
  let pagefindUI: any = null;
  let pendingKeyword = '';

  function openSearch(keyword = '') {
    modal!.classList.remove('hidden');
    modal!.classList.add('flex');
    // 首次打开时加载 Pagefind UI
    if (!pagefindInited && searchContainer) {
      pendingKeyword = keyword;
      loadPagefind();
    } else if (pagefindUI && keyword) {
      pagefindUI.triggerSearch(keyword);
    }
    // 延迟聚焦输入框
    setTimeout(() => {
      const input = searchContainer?.querySelector('input');
      input?.focus();
    }, 100);
  }

  function closeSearch() {
    modal!.classList.add('hidden');
    modal!.classList.remove('flex');
  }

  function loadPagefind() {
    pagefindInited = true;
    // Pagefind 索引仅在 build 后生成；dev 模式下跳过
    if (import.meta.env.DEV) {
      searchContainer!.innerHTML =
        '<p class="text-center text-sm text-neutral-500 py-8">搜索索引仅在生产构建后可用，请使用 pnpm build 后查看效果。</p>';
      return;
    }
    // 动态加载 Pagefind UI
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/pagefind/pagefind-ui.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = '/pagefind/pagefind-ui.js';
    script.onload = () => {
      const w = window as unknown as { PagefindUI: any };
      if (typeof w.PagefindUI !== 'undefined') {
        pagefindUI = new w.PagefindUI({
          element: '#search',
          showSubResults: true,
          showImages: false,
          excerptLength: 18,
          resetStyles: false,
        });
        if (pendingKeyword) {
          pagefindUI.triggerSearch(pendingKeyword);
          pendingKeyword = '';
        }
      }
    };
    script.onerror = () => {
      searchContainer!.innerHTML =
        '<p class="text-center text-sm text-neutral-500 py-8">搜索索引未生成，请先执行 pnpm build。</p>';
    };
    document.body.appendChild(script);
  }

  openBtn?.addEventListener('click', () => openSearch());
  // 供首页等页面触发的全站搜索
  window.addEventListener('open-site-search', (e) => {
    const kw = (e as CustomEvent).detail?.keyword || '';
    openSearch(kw);
  });
  closeBtn?.addEventListener('click', closeSearch);
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeSearch();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSearch();
    // Cmd/Ctrl + K 打开搜索
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openSearch();
    }
  });
</script>
```

## src/pages/about.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="关于本站" description="平台定位、内容来源、使用边界与免责声明">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">关于本站</h1>
    <p class="mt-2 text-neutral-600">平台定位、内容来源、使用边界与免责声明。</p>
  </header>
  <div class="rounded-lg border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
    内容建设中 · P4 阶段完善
  </div>
</BaseLayout>
```

## src/pages/ai-tools.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import data from '../data/manual/ai-tools.json';

const categories = data.categories;
const tools = data.tools;
const featured = data.featured;
const catMap = Object.fromEntries(categories.map((c) => [c.key, c.label]));

const priceClass: Record<string, string> = {
  '免费': 'bg-green-50 text-green-700',
  '付费': 'bg-amber-50 text-amber-700',
  '免费增值': 'bg-blue-50 text-blue-700',
};

const recClass: Record<string, string> = {
  '编辑推荐': 'bg-red-50 text-red-600',
  '科研常用': 'bg-purple-50 text-purple-600',
  '宣教常用': 'bg-cyan-50 text-cyan-600',
};

// AI 工具页专属 Footer：仅 4 个行业导航链接
const aiLinks = [
  { label: 'Toolify.ai', href: 'https://toolifyai.cn/' },
  { label: 'Futurepedia', href: 'https://futurepedia.io/' },
  { label: '通往 AGI 之路', href: 'https://www.waytoagi.com/zh' },
  { label: 'AIHot News', href: 'https://aihot.news/' },
];
const currentYear = new Date().getFullYear();
---

<BaseLayout title="AI 工具" description="发现适合医学临床、科研学习、医学教学及日常办公的 AI 工具">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">AI 工具</h1>
    <p class="mt-2 max-w-3xl text-neutral-600">
      发现适合医学临床、科研学习、医学教学及日常办公的 AI 工具，为医疗工作者提供实用参考。
    </p>
    <p class="mt-2 text-xs text-neutral-400">
      共收录 <span class="font-medium text-neutral-700">{tools.length}</span> 款工具 · 最后更新：{data.updated}
    </p>
  </header>

  <!-- 顶部精选推荐区（3 列卡片 + 浮窗二维码） -->
  <section class="mb-10">
    <h2 class="mb-4 text-lg font-semibold text-neutral-900">精选推荐</h2>
    <div class="grid gap-4 md:grid-cols-3">
      {
        featured.map((f) => (
          <div
            class="qr-card group cursor-pointer rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:border-blue-300 hover:shadow-md"
            data-qr={f.qr}
            data-name={f.name}
            data-badge={f.badge}
            data-desc={f.desc}
          >
            <span class="inline-block rounded-full bg-blue-600 px-2.5 py-0.5 text-xs font-medium text-white">{f.badge}</span>
            <h3 class="mt-3 text-base font-semibold text-neutral-900">{f.name}</h3>
            <p class="mt-1.5 text-sm leading-relaxed text-neutral-600">{f.desc}</p>
            {
              f.channels && f.channels.length > 0 && (
                <ul class="mt-3 space-y-1.5 border-t border-neutral-100 pt-3">
                  {
                    f.channels.map((c: { label: string; value: string }) => (
                      <li class="text-xs leading-relaxed text-neutral-500">
                        {
                          c.value.startsWith('http') ? (
                            <a href={c.value} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline" onclick="event.stopPropagation()">
                              {c.label}：{c.value}
                            </a>
                          ) : (
                            <span><span class="font-medium text-neutral-700">{c.label}：</span>{c.value}</span>
                          )
                        }
                      </li>
                    ))
                  }
                </ul>
              )
            }
            <span class="mt-4 inline-flex items-center gap-1 text-sm font-medium text-blue-600 group-hover:underline">
              查看专属二维码 / 扫码领积分 →
            </span>
          </div>
        ))
      }
    </div>
  </section>

  <!-- 场景分类导航 -->
  <section class="mb-6">
    <div class="mb-2 flex items-center justify-between">
      <h2 class="text-sm font-semibold uppercase tracking-wide text-neutral-500">场景分类</h2>
      <button id="ai-reset" type="button" class="text-xs text-blue-600 hover:text-blue-700 hover:underline">清除筛选</button>
    </div>
    <div class="flex flex-wrap gap-2">
      {
        categories.map((c) => (
          <button
            type="button"
            data-cat={c.key}
            class="cat-btn rounded-full border border-neutral-300 bg-white px-3.5 py-1.5 text-sm text-neutral-600 transition hover:border-blue-500 hover:text-blue-600"
          >
            {c.label}
          </button>
        ))
      }
    </div>
  </section>

  <!-- 搜索 -->
  <div class="mb-6">
    <div class="relative">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <input
        id="ai-search"
        type="search"
        placeholder="搜索工具名称、功能描述或场景标签，如：文献、PPT、剪辑、编程…"
        class="w-full rounded-xl border border-neutral-300 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
      />
    </div>
  </div>

  <!-- 结果计数 -->
  <p id="ai-count" class="mb-4 text-sm text-neutral-500"></p>

  <!-- 工具卡片 3 列 -->
  <ul id="ai-list" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {
      tools.map((t, idx) => {
        const searchText = `${t.name} ${t.provider} ${t.type} ${t.tags.join(' ')} ${t.capability} ${t.positioning} ${t.categories.map((c) => catMap[c] ?? c).join(' ')}`.toLowerCase();
        return (
          <li
            class="ai-card group cursor-pointer rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:border-blue-300 hover:shadow-md"
            data-idx={idx}
            data-cats={t.categories.join(',')}
            data-search={searchText}
          >
            <div class="flex items-start gap-3">
              <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-neutral-100 text-2xl">{t.icon}</span>
              <div class="min-w-0">
                <h3 class="truncate text-base font-semibold text-neutral-900">{t.name}</h3>
                <p class="mt-0.5 truncate text-xs text-neutral-400">{t.provider}</p>
              </div>
            </div>

            <div class="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
              <span class="rounded bg-neutral-100 px-2 py-0.5 text-neutral-600">{t.type}</span>
              <span class={`rounded px-2 py-0.5 font-medium ${priceClass[t.price] ?? 'bg-neutral-100 text-neutral-600'}`}>{t.price}</span>
              {t.recommend.map((r) => (
                <span class={`rounded px-2 py-0.5 font-medium ${recClass[r] ?? 'bg-neutral-100 text-neutral-600'}`}>{r}</span>
              ))}
            </div>

            <p class="mt-3 text-xs font-medium text-neutral-500">{t.positioning}</p>
            <p class="mt-1 text-sm leading-relaxed text-neutral-700">{t.capability}</p>

            <div class="mt-3 flex flex-wrap gap-1.5">
              {t.tags.map((tag) => (
                <span class="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">#{tag}</span>
              ))}
            </div>

            <span class="mt-3 inline-flex items-center gap-1 text-xs font-medium text-blue-600 opacity-0 transition group-hover:opacity-100">
              查看详情 →
            </span>
          </li>
        );
      })
    }
  </ul>

  <div id="ai-empty" class="hidden rounded-xl border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
    没有匹配的工具，请调整筛选条件。
  </div>

  <!-- 免责声明 -->
  <div class="mt-10 rounded-lg border border-neutral-200 bg-neutral-50 p-4 text-xs text-neutral-500">
    <p class="leading-relaxed">
      本页仅为第三方 AI 工具导航目录，所有工具均为外部链接跳转，MedAI Hub 不开发、不维护、不运营任何站内 AI 对话服务。
      工具内容、服务质量、隐私条款和数据安全由各自的第三方平台负责。专业医疗相关决策请谨慎评估 AI 输出结果，结合临床实际与权威指南核验。
    </p>
  </div>

  <!-- AI 工具页专属 Footer：行业导航矩阵 -->
  <footer class="mt-10 border-t border-neutral-200 bg-neutral-50">
    <div class="py-10">
      <div class="mb-5">
        <h3 class="text-sm font-semibold text-neutral-900">行业优质 AI 导航矩阵与友情链接</h3>
        <p class="mt-1 text-xs text-neutral-400">以下为外部资源链接，点击一键跳转</p>
      </div>
      <ul class="flex flex-wrap gap-3">
        {
          aiLinks.map((link) => (
            <li>
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 rounded-lg border border-neutral-200 bg-white px-3.5 py-2 text-sm text-neutral-700 transition hover:border-blue-300 hover:text-blue-600"
              >
                {link.label}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M15 3h6v6"></path>
                  <path d="M10 14 21 3"></path>
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                </svg>
              </a>
            </li>
          ))
        }
      </ul>
      <div class="mt-8 border-t border-neutral-200 pt-6 text-xs leading-relaxed text-neutral-400">
        <p>© {currentYear} MedAI Hub · 医疗 AI 知识与工具平台</p>
        <p class="mt-1">本站内容仅供医学专业人士参考，不构成诊疗建议；AI 工具信息请以各官网为准。</p>
      </div>
    </div>
  </footer>
</BaseLayout>

<!-- 二维码浮窗 -->
<div id="qr-modal" class="fixed inset-0 z-[110] hidden items-center justify-center bg-black/50 p-4">
  <div class="w-full max-w-sm rounded-xl bg-white p-6 text-center shadow-2xl">
    <div class="flex justify-end">
      <button id="qr-close" type="button" class="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700" aria-label="关闭">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 6 6 18"></path><path d="m6 6 12 12"></path>
        </svg>
      </button>
    </div>
    <img id="qr-img" src="" alt="二维码海报" class="mx-auto h-56 w-56 rounded-lg border border-neutral-200 object-contain" />
    <h3 id="qr-name" class="mt-4 text-lg font-semibold text-neutral-900"></h3>
    <p id="qr-badge" class="mt-1 inline-block rounded-full bg-blue-600 px-2.5 py-0.5 text-xs font-medium text-white"></p>
    <p id="qr-desc" class="mt-3 text-sm leading-relaxed text-neutral-600"></p>
    <p class="mt-3 text-xs text-neutral-400">扫描上方二维码领取福利 / 访问服务</p>
  </div>
</div>

<!-- 轻量详情弹窗 -->
<div
  id="ai-modal"
  class="fixed inset-0 z-[100] hidden items-center justify-center bg-black/50 p-4"
>
  <div class="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-2xl">
    <div class="mb-4 flex items-start justify-between">
      <div class="flex items-center gap-3">
        <span id="ai-m-icon" class="flex h-12 w-12 items-center justify-center rounded-lg bg-neutral-100 text-2xl"></span>
        <div>
          <h3 id="ai-m-name" class="text-lg font-semibold text-neutral-900"></h3>
          <p id="ai-m-meta" class="text-xs text-neutral-400"></p>
        </div>
      </div>
      <button id="ai-modal-close" type="button" class="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700" aria-label="关闭">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 6 6 18"></path><path d="m6 6 12 12"></path>
        </svg>
      </button>
    </div>
    <div id="ai-modal-body" class="text-sm leading-relaxed text-neutral-700"></div>
  </div>
</div>

<script define:vars={{ toolsData: tools }}>
  const cards = Array.from(document.querySelectorAll<HTMLElement>('.ai-card'));
  const catBtns = document.querySelectorAll<HTMLElement>('.cat-btn');
  const searchInput = document.getElementById('ai-search') as HTMLInputElement | null;
  const resetBtn = document.getElementById('ai-reset');
  const countEl = document.getElementById('ai-count');
  const emptyEl = document.getElementById('ai-empty');

  const activeCats = new Set<string>();
  let query = '';

  function applyFilters() {
    let visible = 0;
    cards.forEach((card) => {
      const cats = card.dataset.cats!.split(',').filter(Boolean);
      const matchCat = activeCats.size === 0 || Array.from(activeCats).some((c) => cats.includes(c));
      const matchSearch = !query || card.dataset.search!.includes(query);
      const show = matchCat && matchSearch;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    countEl!.textContent = `共 ${visible} 款工具`;
    emptyEl!.classList.toggle('hidden', visible > 0);
  }

  catBtns.forEach((btn) =>
    btn.addEventListener('click', () => {
      const key = btn.dataset.cat!;
      const on = activeCats.has(key);
      if (on) {
        activeCats.delete(key);
        btn.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-600');
        btn.classList.add('border-neutral-300', 'bg-white', 'text-neutral-600');
      } else {
        activeCats.add(key);
        btn.classList.add('border-blue-500', 'bg-blue-50', 'text-blue-600');
        btn.classList.remove('border-neutral-300', 'bg-white', 'text-neutral-600');
      }
      applyFilters();
    }),
  );

  searchInput?.addEventListener('input', () => {
    query = searchInput.value.trim().toLowerCase();
    applyFilters();
  });

  resetBtn?.addEventListener('click', () => {
    activeCats.clear();
    query = '';
    if (searchInput) searchInput.value = '';
    catBtns.forEach((b) => {
      b.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-600');
      b.classList.add('border-neutral-300', 'bg-white', 'text-neutral-600');
    });
    applyFilters();
  });

  // 详情弹窗
  const modal = document.getElementById('ai-modal');
  const modalClose = document.getElementById('ai-modal-close');
  const mIcon = document.getElementById('ai-m-icon');
  const mName = document.getElementById('ai-m-name');
  const mMeta = document.getElementById('ai-m-meta');
  const mBody = document.getElementById('ai-modal-body');

  function esc(s: string) {
    return s.replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]!));
  }

  function openModal(idx: number) {
    const t = toolsData[idx];
    if (!t) return;
    mIcon!.textContent = t.icon;
    mName!.textContent = t.name;
    mMeta!.textContent = `${t.provider} · ${t.type} · ${t.price}`;

    const badges = [
      `<span class="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">${esc(t.type)}</span>`,
      `<span class="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">${esc(t.price)}</span>`,
      ...(t.recommend || []).map((r: string) => `<span class="rounded bg-red-50 px-2 py-0.5 text-xs text-red-600">${esc(r)}</span>`),
    ].join(' ');

    const features = (t.detail.features || []).map((f: string) => `<li>${esc(f)}</li>`).join('');
    const scenarios = (t.detail.scenarios || []).map((s: string) => `<li>${esc(s)}</li>`).join('');

    mBody!.innerHTML = `
      <div class="mb-3 flex flex-wrap gap-1.5">${badges}</div>
      <p class="text-neutral-700">${esc(t.detail.intro)}</p>
      <h4 class="mt-4 mb-1.5 font-semibold text-neutral-900">主要功能</h4>
      <ul class="list-inside list-disc space-y-1 text-neutral-700">${features}</ul>
      <h4 class="mt-4 mb-1.5 font-semibold text-neutral-900">适用人群</h4>
      <p class="text-neutral-700">${esc(t.detail.audience)}</p>
      <h4 class="mt-4 mb-1.5 font-semibold text-neutral-900">典型应用场景</h4>
      <ul class="list-inside list-disc space-y-1 text-neutral-700">${scenarios}</ul>
      <h4 class="mt-4 mb-1.5 font-semibold text-neutral-900">使用限制 / 注意事项</h4>
      <p class="text-neutral-700">${esc(t.detail.limitations)}</p>
      ${t.url ? `<a href="${esc(t.url)}" target="_blank" rel="noopener noreferrer" class="mt-5 inline-flex items-center gap-1.5 rounded-md bg-neutral-900 px-4 py-2 text-xs font-medium text-white hover:bg-neutral-700">访问官网 →</a>` : ''}
    `;

    modal!.classList.remove('hidden');
    modal!.classList.add('flex');
  }

  function closeModal() {
    modal!.classList.add('hidden');
    modal!.classList.remove('flex');
  }

  cards.forEach((card) =>
    card.addEventListener('click', () => openModal(Number(card.dataset.idx))),
  );
  modalClose?.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // 二维码浮窗
  const qrModal = document.getElementById('qr-modal');
  const qrClose = document.getElementById('qr-close');
  const qrImg = document.getElementById('qr-img') as HTMLImageElement | null;
  const qrName = document.getElementById('qr-name');
  const qrBadge = document.getElementById('qr-badge');
  const qrDesc = document.getElementById('qr-desc');

  const qrCards = document.querySelectorAll<HTMLElement>('.qr-card');
  qrCards.forEach((card) =>
    card.addEventListener('click', () => {
      if (qrImg) qrImg.src = card.dataset.qr || '';
      if (qrName) qrName.textContent = card.dataset.name || '';
      if (qrBadge) qrBadge.textContent = card.dataset.badge || '';
      if (qrDesc) qrDesc.textContent = card.dataset.desc || '';
      qrModal!.classList.remove('hidden');
      qrModal!.classList.add('flex');
    }),
  );
  qrClose?.addEventListener('click', () => {
    qrModal!.classList.add('hidden');
    qrModal!.classList.remove('flex');
  });
  qrModal?.addEventListener('click', (e) => {
    if (e.target === qrModal) {
      qrModal.classList.add('hidden');
      qrModal.classList.remove('flex');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      qrModal?.classList.add('hidden');
      qrModal?.classList.remove('flex');
    }
  });

  applyFilters();
</script>
```

## src/pages/drug-labels.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

const allLabels = await getCollection('drug-labels', ({ data }) => !data.draft);

// 按通用名字母序
const labels = allLabels.sort((a, b) => a.data.drugName.localeCompare(b.data.drugName, 'zh-CN'));

// 各维度去重
const antibioticClasses = [...new Set(labels.map((l) => l.data.antibioticClass).filter(Boolean))].sort();
const dosageForms = [...new Set(labels.map((l) => l.data.dosageForm))].sort();
const indications = [...new Set(labels.flatMap((l) => l.data.indications))].sort();
---

<BaseLayout title="药品说明书" description="抗感染核心品种说明书提取库">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">药品说明书</h1>
    <p class="mt-2 text-neutral-600">
      抗感染核心品种 · 适应证、用法用量、禁忌、特殊人群、肝肾功能调整、相互作用与给药配置 · 共 {labels.length} 种
    </p>
  </header>

  <!-- 筛选器 -->
  <div class="mb-8 rounded-xl border border-neutral-200 bg-neutral-50 p-5">
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <div>
        <label for="dl-search" class="mb-1.5 block text-sm font-medium text-neutral-700">搜索</label>
        <input
          id="dl-search"
          type="search"
          placeholder="药品名、商品名、适应证..."
          class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div>
        <label for="dl-class" class="mb-1.5 block text-sm font-medium text-neutral-700">抗菌药物分类</label>
        <select id="dl-class" class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
          <option value="">全部</option>
          {antibioticClasses.map((c) => <option value={c}>{c}</option>)}
        </select>
      </div>
      <div>
        <label for="dl-form" class="mb-1.5 block text-sm font-medium text-neutral-700">剂型</label>
        <select id="dl-form" class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
          <option value="">全部</option>
          {dosageForms.map((f) => <option value={f}>{f}</option>)}
        </select>
      </div>
      <div>
        <label for="dl-ind" class="mb-1.5 block text-sm font-medium text-neutral-700">适应证</label>
        <select id="dl-ind" class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
          <option value="">全部</option>
          {indications.map((i) => <option value={i}>{i}</option>)}
        </select>
      </div>
    </div>
    <div class="mt-4 flex items-center justify-between">
      <span class="text-sm text-neutral-500">匹配 <span id="dl-count" class="font-medium text-neutral-900">{labels.length}</span> 种</span>
      <button id="dl-reset" type="button" class="rounded-md px-3 py-1.5 text-sm text-neutral-600 hover:bg-neutral-200">重置筛选</button>
    </div>
  </div>

  <!-- 列表 -->
  <ul id="dl-list" class="grid gap-4">
    {
      labels.map((label) => {
        const searchText = `${label.data.drugName} ${label.data.brandNames.join(' ')} ${label.data.indications.join(' ')} ${label.data.description}`.toLowerCase();
        return (
          <li
            class="dl-card rounded-xl border border-neutral-200 p-5 transition hover:border-blue-400 hover:shadow-md"
            data-class={label.data.antibioticClass}
            data-form={label.data.dosageForm}
            data-ind={label.data.indications.join('|')}
            data-search={searchText}
          >
            <div class="flex flex-wrap items-center gap-2 text-xs text-neutral-500">
              <span class="rounded bg-purple-50 px-2 py-0.5 font-medium text-purple-700">{label.data.antibioticClass}</span>
              <span>{label.data.dosageForm}</span>
              {label.data.renalAdjustment && <span class="rounded bg-amber-50 px-2 py-0.5 text-amber-700">肾功能需调整</span>}
            </div>
            <h2 class="mt-2">
              <a href={`/drug-labels/${label.slug}`} class="text-lg font-semibold text-neutral-900 hover:text-blue-600">
                {label.data.drugName}
              </a>
            </h2>
            {label.data.brandNames.length > 0 && (
              <p class="mt-1 text-sm text-neutral-500">商品名：{label.data.brandNames.join('、')}</p>
            )}
            <p class="mt-1 text-xs text-neutral-400">{label.data.manufacturer} · ATC {label.data.atcCode || '-'}</p>
            {label.data.description && (
              <p class="mt-2 text-sm text-neutral-600 line-clamp-2">{label.data.description}</p>
            )}
            <div class="mt-3 flex flex-wrap gap-1.5">
              {label.data.strengths.map((s) => (
                <span class="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">{s}</span>
              ))}
            </div>
          </li>
        );
      })
    }
  </ul>

  <div id="dl-empty" class="hidden rounded-xl border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
    没有匹配的药品，请调整筛选条件。
  </div>
</BaseLayout>

<script>
  const searchInput = document.getElementById('dl-search') as HTMLInputElement;
  const classSel = document.getElementById('dl-class') as HTMLSelectElement;
  const formSel = document.getElementById('dl-form') as HTMLSelectElement;
  const indSel = document.getElementById('dl-ind') as HTMLSelectElement;
  const resetBtn = document.getElementById('dl-reset');
  const cards = document.querySelectorAll<HTMLElement>('.dl-card');
  const countEl = document.getElementById('dl-count');
  const emptyEl = document.getElementById('dl-empty');

  function applyFilters() {
    const q = searchInput.value.trim().toLowerCase();
    const cls = classSel.value;
    const form = formSel.value;
    const ind = indSel.value;

    let visible = 0;
    cards.forEach((card) => {
      const matchSearch = !q || card.dataset.search?.includes(q);
      const matchClass = !cls || card.dataset.class === cls;
      const matchForm = !form || card.dataset.form === form;
      const matchInd = !ind || (card.dataset.ind ?? '').split('|').includes(ind);

      const show = matchSearch && matchClass && matchForm && matchInd;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (countEl) countEl.textContent = String(visible);
    if (emptyEl) emptyEl.classList.toggle('hidden', visible > 0);
  }

  [searchInput, classSel, formSel, indSel].forEach((el) =>
    el.addEventListener('input', applyFilters)
  );

  resetBtn?.addEventListener('click', () => {
    searchInput.value = '';
    classSel.value = '';
    formSel.value = '';
    indSel.value = '';
    applyFilters();
  });
</script>
```

## src/pages/drug-labels/[slug].astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const labels = await getCollection('drug-labels', ({ data }) => !data.draft);
  return labels.map((label) => ({
    params: { slug: label.slug },
    props: { label },
  }));
}

const { label } = Astro.props;
const { Content } = await label.render();
const { data } = label;
---

<BaseLayout title={data.drugName} description={data.description}>
  <article class="prose prose-neutral max-w-none">
    <!-- 返回链接 -->
    <a href="/drug-labels" class="inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-blue-600">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
      </svg>
      返回药品说明书列表
    </a>

    <!-- 元信息徽章 -->
    <div class="mt-4 flex flex-wrap gap-2 text-xs">
      <span class="rounded bg-purple-50 px-2.5 py-1 font-medium text-purple-700">{data.antibioticClass || '—'}</span>
      <span class="rounded bg-neutral-100 px-2.5 py-1 text-neutral-600">{data.dosageForm}</span>
      {data.renalAdjustment && <span class="rounded bg-amber-50 px-2.5 py-1 text-amber-700">需肾功能调整</span>}
      {data.hepaticAdjustment && <span class="rounded bg-amber-50 px-2.5 py-1 text-amber-700">需肝功能调整</span>}
      <span class="rounded bg-green-50 px-2.5 py-1 text-green-700">审核：{data.reviewDate}</span>
    </div>

    <!-- 标题 -->
    <h1 class="mt-4 text-3xl font-bold text-neutral-900">{data.drugName}</h1>

    {data.brandNames.length > 0 && (
      <p class="mt-2 text-sm text-neutral-500">商品名：{data.brandNames.join('、')}</p>
    )}
    <p class="mt-1 text-sm text-neutral-500">{data.manufacturer} · ATC {data.atcCode || '-'}</p>

    {data.description && (
      <p class="mt-3 text-lg text-neutral-600">{data.description}</p>
    )}

    <!-- 规格 -->
    <div class="mt-4 flex flex-wrap gap-1.5">
      {data.strengths.map((s) => (
        <span class="rounded-lg bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">{s}</span>
      ))}
    </div>

    <!-- 结构化信息 -->
    <div class="mt-5 grid gap-4 border-y border-neutral-200 py-5 md:grid-cols-2">
      <div>
        <h3 class="mb-2 text-sm font-semibold text-neutral-700">适应证</h3>
        <ul class="list-disc space-y-1 pl-5 text-sm text-neutral-600">
          {data.indications.map((i) => <li>{i}</li>)}
        </ul>
      </div>
      {data.contraindications.length > 0 && (
        <div>
          <h3 class="mb-2 text-sm font-semibold text-neutral-700">禁忌</h3>
          <ul class="list-disc space-y-1 pl-5 text-sm text-neutral-600">
            {data.contraindications.map((c) => <li>{c}</li>)}
          </ul>
        </div>
      )}
      {data.specialPopulations.length > 0 && (
        <div>
          <h3 class="mb-2 text-sm font-semibold text-neutral-700">特殊人群</h3>
          <ul class="list-disc space-y-1 pl-5 text-sm text-neutral-600">
            {data.specialPopulations.map((s) => <li>{s}</li>)}
          </ul>
        </div>
      )}
      {data.drugInteractions.length > 0 && (
        <div>
          <h3 class="mb-2 text-sm font-semibold text-neutral-700">药物相互作用</h3>
          <ul class="list-disc space-y-1 pl-5 text-sm text-neutral-600">
            {data.drugInteractions.map((d) => <li>{d}</li>)}
          </ul>
        </div>
      )}
    </div>

    {data.preparation && (
      <div class="mt-4 rounded-lg bg-blue-50 p-4">
        <h3 class="mb-2 text-sm font-semibold text-blue-800">给药配置</h3>
        <p class="text-sm text-blue-700">{data.preparation}</p>
      </div>
    )}

    <!-- 正文 -->
    <div class="mt-6">
      <Content />
    </div>

    <!-- 原文链接 -->
    <div class="mt-8 flex flex-wrap items-center gap-4 border-t border-neutral-200 pt-6">
      {data.sourceUrl && (
        <a
          href={data.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          查看原文说明书
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3h6v6" />
            <path d="M10 14 21 3" />
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          </svg>
        </a>
      )}
      <p class="text-xs text-neutral-500">
        本内容为人工整理的药品说明书摘要，仅供专业学术参考，不能替代临床决策与药品说明书原文。
      </p>
    </div>
  </article>
</BaseLayout>
```

## src/pages/guides.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

// 多维分类维度定义（对齐 Evidence Navigator 体系）
// key: 对应 content.config.ts 中 schema 字段
// field: 对应卡片上的 data-* 属性（kebab-case）
const FILTER_DIMENSIONS = [
  {
    key: 'docType',
    field: 'data-doc-type',
    label: '指南共识',
    options: ['指南', '专家共识', '推荐依据'],
  },
  {
    key: 'pathogens',
    field: 'data-pathogens',
    label: '致病菌与耐药菌',
    options: [
      '曲霉', '念珠菌', '毛霉', '隐球菌',
      'CRAB', 'CRE/CRKP', 'CRPA', '嗜麦芽窄食单胞菌', 'MRSA/VRE',
      'CRE混合感染', 'CRAB混合感染', '多病原联合治疗',
    ],
  },
  {
    key: 'infectionSites',
    field: 'data-infection-sites',
    label: '感染部位与临床场景',
    options: [
      '肺部感染', '血流感染', '中枢神经系统感染', '腹腔感染',
      '皮肤软组织感染', '泌尿系感染', '肝移植', '肺移植', '肾移植',
    ],
  },
  {
    key: 'specialPopulations',
    field: 'data-special-populations',
    label: '特殊人群与器官支持',
    options: ['CRRT', 'ECMO', 'ARDS'],
  },
  {
    key: 'imagingDiagnosis',
    field: 'data-imaging-diagnosis',
    label: '医学影像与诊断',
    options: ['肺部CT影像', '真菌/耐药菌影像鉴别', 'TDM'],
  },
  {
    key: 'comparisons',
    field: 'data-comparisons',
    label: '疗效与安全性比较',
    options: [
      '与多黏菌素对比', '与依拉环素对比', '与舒巴坦/度洛巴坦对比',
      '与替加环素对比', '与伏立康唑/艾沙康唑对比',
    ],
  },
];

// 获取所有已发布指南（排除草稿与模板），按年份倒序排列
const guides = (await getCollection('guides', ({ data }) => !data.draft))
  .sort((a, b) => b.data.year - a.data.year);
---

<BaseLayout title="抗感染指南" description="权威抗感染指南与临床证据知识库">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">抗感染指南</h1>
    <p class="mt-2 text-neutral-600">
      按发布时间由新到旧排列 · 共 {guides.length} 篇
    </p>
  </header>

  <!-- 搜索框 -->
  <div class="mb-4">
    <input
      id="guides-search"
      type="search"
      placeholder="搜索标题、摘要、组织、病原体..."
      class="w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
    />
  </div>

  <!-- 可折叠多维筛选面板 -->
  <div id="filter-panel" class="mb-6 rounded-xl border border-neutral-200 bg-neutral-50/60 p-4">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-sm font-semibold text-neutral-700">多维分类筛选</h2>
      <button
        id="filter-clear"
        type="button"
        class="text-xs text-blue-600 hover:text-blue-700 hover:underline"
      >
        清除全部筛选
      </button>
    </div>
    <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {
        FILTER_DIMENSIONS.map((dim) => (
          <details class="group rounded-lg border border-neutral-200 bg-white">
            <summary class="cursor-pointer select-none px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50">
              {dim.label}
            </summary>
            <div class="max-h-48 overflow-y-auto border-t border-neutral-100 px-3 py-2">
              {dim.options.map((opt) => (
                <label class="flex items-center gap-2 py-1 text-sm text-neutral-600 hover:text-neutral-900">
                  <input
                    type="checkbox"
                    class="filter-checkbox h-4 w-4 rounded border-neutral-300 text-blue-600 focus:ring-blue-500"
                    data-dim={dim.key}
                    value={opt}
                  />
                  <span>{opt}</span>
                </label>
              ))}
            </div>
          </details>
        ))
      }
    </div>
  </div>

  <!-- 指南列表 -->
  <ul id="guides-list" class="grid gap-4">
    {
      guides.map((guide) => {
        const searchText = `${guide.data.title} ${guide.data.description} ${guide.data.organization} ${guide.data.syndromes.join(' ')} ${guide.data.pathogens.join(' ')} ${guide.data.tags.join(' ')}`.toLowerCase();
        return (
          <li
            class="guide-card rounded-xl border border-neutral-200 p-5 transition hover:border-blue-400 hover:shadow-md"
            data-search={searchText}
            data-doc-type={guide.data.docType.join(' ')}
            data-pathogens={guide.data.pathogens.join(' ')}
            data-infection-sites={guide.data.infectionSites.join(' ')}
            data-special-populations={guide.data.specialPopulations.join(' ')}
            data-imaging-diagnosis={guide.data.imagingDiagnosis.join(' ')}
            data-comparisons={guide.data.comparisons.join(' ')}
          >
            <div class="flex flex-wrap items-center gap-2 text-xs text-neutral-500">
              <span class="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">{guide.data.organization}</span>
              <span>{guide.data.year}</span>
              <span>·</span>
              <span>{guide.data.version}</span>
              {guide.data.docType.map((t) => (
                <span class="rounded bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">{t}</span>
              ))}
            </div>
            <h2 class="mt-2">
              <a href={`/guides/${guide.slug}`} class="text-lg font-semibold text-neutral-900 hover:text-blue-600">
                {guide.data.title}
              </a>
            </h2>
            {guide.data.description && (
              <p class="mt-2 text-sm text-neutral-600 line-clamp-2">{guide.data.description}</p>
            )}
            <div class="mt-3 flex flex-wrap gap-1.5">
              {guide.data.infectionSites.map((s) => (
                <span class="rounded bg-cyan-50 px-2 py-0.5 text-xs text-cyan-700">{s}</span>
              ))}
              {guide.data.pathogens.slice(0, 4).map((p) => (
                <span class="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">{p}</span>
              ))}
            </div>
          </li>
        );
      })
    }
  </ul>

  <div id="guides-empty" class="hidden rounded-xl border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
    没有匹配的指南或证据，请调整搜索关键词或筛选条件。
  </div>
</BaseLayout>

<script define:vars={{ dimensions: FILTER_DIMENSIONS }}>
  const searchInput = document.getElementById('guides-search');
  const cards = document.querySelectorAll('.guide-card');
  const emptyEl = document.getElementById('guides-empty');
  const clearBtn = document.getElementById('filter-clear');
  const checkboxes = document.querySelectorAll('.filter-checkbox');

  // 维度 key -> 卡片字段名映射
  const fieldMap = {};
  dimensions.forEach((d) => {
    fieldMap[d.key] = d.field;
  });

  function getSelected() {
    const selected = {};
    checkboxes.forEach((cb) => {
      if (cb.checked) {
        const dim = cb.dataset.dim;
        if (!selected[dim]) selected[dim] = new Set();
        selected[dim].add(cb.value);
      }
    });
    return selected;
  }

  function applyFilters() {
    const q = searchInput.value.trim().toLowerCase();
    const selected = getSelected();
    let visible = 0;

    cards.forEach((card) => {
      const matchSearch = !q || (card.dataset.search || '').includes(q);

      // 同维度内 OR，跨维度 AND
      let matchDims = true;
      for (const dim in selected) {
        const field = fieldMap[dim];
        const cardTags = (card.getAttribute(field) || '').split(' ').filter(Boolean);
        const hit = [...selected[dim]].some((v) => cardTags.includes(v));
        if (!hit) {
          matchDims = false;
          break;
        }
      }

      const show = matchSearch && matchDims;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (emptyEl) emptyEl.classList.toggle('hidden', visible > 0);
  }

  searchInput.addEventListener('input', applyFilters);
  checkboxes.forEach((cb) => cb.addEventListener('change', applyFilters));
  clearBtn?.addEventListener('click', () => {
    checkboxes.forEach((cb) => (cb.checked = false));
    applyFilters();
  });
</script>
```

## src/pages/guides/[slug].astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const guides = await getCollection('guides', ({ data }) => !data.draft);
  return guides.map((guide) => ({
    params: { slug: guide.slug },
    props: { guide },
  }));
}

const { guide } = Astro.props;
const { Content } = await guide.render();
const { data } = guide;
---

<BaseLayout title={data.title} description={data.description}>
  <article class="prose prose-neutral max-w-none">
    <!-- 返回链接 -->
    <a href="/guides" class="inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-blue-600">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 19-7-7 7-7" />
        <path d="M19 12H5" />
      </svg>
      返回指南列表
    </a>

    <!-- 元信息徽章 -->
    <div class="mt-4 flex flex-wrap gap-2 text-xs">
      <span class="rounded bg-blue-50 px-2.5 py-1 font-medium text-blue-700">{data.organization}</span>
      <span class="rounded bg-neutral-100 px-2.5 py-1 text-neutral-600">{data.year}</span>
      <span class="rounded bg-neutral-100 px-2.5 py-1 text-neutral-600">{data.version}</span>
      <span class="rounded bg-green-50 px-2.5 py-1 text-green-700">审核：{data.reviewDate}</span>
    </div>

    <!-- 标题 -->
    <h1 class="mt-4 text-3xl font-bold text-neutral-900">{data.title}</h1>

    {data.description && (
      <p class="mt-3 text-lg text-neutral-600">{data.description}</p>
    )}

    <!-- 分类标签 -->
    <div class="mt-5 space-y-2 border-y border-neutral-200 py-4">
      {data.syndromes.length > 0 && (
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-sm font-medium text-neutral-500">适用综合征：</span>
          {data.syndromes.map((s) => (
            <span class="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700">{s}</span>
          ))}
        </div>
      )}
      {data.pathogens.length > 0 && (
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-sm font-medium text-neutral-500">涉及病原体：</span>
          {data.pathogens.map((p) => (
            <span class="rounded bg-amber-50 px-2 py-0.5 text-xs text-amber-700">{p}</span>
          ))}
        </div>
      )}
      {data.antibioticClasses.length > 0 && (
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-sm font-medium text-neutral-500">抗菌药物分类：</span>
          {data.antibioticClasses.map((c) => (
            <span class="rounded bg-purple-50 px-2 py-0.5 text-xs text-purple-700">{c}</span>
          ))}
        </div>
      )}
    </div>

    <!-- 正文 -->
    <div class="mt-6">
      <Content />
    </div>

    <!-- 原文链接 -->
    <div class="mt-8 flex flex-wrap items-center gap-4 border-t border-neutral-200 pt-6">
      <a
        href={data.sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        阅读原文指南
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 3h6v6" />
          <path d="M10 14 21 3" />
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
        </svg>
      </a>
      <p class="text-xs text-neutral-500">
        本站仅存储人工整理的指南摘要，内容仅供专业学术参考，不能替代临床决策。
      </p>
    </div>
  </article>
</BaseLayout>
```

## src/pages/index.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import industryData from '../data/auto/industry.json';
import researchData from '../data/auto/research.json';
import type { IndustryNews, ResearchNews } from '../types/news';

// 各取最新 3 条
const industryNews = (industryData as IndustryNews[])
  .sort((a, b) => new Date(b.publishTime).getTime() - new Date(a.publishTime).getTime())
  .slice(0, 3);

const researchNews = (researchData as ResearchNews[])
  .sort((a, b) => new Date(b.publishTime).getTime() - new Date(a.publishTime).getTime())
  .slice(0, 3);

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}

// 高价值分类彩色徽章
const categoryBadgeClass: Record<string, string> = {
  '真菌与耐药': 'bg-pink-50 text-pink-700',
  'AMR': 'bg-red-50 text-red-700',
  '感染影像': 'bg-cyan-50 text-cyan-700',
  'AI临床': 'bg-violet-50 text-violet-700',
  '耐药监测': 'bg-orange-50 text-orange-700',
};
---

<BaseLayout title="首页" description="MedAI Hub — 医药垂直专业信息与临床知识平台">
  <section class="text-center">
    <h1 class="text-3xl font-semibold leading-tight sm:text-4xl">MedAI Hub</h1>
    <p class="mx-auto mt-3 max-w-2xl text-neutral-600">
      面向医药从业者与临床专业人群的资讯、指南与临床工具平台
    </p>

    <!-- 全站中央搜索框 -->
    <form id="home-search" class="mx-auto mt-8 max-w-xl">
      <div class="flex items-center gap-2 rounded-xl border border-neutral-300 bg-white p-1.5 shadow-sm transition focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100">
        <svg class="ml-2 h-4 w-4 shrink-0 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input
          id="home-search-input"
          type="search"
          placeholder="搜索全站指南、资讯与工具…"
          class="w-full bg-transparent px-2 py-2 text-sm outline-none"
        />
        <button type="submit" class="shrink-0 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700">
          搜索
        </button>
      </div>
    </form>
  </section>

  <!-- 双视角最新资讯 -->
  <section class="mt-14 grid gap-8 md:grid-cols-2">
    <!-- 行业资讯 -->
    <div>
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">行业资讯</h2>
        <a href="/industry" class="text-sm text-blue-600 hover:underline">查看全部 →</a>
      </div>
      <ul class="space-y-3">
        {
          industryNews.map((item) => (
            <li class="rounded-lg border border-neutral-200 p-4 transition hover:border-neutral-400">
              <div class="mb-1 flex items-center gap-2 text-xs text-neutral-400">
                <span class={`rounded px-1.5 py-0.5 ${categoryBadgeClass[item.category] ?? 'bg-blue-50 text-blue-700'}`}>{item.category}</span>
                <span>{formatDate(item.publishTime)}</span>
              </div>
              <a
                href={`/industry/${item.id}`}
                class="line-clamp-2 text-sm font-medium text-neutral-900 hover:text-blue-600"
              >
                {item.title}
              </a>
              <p class="mt-1.5 line-clamp-2 text-xs text-neutral-500">{item.summary}</p>
            </li>
          ))
        }
      </ul>
    </div>

    <!-- 科研前沿 -->
    <div>
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">科研前沿</h2>
        <a href="/research" class="text-sm text-blue-600 hover:underline">查看全部 →</a>
      </div>
      <ul class="space-y-3">
        {
          researchNews.map((item) => (
            <li class="rounded-lg border border-neutral-200 p-4 transition hover:border-neutral-400">
              <div class="mb-1 flex items-center gap-2 text-xs text-neutral-400">
                <span class="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700">{item.studyType}</span>
                {item.isPreprint && (
                  <span class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">预印本</span>
                )}
                <span>{formatDate(item.publishTime)}</span>
              </div>
              <a
                href={`/research/${item.id}`}
                class="line-clamp-2 text-sm font-medium text-neutral-900 hover:text-blue-600"
              >
                {item.title}
              </a>
              <p class="mt-1.5 line-clamp-2 text-xs text-neutral-500">{item.coreFindings}</p>
            </li>
          ))
        }
      </ul>
    </div>
  </section>

</BaseLayout>

<script>
  const form = document.getElementById('home-search');
  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('home-search-input') as HTMLInputElement | null;
    const kw = input?.value.trim() || '';
    window.dispatchEvent(new CustomEvent('open-site-search', { detail: { keyword: kw } }));
  });
</script>
```

## src/pages/industry.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import industryData from '../data/auto/industry.json';
import type { IndustryNews } from '../types/news';

// 按发布时间倒序
const news = (industryData as IndustryNews[]).sort(
  (a, b) => new Date(b.publishTime).getTime() - new Date(a.publishTime).getTime(),
);

function formatDateKey(iso: string) {
  const d = new Date(iso);
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}
function formatYear(iso: string) {
  return new Date(iso).getFullYear();
}
function formatTime(iso: string) {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

// 按日期分组（时间轴流）
const groups: Array<{ date: string; year: number; items: IndustryNews[] }> = [];
for (const item of news) {
  const date = formatDateKey(item.publishTime);
  const year = formatYear(item.publishTime);
  let g = groups.find((x) => x.date === date);
  if (!g) {
    g = { date, year, items: [] };
    groups.push(g);
  }
  g.items.push(item);
}

const factTypeLabel: Record<string, { text: string; class: string }> = {
  fact: { text: '事实', class: 'bg-neutral-100 text-neutral-700' },
  analysis: { text: '分析', class: 'bg-amber-50 text-amber-700' },
  forecast: { text: '预测', class: 'bg-purple-50 text-purple-700' },
};

const categoryBadgeClass: Record<string, string> = {
  '真菌与耐药': 'bg-pink-50 text-pink-700 border border-pink-200',
  'AMR': 'bg-red-50 text-red-700 border border-red-200',
  '感染影像': 'bg-cyan-50 text-cyan-700 border border-cyan-200',
  'AI临床': 'bg-violet-50 text-violet-700 border border-violet-200',
  '耐药监测': 'bg-orange-50 text-orange-700 border border-orange-200',
};

// 行业资讯页专属 Footer：行业优质 AI 导航矩阵与友情链接
const aiLinks = [
  { label: 'Toolify.ai', href: 'https://toolifyai.cn/' },
  { label: 'Futurepedia', href: 'https://futurepedia.io/' },
  { label: '通往 AGI 之路', href: 'https://www.waytoagi.com/zh' },
  { label: 'AIHot News', href: 'https://aihot.news/' },
  { label: '个人专属主页/知识库', href: 'https://lubiny0601-spec.github.io/' },
];
const currentYear = new Date().getFullYear();
---

<BaseLayout title="行业资讯" description="医药行业政策、医保、管线与市场格局资讯时间轴">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">行业资讯</h1>
    <p class="mt-2 text-neutral-600">
      关注医药行业政策、企业动态、药品市场与市场准入变化，为医药从业者提供及时的行业信息。
    </p>
  </header>

  {
    news.length === 0 && (
      <div class="rounded-lg border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
        暂无资讯数据
      </div>
    )
  }

  {
    groups.map((group) => (
      <section class="relative mb-10">
        <!-- 日期标题 -->
        <div class="mb-4 flex items-baseline gap-2">
          <h2 class="text-lg font-semibold text-neutral-900">{group.year}年{group.date}</h2>
          <span class="text-xs text-neutral-400">{group.items.length} 条</span>
        </div>

        <ul class="space-y-5">
          {
            group.items.map((item, idx) => {
              const ft = factTypeLabel[item.factType];
              const isLast = idx === group.items.length - 1;
              return (
                <li class="relative pl-8">
                  {/* 时间轴圆点 */}
                  <span class="absolute left-0 top-1.5 h-3 w-3 rounded-full bg-blue-500 ring-4 ring-blue-100"></span>
                  {/* 连接线（非最后一项） */}
                  {!isLast && (
                    <span class="absolute left-1.5 top-7 bottom-0 w-px bg-neutral-200"></span>
                  )}

                  <div class="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:shadow-md">
                    {/* 时间 + 来源 + 徽章 */}
                    <div class="flex flex-wrap items-center gap-2 text-xs text-neutral-400">
                      <time class="font-medium text-neutral-600">{formatTime(item.publishTime)}</time>
                      <span>{item.sourceName}</span>
                      <span class={`rounded px-1.5 py-0.5 ${categoryBadgeClass[item.category] ?? 'bg-blue-50 text-blue-700'}`}>{item.category}</span>
                      <span class={`rounded px-1.5 py-0.5 ${ft.class}`}>{ft.text}</span>
                      {item.isCluster && (
                        <span class="rounded bg-emerald-50 px-1.5 py-0.5 text-emerald-700">多源聚合</span>
                      )}
                    </div>

                    {/* 标题 */}
                    <a
                      href={`/industry/${item.id}`}
                      class="mt-2 block text-lg font-medium text-neutral-900 hover:text-blue-600 hover:underline"
                    >
                      {item.title}
                    </a>

                    {/* AI 摘要 */}
                    <p class="mt-2 text-sm leading-relaxed text-neutral-700">
                      <span class="mr-1 font-medium text-neutral-900">AI 摘要：</span>
                      {item.summary}
                    </p>

                    {/* 推荐理由 */}
                    <p class="mt-2 text-sm leading-relaxed text-neutral-600">
                      <span class="mr-1 font-medium text-neutral-900">推荐理由：</span>
                      {item.impact}
                    </p>

                    {/* 标签 */}
                    {item.tags.length > 0 && (
                      <div class="mt-3 flex flex-wrap gap-1.5">
                        {item.tags.map((tag) => (
                          <span class="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </li>
              );
            })
          }
        </ul>
      </section>
    ))
  }

  <!-- 行业资讯页专属 Footer：行业优质 AI 导航矩阵与友情链接 -->
  <footer class="mt-12 border-t border-neutral-200 bg-neutral-50">
    <div class="py-10">
      <div class="mb-5">
        <h3 class="text-sm font-semibold text-neutral-900">行业优质 AI 导航矩阵与友情链接</h3>
        <p class="mt-1 text-xs text-neutral-400">以下为外部资源链接，点击一键跳转</p>
      </div>
      <ul class="flex flex-wrap gap-3">
        {
          aiLinks.map((link) => (
            <li>
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 rounded-lg border border-neutral-200 bg-white px-3.5 py-2 text-sm text-neutral-700 transition hover:border-blue-300 hover:text-blue-600"
              >
                {link.label}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M15 3h6v6"></path>
                  <path d="M10 14 21 3"></path>
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                </svg>
              </a>
            </li>
          ))
        }
      </ul>
      <div class="mt-8 border-t border-neutral-200 pt-6 text-xs leading-relaxed text-neutral-400">
        <p>© {currentYear} MedAI Hub · 医疗 AI 知识与工具平台</p>
        <p class="mt-1">本站内容仅供医学专业人士参考，不构成诊疗建议；AI 工具信息请以各官网为准。</p>
      </div>
    </div>
  </footer>
</BaseLayout>
```

## src/pages/industry/[id].astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import ScoreBadge from '../../components/ScoreBadge.astro';
import industryData from '../../data/auto/industry.json';
import type { IndustryNews } from '../../types/news';

export async function getStaticPaths() {
  return (industryData as IndustryNews[]).map((item) => ({
    params: { id: item.id },
    props: { item },
  }));
}

const { item } = Astro.props as { item: IndustryNews };

const factTypeLabel: Record<string, { text: string; class: string }> = {
  fact: { text: '事实', class: 'bg-neutral-100 text-neutral-700' },
  analysis: { text: '分析', class: 'bg-amber-50 text-amber-700' },
  forecast: { text: '预测', class: 'bg-purple-50 text-purple-700' },
};

const ft = factTypeLabel[item.factType];

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const axes = [
  { label: '政策/医保影响度', value: item.scores.policyImpact },
  { label: '市场/销售额波及面', value: item.scores.marketImpact },
  { label: '产品/管线突破性', value: item.scores.breakthrough },
  { label: '企业/竞争格局影响', value: item.scores.competitiveImpact },
  { label: '时效性与权威可信度', value: item.scores.timelinessAuthority },
];
---

<BaseLayout title={item.title} description={item.summary}>
  <article class="mx-auto max-w-3xl">
    <!-- 返回链接 -->
    <a href="/industry" class="mb-6 inline-block text-sm text-blue-600 hover:underline">
      ← 返回行业资讯列表
    </a>

    <!-- 元信息 -->
    <div class="mb-4 flex flex-wrap items-center gap-2 text-xs">
      <span class="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">{item.category}</span>
      <span class={`rounded px-2 py-0.5 ${ft.class}`}>{ft.text}</span>
      {item.isCluster && (
        <span class="rounded bg-emerald-50 px-2 py-0.5 text-emerald-700">多源聚合</span>
      )}
    </div>

    <!-- 标题 -->
    <h1 class="text-2xl font-semibold leading-tight">{item.title}</h1>

    <!-- 来源与时间 -->
    <div class="mt-3 text-sm text-neutral-500">
      来源：
      <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
        {item.sourceName}
      </a>
      <span class="mx-2">·</span>
      <span>事件时间：{item.eventTime}</span>
      <span class="mx-2">·</span>
      <span>发布时间：{formatDate(item.publishTime)}</span>
    </div>

    <!-- 事实/分析/预测 区分提示（PRD 3.3） -->
    <div class="mt-4 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
      本条资讯为「{ft.text}」类内容。事实为已证实信息，分析为基于事实的解读，预测为对未来趋势的判断，请审慎参考。
    </div>

    <!-- AI 摘要 -->
    <section class="mt-8">
      <h2 class="mb-2 text-lg font-semibold">AI 摘要</h2>
      <p class="leading-relaxed text-neutral-700">{item.summary}</p>
    </section>

    <!-- 行业影响评估 -->
    <section class="mt-6">
      <h2 class="mb-2 text-lg font-semibold">行业影响评估</h2>
      <p class="leading-relaxed text-neutral-700">{item.impact}</p>
    </section>

    <!-- 五轴评分 -->
    <section class="mt-8">
      <h2 class="mb-3 text-lg font-semibold">五轴评分</h2>
      <ScoreBadge totalScore={item.totalScore} axes={axes} />
      <p class="mt-2 text-xs text-neutral-400">满分 50 分，准入线 35 分（双 Agent 审核通过）</p>
    </section>

    <!-- 标签 -->
    {item.tags.length > 0 && (
      <section class="mt-8">
        <h2 class="mb-2 text-lg font-semibold">标签</h2>
        <div class="flex flex-wrap gap-2">
          {item.tags.map((tag) => (
            <span class="rounded-full bg-neutral-100 px-3 py-1 text-sm text-neutral-600">#{tag}</span>
          ))}
        </div>
      </section>
    )}

    <!-- 外链 -->
    <section class="mt-8 border-t border-neutral-200 pt-6">
      <a
        href={item.sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1 rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
      >
        阅读原文 →
      </a>
      <p class="mt-2 text-xs text-neutral-400">本站仅存储结构化摘要与外链，不存储原文全文。</p>
    </section>
  </article>
</BaseLayout>
```

## src/pages/research.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import researchData from '../data/auto/research.json';
import type { ResearchNews } from '../types/news';

// 按发布时间倒序
const news = (researchData as ResearchNews[]).sort(
  (a, b) => new Date(b.publishTime).getTime() - new Date(a.publishTime).getTime(),
);

const studyTypes = [...new Set(news.map((n) => n.studyType))];

const studyTypeLabel: Record<string, string> = {
  'RCT': 'RCT / 临床研究',
  'cohort': '队列研究',
  'real-world': '真实世界研究',
  'meta-analysis': 'Meta 分析',
  'review': '综述',
  'preprint': '预印本',
  'other': '其他',
};

// 证据等级徽章颜色（按等级代码/说明）
function evidenceClass(level: string) {
  if (level.startsWith('1') || level.includes('专家共识') || level.includes('指南')) {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }
  if (level.startsWith('2')) {
    return 'bg-blue-50 text-blue-700 border-blue-200';
  }
  return 'bg-neutral-100 text-neutral-600 border-neutral-200';
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}
---

<BaseLayout title="科研前沿" description="临床研究、课题线索与科研方法">
  <header class="mb-6">
    <h1 class="text-2xl font-semibold">科研前沿</h1>
    <p class="mt-2 text-neutral-600">
      追踪医学领域重要研究进展，关注临床试验、系统评价、指南共识及高质量原始研究，帮助医生和科研人员快速了解最新证据。
    </p>
  </header>

  <!-- 顶部搜索框 -->
  <div class="mb-5">
    <div class="relative">
      <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <input
        id="research-search"
        type="search"
        placeholder="搜索病原体或关键字，如：曲霉、TDM、CRAB…"
        class="w-full rounded-xl border border-neutral-300 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
      />
    </div>
  </div>

  <!-- 证据类型快速筛选（单行） -->
  <div class="mb-6 rounded-xl border border-neutral-200 bg-neutral-50 p-4">
    <div class="mb-2 flex items-center justify-between">
      <span class="text-xs font-semibold uppercase tracking-wide text-neutral-500">证据类型</span>
      <button id="research-reset" type="button" class="text-xs text-blue-600 hover:text-blue-700 hover:underline">
        清除筛选
      </button>
    </div>
    <div class="flex flex-wrap gap-2">
      {
        studyTypes.map((t) => (
          <button
            type="button"
            data-type={t}
            class="type-tag rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs text-neutral-600 transition hover:border-blue-500 hover:text-blue-600"
          >
            {studyTypeLabel[t] ?? t}
          </button>
        ))
      }
    </div>
  </div>

  <!-- 结果计数 -->
  <p id="research-count" class="mb-4 text-sm text-neutral-500"></p>

  {
    news.length === 0 && (
      <div class="rounded-lg border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
        暂无资讯数据
      </div>
    )
  }

  <ul id="research-list" class="space-y-5">
    {
      news.map((item) => (
        <li
          class="news-card rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          data-type={item.studyType}
          data-tags={item.tags.join(',')}
          data-search={`${item.title} ${item.coreFindings} ${item.inspiration} ${item.tags.join(' ')} ${item.evidenceLevel}`.toLowerCase()}
        >
          <div class="mb-3 flex flex-wrap items-center gap-2 text-xs">
            {/* 证据等级（突出） */}
            <span class={`rounded border px-2 py-0.5 font-semibold ${evidenceClass(item.evidenceLevel)}`}>
              证据等级：{item.evidenceLevel}
            </span>
            <span class="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
              {studyTypeLabel[item.studyType] ?? item.studyType}
            </span>
            {item.sampleSize && (
              <span class="rounded bg-neutral-100 px-2 py-0.5 text-neutral-600">{item.sampleSize}</span>
            )}
            {item.isPreprint && (
              <span class="rounded bg-amber-50 px-2 py-0.5 font-medium text-amber-700">
                ⚠ 预印本 · 未同行评议
              </span>
            )}
            <span class="ml-auto text-neutral-400">
              {item.sourceName} · {formatDate(item.publishTime)}
            </span>
          </div>

          {/* 标题 → 详情页 */}
          <a
            href={`/research/${item.id}`}
            class="block text-lg font-medium text-neutral-900 hover:text-blue-600 hover:underline"
          >
            {item.title}
          </a>

          {/* 核心发现（突出） */}
          <div class="mt-3 rounded-lg border-l-4 border-blue-400 bg-blue-50/50 p-3">
            <p class="text-sm leading-relaxed text-neutral-800">
              <span class="mr-1 font-semibold text-blue-700">核心发现：</span>
              {item.coreFindings}
            </p>
          </div>

          {/* 临床启发 */}
          <p class="mt-3 text-sm leading-relaxed text-neutral-700">
            <span class="mr-1 font-medium text-neutral-900">临床启发：</span>
            {item.inspiration}
          </p>

          {/* 研究局限（次要信息） */}
          {item.limitations && (
            <p class="mt-2 text-xs leading-relaxed text-neutral-500">
              <span class="mr-1 font-medium">研究局限：</span>
              {item.limitations}
            </p>
          )}

          {/* 底部 Tag（可点击联动过滤）+ 研究原文入口 */}
          <div class="mt-3 flex flex-wrap items-center gap-1.5">
            {item.tags.map((tag) => (
              <button
                type="button"
                data-tag={tag}
                class="tag-btn rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600 transition hover:bg-amber-100 hover:text-amber-700"
              >
                #{tag}
              </button>
            ))}
            {item.sourceUrl && (
              <a
                href={item.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                class="ml-auto inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800"
              >
                研究原文 →
              </a>
            )}
          </div>
        </li>
      ))
    }
  </ul>

  <div id="research-empty" class="hidden rounded-lg border border-dashed border-neutral-300 p-10 text-center text-neutral-500">
    没有匹配的文献
  </div>
</BaseLayout>

<script>
  const cards = Array.from(document.querySelectorAll<HTMLElement>('.news-card'));
  const typeTags = document.querySelectorAll<HTMLElement>('.type-tag');
  const tagBtns = document.querySelectorAll<HTMLElement>('.tag-btn');
  const searchInput = document.getElementById('research-search') as HTMLInputElement | null;
  const resetBtn = document.getElementById('research-reset');
  const countEl = document.getElementById('research-count');
  const emptyEl = document.getElementById('research-empty');

  const activeTypes = new Set<string>();
  const activeTags = new Set<string>();
  let query = '';

  function applyFilters() {
    let visible = 0;
    cards.forEach((card) => {
      const type = card.dataset.type!;
      const tags = card.dataset.tags!.split(',');
      const searchText = card.dataset.search ?? '';

      const matchType = activeTypes.size === 0 || activeTypes.has(type);
      const matchTags =
        activeTags.size === 0 ||
        Array.from(activeTags).some((t) => tags.includes(t));
      const matchSearch = !query || searchText.includes(query);

      const show = matchType && matchTags && matchSearch;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    countEl!.textContent = `共 ${visible} 条文献`;
    emptyEl!.classList.toggle('hidden', visible > 0);
  }

  function toggleType(btn: HTMLElement) {
    const value = btn.dataset.type!;
    const on = activeTypes.has(value);
    if (on) {
      activeTypes.delete(value);
      btn.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-600');
      btn.classList.add('border-neutral-300', 'bg-white', 'text-neutral-600');
    } else {
      activeTypes.add(value);
      btn.classList.add('border-blue-500', 'bg-blue-50', 'text-blue-600');
      btn.classList.remove('border-neutral-300', 'bg-white', 'text-neutral-600');
    }
    applyFilters();
  }

  function toggleTag(btn: HTMLElement) {
    const value = btn.dataset.tag!;
    const on = activeTags.has(value);
    if (on) {
      activeTags.delete(value);
      btn.classList.remove('bg-amber-100', 'text-amber-700');
      btn.classList.add('bg-neutral-100', 'text-neutral-600');
    } else {
      activeTags.add(value);
      btn.classList.add('bg-amber-100', 'text-amber-700');
      btn.classList.remove('bg-neutral-100', 'text-neutral-600');
    }
    applyFilters();
  }

  typeTags.forEach((btn) => btn.addEventListener('click', () => toggleType(btn)));
  tagBtns.forEach((btn) => btn.addEventListener('click', () => toggleTag(btn)));

  searchInput?.addEventListener('input', () => {
    query = searchInput.value.trim().toLowerCase();
    applyFilters();
  });

  resetBtn?.addEventListener('click', () => {
    activeTypes.clear();
    activeTags.clear();
    query = '';
    if (searchInput) searchInput.value = '';
    typeTags.forEach((b) => {
      b.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-600');
      b.classList.add('border-neutral-300', 'bg-white', 'text-neutral-600');
    });
    tagBtns.forEach((b) => {
      b.classList.remove('bg-amber-100', 'text-amber-700');
      b.classList.add('bg-neutral-100', 'text-neutral-600');
    });
    applyFilters();
  });

  applyFilters();
</script>
```

## src/pages/research/[id].astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import ScoreBadge from '../../components/ScoreBadge.astro';
import researchData from '../../data/auto/research.json';
import type { ResearchNews } from '../../types/news';

export async function getStaticPaths() {
  return (researchData as ResearchNews[]).map((item) => ({
    params: { id: item.id },
    props: { item },
  }));
}

const { item } = Astro.props as { item: ResearchNews };

const studyTypeLabel: Record<string, string> = {
  'RCT': 'RCT',
  'cohort': '队列研究',
  'real-world': '真实世界研究',
  'meta-analysis': 'Meta 分析',
  'review': '综述',
  'preprint': '预印本',
  'other': '其他',
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const axes = [
  { label: '课题启发性', value: item.scores.topicInspiration },
  { label: '临床可落地性', value: item.scores.clinicalApplicability },
  { label: '证据等级', value: item.scores.evidenceLevel },
  { label: '专科普适性', value: item.scores.specialtyUniversality },
  { label: '科研增益价值', value: item.scores.researchValue },
];
---

<BaseLayout title={item.title} description={item.coreFindings}>
  <article class="mx-auto max-w-3xl">
    <!-- 返回链接 -->
    <a href="/research" class="mb-6 inline-block text-sm text-blue-600 hover:underline">
      ← 返回科研前沿列表
    </a>

    <!-- 预印本强制警示（PRD 4.2） -->
    {item.isPreprint && (
      <div class="mb-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        ⚠️ 本文为预印本，<strong>尚未经过同行评议</strong>，结论可能存在偏差，仅供科研参考，不作为临床决策依据。
      </div>
    )}

    <!-- 元信息 -->
    <div class="mb-4 flex flex-wrap items-center gap-2 text-xs">
      <span class="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
        {studyTypeLabel[item.studyType] ?? item.studyType}
      </span>
      {item.sampleSize && (
        <span class="rounded bg-neutral-100 px-2 py-0.5 text-neutral-600">{item.sampleSize}</span>
      )}
      <span class="rounded bg-neutral-100 px-2 py-0.5 text-neutral-600">证据等级：{item.evidenceLevel}</span>
    </div>

    <!-- 标题 -->
    <h1 class="text-2xl font-semibold leading-tight">{item.title}</h1>

    <!-- 来源与时间 -->
    <div class="mt-3 text-sm text-neutral-500">
      来源：
      <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
        {item.sourceName}
      </a>
      <span class="mx-2">·</span>
      <span>发表状态：{item.publishStatus === 'published' ? '已发表' : item.publishStatus === 'preprint' ? '预印本' : '在审'}</span>
      <span class="mx-2">·</span>
      <span>发布时间：{formatDate(item.publishTime)}</span>
    </div>

    <!-- 核心发现 -->
    <section class="mt-8">
      <h2 class="mb-2 text-lg font-semibold">核心发现</h2>
      <p class="leading-relaxed text-neutral-700">{item.coreFindings}</p>
    </section>

    <!-- 研究局限 -->
    <section class="mt-6">
      <h2 class="mb-2 text-lg font-semibold">研究局限</h2>
      <p class="leading-relaxed text-neutral-700">{item.limitations}</p>
    </section>

    <!-- 临床/科研启发 -->
    <section class="mt-6">
      <h2 class="mb-2 text-lg font-semibold">临床 / 科研启发</h2>
      <p class="leading-relaxed text-neutral-700">{item.inspiration}</p>
    </section>

    <!-- 五轴评分 -->
    <section class="mt-8">
      <h2 class="mb-3 text-lg font-semibold">五轴评分</h2>
      <ScoreBadge totalScore={item.totalScore} axes={axes} />
      <p class="mt-2 text-xs text-neutral-400">满分 50 分，准入线 35 分（双 Agent 审核通过）</p>
    </section>

    <!-- 标签 -->
    {item.tags.length > 0 && (
      <section class="mt-8">
        <h2 class="mb-2 text-lg font-semibold">标签</h2>
        <div class="flex flex-wrap gap-2">
          {item.tags.map((tag) => (
            <span class="rounded-full bg-neutral-100 px-3 py-1 text-sm text-neutral-600">#{tag}</span>
          ))}
        </div>
      </section>
    )}

    <!-- 外链 -->
    <section class="mt-8 border-t border-neutral-200 pt-6">
      <a
        href={item.sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1 rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
      >
        阅读原文 →
      </a>
      <p class="mt-2 text-xs text-neutral-400">本站仅存储结构化摘要与外链，不存储原文全文。</p>
    </section>
  </article>
</BaseLayout>
```

## src/pages/tools.astro

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';

const tools = [
  {
    title: '肌酐清除率',
    formula: 'Cockcroft-Gault',
    desc: '经典公式，用于肾功能评估与药物剂量调整。',
    href: '/tools/cockcroft-gault',
    color: 'blue',
  },
  {
    title: 'eGFR',
    formula: 'CKD-EPI 2021',
    desc: '推荐公式，基于 Scr 估算肾小球滤过率。',
    href: '/tools/egfr',
    color: 'blue',
  },
  {
    title: 'qSOFA / SOFA',
    formula: '脓毒症评分',
    desc: '快速筛查 + 完整器官功能衰竭评估。',
    href: '/tools/sofa',
    color: 'amber',
  },
  {
    title: 'PaO₂/FiO₂ 氧合指数',
    formula: 'P/F 比',
    desc: '评估氧合功能与 ARDS 严重程度（柏林定义）。',
    href: '/tools/pf-ratio',
    color: 'blue',
  },
  {
    title: 'CURB-65 评分',
    formula: 'CAP 严重度',
    desc: '社区获得性肺炎严重程度评估，指导诊疗决策。',
    href: '/tools/curb-65',
    color: 'amber',
  },
  {
    title: 'APACHE II 评分',
    formula: '危重评分',
    desc: '急性生理与慢性健康评分，ICU 危重分层。',
    href: '/tools/apache-ii',
    color: 'purple',
  },
  {
    title: 'ARC 筛查',
    formula: '肾清除过度',
    desc: '识别 CrCl 过高导致的抗菌药物剂量不足风险。',
    href: '/tools/arc',
    color: 'green',
  },
  {
    title: '抗感染药物剂量',
    formula: '肾功能调整参考表',
    desc: '常用抗感染药物在不同肾功能水平下的剂量对照。',
    href: '/tools/dosing-reference',
    color: 'green',
  },
];

const drugLabels = [
  { name: '头孢他啶阿维巴坦（思福妥®）', href: '/drug-labels/ceftazidime-avibactam' },
  { name: '氨曲南阿维巴坦（Emblaveo）', href: '/drug-labels/aztreonam-avibactam' },
  { name: '注射用舒巴坦钠/度洛巴坦钠组合包装（双坦 / XACDURO）', href: '/drug-labels/sulbactam-durlobactam' },
  { name: '注射用依拉环素（依嘉 / XERAVA）', href: '/drug-labels/eravacycline' },
  { name: '亚胺西瑞（锐可博®/RECARBRIO®）', href: '/drug-labels/imipenem-cilastatin-relebactam' },
  { name: '硫酸艾沙康唑注射液（康新博）', href: '/drug-labels/isavuconazole-injection' },
  { name: '硫酸艾沙康唑胶囊（康新博）', href: '/drug-labels/isavuconazole-capsule' },
  { name: '伏立康唑注射液（威凡®）', href: '/drug-labels/voriconazole-injection' },
  { name: '伏立康唑片（威凡®）', href: '/drug-labels/voriconazole-tablet' },
  { name: '两性霉素B脂质体（AmBisome）', href: '/drug-labels/amphotericin-b-liposome' },
  { name: '两性霉素B胆固醇硫酸酯（ABelcet）', href: '/drug-labels/amphotericin-b-cholesterol' },
];

const colorMap: Record<string, string> = {
  blue: 'bg-blue-50 text-blue-700 border-blue-200',
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  purple: 'bg-purple-50 text-purple-700 border-purple-200',
  green: 'bg-green-50 text-green-700 border-green-200',
};
---

<BaseLayout title="临床工具" description="纯前端本地计算，完全离线可用">
  <header class="mb-8">
    <h1 class="text-2xl font-semibold">临床工具</h1>
    <p class="mt-2 text-neutral-600">
      所有工具完全在您的浏览器本地运行，不收集、不上传任何患者数据，支持离线使用。
    </p>
  </header>

  <!-- 计算器入口 -->
  <section class="mb-10">
    <h2 class="mb-4 text-lg font-semibold text-neutral-900">计算器 / 评分</h2>
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {
        tools.map((t) => (
          <a
            href={t.href}
            class="block rounded-xl border border-neutral-200 p-5 transition hover:border-blue-400 hover:shadow-md"
          >
            <span class={`inline-block rounded-md border px-2 py-0.5 text-xs font-medium ${colorMap[t.color]}`}>
              {t.formula}
            </span>
            <h3 class="mt-3 text-lg font-semibold text-neutral-900">{t.title}</h3>
            <p class="mt-1.5 text-sm text-neutral-500">{t.desc}</p>
            <span class="mt-3 inline-flex items-center gap-1 text-sm text-blue-600">
              打开工具 →
            </span>
          </a>
        ))
      }
    </div>
  </section>

  <!-- 药品说明书快速入口 -->
  <section>
    <h2 class="mb-4 text-lg font-semibold text-neutral-900">药品说明书（抗感染核心品种）</h2>
    <div class="grid gap-3 sm:grid-cols-2">
      {
        drugLabels.map((d) => (
          <a
            href={d.href}
            class="block rounded-lg border border-neutral-200 bg-neutral-50 p-4 transition hover:border-blue-400 hover:bg-white hover:shadow-sm"
          >
            <div class="text-sm font-medium text-neutral-900">{d.name}</div>
            <div class="mt-1 text-xs text-neutral-500">适应证 · 用法用量 · 禁忌 · 肾功能调整</div>
          </a>
        ))
      }
    </div>
    <a href="/drug-labels" class="mt-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
      查看全部药品说明书 →
    </a>
  </section>
</BaseLayout>
```

## src/pages/tools/apache-ii.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import ApacheII from '../../components/tools/ApacheII';
---

<BaseLayout title="APACHE II 危重评分" description="急性生理与慢性健康评分">
  <ApacheII client:load />
</BaseLayout>
```

## src/pages/tools/arc.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import ARC from '../../components/tools/ARC';
---

<BaseLayout title="ARC 肾清除过度筛查" description="识别肌酐清除率过高导致的抗菌药物剂量不足风险">
  <ARC client:load />
</BaseLayout>
```

## src/pages/tools/cockcroft-gault.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import CockcroftGault from '../../components/tools/CockcroftGault';
---

<BaseLayout title="肌酐清除率计算器" description="Cockcroft-Gault 公式 CrCl 计算">
  <CockcroftGault client:load />
</BaseLayout>
```

## src/pages/tools/curb-65.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import CURB65 from '../../components/tools/CURB65';
---

<BaseLayout title="CURB-65 评分" description="社区获得性肺炎严重程度评估">
  <CURB65 client:load />
</BaseLayout>
```

## src/pages/tools/dosing-reference.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import data from '../../data/manual/dosing-reference.json';

type DrugRow = Record<string, string | undefined> & {
  name: string;
  class: string;
  normal: string;
  hepatic: string;
  notes?: string;
  tdm?: string;
};

// 各肾功能区间（标签 + 候选字段），兼容历史 crd_* / crcl_* 两种前缀
const doseRows: Array<{ label: string; keys: string[]; tone: string }> = [
  { label: 'CrCl ≥ 130（ARC）', keys: ['crcl_ge130'], tone: 'text-red-700' },
  { label: 'CrCl 30-44', keys: ['crcl30_44'], tone: 'text-amber-700' },
  { label: 'CrCl 15-29', keys: ['crcl15_29'], tone: 'text-red-700' },
  { label: 'CrCl 50-80', keys: ['crd50_80', 'crcl50_80'], tone: 'text-neutral-600' },
  { label: 'CrCl 30-50', keys: ['crd30_50', 'crcl30_50'], tone: 'text-neutral-600' },
  { label: 'CrCl 30-40', keys: ['crd30_40', 'crcl30_40'], tone: 'text-neutral-600' },
  { label: 'CrCl 20-50', keys: ['crd20_50', 'crcl20_50'], tone: 'text-neutral-600' },
  { label: 'CrCl 15-30', keys: ['crd15_30', 'crcl15_30'], tone: 'text-amber-700' },
  { label: 'CrCl 10-30', keys: ['crd10_30', 'crcl10_30'], tone: 'text-amber-700' },
  { label: 'CrCl 10-25', keys: ['crd10_25', 'crcl10_25'], tone: 'text-amber-700' },
  { label: 'CrCl 10-20', keys: ['crd10_20', 'crcl10_20'], tone: 'text-amber-700' },
  { label: 'CrCl 5-15', keys: ['crd5_15', 'crcl5_15'], tone: 'text-amber-700' },
  { label: 'CrCl < 50', keys: ['crd_lt50', 'crcl_lt50'], tone: 'text-red-700' },
  { label: 'CrCl < 30', keys: ['crd_lt30', 'crcl_lt30'], tone: 'text-red-700' },
  { label: 'CrCl < 15', keys: ['crd_lt15', 'crcl_lt15'], tone: 'text-red-700' },
  { label: 'CrCl < 10', keys: ['crd_lt10', 'crcl_lt10'], tone: 'text-red-700' },
  { label: 'CrCl < 5', keys: ['crd_lt5', 'crcl_lt5'], tone: 'text-red-700' },
];

const drugs = data.drugs as DrugRow[];

function getDose(d: DrugRow, keys: string[]): string | undefined {
  for (const k of keys) {
    const v = d[k];
    if (v) return v;
  }
  return undefined;
}
---

<BaseLayout title="抗感染药物剂量调整参考" description="常用抗感染药物在不同肾功能水平下的剂量调整表">
  <header class="mb-6">
    <h1 class="text-2xl font-semibold">抗感染药物剂量调整参考表</h1>
    <p class="mt-2 text-sm text-neutral-600">{data.notes}</p>
    <p class="mt-1 text-xs text-neutral-400">最后更新：{data.updated} · 仅供专业学术参考</p>
  </header>

  <!-- 筛选 -->
  <div class="mb-5 rounded-xl border border-neutral-200 bg-neutral-50 p-4">
    <input
      id="dr-search"
      type="search"
      placeholder="搜索药物名称或分类..."
      class="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
    />
  </div>

  <ul id="dr-list" class="grid gap-4">
    {
      drugs.map((d) => {
        const searchText = `${d.name} ${d.class}`.toLowerCase();
        return (
          <li
            class="dr-card rounded-xl border border-neutral-200 p-5"
            data-search={searchText}
          >
            <div class="mb-3 flex flex-wrap items-center gap-2">
              <h2 class="text-lg font-semibold text-neutral-900">{d.name}</h2>
              <span class="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">{d.class}</span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full min-w-[600px] text-xs">
                <thead class="bg-neutral-100 text-neutral-700">
                  <tr>
                    <th class="p-2 text-left font-medium">肾功能</th>
                    <th class="p-2 text-left font-medium">剂量</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-neutral-200">
                  <tr><td class="p-2 font-medium text-green-700">正常</td><td class="p-2">{d.normal}</td></tr>
                  {doseRows.map((r) => {
                    const val = getDose(d, r.keys);
                    return val ? (
                      <tr><td class={`p-2 ${r.tone}`}>{r.label}</td><td class="p-2">{val}</td></tr>
                    ) : null;
                  })}
                  {d.dialysis && <tr><td class="p-2 text-red-700">透析</td><td class="p-2">{d.dialysis}</td></tr>}
                  <tr><td class="p-2 font-medium text-purple-700">肝功能</td><td class="p-2">{d.hepatic}</td></tr>
                  {d.tdm && <tr class="bg-emerald-50/60"><td class="p-2 font-medium text-emerald-700">TDM 目标</td><td class="p-2">{d.tdm}</td></tr>}
                </tbody>
              </table>
            </div>
            {d.notes && (
              <p class="mt-2 rounded bg-amber-50 p-2 text-xs text-amber-800">⚠ {d.notes}</p>
            )}
          </li>
        );
      })
    }
  </ul>

  <div class="mt-8 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
    <strong class="block text-amber-900">⚠ 安全声明</strong>
    <p class="mt-1 leading-relaxed">
      本表为常用抗感染药物在不同肾功能水平下的剂量调整参考，仅供专业学术参考，不能替代药品说明书和临床决策。
      实际应用中应结合患者具体情况，必要时进行 TDM 监测。CrCl 单位 mL/min。
    </p>
  </div>
</BaseLayout>

<script>
  const input = document.getElementById('dr-search') as HTMLInputElement;
  const cards = document.querySelectorAll<HTMLElement>('.dr-card');
  input?.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    cards.forEach((c) => {
      c.style.display = !q || (c.dataset.search ?? '').includes(q) ? '' : 'none';
    });
  });
</script>
```

## src/pages/tools/egfr.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import EGFR from '../../components/tools/EGFR';
---

<BaseLayout title="eGFR 计算器" description="CKD-EPI 2021 公式 eGFR 估算">
  <EGFR client:load />
</BaseLayout>
```

## src/pages/tools/pf-ratio.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import PFRatio from '../../components/tools/PFRatio';
---

<BaseLayout title="PaO₂/FiO₂ 氧合指数" description="评估氧合功能与 ARDS 严重程度">
  <PFRatio client:load />
</BaseLayout>
```

## src/pages/tools/sofa.astro

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import SOFA from '../../components/tools/SOFA';
---

<BaseLayout title="qSOFA / SOFA 评分" description="快速 SOFA 与完整 SOFA 评分计算">
  <SOFA client:load />
</BaseLayout>
```

## src/styles/global.css

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";

@theme {
  --font-sans:
    system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial,
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}
```

## src/types/news.ts

```ts
// 资讯共享类型定义
// 严格对齐 PRD 第 3.3、4.3、5.2 节【确定】字段

// 事实类型：明确区分事实 / 分析 / 预测（PRD 3.3）
export type FactType = 'fact' | 'analysis' | 'forecast';

// ===== 行业资讯 =====

// 行业资讯五轴评分（PRD 5.2）
export interface IndustryScores {
  policyImpact: number;          // 政策/医保影响度 (1-10)
  marketImpact: number;          // 市场/销售额波及面 (1-10)
  breakthrough: number;          // 产品/管线突破性 (1-10)
  competitiveImpact: number;     // 企业/竞争格局影响 (1-10)
  timelinessAuthority: number;   // 时效性与权威可信度 (1-10)
}

export interface IndustryNews {
  id: string;
  title: string;                          // 标题
  eventTime: string;                      // 事件发生时间 (ISO)
  publishTime: string;                    // 发布时间 (ISO)
  sourceName: string;                     // 来源名称
  sourceUrl: string;                      // 原始链接
  category: string;                       // 事件分类（集采/医保/BD/获批/财报/政策/反腐）
  tags: string[];                         // 标签
  summary: string;                        // AI 摘要
  impact: string;                         // 行业影响评估
  scores: IndustryScores;                 // 五轴评分
  totalScore: number;                     // 总分（满分 50，准入线 35）
  isCluster: boolean;                     // 多来源/聚类标记
  factType: FactType;                     // 事实/分析/预测
}

// ===== 科研资讯 =====

// 科研资讯五轴评分（PRD 5.2）
export interface ResearchScores {
  topicInspiration: number;       // 课题启发性 (1-10)
  clinicalApplicability: number;  // 临床可落地性 (1-10)
  evidenceLevel: number;          // 证据等级 (1-10)
  specialtyUniversality: number;  // 专科普适性 (1-10)
  researchValue: number;          // 科研增益价值 (1-10)
}

export type StudyType = 'RCT' | 'cohort' | 'real-world' | 'meta-analysis' | 'review' | 'preprint' | 'other';
export type PublishStatus = 'published' | 'preprint' | 'in-review';

export interface ResearchNews {
  id: string;
  title: string;                          // 研究标题
  sourceName: string;                     // 原始来源（期刊/平台）
  sourceUrl: string;                      // 原始链接
  studyType: StudyType;                   // 研究类型
  publishStatus: PublishStatus;           // 发表状态
  sampleSize?: string | null;              // 样本量（若原文提供）
  publishTime: string;                    // 发布时间 (ISO)
  coreFindings: string;                   // 核心发现
  limitations: string;                    // 研究局限
  inspiration: string;                    // 临床/科研启发
  evidenceLevel: string;                  // 证据等级提示
  scores: ResearchScores;                 // 五轴评分
  totalScore: number;                     // 总分（满分 50，准入线 35）
  isPreprint: boolean;                    // 是否预印本（强制标注"未同行评议"）
  tags: string[];                         // 标签
}
```

