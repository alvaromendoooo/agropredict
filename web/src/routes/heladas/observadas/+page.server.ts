import { fail, json } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';
import { errorOutcome, isPending, nameList, pdfResponse } from '$lib/server/helpers';

const TIPOS = ['Hora', 'Dia', 'Semana'];

export const load: PageServerLoad = async () => {
let varieties: string[] = [];
try {
varieties = nameList(await dataService.variedades());
} catch {
varieties = [];
}
return { varieties };
};

function buildPayload(body: Record<string, unknown>): Record<string, unknown> | string {
const tipo = String(body['tipo'] ?? 'Dia');
if (!TIPOS.includes(tipo)) return 'Invalid data type';

const code = String(body['code'] ?? '').trim();
if (!code) return 'A province or station code is required';

const payload: Record<string, unknown> = {
evaluacion: Boolean(body['evaluacion']),
variedades: Array.isArray(body['variedades']) ? body['variedades'] : undefined
};
if (body['source'] === 'estacion') payload['codigo_estacion'] = code;
else payload['codigo_provincia'] = code;

return payload;
}

export const actions: Actions = {
predict: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
if (!body) return fail(400, { message: 'Invalid payload' });

const payload = buildPayload(body);
if (typeof payload === 'string') return fail(400, { message: payload });

try {
const data = await predictor.heladasObservadas(String(body['tipo']), payload);
if (isPending(data)) return json({ __pending: true });
return json({ result: data });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
},

pdf: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
if (!body) return fail(400, { message: 'Invalid payload' });

const payload = buildPayload(body);
if (typeof payload === 'string') return fail(400, { message: payload });

try {
const tipo = String(body['tipo']).toLowerCase();
const out = await predictor.heladasObservadasPdf(
String(body['tipo']),
payload,
`agro-predict-frost-observed-${tipo}.pdf`
);
if (out.kind === 'json') return json({ pdfAvailable: false });
return pdfResponse(out.bytes, out.filename);
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
