<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import RiskBadge from '$lib/components/RiskBadge.svelte';
import PendingBanner from '$lib/components/PendingBanner.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import PdfDownloadButton from '$lib/components/PdfDownloadButton.svelte';
import { callAction } from '$lib/client';
import { t } from '$lib/i18n';

let { data } = $props();

let cultivo = $state('');
let loading = $state(false);
let pending = $state(false);
let attempts = $state(0);
let result = $state<unknown>(null);
let errorMessage = $state('');

interface PlagaEntry {
nombre?: unknown;
agente_causante?: unknown;
tipo?: unknown;
momento_critico?: unknown;
observaciones?: unknown;
mas_info?: unknown;
nivel_riesgo?: unknown;
}

interface CropEntry {
cultivo?: { nombre?: unknown; grupo?: unknown } | null;
plagas?: PlagaEntry[] | null;
}

const entries = $derived<Array<CropEntry>>(
result === null
? []
: Array.isArray(result)
? (result as CropEntry[])
: [result as CropEntry]
);

async function calculate(): Promise<void> {
loading = true;
pending = false;
attempts = 0;
errorMessage = '';

const outcome = await callAction<unknown>(
'predict',
{ cultivo },
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

function payload() {
return { cultivo };
}
</script>

<PageHeader title={$t('pestsCalc.title')} subtitle={$t('pestsCalc.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('pestsCalc.crop')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
calculate();
}}
>
<Field label={$t('pestsCalc.crop')} help={$t('pestsCalc.cropHelp')}>
<TextInput bind:value={cultivo} placeholder={$t('pestsCalc.cropPlaceholder')} list="crop-names" />
</Field>

<datalist id="crop-names">
{#each data.crops as crop (crop)}
<option value={crop}></option>
{/each}
</datalist>

<button
type="submit"
disabled={loading || cultivo.trim() === ''}
class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60"
>
{loading ? $t('common.loading') : $t('pestsCalc.calculate')}
</button>
</form>
</Panel>

<div class="space-y-6">
<PendingBanner visible={pending} {attempts} labelKey="pestsCalc.pending" descKey="common.loading" />
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result !== null}
<div class="space-y-6">
<div class="flex justify-end">
<PdfDownloadButton kind="plagas-calculadas" payload={payload} filename="agro-predict-pests.pdf" disabled={loading} />
</div>

{#each entries as entry, cropIndex (cropIndex)}
<section class="rounded-xl border border-slate-200 bg-white shadow-sm">
<header class="border-b border-slate-100 px-5 py-4">
<h2 class="text-base font-semibold text-slate-900">
{String(entry.cultivo?.nombre ?? cultivo)}
</h2>
{#if entry.cultivo?.grupo}
<p class="mt-0.5 text-sm text-slate-500">{$t('pestsCalc.cropGroup')}: {String(entry.cultivo.grupo)}</p>
{/if}
</header>

<div class="grid gap-4 p-5 sm:grid-cols-2">
{#if !entry.plagas || entry.plagas.length === 0}
<p class="text-sm text-slate-400">{$t('pestsCalc.noPests')}</p>
{/if}

{#each entry.plagas ?? [] as plaga, pestIndex (pestIndex)}
<article class="rounded-xl border border-slate-200 p-4">
<div class="flex items-start justify-between gap-2">
<h3 class="text-sm font-bold text-slate-900">{String(plaga.nombre ?? '—')}</h3>
<RiskBadge size="sm" label={plaga.nivel_riesgo} />
</div>

<p class="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400">{$t('pestsCalc.riskThisWeek')}</p>

{#if plaga.agente_causante}
<p class="mt-2 text-sm text-slate-600"><span class="font-semibold">{$t('pestsCalc.agent')}:</span> {String(plaga.agente_causante)}</p>
{/if}

{#if plaga.tipo}
<p class="mt-1 text-sm text-slate-600"><span class="font-semibold">{$t('pestsCalc.agentType')}:</span> {String(plaga.tipo)}</p>
{/if}

{#if plaga.momento_critico}
<p class="mt-2 text-sm text-slate-600"><span class="font-semibold">{$t('pestsCalc.criticalMoment')}:</span> {String(plaga.momento_critico)}</p>
{/if}

{#if plaga.observaciones}
<p class="mt-2 text-sm text-slate-600"><span class="font-semibold">{$t('pestsCalc.observations')}:</span> {String(plaga.observaciones)}</p>
{/if}

{#if plaga.mas_info}
<a href={String(plaga.mas_info)} target="_blank" rel="noreferrer" class="mt-3 inline-block text-sm font-medium text-agro-600 hover:text-agro-700">
{$t('pestsCalc.moreInfo')} →
</a>
{/if}
</article>
{/each}
</div>
</section>
{/each}
</div>
{/if}
</div>
</div>
