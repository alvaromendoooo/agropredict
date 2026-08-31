<script lang="ts">
import { formatValue } from '$lib/utils/format';

interface Item {
label: string;
value: unknown;
}

let { items, columns = 2 }: { items: Item[]; columns?: 2 | 3 } = $props();

const visible = $derived(
items.filter(
(item) => item.value !== undefined && item.value !== null && item.value !== ''
)
);
</script>

{#if visible.length > 0}
<dl class="grid gap-4 {columns === 3 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'}">
{#each visible as item (item.label)}
<div class="rounded-lg border border-slate-100 bg-slate-50/60 px-4 py-3">
<dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{item.label}</dt>
<dd class="mt-1 break-words text-sm font-medium text-slate-800">
{formatValue(item.value)}
</dd>
</div>
{/each}
</dl>
{/if}
