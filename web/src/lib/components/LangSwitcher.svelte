<script lang="ts">
import { locale, locales, setLocale } from '$lib/i18n';
</script>

<div class="flex items-center rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-semibold">
{#each locales as l (l)}
<button
type="button"
onclick={() => setLocale(l)}
class="rounded-md px-2.5 py-1 uppercase transition-colors {$locale === l
? 'bg-agro-600 text-white'
: 'text-slate-500 hover:text-slate-800'}"
>
{l}
</button>
{/each}
</div>
