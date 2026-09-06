<script lang="ts">
import PageHeader from '$lib/components/PageHeader.svelte';
import Panel from '$lib/components/Panel.svelte';
import Field from '$lib/components/Field.svelte';
import TextInput from '$lib/components/TextInput.svelte';
import DataTable from '$lib/components/DataTable.svelte';
import ErrorState from '$lib/components/ErrorState.svelte';
import EmptyState from '$lib/components/EmptyState.svelte';
import { callAction } from '$lib/client';
import { collectRows, isPlainObject } from '$lib/utils/format';
import { alertLevelColor } from '$lib/utils/risk';
import { t } from '$lib/i18n';

let grupo = $state('');
let tipo = $state('');

let loading = $state(false);
let result = $state<unknown>(null);
let errorMessage = $state('');

interface CalendarEntry {
nombre: string;
tipo: string;
weeks: Array<{ week: number; level: unknown }>;
}

function extract(value: unknown): CalendarEntry[] {
const raw = Array.isArray(value) ? value : [value];
const byId = new Map<string, CalendarEntry>();
for (const item of raw) {
if (!isPlainObject(item)) continue;
const publicId = String(item['public_id'] ?? '');
if (publicId === '') continue;
let entry = byId.get(publicId);
if (!entry) {
entry = { nombre: String(item['nombre'] ?? publicId), tipo: String(item['tipo'] ?? ''), weeks: [] };
byId.set(publicId, entry);
}
const calendar = item['calendario'];
if (Array.isArray(calendar) && calendar.length > 0 && entry.weeks.length === 0) {
entry.weeks = calendar
.filter(isPlainObject)
 .map((weekRow) => ({ week: Number(weekRow['semana'] ?? 0), level: weekRow['nivel_alerta'] }))
.filter((week) => week.week > 0)
.sort((a, b) => a.week - b.week);
}
}
return [...byId.values()];
}

const entries = $derived(result === null ? [] : extract(result));
const fallbackRows = $derived(
entries.length === 0 && result !== null ? collectRows(result) : []
);

async function query(): Promise<void> {
loading = true;
errorMessage = '';

const outcome = await callAction<unknown>('query', { grupo, tipo });
loading = false;
if (!outcome.ok) {
errorMessage = outcome.message;
return;
}
if (outcome.pending) return;
result = outcome.result;
}
</script>

<PageHeader title={$t('pestCalendar.title')} subtitle={$t('pestCalendar.subtitle')} />

<div class="grid items-start gap-6 lg:grid-cols-[380px_1fr]">
<Panel title={$t('pestCalendar.filter')}>
<form
class="space-y-4"
onsubmit={(event) => {
event.preventDefault();
query();
}}
>
<Field label={$t('pestCalendar.group')} help={$t('pestCalendar.requiredHint')}>
<TextInput bind:value={grupo} placeholder={$t('pestCalendar.groupPlaceholder')} list="pest-groups" />
</Field>
<datalist id="pest-groups">
{#each ['cereales', 'arbol_frutal', 'hortaliza_fruto'] as group (group)}<option value={group}></option>{/each}
</datalist>
<Field label={$t('pestCalendar.type')}>
<TextInput bind:value={tipo} placeholder={$t('pestCalendar.typePlaceholder')} list="pest-types" />
</Field>
<datalist id="pest-types">
{#each ['plaga', 'enfermedad', 'hongo', 'insecto', 'bacteria', 'acaro', 'oomiceto', 'nematodo'] as pestType (pestType)}<option value={pestType}></option>{/each}
</datalist>

<button type="submit" disabled={loading || grupo.trim() === '' || tipo.trim() === ''} class="w-full rounded-lg bg-agro-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60">
{loading ? $t('common.loading') : $t('pestCalendar.filter')}
</button>
</form>
</Panel>

<div class="space-y-6">
{#if errorMessage}<ErrorState message={errorMessage} />{/if}

{#if result !== null}
{#if entries.length === 0 && fallbackRows.length === 0}
<EmptyState message={$t('common.noData')} />
{:else if entries.length > 0}
<div class="space-y-4">
{#each entries as entry, index (index)}
<article class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
<div class="flex flex-wrap items-center gap-2">
<h3 class="text-sm font-bold text-slate-900">{entry.nombre}</h3>
{#if entry.tipo}<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">{entry.tipo}</span>{/if}
</div>

<p class="mb-2 mt-3 text-xs font-semibold uppercase tracking-wide text-slate-400">{$t('pestCalendar.calendar')}</p>
<div class="flex flex-wrap gap-1">
{#each entry.weeks as week (week.week)}
<span
class="flex h-7 w-7 items-center justify-center rounded text-[10px] font-bold text-slate-900/70 {alertLevelColor(week.level)}"
title="{$t('pestCalendar.week')} {week.week}: {$t('pestCalendar.alertLevel')} {String(week.level ?? '—')}"
>
{week.week}
</span>
{/each}
</div>
</article>
{/each}
</div>
{:else}
<DataTable rows={fallbackRows} />
{/if}
{/if}
</div>
</div>
