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
