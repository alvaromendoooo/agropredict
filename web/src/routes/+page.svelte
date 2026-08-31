<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import StatCard from '$lib/components/StatCard.svelte';
import { t } from '$lib/i18n';

let { data } = $props();

const frost = $derived(
data.frost && typeof data.frost === 'object' ? (data.frost as Record<string, unknown>) : null
);

const frostExpected = $derived(
frost ? frost['existencia_heladas'] ?? frost['existencia_heladas_mañana'] : undefined
);

const frostIsYes = $derived(
frostExpected === true ||
String(frostExpected ?? '').toUpperCase() === 'TRUE' ||
/SI\b|YES/i.test(String(frostExpected ?? ''))
);
const frostIsNo = $derived(
!frostIsYes &&
(frostExpected === false || /NO/i.test(String(frostExpected ?? '')) === true) &&
String(frostExpected ?? '') !== ''
);

const quickLinks = [
{
href: '/heladas/observadas',
titleKey: 'dashboard.frostObserved',
descKey: 'dashboard.frostObservedDesc'
},
{
href: '/heladas/futuras',
titleKey: 'dashboard.frostForecast',
descKey: 'dashboard.frostForecastDesc'
},
{
href: '/plagas/calculadas',
titleKey: 'dashboard.pestsCalculated',
descKey: 'dashboard.pestsCalculatedDesc'
},
{
href: '/plagas/estimadas',
titleKey: 'dashboard.pestsEstimated',
descKey: 'dashboard.pestsEstimatedDesc'
}
];
</script>

<PageHeader title={$t('dashboard.title')} subtitle={$t('dashboard.subtitle')} />

<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
<StatCard label={$t('dashboard.statCrops')} value={String(data.crops.length)} />
<StatCard label={$t('dashboard.statPests')} value={String(data.pests.length)} />
<StatCard label={$t('dashboard.statSensors')} value={String(data.sensors.length)} />

<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
<p class="text-sm font-medium text-slate-500">{$t('dashboard.statFrost')}</p>
<div class="mt-2">
{#if frostExpected === undefined || frostExpected === null || frostExpected === ''}
<span class="text-2xl font-bold tracking-tight text-slate-300">{$t('dashboard.unknown')}</span>
{:else if frostIsYes}
<span class="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-semibold text-red-800 ring-1 ring-inset ring-red-600/20">{$t('dashboard.yes')}</span>
{:else if frostIsNo}
<span class="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-green-800 ring-1 ring-inset ring-green-600/20">{$t('dashboard.no')}</span>
{:else}
<span class="text-sm font-semibold text-slate-700">{String(frostExpected)}</span>
{/if}
</div>
<p class="mt-1 text-xs text-slate-400">{$t('dashboard.frostHint')}</p>
</div>
</div>

<h2 class="mb-1 mt-8 text-lg font-semibold text-slate-900">{$t('dashboard.quickAccess')}</h2>
<p class="mb-4 text-sm text-slate-500">{$t('dashboard.quickAccessDesc')}</p>

<div class="grid gap-4 sm:grid-cols-2">
{#each quickLinks as link (link.href)}
<a
href={link.href}
class="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-agro-400 hover:shadow-md"
>
<h3 class="text-base font-semibold text-slate-900 group-hover:text-agro-700">
{$t(link.titleKey)}
</h3>
<p class="mt-1 text-sm text-slate-500">{$t(link.descKey)}</p>
<p class="mt-3 text-sm font-medium text-agro-600">{$t('dashboard.viewDetails')} →</p>
</a>
{/each}
</div>
