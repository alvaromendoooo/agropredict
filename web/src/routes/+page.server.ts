import type { PageServerLoad } from './$types';
import { dataService } from '$lib/server/dataService';
import { predictor } from '$lib/server/predictor';

function asArray(value: unknown): unknown[] {
return Array.isArray(value) ? value : [];
}

export const load: PageServerLoad = async () => {
const [crops, sensors, pests, frost] = await Promise.allSettled([
dataService.crops(),
dataService.metadatos('sensores'),
dataService.pestCalendars({}),
predictor.heladasFuturas('provincial', { codigo_provincia: 'CC' })
]);

const fulfilled = <T>(result: PromiseSettledResult<T>, fallback: T): T =>
result.status === 'fulfilled' ? result.value : fallback;

return {
crops: asArray(fulfilled(crops, [] as unknown)),
sensors: asArray(fulfilled(sensors, [] as unknown)),
pests: asArray(fulfilled(pests, [] as unknown)),
frost: fulfilled(frost, null as unknown)
};
};
