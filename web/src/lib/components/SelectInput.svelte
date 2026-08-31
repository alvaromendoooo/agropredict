<script lang="ts">
interface Option {
value: string;
label: string;
}

let {
value = $bindable(),
options,
placeholder
}: { value: string; options: Option[]; placeholder?: string } = $props();
</script>

<select
bind:value
class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-agro-500 focus:outline-none focus:ring-2 focus:ring-agro-500/30"
>
{#if placeholder}<option value="" disabled>{placeholder}</option>{/if}
{#each options as option (option.value)}
<option value={option.value}>{option.label}</option>
{/each}
</select>
