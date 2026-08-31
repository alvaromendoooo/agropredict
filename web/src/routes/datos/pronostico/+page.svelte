<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import SelectInput from '$lib/components/SelectInput.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import KVGrid from '$lib/components/KVGrid.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import EmptyState from '$lib/components/EmptyState.svelte';
import { callAction } from '$lib/client';
import { collectRows, firstKey } from '$lib/utils/format';
import { t } from '$lib/i18n';

let zona = $state('provincial');
let prediccion = $state('actual');
let identifier = $state('CC');

let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<Record<string, unknown> | null>(null);
let errorMessage = $state('');

const zonaOptions = $derived([
{ value: 'provincial', label: $t('forecastView.zoneProv') },
{ value: 'nacional', label: $t('forecastView.zoneNat') },
{ value: 'ccaa', label: $t('forecastView.zoneCcaa') }
]);
const prediccionOptions = $derived([
{ value: 'actual', label: $t('forecastView.actual') },
{ value: 'futura', label: $t('forecastView.futura') }
]);

async function query(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';

const outcome = await callAction<Record<string, unknown>>(
'query',
{ zona, prediccion, identifier },
{
poll: true,
maxPolls: 20,
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

const rows = $derived(result ? collectRows(firstKey(result, ['temperatura_localidades'])) : []);
const summaryItems = $derived(
result && typeof result === 'object'
? [
{ label: $t('frostForecast.forecastDate'), value: firstKey(result, ['fecha_prediccion', 'fecha']) },
{ label: $t('frostForecast.skyState'), value: firstKey(result, ['estado_cielo']) },
{ label: $t('frostForecast.trendMax'), value: firstKey(result, ['tendencia_temp_max']) },
{ label: $t('frostForecast.trendMin'), value: firstKey(result, ['tendencia_temp_min']) },
{ label: $t('frostForecast.precipitation'), value: firstKey(result, ['precipitaciones']) },
{ label: $t('frostForecast.snowLevel'), value: firstKey(result, ['cotas_nieve']) },
{ label: $t('frostForecast.windGusts'), value: firstKey(result, ['rachas_viento']) },
{ label: $t('frostForecast.frostExpected'), value: firstKey(result, ['existencia_heladas']) }
]
: []
);
</script>

<PageHeader title={$t('forecastView.title')} subtitle={$t('forecastView.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('forecastView.query')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
query();
}}
>
<Field label={$t('forecastView.zone')}>
<SelectInput bind:value={zona} options={zonaOptions} />
</Field>
<Field label={$t('forecastView.prediction')}>
<SelectInput bind:value={prediccion} options={prediccionOptions} />
</Field>

{#if zona !== 'nacional'}
<Field label={$t('forecastView.identifier')} help={$t('forecastView.identifierHelp')}>
<TextInput bind:value={identifier} placeholder="CC" />
</Field>
{/if}

<button type="submit" disabled={loading} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('forecastView.query')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner visible={pending} {attempts} labelKey="common.loading" descKey="common.loading" />
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result}
<Panel title={$t('forecastView.results')}>
<div class="space-y-5">
<KVGrid items={summaryItems} columns={3} />
{#if rows.length > 0}
<div>
<h3 class="mb-2 text-sm font-semibold text-slate-700">{$t('frostForecast.localityTemps')}</h3>
<DataTable {rows} max={5} />
</div>
{:else}
<EmptyState message={$t('common.noData')} />
{/if}
</div>
</Panel>
{/if}
</div>
</div>
