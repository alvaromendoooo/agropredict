<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import { callAction } from '$lib/client';
import { collectRows } from '$lib/utils/format';
import { t } from '$lib/i18n';

let { data } = $props();

const TABS = [
{ id: 'parcelas', labelKey: 'parcels.tabParcels' },
{ id: 'dispositivos', labelKey: 'parcels.tabDevices' },
{ id: 'sensores', labelKey: 'parcels.tabSensors' }
];

let tab = $state('parcelas');
let rows = $derived(collectRows(data.initial));
let loading = $state(false);
let errorMessage = $state('');

async function load(selected: string): Promise<void> {
tab = selected;
loading = true;
errorMessage = '';

const outcome = await callAction<unknown>('load', { tipo: selected });
loading = false;
if (!outcome.ok) {
errorMessage = outcome.message;
return;
}
if (outcome.pending) return;
rows = collectRows(outcome.result);
}
</script>

<PageHeader title={$t('parcels.title')} subtitle={$t('parcels.subtitle')} />

{#if errorMessage}<ErrorState message={errorMessage} />{/if}

<div class="space-y-4">
<div class="flex gap-2">
{#each TABS as item (item.id)}
<button
type="button"
onclick={() => load(item.id)}
class="rounded-lg border px-4 py-2 text-sm font-medium transition {tab === item.id
? 'border-agro-600 bg-agro-50 text-agro-800'
: 'border-slate-300 bg-white text-slate-600 hover:border-agro-400'}"
>
{$t(item.labelKey)}
</button>
{/each}
</div>

<Panel title={$t(TABS.find((item) => item.id === tab)?.labelKey ?? 'parcels.tabParcels')}>
{#if loading}
<p class="py-6 text-center text-sm text-slate-400">{$t('common.loading')}</p>
{:else}
<DataTable {rows} max={8} />
{/if}
</Panel>
</div>
