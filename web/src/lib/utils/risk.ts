export type RiskLevel = 'critical' | 'high' | 'moderate' | 'low' | 'none' | 'unknown';

/** Maps the heterogeneous risk labels of the APIs to a canonical level. */
export function riskLevel(label: unknown): RiskLevel {
const s = String(label ?? '').toUpperCase();
if (!s) return 'unknown';
if (/CRIT/.test(s)) return 'critical';
if (/ALTA|HIGH|SEVERA/.test(s)) return 'high';
if (/MODER|MEDIA/.test(s)) return 'moderate';
if (/DEBIL|WEAK|BAJA|LOW/.test(s)) return 'low';
if (/SIN|NO.RISK|NONE/.test(s)) return 'none';
return 'unknown';
}

const BADGE: Record<RiskLevel, string> = {
critical: 'bg-red-100 text-red-800 ring-red-600/20',
high: 'bg-orange-100 text-orange-800 ring-orange-600/20',
moderate: 'bg-amber-100 text-amber-800 ring-amber-600/20',
low: 'bg-lime-100 text-lime-800 ring-lime-600/20',
none: 'bg-green-100 text-green-800 ring-green-600/20',
unknown: 'bg-slate-100 text-slate-600 ring-slate-500/20'
};

export const RISK_DOT: Record<RiskLevel, string> = {
critical: 'bg-red-500',
high: 'bg-orange-500',
moderate: 'bg-amber-500',
low: 'bg-lime-500',
none: 'bg-green-500',
unknown: 'bg-slate-400'
};

export function riskBadgeClass(label: unknown): string {
return BADGE[riskLevel(label)];
}

/** Weekly alert level (0-100 scale) of the ITACyL pest calendars. */
export function alertLevelColor(level: unknown): string {
const n = Number(level);
if (!Number.isFinite(n)) return 'bg-slate-200';
if (n < 50) return 'bg-lime-400';
if (n < 75) return 'bg-amber-400';
return 'bg-red-500';
}

/** Palette used by the chart components. */
export const CHART_COLORS = ['#16a34a', '#2563eb', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9'];
