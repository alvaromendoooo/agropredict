import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome, readActionPayload } from '$lib/server/helpers';

export const load: PageServerLoad = async () => {
try {
return { initial: await dataService.metadatos('parcelas') };
} catch {
return { initial: [] };
}
};

export const actions: Actions = {
load: async ({ request }) => {
const body = await readActionPayload(request);
const tipo = String(body?.['tipo'] ?? 'parcelas');
if (!['parcelas', 'dispositivos', 'sensores'].includes(tipo)) {
return fail(400, { message: 'Invalid metadata type' });
}

try {
return { result: await dataService.metadatos(tipo) };
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
