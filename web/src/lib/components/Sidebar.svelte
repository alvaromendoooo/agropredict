<script lang="ts">
import { page } from '$app/stores';
import { t } from '$lib/i18n';

let { open = false, onclose }: { open?: boolean; onclose?: () => void } = $props();

interface NavItem {
href: string;
labelKey: string;
icon: string;
}

interface NavSection {
titleKey: string;
items: NavItem[];
}

const sections: NavSection[] = [
{
titleKey: 'nav.sectionAnalysis',
items: [
{
href: '/heladas/observadas',
labelKey: 'nav.frostObserved',
icon: 'M12 2v20M4.5 6.5l15 11M19.5 6.5l-15 11'
},
{
href: '/heladas/futuras',
labelKey: 'nav.frostForecast',
icon: 'M6 18a4 4 0 1 1 .6-7.96A6 6 0 0 1 18 9a3.5 3.5 0 0 1 0 9H6zM10 21l-1 2m4-2l-1 2m4-2l-1 2'
},
{
href: '/plagas/calculadas',
labelKey: 'nav.pestsCalculated',
icon: 'M12 8a4 4 0 0 1 4 4v3a4 4 0 0 1-8 0v-3a4 4 0 0 1 4-4zM12 8V5M8 10L5 7m11 3l3-3M8 16l-3 3m11-3l3 3'
},
{
href: '/plagas/estimadas',
labelKey: 'nav.pestsEstimated',
icon: 'M12 8a4 4 0 0 1 4 4v3a4 4 0 0 1-8 0v-3a4 4 0 0 1 4-4zM12 8V5M8 10L5 7m11 3l3-3M8 16l-3 3m11-3l3 3'
}
]
},
{
titleKey: 'nav.sectionData',
items: [
{
href: '/datos/clima',
labelKey: 'nav.climate',
icon: 'M4 19V5m0 14h16M8 15v-4m4 4V8m4 7v-2'
},
{
href: '/datos/pronostico',
labelKey: 'nav.forecast',
icon: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4l1.4 1.4m0-14.2l-1.4 1.4M6.3 17.7l-1.4 1.4'
},
{
href: '/datos/cultivos',
labelKey: 'nav.crops',
icon: 'M5 21c8 0 14-6 14-14V4h-3C8 4 5 10 5 16v5zM5 21c0-6 3-9 8-11'
},
{
href: '/datos/parcelas',
labelKey: 'nav.parcels',
icon: 'M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14m6-12v14'
},
{
href: '/datos/sensores',
labelKey: 'nav.sensors',
icon: 'M8 8h8v8H8zM4 4h16v16H4z'
},
{
href: '/calendario-plagas',
labelKey: 'nav.pestCalendar',
icon: 'M3 6h18v15H3zM3 10h18M8 2v4M16 2v4'
}
]
}
];

const isActive = (href: string): boolean => $page.url.pathname === href;
</script>

{#if open}
<button
type="button"
aria-label="close menu"
onclick={onclose}
class="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
></button>
{/if}

<aside
class="fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:static lg:translate-x-0 {open
? 'translate-x-0'
: '-translate-x-full'}"
>
<div class="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
<img src="/favicon.svg" alt="" class="h-9 w-9" />
<div>
<p class="text-sm font-bold text-slate-900">{$t('common.appName')}</p>
<p class="text-[11px] leading-tight text-slate-400">{$t('common.tagline')}</p>
</div>
</div>

<nav class="flex-1 space-y-6 overflow-y-auto px-3 py-4">
<a
href="/"
onclick={onclose}
class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive('/')
? 'bg-agro-50 text-agro-800'
: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}"
>
<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5L12 3l9 7.5M5 9.5V21h14V9.5" /></svg>
{$t('nav.dashboard')}
</a>

{#each sections as section (section.titleKey)}
<div>
<p class="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
{$t(section.titleKey)}
</p>
<div class="space-y-0.5">
{#each section.items as item (item.href)}
<a
href={item.href}
onclick={onclose}
class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive(item.href)
? 'bg-agro-50 text-agro-800'
: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}"
>
<svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d={item.icon} /></svg>
{$t(item.labelKey)}
</a>
{/each}
</div>
</div>
{/each}
</nav>
</aside>
