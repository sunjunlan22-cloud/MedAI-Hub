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
