<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import ChartCard from '$lib/components/ChartCard.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import EmptyState from '$lib/components/EmptyState.svelte';
import { callAction } from '$lib/client';
import { t } from '$lib/i18n';
import { toast } from '$lib/stores/toast';
import { collectRows, isPlainObject, todayISO } from '$lib/utils/format';

let source = $state('provincia');
let code = $state('CC');
let type = $state('DIA');
let startDate = $state(todayISO(-30));
let endDate = $state(todayISO());

let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<Record<string, unknown> | null>(null);
let errorMessage = $state('');

const typeOptions = $derived([
{ value: 'HORA', label: $t('climate.hourly') },
{ value: 'DIA', label: $t('climate.daily') },
{ value: 'SEMANA', label: $t('climate.weekly') }
]);

async function query(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';

const outcome = await callAction<Record<string, unknown>>(
'query',
{ source, code, type, startDate, endDate },
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

async function retryPending(): Promise<void> {
const outcome = await callAction('retryPending');
toast(outcome.ok ? 'success' : 'error', outcome.ok ? $t('common.refresh') : outcome.message);
}

const rows = $derived(result ? collectRows(result) : []);

const DATE_KEYS = ['fecha', 'timestamp', 'fecha_hora', 'fechaHora', 'date'];
const dateKey = $derived(
rows.length > 0 ? (DATE_KEYS.find((key) => rows[0][key] !== undefined) ?? '') : ''
);
const labels = $derived(
dateKey ? rows.map((row) => String(row[dateKey] ?? '').slice(0, 16)) : rows.map((_, i) => i + 1)
);

const toNumbers = (key: string): (number | null)[] =>
rows.map((row) => {
const value = row[key];
if (typeof value === 'number') return value;
if (typeof value === 'string' && value !== '' && Number.isFinite(Number(value))) {
return Number(value);
}
return null;
});

const hasAny = (key: string): boolean => rows.some((row) => row[key] !== undefined && row[key] !== null);

const tempDatasets = $derived(
[
{ label: 'tempMax', data: toNumbers('tempMax'), has: hasAny('tempMax') },
{ label: 'tempMedia', data: toNumbers('tempMedia'), has: hasAny('tempMedia') },
{ label: 'tempMin', data: toNumbers('tempMin'), has: hasAny('tempMin') }
]
.filter((d) => d.has)
.map(({ label, data }) => ({ label, data }))
);
const humidityDatasets = $derived(hasAny('humedadMedia') ? [{ label: 'humedadMedia', data: toNumbers('humedadMedia') }] : []);
const precipDatasets = $derived(hasAny('precipitacion') ? [{ label: 'precipitacion', data: toNumbers('precipitacion') }] : []);
const windDatasets = $derived(hasAny('velViento') ? [{ label: 'velViento', data: toNumbers('velViento') }] : []);
</script>

<PageHeader title={$t('climate.title')} subtitle={$t('climate.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('climate.title')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
query();
}}
>
<Field label={$t('climate.source')}>
<div class="grid grid-cols-2 gap-2">
<button type="button" onclick={() => { source = 'provincia'; code = 'CC'; }} class="rounded-lg border px-3 py-2 text-sm font-medium {source === 'provincia' ? 'border-agro-600 bg-agro-50 text-agro-800' : 'border-slate-300 bg-white text-slate-600'}">{$t('climate.byProvince')}</button>
<button type="button" onclick={() => { source = 'estacion'; code = ''; }} class="rounded-lg border px-3 py-2 text-sm font-medium {source === 'estacion' ? 'border-agro-600 bg-agro-50 text-agro-800' : 'border-slate-300 bg-white text-slate-600'}">{$t('climate.byStation')}</button>
</div>
</Field>

{#if source === 'provincia'}
<Field label={$t('climate.provinceCode')}>
<SelectInput bind:value={code} options={[{ value: 'CC', label: 'CC - Cáceres' }, { value: 'BA', label: 'BA - Badajoz' }]} />
</Field>
{:else}
<Field label={$t('climate.stationCode')} help={$t('climate.stationCodeHelp')}>
<TextInput bind:value={code} placeholder="CC01" />
</Field>
{/if}

<Field label={$t('climate.dataType')}>
<SelectInput bind:value={type} options={typeOptions} />
</Field>

<div class="grid grid-cols-2 gap-3">
<Field label={$t('climate.startDate')}>
<TextInput bind:value={startDate} type="date" />
</Field>
<Field label={$t('climate.endDate')}>
<TextInput bind:value={endDate} type="date" />
</Field>
</div>

<button type="submit" disabled={loading} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('climate.query')}
</button>

<button type="button" onclick={retryPending} class="w-full rounded-lg border border-slate-300 px-4 py-2 text-xs font-medium text-slate-500 hover:border-agro-400 hover:text-agro-600">
{$t('climate.retryPending')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner visible={pending} {attempts} labelKey="climate.pending" descKey="climate.pendingDesc" />
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result}
{#if rows.length === 0}
<EmptyState message={$t('common.noData')} />
{:else}
<div class="space-y-4">
<p class="text-sm font-medium text-slate-500">{$t('climate.records')}: {rows.length}</p>

{#if tempDatasets.length > 0}
<ChartCard title={$t('climate.tempChart')} {labels} datasets={tempDatasets} />
{/if}
{#if humidityDatasets.length > 0}
<ChartCard title={$t('climate.humidityChart')} {labels} datasets={humidityDatasets} />
{/if}
{#if precipDatasets.length > 0}
<ChartCard title={$t('climate.precipChart')} {labels} datasets={precipDatasets} />
{/if}
{#if windDatasets.length > 0}
<ChartCard title={$t('climate.windChart')} {labels} datasets={windDatasets} />
{/if}

<DataTable {rows} max={10} />
</div>
{/if}
{/if}
</div>
</div>
