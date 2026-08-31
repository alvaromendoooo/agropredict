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

export const actions: Actions = {
predict: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const cultivo = String(body?.['cultivo'] ?? '').trim();
if (!cultivo) return fail(400, { message: 'A crop name is required' });

try {
const data = await predictor.plagasCalculadas(cultivo);
if (isPending(data)) return json({ __pending: true });
return json({ result: data });
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
},

pdf: async ({ request }) => {
const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
const cultivo = String(body?.['cultivo'] ?? '').trim();
if (!cultivo) return fail(400, { message: 'A crop name is required' });

try {
const out = await predictor.plagasCalculadasPdf(
cultivo,
`agro-predict-pests-${cultivo.toLowerCase()}.pdf`
);
if (out.kind === 'json') return json({ pdfAvailable: false });
return pdfResponse(out.bytes, out.filename);
} catch (err) {
const outcome = errorOutcome(err);
return fail(outcome.status, { message: outcome.message });
}
}
};
