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
