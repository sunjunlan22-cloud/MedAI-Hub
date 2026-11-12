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
