<script lang="ts">
let { label, value, hint }: { label: string; value: string; hint?: string } = $props();
</script>

<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
<p class="text-sm font-medium text-slate-500">{label}</p>
<p class="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
{#if hint}<p class="mt-1 text-xs text-slate-400">{hint}</p>{/if}
</div>
