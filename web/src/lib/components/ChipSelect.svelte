<script lang="ts">
let {
options,
selected = $bindable(),
placeholder
}: { options: string[]; selected: string[]; placeholder?: string } = $props();

function toggle(option: string): void {
selected = selected.includes(option)
? selected.filter((s) => s !== option)
: [...selected, option];
}
</script>

{#if options.length === 0}
<p class="text-xs text-slate-400">{placeholder}</p>
{:else}
<div class="flex flex-wrap gap-2">
{#each options as option (option)}
<button
type="button"
onclick={() => toggle(option)}
class="rounded-full border px-3 py-1 text-xs font-medium transition {selected.includes(option)
? 'border-agro-600 bg-agro-600 text-white'
: 'border-slate-300 bg-white text-slate-600 hover:border-agro-400'}"
>
{option}
</button>
{/each}
</div>
{/if}
