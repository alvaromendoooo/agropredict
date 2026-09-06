<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import RiskBadge from '$lib/components/RiskBadge.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import PdfDownloadButton from '$lib/components/PdfDownloadButton.svelte';
import { callAction } from '$lib/client';
import { t } from '$lib/i18n';
import { riskBadgeClass, RISK_DOT, riskLevel } from '$lib/utils/risk';

let { data } = $props();

let cultivo = $state('');
let idPlaga = $state('');
let fechaInicio = $state('');
let fechaFin = $state('');
let parcela = $state('');
let codigoEstacion = $state('');
let codigoProvincia = $state('');
let sensores = $state<Array<{ sensor: string; nombre_predictor_plaga: string }>>([]);

let pestOptions = $state<Array<{ value: string; label: string }>>([]);
let pestsLoading = $state(false);

let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<Record<string, unknown> | null>(null);
let errorMessage = $state('');
let selectedDay = $state(0);
let selectedPlagaIndex = $state(0);

interface DayProbability {
fecha?: unknown;
nivel_riesgo?: unknown;
mensaje?: unknown;
condiciones_cumplidas?: unknown;
condiciones_pendientes?: unknown;
}

interface PlagaEvaluada {
plaga_id?: unknown;
nombre?: unknown;
tipo?: unknown;
ventana_temporal?: unknown;
datos_probabilidad?: DayProbability[];
}

const plagasEvaluadas = $derived<PlagaEvaluada[]>(
result && Array.isArray(result['plagas_evaluadas'])
? (result['plagas_evaluadas'] as PlagaEvaluada[])
: []
);

const currentPlaga = $derived(plagasEvaluadas[selectedPlagaIndex] ?? null);
const currentDays = $derived(currentPlaga?.datos_probabilidad ?? []);
const currentDay = $derived(currentDays[selectedDay] ?? null);

const asArray = (value: unknown): string[] =>
Array.isArray(value) ? value.map((v) => String(v)) : [];

async function loadPests(): Promise<void> {
idPlaga = '';
pestOptions = [];
if (cultivo.trim() === '') return;

pestsLoading = true;
const outcome = await callAction<unknown>('pests', { cultivo });
pestsLoading = false;
if (!outcome.ok || outcome.pending) return;

const raw = outcome.result;
const list = Array.isArray(raw) ? raw : [];
const options: Array<{ value: string; label: string }> = [];
for (const cropEntry of list) {
const plagas = (cropEntry as Record<string, unknown>)?.['plaga'];
if (!Array.isArray(plagas)) continue;
for (const plaga of plagas) {
const record = plaga as Record<string, unknown>;
const publicId = String(record['public_id'] ?? '');
if (!publicId) continue;
options.push({
value: publicId,
label: `${publicId} - ${String(record['nombre'] ?? '')}`
});
}
}
pestOptions = options;
}

async function predict(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';
selectedDay = 0;
selectedPlagaIndex = 0;

const outcome = await callAction<Record<string, unknown>>(
'predict',
{
cultivo,
id_plaga: idPlaga,
fecha_inicio: fechaInicio,
fecha_fin: fechaFin,
parcela,
codigo_estacion: codigoEstacion,
codigo_provincia: codigoProvincia,
datos_sensores: sensores
},
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
return {
cultivo,
id_plaga: idPlaga,
fecha_inicio: fechaInicio,
fecha_fin: fechaFin,
parcela,
codigo_estacion: codigoEstacion,
codigo_provincia: codigoProvincia,
datos_sensores: sensores
};
}

function addSensor(): void {
sensores = [...sensores, { sensor: '', nombre_predictor_plaga: '' }];
}

function removeSensor(index: number): void {
sensores = sensores.filter((_, i) => i !== index);
}

function dayLabel(fecha: unknown): string {
const raw = String(fecha ?? '');
return raw.length >= 10 ? raw.slice(0, 10) : raw;
}
</script>

<PageHeader title={$t('pestsEst.title')} subtitle={$t('pestsEst.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('pestsEst.title')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
predict();
}}
>
<Field label={$t('pestsEst.crop')}>
<TextInput
bind:value={cultivo}
placeholder={$t('pestsEst.cropPlaceholder')}
list="crops-est"
/>
</Field>
<datalist id="crops-est">
{#each data.crops as crop (crop)}<option value={crop}></option>{/each}
</datalist>
<button
type="button"
onclick={loadPests}
disabled={cultivo.trim() === '' || pestsLoading}
class="w-full rounded-lg border border-agro-600 px-4 py-2 text-sm font-semibold text-agro-700 transition hover:bg-agro-50 disabled:cursor-not-allowed disabled:opacity-60"
>
{pestsLoading ? $t('common.loading') : $t('pestsEst.pest')} ↻
</button>
<p class="text-xs text-slate-400">{$t('pestsEst.pestSelectFirst')}</p>

<Field label={$t('pestsEst.pest')}>
<SelectInput bind:value={idPlaga} options={pestOptions} placeholder={$t('pestsEst.pestSelectFirst')} />
</Field>

<div class="grid grid-cols-2 gap-3">
<Field label={$t('pestsEst.startDate')}>
<TextInput bind:value={fechaInicio} type="date" />
</Field>
<Field label={$t('pestsEst.endDate')}>
<TextInput bind:value={fechaFin} type="date" />
</Field>
</div>

<details class="rounded-lg border border-slate-200 px-4 py-3">
<summary class="cursor-pointer text-sm font-semibold text-slate-700">{$t('common.advancedOptions')}</summary>
<div class="mt-4 space-y-4">
<Field label={$t('pestsEst.parcel')}>
<TextInput bind:value={parcela} placeholder="PARC-001" />
</Field>
<div class="grid grid-cols-2 gap-3">
<Field label={$t('pestsEst.stationCode')}>
<TextInput bind:value={codigoEstacion} placeholder="CC01" />
</Field>
<Field label={$t('pestsEst.provinceCode')}>
<TextInput bind:value={codigoProvincia} placeholder="CC" />
</Field>
</div>

<div>
<p class="text-sm font-medium text-slate-700">{$t('pestsEst.sensors')}</p>
<p class="mt-1 text-xs text-slate-400">{$t('pestsEst.sensorsHelp')}</p>
<div class="mt-2 space-y-2">
{#each sensores as row, index (index)}
<div class="flex items-center gap-2">
<input
type="text"
bind:value={sensores[index].sensor}
placeholder={$t('pestsEst.sensorEui')}
class="w-1/2 rounded-lg border border-slate-300 px-2 py-1.5 text-xs focus:border-agro-500 focus:outline-none"
/>
<input
type="text"
bind:value={sensores[index].nombre_predictor_plaga}
placeholder={$t('pestsEst.sensorField')}
class="w-1/2 rounded-lg border border-slate-300 px-2 py-1.5 text-xs focus:border-agro-500 focus:outline-none"
/>
<button type="button" onclick={() => removeSensor(index)} class="rounded-md px-2 py-1 text-xs font-semibold text-red-600 hover:bg-red-50">{$t('pestsEst.removeSensor')}</button>
</div>
{/each}
</div>
<button type="button" onclick={addSensor} class="mt-2 rounded-md border border-dashed border-slate-300 px-3 py-1 text-xs font-medium text-slate-500 hover:border-agro-400 hover:text-agro-600">
+ {$t('pestsEst.addSensor')}
</button>
</div>
</div>
</details>

<button type="submit" disabled={loading} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('pestsEst.predict')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner visible={pending} {attempts} labelKey="pestsEst.pending" descKey="common.loading" />
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result}
<Panel title={$t('pestsEst.results')}>
<div class="space-y-6">
<div class="flex justify-end">
<PdfDownloadButton kind="plagas-estimadas" payload={payload} filename="agro-predict-pests-estimated.pdf" disabled={loading} />
</div>

{#each plagasEvaluadas as plaga, plagaIndex (plagaIndex)}
<article class="rounded-xl border border-slate-200 p-4">
<button
type="button"
onclick={() => { selectedPlagaIndex = plagaIndex; selectedDay = 0; }}
class="block w-full text-left"
>
<h3 class="text-sm font-bold {selectedPlagaIndex === plagaIndex ? 'text-agro-700' : 'text-slate-900'}">
{String(plaga.nombre ?? '—')}
{#if plaga.tipo}<span class="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">{String(plaga.tipo)}</span>{/if}
</h3>
</button>

{#if selectedPlagaIndex === plagaIndex}
<p class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-slate-400">{$t('pestsEst.timeline')}</p>
<div class="flex flex-wrap gap-1.5">
{#each plaga.datos_probabilidad ?? [] as day, dayIndex (dayIndex)}
<button
type="button"
onclick={() => { selectedDay = dayIndex; }}
class="rounded-lg border px-2 py-1.5 text-center text-[11px] font-semibold transition {selectedDay === dayIndex
? 'border-slate-900 ring-2 ring-slate-900/20'
: 'border-transparent'} {riskBadgeClass(day.nivel_riesgo)}"
>
<span class="block">{dayLabel(day.fecha)}</span>
</button>
{/each}
</div>

{#if currentDay}
<div class="mt-4 rounded-lg border border-slate-200 bg-slate-50/60 p-4">
<div class="flex flex-wrap items-center gap-3">
<RiskBadge size="sm" label={currentDay.nivel_riesgo} />
<span class="text-sm font-semibold text-slate-700">{dayLabel(currentDay.fecha)}</span>
</div>

{#if currentDay.mensaje}<p class="mt-2 text-sm text-slate-600">{String(currentDay.mensaje)}</p>{/if}

{#if asArray(currentDay.condiciones_cumplidas).length > 0}
<p class="mt-3 text-xs font-semibold uppercase tracking-wide text-green-600">{$t('pestsEst.conditionsMet')}</p>
<ul class="mt-1 list-inside list-disc text-sm text-slate-600">
{#each asArray(currentDay.condiciones_cumplidas) as condition (condition)}<li>{condition}</li>{/each}
</ul>
{/if}

{#if asArray(currentDay.condiciones_pendientes).length > 0}
<p class="mt-3 text-xs font-semibold uppercase tracking-wide text-amber-600">{$t('pestsEst.conditionsPending')}</p>
<ul class="mt-1 list-inside list-disc text-sm text-slate-600">
{#each asArray(currentDay.condiciones_pendientes) as condition (condition)}<li>{condition}</li>{/each}
</ul>
{/if}

{#if plaga.ventana_temporal}
<p class="mt-3 text-xs text-slate-400">{$t('pestsEst.window')}: {JSON.stringify(plaga.ventana_temporal)}</p>
{/if}
</div>
{/if}
{/if}
</article>
{/each}
</div>
</Panel>
{/if}
</div>
</div>
