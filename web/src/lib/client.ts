import { parse } from 'devalue';

export type ActionResult<T = unknown> =
| { ok: true; pending: false; result: T }
| { ok: true; pending: true }
| { ok: false; status: number; message: string };

export interface CallOptions {
/** Keep re-invoking the action while the backend reports PENDING/LOADING. */
poll?: boolean;
maxPolls?: number;
delayMs?: number;
onPending?: (attempt: number) => void;
}

export function sleep(ms: number): Promise<void> {
return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Invokes a named form action of the current route and normalises the outcome.
 *
 * Server actions answer with:
 * - `{ result: ... }`            -> ok
 * - `{ __pending: true }`        -> data still being ingested (pollable)
 * - `fail(status, { message })`  -> normalized error
 */
export async function callAction<T = unknown>(
action: string,
payload?: unknown,
opts: CallOptions = {}
): Promise<ActionResult<T>> {
const maxPolls = opts.maxPolls ?? 30;
const delayMs = opts.delayMs ?? 2500;
const poll = opts.poll ?? false;

for (let attempt = 0; ; attempt++) {
let response: Response;
try {
response = await fetch(`?/${action}`, {
method: 'POST',
// SvelteKit form actions only accept form-encoded bodies
headers: { 'content-type': 'application/x-www-form-urlencoded' },
body: new URLSearchParams({ payload: JSON.stringify(payload ?? {}) })
});
} catch {
return { ok: false, status: 0, message: 'Network error' };
}

let body: unknown = null;
try {
body = await response.json();
} catch {
body = null;
}

// Kit wraps action results in an envelope: { type, status, data } where data is a
// devalue string of [returnValue]. Direct shapes are still supported.
const envelope = body as { type?: string; status?: number; data?: string; message?: string } | null;
let value: unknown = body;
let status = response.status;
let message: string | undefined;
if (envelope && typeof envelope.type === 'string' && typeof envelope.data === 'string') {
try {
value = parse(envelope.data) as unknown;
} catch {
value = null;
}
if (envelope.type === 'failure') {
status = envelope.status ?? response.status;
message = (value as { message?: string } | null)?.message ?? `HTTP ${status}`;
return { ok: false, status, message };
}
}

if (!response.ok) {
return { ok: false, status, message: message ?? `HTTP ${response.status}` };
}

const resultShape = value as { __pending?: boolean; result?: T } | null;
if (resultShape?.__pending) {
if (!poll || attempt >= maxPolls) return { ok: true, pending: true };
opts.onPending?.(attempt + 1);
await sleep(delayMs);
continue;
}

return {
ok: true,
pending: false,
result: (resultShape?.result !== undefined ? resultShape.result : value) as T
};
}
}
