<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import EmptyState from '$lib/components/EmptyState.svelte';
import { callAction } from '$lib/client';
import { collectRows, isPlainObject } from '$lib/utils/format';
import { t } from '$lib/i18n';

let { data } = $props();

interface CropRecord {
nombre?: unknown;
nombre_cientifico?: unknown;
grupo?: unknown;
descripcion?: unknown;
}

const cropRows = $derived<Record<string, unknown>[]>(
(Array.isArray(data.crops) ? data.crops : []).map((item) =>
isPlainObject(item) ? item : { nombre: item }
)
);
const cropNames = $derived(cropRows.map((crop) => String(crop.nombre ?? '')).filter((n) => n !== ''));
const modelRows = $derived(Array.isArray(data.modelos) ? (data.modelos as Record<string, unknown>[]) : []);
const stageRows = $derived(Array.isArray(data.etapas) ? (data.etapas as Record<string, unknown>[]) : []);

let selectedCrop = $state('');
let varieties = $state<string[]>([]);
let varietiesLoading = $state(false);

let selectedVariety = $state('');
let umbrales = $state<Record<string, unknown>[] | null>(null);
let horasFrio = $state<Record<string, unknown>[] | null>(null);
let detailError = $state('');

let selectedModel = $state('');
let modelVarieties = $state<Record<string, unknown>[]>([]);

const cropOptions = $derived(cropNames.map((name) => ({ value: name, label: name })));
const varietyOptions = $derived(varieties.map((name) => ({ value: name, label: name })));
const modelOptions = $derived(
modelRows
.map((row) => String(row['codigo'] ?? row['id'] ?? row['nombre'] ?? ''))
.filter((code) => code !== '')
.map((code) => ({ value: code, label: code }))
);

async function loadVarieties(): Promise<void> {
varieties = [];
selectedVariety = '';
umbrales = null;
horasFrio = null;
if (selectedCrop === '') return;

varietiesLoading = true;
const outcome = await callAction<unknown>('variedades', { cultivo: selectedCrop });
varietiesLoading = false;
if (!outcome.ok || outcome.pending) return;

const raw = outcome.result;
varieties = (Array.isArray(raw) ? raw : [])
.map((item) =>
typeof item === 'string'
? item
: String((item as Record<string, unknown>)?.['nombre'] ?? '')
)
.filter((name) => name !== '');
}

async function loadVarietyData(): Promise<void> {
umbrales = null;
horasFrio = null;
detailError = '';
if (selectedVariety === '') return;

const [umbralesOut, frioOut] = await Promise.all([
callAction<unknown>('umbrales', { nombre: selectedVariety }),
callAction<unknown>('horasFrio', { nombre: selectedVariety })
]);

if (!umbralesOut.ok && !frioOut.ok) {
detailError = 'message' in umbralesOut ? umbralesOut.message : 'Error';
return;
}

umbrales = umbralesOut.ok && !umbralesOut.pending ? collectRows(umbralesOut.result) : [];
horasFrio = frioOut.ok && !frioOut.pending ? collectRows(frioOut.result) : [];
}

async function loadModelVarieties(): Promise<void> {
modelVarieties = [];
if (selectedModel === '') return;
const outcome = await callAction<unknown>('modeloVariedades', { codigo: selectedModel });
if (!outcome.ok || outcome.pending) return;
modelVarieties = collectRows(outcome.result);
}
</script>

<PageHeader title={$t('crops.title')} subtitle={$t('crops.subtitle')} />

<div class="grid gap-6 lg:grid-cols-2">
<Panel title={$t('crops.crops')} subtitle={$t('crops.selectCrop')}>
<div class="space-y-4">
<Field label={$t('crops.name')}>
<SelectInput bind:value={selectedCrop} options={cropOptions} placeholder={$t('crops.selectCrop')} />
</Field>
<button
type="button"
onclick={loadVarieties}
disabled={selectedCrop === '' || varietiesLoading}
class="w-full rounded-lg border border-agro-600 px-4 py-2 text-sm font-semibold text-agro-700 transition hover:bg-agro-50 disabled:cursor-not-allowed disabled:opacity-60"
>
{$t('crops.varieties')} {varietiesLoading ? '...' : '↻'}
</button>

{#if varieties.length > 0}
<Field label={$t('crops.varietyName')}>
<SelectInput bind:value={selectedVariety} options={varietyOptions} placeholder={$t('crops.varietyName')} />
</Field>
<button
type="button"
onclick={loadVarietyData}
disabled={selectedVariety === ''}
class="w-full rounded-lg bg-agro-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60"
>
{$t('crops.loadUmbrales')}
</button>
{:else if selectedCrop !== '' && !varietiesLoading}
<EmptyState message={$t('common.noData')} />
{/if}

{#if detailError}<ErrorState message={detailError} />{/if}

{#if umbrales !== null && umbrales.length > 0}
<div>
<h3 class="mb-2 mt-4 text-sm font-semibold text-slate-700">{$t('crops.thresholds')}</h3>
<DataTable rows={umbrales} max={9} />
</div>
{/if}
{#if horasFrio !== null && horasFrio.length > 0}
<div>
<h3 class="mb-2 mt-4 text-sm font-semibold text-slate-700">{$t('crops.chillHours')}</h3>
<DataTable rows={horasFrio} max={6} />
</div>
{/if}
</div>
</Panel>

<div class="space-y-6">
<Panel title={$t('crops.models')} subtitle={$t('crops.selectModel')}>
<div class="space-y-4">
<Field label={$t('crops.chillModel')}>
<SelectInput bind:value={selectedModel} options={modelOptions} placeholder={$t('crops.selectModel')} />
</Field>
<button
type="button"
onclick={loadModelVarieties}
disabled={selectedModel === ''}
class="w-full rounded-lg border border-agro-600 px-4 py-2 text-sm font-semibold text-agro-700 transition hover:bg-agro-50 disabled:cursor-not-allowed disabled:opacity-60"
>
{$t('crops.modelVarieties')}
</button>
{#if modelVarieties.length > 0}
<DataTable rows={modelVarieties} />
{/if}
</div>
</Panel>

<Panel title={$t('crops.phenostages')}>
{#if stageRows.length > 0}
<DataTable rows={stageRows} max={4} />
{:else}
<EmptyState message={$t('common.noData')} />
{/if}
</Panel>
</div>
</div>

{#if cropRows.length > 0}
<div class="mt-6">
<Panel title={$t('crops.crops')}>
<DataTable rows={cropRows} max={6} />
</Panel>
</div>
{/if}
