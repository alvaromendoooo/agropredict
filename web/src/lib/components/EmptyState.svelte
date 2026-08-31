<script lang="ts">
let { message }: { message: string } = $props();
</script>

<div class="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
<p class="text-sm text-slate-500">{message}</p>
</div>
