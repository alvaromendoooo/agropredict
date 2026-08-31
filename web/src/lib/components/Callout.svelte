<script lang="ts">
let {
title,
message,
tone = 'info'
}: { title?: string; message: string; tone?: 'info' | 'warning' } = $props();
</script>

<div
class="rounded-xl border p-4 {tone === 'warning'
? 'border-amber-200 bg-amber-50 text-amber-900'
: 'border-sky-200 bg-sky-50 text-sky-900'}"
>
{#if title}<p class="text-sm font-semibold">{title}</p>{/if}
<p class="text-sm">{message}</p>
</div>
