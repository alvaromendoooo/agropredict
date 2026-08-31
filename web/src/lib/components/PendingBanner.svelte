<script lang="ts">
import { t } from '$lib/i18n';

let {
visible,
attempts = 0,
labelKey,
descKey
}: { visible: boolean; attempts?: number; labelKey: string; descKey: string } = $props();
</script>

{#if visible}
<div class="mb-4 overflow-hidden rounded-xl border border-amber-200 bg-amber-50">
<div class="h-1 w-full animate-pulse bg-gradient-to-r from-amber-300 via-amber-500 to-amber-300"></div>
<div class="px-4 py-3">
<p class="text-sm font-semibold text-amber-900">{$t(labelKey, { n: attempts })}</p>
<p class="mt-0.5 text-xs text-amber-700">{$t(descKey)}</p>
</div>
</div>
{/if}
