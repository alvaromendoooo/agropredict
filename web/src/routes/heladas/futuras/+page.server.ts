import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';
import { errorOutcome, isPending, nameList, pdfResponse, readActionPayload } from '$lib/server/helpers';

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
const body = await readActionPayload(request);
if (!body) return fail(400, { message: 'Invalid payload' });

const payload = buildPayload(body);
if (typeof payload === 'string') return fail(400, { message: payload });

try {
const zona = String(body['zona']);
const forecastQuery = zona === 'provincial' ? { provinciaId: String(body['code'] ?? '') } : {};
// El pronostico de data-service puede seguir ingiriendose (AEMET + IA): si aun no
// esta listo avisamos al cliente (__pending) para que vuelva a intentarlo.
const snapshot = await dataService.forecast(zona, 'tomorrow', forecastQuery);
if (isPending(snapshot)) return { __pending: true };

const data = await predictor.heladasFuturas(zona, payload);
if (isPending(data)) return { __pending: true };
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
// 503/504 = data still being ingested or processed: the client polls again.
if (outcome.status === 503 || outcome.status === 504) return { __pending: true };
return fail(outcome.status, { message: outcome.message });
}
},

};
