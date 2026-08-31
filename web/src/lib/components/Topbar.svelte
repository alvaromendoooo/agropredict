<script lang="ts">
import LangSwitcher from './LangSwitcher.svelte';

let { onmenu }: { onmenu?: () => void } = $props();
</script>

<header class="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur sm:px-6">
<button
type="button"
onclick={onmenu}
class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
aria-label="menu"
>
<svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
</button>
<div class="flex-1"></div>
<LangSwitcher />
</header>
