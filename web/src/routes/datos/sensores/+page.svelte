<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import ChartCard from '$lib/components/ChartCard.svelte';
import Callout from '$lib/components/Callout.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import EmptyState from '$lib/components/EmptyState.svelte';
import { callAction } from '$lib/client';
import { collectRows, isPlainObject, todayISO } from '$lib/utils/format';
import { t } from '$lib/i18n';

let eui = $state('');
let campo = $state('');
let fechaInicio = $state(todayISO(-15));
let fechaFin = $state(todayISO());

let loading = $state(false);
let result = $state<unknown>(null);
let notFoundMessage = $state('');
let errorMessage = $state('');

const FIELD_SUGGESTIONS = ['humedad_foliar', 'temperatura_max', 'temperatura_min', 'temperatura_suelo', 'temperatura_hojas'];

interface MeasurementRow {
	[key: string]: unknown;
timestamp: string;
campo: string;
valor: number | null;
eui: string;
}

function flatten(value: unknown): MeasurementRow[] {
const groups = Array.isArray(value) ? value : [value];
const rows: MeasurementRow[] = [];
for (const group of groups) {
if (!isPlainObject(group)) continue;
const groupEui = String(group['eui'] ?? eui);
const resultados = group['resultados'];
if (!Array.isArray(resultados)) continue;
for (const item of resultados) {
if (!isPlainObject(item)) continue;
const raw = item['valor'];
rows.push({
timestamp: String(item['timestamp'] ?? ''),
campo: String(item['campo'] ?? ''),
valor: typeof raw === 'number' ? raw : Number.isFinite(Number(raw)) ? Number(raw) : null,
eui: groupEui
});
}
}
return rows.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

const rows = $derived(result === null ? [] : flatten(result));

const campos = $derived([...new Set(rows.map((row) => row.campo))]);

const chart = $derived(
rows.length > 0
? {
labels: rows.map((row) => row.timestamp.slice(0, 16)),
datasets: campos.map((campoItem) => ({
label: campoItem,
data: rows.map((row) => (row.campo === campoItem ? row.valor : null))
}))
}
: null
);

async function query(): Promise<void> {
loading = true;
notFoundMessage = '';
errorMessage = '';

const outcome = await callAction<unknown>('query', {
eui,
nombre_predictor: campo,
fecha_inicio: fechaInicio,
fecha_fin: fechaFin
});

loading = false;
if (!outcome.ok) {
if (outcome.status === 404) {
notFoundMessage = outcome.message;
result = null;
} else {
errorMessage = outcome.message;
}
return;
}
if (outcome.pending) return;
result = outcome.result;
}
</script>

<PageHeader title={$t('sensors.title')} subtitle={$t('sensors.subtitle')} />

<Callout message={$t('sensors.noProvider')} tone="info" />

<div class="mt-6 grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('sensors.query')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
query();
}}
>
<Field label={$t('sensors.eui')}>
<TextInput bind:value={eui} placeholder={$t('sensors.euiPlaceholder')} />
</Field>

<Field label={$t('sensors.field')} help={$t('sensors.fieldHelp')}>
<TextInput bind:value={campo} placeholder={$t('sensors.fieldPlaceholder')} list="sensor-fields" />
</Field>
<datalist id="sensor-fields">
{#each FIELD_SUGGESTIONS as suggestion (suggestion)}<option value={suggestion}></option>{/each}
</datalist>

<div class="grid grid-cols-2 gap-3">
<Field label={$t('sensors.startDate')}>
<TextInput bind:value={fechaInicio} type="date" />
</Field>
<Field label={$t('sensors.endDate')}>
<TextInput bind:value={fechaFin} type="date" />
</Field>
</div>

<button type="submit" disabled={loading} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('sensors.query')}
</button>
</form>
</Panel>

<div class="space-y-6">
{#if notFoundMessage}
<EmptyState message={notFoundMessage} />
{:else if errorMessage}
<ErrorState message={errorMessage} />
{:else if result !== null}
{#if rows.length === 0}
<EmptyState message={$t('common.noData')} />
{:else}
<div class="space-y-4">
<p class="text-sm font-medium text-slate-500">{$t('sensors.measurements')}: {rows.length}</p>
{#if chart}<ChartCard title={$t('sensors.chart')} labels={chart.labels} datasets={chart.datasets} />{/if}
<DataTable rows={rows} max={5} />
</div>
{/if}
{/if}
</div>
</div>
