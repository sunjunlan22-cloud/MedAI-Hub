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
