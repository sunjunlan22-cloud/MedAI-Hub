// MedAI Hub — PubMed 检索 / 文献详情（Netlify Function）
// 通过 NCBI E-utilities 官方接口按需检索，支持分页、超时、限流、缓存与错误处理。
//
// 端点（配合 netlify.toml redirects 暴露为 /api/pubmed）：
//   GET /api/pubmed?q=<term>&page=1&retmax=20          -> 检索（esearch + efetch）
//   GET /api/pubmed?pmid=36578069                      -> 单篇详情（efetch）
//
// 环境变量（可选，均非必需）：
//   NCBI_API_KEY  — NCBI API Key，提升限流（3 -> 10 req/s）
//   NCBI_EMAIL    — 联系邮箱（配合 API Key 使用）
//   NCBI_TOOL     — 调用方标识（默认 medai-hub）

const EUTILS = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils';
const DEFAULT_TOOL = 'medai-hub';
const TIMEOUT_MS = 12000;
const MAX_RETMAX = 50; // 按需检索上限（与定时快照 top-10 策略解耦）

const apiKey = (process.env.NCBI_API_KEY || '').trim();
const tool = (process.env.NCBI_TOOL || DEFAULT_TOOL).trim();
const email = (process.env.NCBI_EMAIL || '').trim();

// —— 极简限流（进程内）：NCBI 建议无 key ≤3 req/s，有 key ≤10 req/s ——
let lastRequestAt = 0;
const MIN_INTERVAL_MS = apiKey ? 100 : 350;
async function throttle() {
  const now = Date.now();
  const wait = Math.max(0, MIN_INTERVAL_MS - (now - lastRequestAt));
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastRequestAt = Date.now();
}

// —— 进程内缓存（TTL 5 分钟；serverless 冷启动后失效，仅缓解突发重复请求） ——
const cache = new Map();
const CACHE_TTL_MS = 5 * 60 * 1000;
function cacheGet(key) {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() - hit.ts > CACHE_TTL_MS) {
    cache.delete(key);
    return null;
  }
  return hit.value;
}
function cacheSet(key, value) {
  if (cache.size > 200) {
    const oldest = cache.keys().next().value;
    if (oldest) cache.delete(oldest);
  }
  cache.set(key, { ts: Date.now(), value });
}

function eutilsUrl(path, params) {
  const u = new URL(EUTILS + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') u.searchParams.set(k, v);
  }
  u.searchParams.set('tool', tool);
  if (email) u.searchParams.set('email', email);
  if (apiKey) u.searchParams.set('api_key', apiKey);
  return u.toString();
}

async function fetchWithTimeout(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { 'User-Agent': `${tool}/1.0 (+https://medai-hub.netlify.app)` },
    });
    if (!res.ok) throw new Error(`NCBI 返回 ${res.status}`);
    return res;
  } finally {
    clearTimeout(timer);
  }
}

// —— 轻量 XML 文本抽取（仅用于 efetch 的规整结构，避免引入 DOM 依赖） ——
function decodeEntities(s) {
  return s
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
    .replace(/&amp;/g, '&');
}
function stripTags(s) {
  return decodeEntities(s.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ')).trim();
}
function firstTag(xml, tag) {
  const re = new RegExp(`<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)</${tag}>`, 'i');
  const m = xml.match(re);
  return m ? stripTags(m[1]) : '';
}
function allTags(xml, tag) {
  const re = new RegExp(`<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)</${tag}>`, 'gi');
  const out = [];
  let m;
  while ((m = re.exec(xml)) !== null) out.push(stripTags(m[1]));
  return out.filter(Boolean);
}

function parseArticle(xml) {
  const title = firstTag(xml, 'ArticleTitle') || firstTag(xml, 'VernacularTitle');
  const abstract = (() => {
    const abs = xml.match(/<Abstract[^>]*>([\s\S]*?)<\/Abstract>/i);
    if (!abs) return '';
    const parts = allTags(abs[1], 'AbstractText');
    return parts.join(' ');
  })();

  // 作者：LastName + Initials
  const authors = [];
  const authorRe = /<Author[^>]*>([\s\S]*?)<\/Author>/gi;
  let am;
  while ((am = authorRe.exec(xml)) !== null) {
    const lastName = firstTag(am[1], 'LastName');
    const initials = firstTag(am[1], 'Initials');
    const collective = firstTag(am[1], 'CollectiveName');
    if (collective) authors.push(collective);
    else if (lastName) authors.push(`${lastName} ${initials}`.trim());
  }

  const journal = firstTag(xml, 'Title');
  const journalISO = firstTag(xml, 'ISOAbbreviation');
  const year = firstTag(xml, 'Year');
  const month = firstTag(xml, 'Month');
  const day = firstTag(xml, 'Day');
  const pubDate = [year, month, day].filter(Boolean).join('-');
  const volume = firstTag(xml, 'Volume');
  const issue = firstTag(xml, 'Issue');
  const pages = firstTag(xml, 'MedlinePgn');

  const articleIds = {};
  const idRe = /<ArticleId\s+IdType="([^"]+)"[^>]*>([\s\S]*?)<\/ArticleId>/gi;
  let im;
  while ((im = idRe.exec(xml)) !== null) {
    articleIds[im[1].toLowerCase()] = stripTags(im[2]);
  }

  const mesh = allTags(xml, 'DescriptorName');
  const pubTypes = allTags(xml, 'PublicationType');
  const grants = allTags(xml, 'GrantID');

  // 单位/机构：作者所属 Affiliation
  const affiliations = allTags(xml, 'Affiliation');

  return {
    pmid: firstTag(xml, 'PMID') || articleIds.pmid || '',
    pmcid: articleIds.pmc || '',
    doi: articleIds.doi || '',
    title,
    abstract,
    authors,
    affiliations: affiliations.slice(0, 20),
    journal,
    journalISO: journalISO || journal,
    pubDate,
    volume,
    issue,
    pages,
    mesh,
    pubTypes: pubTypes.filter((t) => t && t !== 'Journal Article'),
    grants,
    source: 'PubMed',
  };
}

async function efetchRecords(ids) {
  const url = eutilsUrl('/efetch.fcgi', {
    db: 'pubmed',
    id: ids.join(','),
    retmode: 'xml',
    rettype: 'abstract',
  });
  await throttle();
  const res = await fetchWithTimeout(url);
  const xml = await res.text();
  const records = [];
  const parts = xml.split(/<PubmedArticle\b/i).slice(1);
  for (const part of parts) {
    const rec = parseArticle(part);
    if (rec.pmid) records.push(rec);
  }
  return records;
}

async function search(term, page, retmax) {
  const retmaxNum = Math.min(Math.max(1, retmax), MAX_RETMAX);
  const retstart = Math.max(0, page - 1) * retmaxNum;

  const cacheKey = `search:${term}|${retstart}|${retmaxNum}`;
  const cached = cacheGet(cacheKey);
  if (cached) return cached;

  const esUrl = eutilsUrl('/esearch.fcgi', {
    db: 'pubmed',
    term,
    retstart,
    retmax: retmaxNum,
    retmode: 'json',
    sort: 'relevance',
  });
  await throttle();
  const esRes = await fetchWithTimeout(esUrl);
  const esJson = await esRes.json();
  const esResult = esJson.esearchresult || {};
  const ids = esResult.idlist || [];
  const count = parseInt(esResult.count || '0', 10);

  let records = [];
  if (ids.length > 0) {
    records = await efetchRecords(ids);
  }

  const result = {
    query: term,
    count, // 去重前的数据库命中总数（提示用，不用于去重统计）
    page,
    retmax: retmaxNum,
    totalPages: Math.ceil(count / retmaxNum),
    records,
  };
  cacheSet(cacheKey, result);
  return result;
}

async function detail(pmid) {
  const cacheKey = `detail:${pmid}`;
  const cached = cacheGet(cacheKey);
  if (cached) return cached;
  const records = await efetchRecords([pmid]);
  const result = records[0] || null;
  if (result) cacheSet(cacheKey, result);
  return result;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

export default async function handler(req) {
  const url = new URL(req.url);
  const params = url.searchParams;

  // CORS 预检
  if (req.method === 'OPTIONS') {
    return new Response('', {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
      },
    });
  }

  if (req.method !== 'GET') {
    return json({ ok: false, error: 'method_not_allowed' }, 405);
  }

  const pmid = params.get('pmid');
  const q = params.get('q');

  try {
    if (pmid && /^\d{1,9}$/.test(pmid)) {
      const rec = await detail(pmid);
      if (!rec) return json({ ok: false, error: 'not_found', message: '未找到该 PMID 对应文献。' }, 404);
      return json({ ok: true, record: rec, retrievedAt: new Date().toISOString() });
    }

    if (q && q.trim()) {
      const page = parseInt(params.get('page') || '1', 10) || 1;
      const retmax = parseInt(params.get('retmax') || '20', 10) || 20;
      const result = await search(q.trim(), page, retmax);
      return json({ ok: true, ...result, retrievedAt: new Date().toISOString() });
    }

    return json({ ok: false, error: 'missing_param', message: '缺少 q（检索词）或 pmid 参数。' }, 400);
  } catch (err) {
    const message = err && err.message ? err.message : 'unknown_error';
    if (/abort|timeout/i.test(message)) {
      return json({ ok: false, error: 'timeout', message: 'PubMed 接口超时，请稍后重试。' }, 504);
    }
    return json({ ok: false, error: 'upstream_error', message: `PubMed 接口调用失败：${message}` }, 502);
  }
}
