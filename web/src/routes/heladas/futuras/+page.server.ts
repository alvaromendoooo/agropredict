import { fail, json } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';
import { errorOutcome, isPending, nameList, pdfResponse } from '$lib/server/helpers';

const ZONAS = ['provincial', 'nacional'];

export const load: PageServerLoad = async () => {
const [localidades, variedades] = await Promise.allSettled([
dataService.localidades(),
dataService.variedades()
]);

return {
localidades:
localidades.status === 'fulfilled' ? nameList(localidades.value) : [],
variedades:
variedades.status === 'fulfilled' ? nameList(variedades.value) : []
};
};

function buildPayload(body: Record<string, unknown>): Record<string, unknown> | string {
const zona = String(body['zona'] ?? 'provincial');
if (!ZONAS.includes(zona)) return 'Invalid zone';

const payload: Record<string, unknown> = {
evaluacion_var: Boolean(body['evaluacion_var']),
evaluacion_loc: Boolean(body['evaluacion_loc']),
variedades: Array.isArray(body['variedades']) ? body['variedades'] : undefined,
localidades: Array.isArray(body['localidades']) ? body['localidades'] : undefined
};

if (zona === 'provincial') {
const code = String(body['code'] ?? '').trim();
if (!code) return 'A province code is required';
payload['codigo_provincia'] = code;
}

return payload;
}

export const actions: Actions = {
predict: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
if (!body) return fail(400, { message: 'Invalid payload' });

const payload = buildPayload(body);
if (typeof payload === 'string') return fail(400, { message: payload });

try {
const data = await predictor.heladasFuturas(String(body['zona']), payload);
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
const out = await predictor.heladasFuturasPdf(
String(body['zona']),
payload,
'agro-predict-frost-forecast.pdf'
);
if (out.kind === 'json') return json({ pdfAvailable: false });
return pdfResponse(out.bytes, out.filename);
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
