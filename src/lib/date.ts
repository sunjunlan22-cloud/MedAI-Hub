// 统一日期格式化：显式以 Asia/Shanghai（东八区）展示，
// 避免构建环境（Netlify 默认 UTC）导致 +08:00 数据在服务端渲染时
// 被换算回前一天、并统一显示为 16:00 的时区偏移问题。
const TZ = 'Asia/Shanghai';

interface DateParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

export function toShanghaiParts(iso: string): DateParts | null {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });
  const parts = fmt.formatToParts(d);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? '';
  const year = parseInt(get('year'), 10);
  const month = parseInt(get('month'), 10);
  const day = parseInt(get('day'), 10);
  const hour = parseInt(get('hour'), 10);
  const minute = parseInt(get('minute'), 10);
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) return null;
  return { year, month, day, hour, minute };
}

// 完整日期：YYYY/MM/DD（如 2025/10/13）
export function formatDateZh(iso?: string | null): string {
  if (!iso) return '日期待核实';
  const p = toShanghaiParts(iso);
  if (!p) return '日期待核实';
  return `${p.year}/${String(p.month).padStart(2, '0')}/${String(p.day).padStart(2, '0')}`;
}

// 短日期键：M月D日（如 10月13日）
export function formatDateKey(iso: string): string {
  const p = toShanghaiParts(iso);
  return p ? `${p.month}月${p.day}日` : '';
}

// 年份
export function formatYear(iso: string): number {
  const p = toShanghaiParts(iso);
  return p ? p.year : new Date().getFullYear();
}

// 时间：HH:mm
export function formatTime(iso: string): string {
  const p = toShanghaiParts(iso);
  return p ? `${String(p.hour).padStart(2, '0')}:${String(p.minute).padStart(2, '0')}` : '';
}

// 完整日期时间：YYYY/MM/DD HH:mm
export function formatDateTimeZh(iso?: string | null): string {
  if (!iso) return '日期待核实';
  const p = toShanghaiParts(iso);
  if (!p) return '日期待核实';
  return `${p.year}/${String(p.month).padStart(2, '0')}/${String(p.day).padStart(2, '0')} ${String(p.hour).padStart(2, '0')}:${String(p.minute).padStart(2, '0')}`;
}
