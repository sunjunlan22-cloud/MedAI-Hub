// MedAI Hub — 文献链接邮件发送（Netlify Function）
// 将具备明确文献身份的条目（科研论文 / 指南引用论文 / 资讯关联论文 / PubMed 结果）
// 以「链接邮件」形式发送到用户填写的邮箱，无需注册。
//
// 端点（配合 netlify.toml redirects 暴露为 /api/send-literature）：
//   POST /api/send-literature   body: { email, item:{ title, authors?, journal?, date?, doi?, pmid?, abstract?, source? } }
//
// 环境变量（缺失任一则「未配置」，不伪造发送成功）：
//   RESEND_API_KEY — 邮件服务 API Key（服务端持有，不暴露给客户端）
//   EMAIL_FROM      — 已通过域名验证的发件地址，如 "MedAI Hub <no-reply@your-domain.com>"
//
// 安全：
//   - 邮件正文由服务端依据白名单字段拼装，不接受客户端任意正文/HTML。
//   - 不抓取任意 URL，仅包含 doi.org / PubMed 官方链接。
//   - 仅向用户本人填写的单一地址发送；进程内短时限额防滥用。
//   - 「受理成功」与「最终送达」分离返回。

const RESEND_API = 'https://api.resend.com/emails';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const MAX_TITLE = 500;
const MAX_ABSTRACT = 4000;

// 短时防滥用限额（进程内 best-effort）。
// 注意：Serverless 多实例下，此 Map 仅对单实例内计数，NOT 可靠的全局限额。
// 生产级全局限流需接入持久化存储（如 Upstash Redis），列为后续项；
// 本阶段以服务端字段白名单 + 固定正文 + 仅发送单一收件地址作为兜底防滥用，
// 并依赖邮件服务商（Resend）自身的限额作为外层约束。
const RATE_LIMIT = { windowMs: 60 * 60 * 1000, max: 10 };
const rateStore = new Map();

function clientIp(req) {
  return (
    req.headers.get('x-nf-client-connection-ip') ||
    req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    req.headers.get('client-ip') ||
    'unknown'
  );
}

function checkRate(ip) {
  const now = Date.now();
  const entry = rateStore.get(ip);
  if (!entry || now - entry.ts > RATE_LIMIT.windowMs) {
    rateStore.set(ip, { ts: now, count: 1 });
    return true;
  }
  if (entry.count >= RATE_LIMIT.max) return false;
  entry.count += 1;
  return true;
}

function sanitize(s, max) {
  if (typeof s !== 'string') return '';
  return s.replace(/[\r\n]+/g, ' ').trim().slice(0, max);
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

export default async function handler(req) {
  if (req.method !== 'POST') {
    return json({ ok: false, error: 'method_not_allowed', message: '仅支持 POST。' }, 405);
  }

  // 未配置邮件服务：明确返回「未配置」，不伪造成功
  const apiKey = (process.env.RESEND_API_KEY || '').trim();
  const from = (process.env.EMAIL_FROM || '').trim();
  if (!apiKey || !from) {
    return json({
      ok: false,
      error: 'not_configured',
      message: '邮件功能暂未开通（服务端未配置 RESEND_API_KEY 或 EMAIL_FROM），请通过原文链接访问。',
      required: ['RESEND_API_KEY', 'EMAIL_FROM'],
    }, 503);
  }

  let body;
  try {
    body = JSON.parse(await req.text() || '{}');
  } catch {
    return json({ ok: false, error: 'bad_request', message: '请求体不是合法 JSON。' }, 400);
  }

  const email = sanitize(body.email, 254);
  const item = body.item && typeof body.item === 'object' ? body.item : {};

  if (!EMAIL_RE.test(email)) {
    return json({ ok: false, error: 'invalid_email', message: '邮箱格式不正确。' }, 400);
  }

  const title = sanitize(item.title, MAX_TITLE);
  const doi = sanitize(item.doi, 128);
  const pmid = sanitize(item.pmid, 32);

  // 明确文献身份：标题 + 至少一个 DOI/PMID
  if (!title) {
    return json({ ok: false, error: 'missing_identity', message: '缺少文献标题。' }, 400);
  }
  if (!doi && !pmid) {
    return json({ ok: false, error: 'missing_identity', message: '该条目缺少 DOI/PMID，暂不支持链接邮件发送。' }, 400);
  }

  const ip = clientIp(req);
  if (!checkRate(ip)) {
    return json({ ok: false, error: 'rate_limited', message: '发送过于频繁，请稍后再试。' }, 429);
  }

  // 服务端拼装正文（白名单字段，不接受任意正文/HTML）
  const authors = sanitize(item.authors, 1000);
  const journal = sanitize(item.journal, 300);
  const date = sanitize(item.date, 64);
  const abstract = sanitize(item.abstract, MAX_ABSTRACT);
  const source = sanitize(item.source, 200);

  const links = [];
  if (doi) links.push(`DOI：https://doi.org/${encodeURIComponent(doi)}`);
  if (pmid) links.push(`PubMed：https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(pmid)}/`);

  const text = [
    `标题：${title}`,
    authors ? `作者：${authors}` : '',
    journal ? `期刊：${journal}` : '',
    date ? `日期：${date}` : '',
    source ? `来源：${source}` : '',
    '',
    '--- 摘要 ---',
    abstract || '（该记录未提供摘要）',
    '',
    '--- 原文链接 ---',
    ...links,
    '',
    '本邮件由 MedAI Hub 文献检索发送。全文访问条件以原站为准；如原文付费或需登录，请通过上述官方链接访问。',
  ].filter((l) => l !== '').join('\n');

  const html = `<div style="font-family:system-ui,sans-serif;line-height:1.6">
    <h2 style="margin:0 0 8px">${escapeHtml(title)}</h2>
    ${[authors && `<p>作者：${escapeHtml(authors)}</p>`, journal && `<p>期刊：${escapeHtml(journal)}</p>`, date && `<p>日期：${escapeHtml(date)}</p>`, source && `<p>来源：${escapeHtml(source)}</p>`].filter(Boolean).join('')}
    <h3 style="margin:16px 0 8px">摘要</h3>
    <p style="white-space:pre-line">${escapeHtml(abstract || '（该记录未提供摘要）')}</p>
    <h3 style="margin:16px 0 8px">原文链接</h3>
    <p>${links.map((l) => { const [label, url] = l.split('：'); return `<a href="${url}" style="color:#2563eb">${escapeHtml(label)}</a>`; }).join(' &nbsp; ')}</p>
    <p style="margin-top:20px;color:#666;font-size:12px">本邮件由 MedAI Hub 文献检索发送。全文访问条件以原站为准。</p>
  </div>`;

  try {
    const res = await fetch(RESEND_API, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from,
        to: [email],
        subject: `【MedAI Hub】文献：${title.slice(0, 60)}`,
        text,
        html,
      }),
    });

    // Resend 返回 200/202 表示受理成功（不保证最终送达）
    if (res.status >= 200 && res.status < 300) {
      return json({ ok: true, accepted: true, message: '已受理发送请求，最终送达状态请以邮箱收件为准。' });
    }
    const detail = await res.text().catch(() => '');
    return json({ ok: false, error: 'send_rejected', message: `邮件服务拒绝发送：${detail.slice(0, 200)}` }, 502);
  } catch (err) {
    return json({ ok: false, error: 'send_failed', message: `邮件服务调用失败：${(err && err.message) || 'unknown'}` }, 502);
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
