<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import Toggle from '$lib/components/Toggle.svelte';
import ChipSelect from '$lib/components/ChipSelect.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import KVGrid from '$lib/components/KVGrid.svelte';
import ChartCard from '$lib/components/ChartCard.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import PdfDownloadButton from '$lib/components/PdfDownloadButton.svelte';
import { callAction } from '$lib/client';
import { collectRows, firstKey, isPlainObject } from '$lib/utils/format';
import { t } from '$lib/i18n';

let { data } = $props();

let zona = $state('provincial');
let code = $state('CC');
let evaluacionVar = $state(false);
let evaluacionLoc = $state(false);
let variedades = $state<string[]>([]);
let localidades = $state<string[]>([]);

let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<Record<string, unknown> | null>(null);
let errorMessage = $state('');

const zonaOptions = $derived([
{ value: 'provincial', label: $t('frostForecast.zoneProv') },
{ value: 'nacional', label: $t('frostForecast.zoneNat') }
]);

async function predict(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';

const outcome = await callAction<Record<string, unknown>>(
'predict',
{
zona,
code,
evaluacion_var: evaluacionVar,
evaluacion_loc: evaluacionLoc,
variedades,
localidades
},
{
poll: true,
maxPolls: 30,
delayMs: 2500,
onPending: (n) => {
pending = true;
attempts = n;
}
}
);

loading = false;
if (!outcome.ok) {
errorMessage = outcome.message;
return;
}
if (outcome.pending) {
pending = false;
errorMessage = $t('common.pollTimeout');
return;
}
result = outcome.result;
}

function payload() {
return {
zona,
code,
evaluacion_var: evaluacionVar,
evaluacion_loc: evaluacionLoc,
variedades,
localidades
};
}

const summaryItems = $derived(
result
? [
{ label: $t('frostForecast.forecastDate'), value: firstKey(result, ['fecha_prediccion', 'fecha']) },
{ label: $t('frostForecast.skyState'), value: firstKey(result, ['estado_cielo']) },
{ label: $t('frostForecast.trendMax'), value: firstKey(result, ['tendencia_temp_max']) },
{ label: $t('frostForecast.trendMin'), value: firstKey(result, ['tendencia_temp_min']) },
{ label: $t('frostForecast.precipitation'), value: firstKey(result, ['precipitaciones']) },
{ label: $t('frostForecast.snowLevel'), value: firstKey(result, ['cotas_nieve']) },
{ label: $t('frostForecast.windGusts'), value: firstKey(result, ['rachas_viento']) },
{ label: $t('frostForecast.fogs'), value: firstKey(result, ['aparicion_nieblas']) },
{ label: $t('frostForecast.frostZone'), value: firstKey(result, ['zona_heladas']) }
]
: []
);

const localidadRows = $derived(
result ? collectRows(firstKey(result, ['temperatura_localidades', 'localidades_clima'])) : []
);

const localidadChart = $derived(
localidadRows.length > 0
? {
labels: localidadRows.map((row) => String(row['nombre'] ?? row['localidad'] ?? '')),
max: localidadRows.map((row) => Number(row['temperatura_maxima'] ?? 0)),
min: localidadRows.map((row) => Number(row['temperatura_minima'] ?? 0))
}
: null
);

const varietyRows = $derived(
result ? collectRows(firstKey(result, ['evaluacion_variedades', 'riesgos_variedades'])) : []
);
const localityEvalRows = $derived(
result ? collectRows(firstKey(result, ['evaluacion_localidades', 'riesgos_localidades'])) : []
);
const frostExpected = $derived(result ? firstKey(result, ['existencia_heladas']) : undefined);
</script>

<PageHeader title={$t('frostForecast.title')} subtitle={$t('frostForecast.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('frostForecast.parameters')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
predict();
}}
>
<Field label={$t('frostForecast.zone')} help={$t('frostForecast.identifierHelp')}>
<SelectInput bind:value={zona} options={zonaOptions} />
</Field>

{#if zona === 'provincial'}
<Field label={$t('frostForecast.province')}>
<SelectInput
bind:value={code}
options={[
{ value: 'CC', label: 'CC - Cáceres' },
{ value: 'BA', label: 'BA - Badajoz' }
]}
/>
</Field>
{/if}

<Toggle bind:checked={evaluacionVar} label={$t('frostForecast.evaluationVarieties')} />
{#if evaluacionVar}
<Field label={$t('frostForecast.varieties')}>
<ChipSelect options={data.variedades} bind:selected={variedades} placeholder={$t('frostForecast.varietiesPlaceholder')} />
</Field>
{/if}

<Toggle bind:checked={evaluacionLoc} label={$t('frostForecast.evaluationLocalities')} />
{#if evaluacionLoc}
<Field label={$t('frostForecast.localities')}>
<ChipSelect options={data.localidades} bind:selected={localidades} placeholder={$t('frostForecast.localitiesPlaceholder')} />
</Field>
{/if}

<button type="submit" disabled={loading} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('frostForecast.predict')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner visible={pending} {attempts} labelKey="frostForecast.pending" descKey="frostForecast.pendingDesc" />
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result}
<Panel title={$t('frostForecast.results')}>
<div class="space-y-5">
<div class="flex flex-wrap items-center gap-3">
{#if frostExpected !== undefined}
<div>
<p class="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">{$t('frostForecast.frostExpected')}</p>
{#if frostExpected === true || /SI\b|TRUE|YES/i.test(String(frostExpected))}
<span class="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-semibold text-red-800 ring-1 ring-inset ring-red-600/20">{$t('dashboard.yes')}</span>
{:else if frostExpected === false || /NO/i.test(String(frostExpected))}
<span class="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-green-800 ring-1 ring-inset ring-green-600/20">{$t('dashboard.no')}</span>
{:else}
<span class="text-sm font-semibold text-slate-700">{String(frostExpected)}</span>
{/if}
</div>
{/if}
<div class="flex-1"></div>
<PdfDownloadButton kind="heladas-futuras" payload={payload} filename="agro-predict-frost-forecast.pdf" disabled={loading} />
</div>

<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostForecast.results')}</h3>
<KVGrid items={summaryItems} columns={3} />
</div>

{#if localidadRows.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostForecast.localityTemps')}</h3>
<DataTable rows={localidadRows} max={4} />
{#if localidadChart}
<div class="mt-4">
<ChartCard labels={localidadChart.labels} datasets={[{ label: $t('frostForecast.maxTemp'), data: localidadChart.max, type: 'bar' }, { label: $t('frostForecast.minTemp'), data: localidadChart.min, type: 'bar' }]} yBeginAtZero={false} />
</div>
{/if}
</div>
{/if}

{#if varietyRows.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostForecast.varietyStress')}</h3>
<DataTable rows={varietyRows} />
</div>
{/if}

{#if localityEvalRows.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostForecast.localityEvaluation')}</h3>
<DataTable rows={localityEvalRows} />
</div>
{/if}
</div>
</Panel>
{/if}
</div>
</div>
