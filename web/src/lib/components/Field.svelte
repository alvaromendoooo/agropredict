<script lang="ts">
import type { Snippet } from 'svelte';

let { label, help, children }: { label: string; help?: string; children: Snippet } = $props();
</script>

<label class="block">
<span class="mb-1 block text-sm font-medium text-slate-700">{label}</span>
{@render children()}
{#if help}<span class="mt-1 block text-xs text-slate-400">{help}</span>{/if}
</label>
