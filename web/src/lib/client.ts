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
headers: { 'content-type': 'application/json' },
body: JSON.stringify(payload ?? {})
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

if (!response.ok) {
const err = body as { message?: string } | null;
return {
ok: false,
status: response.status,
message: err?.message ?? `HTTP ${response.status}`
};
}

const envelope = body as { __pending?: boolean; result?: T } | null;
if (envelope?.__pending) {
if (!poll || attempt >= maxPolls) return { ok: true, pending: true };
opts.onPending?.(attempt + 1);
await sleep(delayMs);
continue;
}

return {
ok: true,
pending: false,
result: (envelope?.result !== undefined ? envelope.result : body) as T
};
}
}
