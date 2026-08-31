export class ApiError extends Error {
constructor(
public readonly status: number,
message: string,
public readonly error?: string
) {
super(message);
this.name = 'ApiError';
}
}

export interface ApiFetchOptions {
base: string;
path: string;
method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
query?: Record<string, string | number | boolean | undefined>;
body?: unknown;
timeoutMs?: number;
}

function buildUrl(opts: ApiFetchOptions): URL {
const base = opts.base.endsWith('/') ? opts.base : `${opts.base}/`;
const url = new URL(opts.path, base);
if (opts.query) {
for (const [key, value] of Object.entries(opts.query)) {
if (value !== undefined) url.searchParams.set(key, String(value));
}
}
return url;
}

function normalizeError(err: unknown): ApiError {
if (err instanceof ApiError) return err;
if (err instanceof Error && err.name === 'AbortError') {
return new ApiError(504, 'Gateway timeout');
}
return new ApiError(502, err instanceof Error ? err.message : 'Network error');
}

/** Typed JSON fetch against a backend service with timeout + error normalization. */
export async function apiFetch<T = unknown>(opts: ApiFetchOptions): Promise<T> {
const url = buildUrl(opts);
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), opts.timeoutMs ?? 45_000);

try {
const response = await fetch(url, {
method: opts.method ?? 'GET',
headers: opts.body !== undefined ? { 'content-type': 'application/json' } : undefined,
body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
signal: controller.signal
});

const contentType = response.headers.get('content-type') ?? '';
const data = contentType.includes('application/json')
? await response.json().catch(() => null)
: null;

if (!response.ok) {
const payload = data as { message?: string; error?: string } | null;
throw new ApiError(
response.status,
payload?.message ?? `HTTP ${response.status}`,
payload?.error
);
}

return (data ?? (await response.text().catch(() => null))) as T;
} catch (err) {
throw normalizeError(err);
} finally {
clearTimeout(timer);
}
}

export type PdfOutcome =
| { kind: 'pdf'; bytes: ArrayBuffer; filename: string }
| { kind: 'json'; data: unknown };

/**
 * Requests a signed PDF report. The predictors answer with the binary file or,
 * when report generation fails, fall back to a JSON response.
 */
export async function fetchPdf(
opts: ApiFetchOptions & { fallbackName: string }
): Promise<PdfOutcome> {
const url = buildUrl(opts);
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), opts.timeoutMs ?? 60_000);

try {
const response = await fetch(url, {
method: opts.method ?? 'POST',
headers: { 'content-type': 'application/json', accept: 'application/pdf' },
body: JSON.stringify(opts.body ?? {}),
signal: controller.signal
});

const contentType = response.headers.get('content-type') ?? '';
if (contentType.includes('application/pdf')) {
const disposition = response.headers.get('content-disposition') ?? '';
const match = /filename="?([^";]+)"?/.exec(disposition);
return {
kind: 'pdf',
bytes: await response.arrayBuffer(),
filename: match?.[1] ?? opts.fallbackName
};
}

const data = contentType.includes('application/json')
? await response.json().catch(() => null)
: null;
if (!response.ok) {
const payload = data as { message?: string; error?: string } | null;
throw new ApiError(
response.status,
payload?.message ?? `HTTP ${response.status}`,
payload?.error
);
}
return { kind: 'json', data };
} catch (err) {
throw normalizeError(err);
} finally {
clearTimeout(timer);
}
}
