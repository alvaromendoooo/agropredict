<script lang="ts">
let {
checked = $bindable(),
label,
help
}: { checked: boolean; label: string; help?: string } = $props();
</script>

<label class="flex items-start gap-3">
<input
type="checkbox"
bind:checked
class="mt-0.5 h-4 w-4 rounded border-slate-300 text-agro-600 focus:ring-agro-500/30"
/>
<span>
<span class="block text-sm font-medium text-slate-700">{label}</span>
{#if help}<span class="block text-xs text-slate-400">{help}</span>{/if}
</span>
</label>
