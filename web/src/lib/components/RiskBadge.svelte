<script lang="ts">
import { riskBadgeClass } from '$lib/utils/risk';

let { label, size = 'md' }: { label: unknown; size?: 'sm' | 'md' } = $props();
</script>

<span
class="inline-flex items-center gap-1.5 rounded-full font-semibold ring-1 ring-inset {riskBadgeClass(label)} {size === 'sm'
? 'px-2 py-0.5 text-xs'
: 'px-3 py-1 text-sm'}"
>
{String(label ?? '—')}
</span>
