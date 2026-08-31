export function sleep(ms: number): Promise<void> {
return new Promise((resolve) => setTimeout(resolve, ms));
}

/** `temperatura_minima` / `tempMin` -> `Temperatura minima` / `Temp Min`. */
export function prettyKey(key: string): string {
return key
.replace(/_/g, ' ')
.replace(/([a-z])([A-Z])/g, '$1 $2')
.replace(/^./, (c) => c.toUpperCase());
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function formatValue(value: unknown): string {
if (value === null || value === undefined) return '—';
if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2);
if (typeof value === 'boolean') return value ? 'true' : 'false';
if (typeof value === 'string') return value;
if (Array.isArray(value)) {
return value.length <= 3
? value.map((v) => formatValue(v)).join(', ')
: `[${value.length} items]`;
}
if (isPlainObject(value)) {
const json = JSON.stringify(value);
return json.length > 140 ? `${json.slice(0, 137)}...` : json;
}
return String(value);
}

export function todayISO(offsetDays = 0): string {
const date = new Date();
date.setDate(date.getDate() + offsetDays);
return date.toISOString().slice(0, 10);
}

/** Finds the first present key among `keys` (top level of the object). */
export function firstKey(obj: Record<string, unknown>, keys: string[]): unknown {
for (const key of keys) {
if (obj[key] !== undefined && obj[key] !== null) return obj[key];
}
return undefined;
}

/**
 * Extracts an array of row objects from an arbitrary API payload: either the
 * payload itself is an array of objects, or it holds one under some key.
 */
export function collectRows(value: unknown): Record<string, unknown>[] {
if (Array.isArray(value)) return value.filter(isPlainObject);
if (isPlainObject(value)) {
for (const inner of Object.values(value)) {
if (Array.isArray(inner) && inner.length > 0 && isPlainObject(inner[0])) {
return inner.filter(isPlainObject);
}
}
}
return [];
}

/** Column keys of a row collection, capped to keep tables readable. */
export function rowKeys(rows: Record<string, unknown>[], max = 8): string[] {
const keys = new Set<string>();
for (const row of rows.slice(0, 20)) {
for (const key of Object.keys(row)) {
if (key !== 'id' && key !== 'estacion_id') keys.add(key);
}
if (keys.size >= max) break;
}
return [...keys].slice(0, max);
}
