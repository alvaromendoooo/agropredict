import { fail, json } from '@sveltejs/kit';
import type { Actions } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome } from '$lib/server/helpers';

export const actions: Actions = {
query: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
if (!body) return fail(400, { message: 'Invalid payload' });

const grupo = String(body['grupo'] ?? '').trim();
const tipo = String(body['tipo'] ?? '').trim();
const id = String(body['id'] ?? '').trim();

try {
const data = await dataService.pestCalendars({
...(grupo ? { grupo } : {}),
...(tipo ? { tipo } : {}),
...(id ? { id } : {})
});
return json({ result: data });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
