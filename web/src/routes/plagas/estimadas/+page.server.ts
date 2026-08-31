import { fail, json } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';
import { errorOutcome, isPending, nameList, pdfResponse } from '$lib/server/helpers';

export const load: PageServerLoad = async () => {
let crops: string[] = [];
try {
crops = nameList(await dataService.crops());
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
/** Loads the pests associated with a crop (for the cascading select). */
pests: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const cultivo = String(body?.['cultivo'] ?? '').trim();
if (!cultivo) return json({ result: [] });

try {
const data = await dataService.cultivoPlagas(cultivo);
return json({ result: data });
} catch {
return json({ result: [] });
}
},

predict: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
if (!body) return fail(400, { message: 'Invalid payload' });

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

try {
const out = await predictor.plagasEstimadasPdf(
body,
'agro-predict-pests-estimated.pdf'
);
if (out.kind === 'json') return json({ pdfAvailable: false });
return pdfResponse(out.bytes, out.filename);
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
