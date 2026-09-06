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

export const actions: Actions = {
predict: async ({ request }) => {
const body = await readActionPayload(request);
const cultivo = String(body['cultivo'] ?? '').trim();
if (!cultivo) return fail(400, { message: 'A crop name is required' });

try {
const data = await predictor.plagasCalculadas(cultivo);
if (isPending(data)) return { __pending: true };
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
if (outcome.status === 503 || outcome.status === 504) return { __pending: true };
return fail(outcome.status, { message: outcome.message });
}
}
};
