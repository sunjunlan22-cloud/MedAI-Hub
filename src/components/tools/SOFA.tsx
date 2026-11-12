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
