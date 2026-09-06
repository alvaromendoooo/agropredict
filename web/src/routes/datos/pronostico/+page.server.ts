import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome, isPending, readActionPayload } from '$lib/server/helpers';

const ZONAS = ['nacional', 'provincial', 'ccaa'];
const PREDICCIONES = ['actual', 'futura'];

export const actions: Actions = {
query: async ({ request }) => {
const body = await readActionPayload(request);
if (!body) return fail(400, { message: 'Invalid payload' });

const zona = String(body['zona'] ?? 'provincial');
const prediccion = String(body['prediccion'] ?? 'actual');
if (!ZONAS.includes(zona) || !PREDICCIONES.includes(prediccion)) {
return fail(400, { message: 'Invalid zone or prediction' });
}

const identifier = String(body['identifier'] ?? '').trim();
const query: { ccaaId?: string; provinciaId?: string } = {};
if (zona === 'provincial') query['provinciaId'] = identifier;
if (zona === 'ccaa') query['ccaaId'] = identifier;

try {
const data = await dataService.forecast(zona, prediccion, query);
if (isPending(data)) return { __pending: true };
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
