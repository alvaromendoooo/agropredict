<script lang="ts">
import { formatValue, prettyKey, rowKeys } from '$lib/utils/format';

let { rows, max = 8 }: { rows: Record<string, unknown>[]; max?: number } = $props();

const keys = $derived(rows.length > 0 ? rowKeys(rows, max) : []);
</script>

{#if rows.length === 0}
<p class="py-6 text-center text-sm text-slate-400">—</p>
{:else}
<div class="max-h-96 overflow-auto rounded-lg border border-slate-200">
<table class="min-w-full divide-y divide-slate-200 text-sm">
<thead class="sticky top-0 bg-slate-50">
<tr>
{#each keys as key (key)}
<th class="whitespace-nowrap px-3 py-2 text-left font-semibold text-slate-600">
{prettyKey(key)}
</th>
{/each}
</tr>
</thead>
<tbody class="divide-y divide-slate-100 bg-white">
{#each rows as row, i (i)}
<tr class="hover:bg-slate-50">
{#each keys as key (key)}
<td class="whitespace-nowrap px-3 py-2 text-slate-700">
{formatValue(row[key])}
</td>
{/each}
</tr>
{/each}
</tbody>
</table>
</div>
{/if}
