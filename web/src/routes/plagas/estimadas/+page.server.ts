import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';
import { errorOutcome, isPending, readActionPayload } from '$lib/server/helpers';

export const load: PageServerLoad = async () => {
let crops: string[] = [];
try {
crops = await dataService.cropNames();
} catch {
crops = [];
}
return { crops };
};

interface SensorRow {
sensor: string;
nombre_predictor_plaga: string;
}

function isoDate(value: unknown, fallback: string): string {
const raw = String(value ?? '').trim();
return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? `${raw}T00:00:00Z` : fallback;
}

export const actions: Actions = {
pests: async ({ request }) => {
const body = await readActionPayload(request);
const cultivo = String(body['cultivo'] ?? '').trim();
if (!cultivo) return { result: [] };
try {
return { result: await dataService.cultivoPlagas(cultivo) };
} catch {
return { result: [] };
}
},

predict: async ({ request }) => {
const body = await readActionPayload(request);
const cultivo = String(body['cultivo'] ?? '').trim();
const idPlaga = String(body['id_plaga'] ?? '').trim();
const fechaInicio = isoDate(body['fecha_inicio'], '');
const fechaFin = isoDate(body['fecha_fin'], '');

if (!cultivo || !idPlaga || !fechaInicio || !fechaFin) {
return fail(400, { message: 'Crop, pest and date range are required' });
}

const sensores = Array.isArray(body['datos_sensores'])
? (body['datos_sensores'] as SensorRow[])
.filter((row) => row && String(row['sensor'] ?? '').trim() && String(row['nombre_predictor_plaga'] ?? '').trim())
.map((row) => ({
sensor: String(row['sensor']).trim(),
nombre_predictor_plaga: String(row['nombre_predictor_plaga']).trim()
}))
: [];

const payload: Record<string, unknown> = {
cultivo,
id_plaga: idPlaga,
fecha_inicio: fechaInicio,
fecha_fin: fechaFin,
datos_sensores: sensores
};

const parcela = String(body['parcela'] ?? '').trim();
const estacion = String(body['codigo_estacion'] ?? '').trim();
const provincia = String(body['codigo_provincia'] ?? '').trim();
if (parcela) payload['parcela'] = parcela;
if (estacion) payload['codigo_estacion'] = estacion;
if (provincia) payload['codigo_provincia'] = provincia;

try {
const data = await predictor.plagasEstimadas(payload);
if (isPending(data)) return { __pending: true };
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
if (outcome.status === 503 || outcome.status === 504) return { __pending: true };
return fail(outcome.status, { message: outcome.message });
}
}
};
