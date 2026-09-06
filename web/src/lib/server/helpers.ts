import { ApiError } from './http';

/** Detects the PENDING/LOADING ingestion states returned by data-service. */
export function isPending(data: unknown): boolean {
return (
!!data &&
typeof data === 'object' &&
['PENDING', 'LOADING'].includes(String((data as Record<string, unknown>)['status']))
);
}

/** Normalises any thrown error into a fail()-friendly outcome. */
export function errorOutcome(err: unknown): { status: number; message: string } {
if (err instanceof ApiError) return { status: err.status, message: err.message };
return { status: 500, message: err instanceof Error ? err.message : 'Unexpected error' };
}

/** Extracts a list of names from an API payload (strings or {nombre} objects). */
export function nameList(value: unknown): string[] {
if (!Array.isArray(value)) return [];
return value
.map((item) =>
typeof item === 'string'
? item
: ((item as Record<string, unknown>)?.['nombre'] as string | undefined)
)
.filter((v): v is string => typeof v === 'string' && v.length > 0);
}

/** Builds the streaming Response for a downloaded PDF report. */
export function pdfResponse(bytes: ArrayBuffer, filename: string): Response {
return new Response(bytes, {
headers: {
'content-type': 'application/pdf',
'content-disposition': `attachment; filename="${filename}"`
}
});
}

/**
 * Reads the JSON payload of an action call. The client sends it form-encoded
 * (SvelteKit actions do not accept application/json bodies) inside a field named payload.
 */
export async function readActionPayload(request: Request): Promise<Record<string, unknown>> {
const form = await request.formData().catch(() => null);
if (!form) return {};
const raw = form.get('payload');
if (typeof raw !== 'string' || raw === '') return {};
try {
const parsed: unknown = JSON.parse(raw);
return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
} catch {
return {};
}
}
