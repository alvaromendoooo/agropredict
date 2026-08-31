<script lang="ts">
import { toasts, dismissToast } from '$lib/stores/toast';

const styles: Record<string, string> = {
success: 'border-green-200 bg-green-50 text-green-800',
error: 'border-red-200 bg-red-50 text-red-800',
info: 'border-sky-200 bg-sky-50 text-sky-800'
};
</script>

<div class="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
{#each $toasts as item (item.id)}
<div class="pointer-events-auto flex items-start gap-2 rounded-lg border p-3 text-sm shadow-lg {styles[item.kind]}">
<span class="flex-1">{item.message}</span>
<button type="button" onclick={() => dismissToast(item.id)} class="text-xs opacity-60 hover:opacity-100">x</button>
</div>
{/each}
</div>
