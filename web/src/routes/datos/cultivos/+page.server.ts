import { fail, json } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome } from '$lib/server/helpers';

export const load: PageServerLoad = async () => {
const [crops, modelos, etapas] = await Promise.allSettled([
dataService.crops(),
dataService.modelos(),
dataService.etapasFenologicas()
]);

const value = (result: PromiseSettledResult<unknown>): unknown =>
result.status === 'fulfilled' ? result.value : [];

return { crops: value(crops), modelos: value(modelos), etapas: value(etapas) };
};

export const actions: Actions = {
variedades: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const cultivo = String(body?.['cultivo'] ?? '').trim();
if (!cultivo) return json({ result: [] });
try {
return json({ result: await dataService.variedades(cultivo) });
} catch {
return json({ result: [] });
}
},

umbrales: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const nombre = String(body?.['nombre'] ?? '').trim();
if (!nombre) return fail(400, { message: 'A variety name is required' });
try {
return json({ result: await dataService.variedadUmbrales(nombre) });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
},

horasFrio: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const nombre = String(body?.['nombre'] ?? '').trim();
if (!nombre) return fail(400, { message: 'A variety name is required' });
try {
return json({ result: await dataService.variedadHorasFrio(nombre) });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
},

modeloVariedades: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const codigo = String(body?.['codigo'] ?? '').trim();
if (!codigo) return fail(400, { message: 'A model code is required' });
try {
return json({ result: await dataService.modeloVariedades(codigo) });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
