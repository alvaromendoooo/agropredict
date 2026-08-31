<script lang="ts">
import type { Snippet } from 'svelte';

let {
title,
subtitle,
children
}: { title?: string; subtitle?: string; children: Snippet } = $props();
</script>

<section class="rounded-xl border border-slate-200 bg-white shadow-sm">
{#if title}
<header class="border-b border-slate-100 px-5 py-4">
<h2 class="text-base font-semibold text-slate-900">{title}</h2>
{#if subtitle}<p class="mt-0.5 text-sm text-slate-500">{subtitle}</p>{/if}
</header>
{/if}
<div class="p-5">{@render children()}</div>
</section>
