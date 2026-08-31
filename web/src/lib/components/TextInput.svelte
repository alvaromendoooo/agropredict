<script lang="ts">
let {
value = $bindable(),
type = 'text',
placeholder = '',
list
}: { value: string; type?: string; placeholder?: string; list?: string } = $props();
</script>

<input
{type}
{placeholder}
{list}
bind:value
class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-agro-500 focus:outline-none focus:ring-2 focus:ring-agro-500/30"
/>
