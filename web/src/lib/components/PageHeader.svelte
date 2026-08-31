<script lang="ts">
let { title, subtitle }: { title: string; subtitle?: string } = $props();
</script>

<header class="mb-6">
<h1 class="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
{#if subtitle}<p class="mt-1 max-w-3xl text-sm text-slate-500">{subtitle}</p>{/if}
</header>
