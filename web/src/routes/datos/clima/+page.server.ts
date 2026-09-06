import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';
import { dataService } from '$lib/server/dataService';
import { errorOutcome, isPending, readActionPayload } from '$lib/server/helpers';

const TYPES = ['HORA', 'DIA', 'SEMANA'];

export const actions: Actions = {
query: async ({ request }) => {
const body = await readActionPayload(request);
if (!body) return fail(400, { message: 'Invalid payload' });

const type = String(body['type'] ?? 'DIA');
if (!TYPES.includes(type)) return fail(400, { message: 'Invalid granularity' });

const startDate = String(body['startDate'] ?? '').trim();
const endDate = String(body['endDate'] ?? '').trim();
if (!startDate || !endDate) return fail(400, { message: 'Both dates are required' });

const code = String(body['code'] ?? '').trim();
if (!code) return fail(400, { message: 'A province or station code is required' });

try {
const data =
body['source'] === 'estacion'
? await dataService.historicalEstacion({
estacionCode: code,
type,
startDate,
endDate
})
: await dataService.historicalProvincias({
provinceCode: code,
type,
startDate,
endDate
});

if (isPending(data)) return { __pending: true };
return { result: data };
} catch (err) {
const outcome = errorOutcome(err);
// 503/504 = data still being ingested or processed: the client polls again.
if (outcome.status === 503 || outcome.status === 504) return { __pending: true };
return fail(outcome.status, { message: outcome.message });
}
},

retryPending: async () => {
try {
await dataService.retryPending();
return { result: true };
} catch (err) {
const outcome = errorOutcome(err);
// 503/504 = data still being ingested or processed: the client polls again.
if (outcome.status === 503 || outcome.status === 504) return { __pending: true };
return fail(outcome.status, { message: outcome.message });
}
}
};
