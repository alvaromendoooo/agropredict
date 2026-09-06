import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome, readActionPayload } from '$lib/server/helpers';

export const actions: Actions = {
query: async ({ request }) => {
const body = await readActionPayload(request);
if (!body) return fail(400, { message: 'Invalid payload' });

const eui = String(body['eui'] ?? '').trim();
const nombrePredictor = String(body['nombre_predictor'] ?? '').trim();
const fechaInicio = String(body['fecha_inicio'] ?? '').trim();
const fechaFin = String(body['fecha_fin'] ?? '').trim();

if (!eui || !nombrePredictor || !fechaInicio || !fechaFin) {
return fail(400, { message: 'EUI, field and both dates are required' });
}

try {
const data = await dataService.sensores({
eui,
nombre_predictor: nombrePredictor,
fecha_inicio: fechaInicio,
fecha_fin: fechaFin
});
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
