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
