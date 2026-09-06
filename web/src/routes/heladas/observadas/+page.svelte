<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import Toggle from '$lib/components/Toggle.svelte';
import ChipSelect from '$lib/components/ChipSelect.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import KVGrid from '$lib/components/KVGrid.svelte';
import RiskBadge from '$lib/components/RiskBadge.svelte';
import Callout from '$lib/components/Callout.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import PdfDownloadButton from '$lib/components/PdfDownloadButton.svelte';
import { callAction } from '$lib/client';
import { collectRows, firstKey } from '$lib/utils/format';
import { t } from '$lib/i18n';

let { data } = $props();

let tipo = $state('Dia');
let source = $state('provincia');
let code = $state('CC');
let evaluacion = $state(false);
let variedades = $state<string[]>([]);

let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<Record<string, unknown> | null>(null);
let errorMessage = $state('');

const tipoOptions = $derived([
{ value: 'Hora', label: $t('frostObserved.hourly') },
{ value: 'Dia', label: $t('frostObserved.daily') },
{ value: 'Semana', label: $t('frostObserved.weekly') }
]);

async function predict(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';

const outcome = await callAction<Record<string, unknown>>(
'predict',
{ tipo, source, code, evaluacion, variedades },
{
poll: true,
maxPolls: 40,
delayMs: 3000,
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
return { tipo, source, code, evaluacion, variedades };
}

const summaryItems = $derived(
result
? [
{
label: $t('frostObserved.daysBelowZero'),
value: firstKey(result, ['dias_bajo_cero'])
},
{
label: $t('frostObserved.minTempRecorded'),
value: firstKey(result, ['temperatura_minima_registrada'])
},
{
label: $t('frostObserved.minTempDates'),
value: firstKey(result, ['fecha_temp_bajo_cero', 'fechas_bajo_cero'])
},
{
label: $t('frostObserved.dataType'),
value: firstKey(result, ['tipo', 'type'])
}
]
: []
);

const blancas = $derived(
result ? collectRows(firstKey(result, ['heladas_blancas', 'riesgos_heladas_blancas'])) : []
);
const negras = $derived(
result ? collectRows(firstKey(result, ['heladas_negras', 'riesgos_heladas_negras'])) : []
);
const varietyRows = $derived(
result
? collectRows(firstKey(result, ['evaluacion_variedades', 'riesgos_variedades', 'variedades']))
: []
);
const alerta = $derived(
result
? (firstKey(result, ['alerta', 'alerta_global']) as Record<string, unknown> | undefined)
: undefined
);
</script>

<PageHeader title={$t('frostObserved.title')} subtitle={$t('frostObserved.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('frostObserved.parameters')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
predict();
}}
>
<Field label={$t('frostObserved.dataType')} help={$t('frostObserved.dataTypeHelp')}>
<SelectInput bind:value={tipo} options={tipoOptions} />
</Field>

<Field label={$t('frostObserved.source')}>
<div class="grid grid-cols-2 gap-2">
<button
type="button"
onclick={() => {
source = 'provincia';
code = 'CC';
}}
class="rounded-lg border px-3 py-2 text-sm font-medium {source === 'provincia'
? 'border-agro-600 bg-agro-50 text-agro-800'
: 'border-slate-300 bg-white text-slate-600'}"
>
{$t('frostObserved.byProvince')}
</button>
<button
type="button"
onclick={() => {
source = 'estacion';
code = '';
}}
class="rounded-lg border px-3 py-2 text-sm font-medium {source === 'estacion'
? 'border-agro-600 bg-agro-50 text-agro-800'
: 'border-slate-300 bg-white text-slate-600'}"
>
{$t('frostObserved.byStation')}
</button>
</div>
</Field>

{#if source === 'provincia'}
<Field label={$t('frostObserved.province')}>
<SelectInput
bind:value={code}
options={[
{ value: 'CC', label: 'CC - Cáceres' },
{ value: 'BA', label: 'BA - Badajoz' }
]}
/>
</Field>
{:else}
<Field label={$t('frostObserved.stationCode')} help={$t('frostObserved.stationCodeHelp')}>
<TextInput bind:value={code} placeholder="CC01" />
</Field>
{/if}

<Toggle
bind:checked={evaluacion}
label={$t('frostObserved.evaluation')}
help={$t('frostObserved.evaluationHelp')}
/>

{#if evaluacion}
<Field label={$t('frostObserved.varieties')}>
<ChipSelect
options={data.varieties}
bind:selected={variedades}
placeholder={$t('frostObserved.varietiesPlaceholder')}
/>
</Field>
{/if}

<button
type="submit"
disabled={loading}
class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60"
>
{loading ? $t('common.loading') : $t('frostObserved.predict')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner
visible={pending}
{attempts}
labelKey="frostObserved.pending"
descKey="frostObserved.pendingDesc"
/>

{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result}
<Panel title={$t('frostObserved.results')}>
<div class="space-y-5">
<div class="flex flex-wrap items-center gap-3">
{#if firstKey(result, ['nivel_riesgo', 'nivel', 'riesgo_global']) !== undefined}
<div>
<p class="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
{$t('frostObserved.riskLevel')}
</p>
<RiskBadge label={firstKey(result, ['nivel_riesgo', 'nivel', 'riesgo_global'])} />
</div>
{/if}
<div class="flex-1"></div>
<PdfDownloadButton
kind="heladas-observadas"
payload={payload}
filename="agro-predict-frost-observed.pdf"
disabled={loading}
/>
</div>

<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostObserved.summary')}</h3>
<KVGrid items={summaryItems} />
</div>

{#if alerta && typeof alerta === 'object' && alerta['mensaje']}
<Callout
title={$t('frostObserved.alert')}
message={String(alerta['mensaje'])}
tone="warning"
/>
{/if}

{#if blancas.length > 0 || negras.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">
{$t('frostObserved.frostEvents')}
</h3>
{#if blancas.length > 0}
<p class="mb-1 mt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
{$t('frostObserved.whiteFrost')}
</p>
<DataTable rows={blancas} />
{/if}
{#if negras.length > 0}
<p class="mb-1 mt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
{$t('frostObserved.blackFrost')}
</p>
<DataTable rows={negras} />
{/if}
</div>
{/if}

{#if varietyRows.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">
{$t('frostObserved.varietyEvaluation')}
</h3>
<DataTable rows={varietyRows} />
</div>
{/if}
</div>
</Panel>
{/if}
</div>
</div>
