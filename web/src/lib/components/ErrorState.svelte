<script lang="ts">
let { message }: { message: string } = $props();
</script>

<div class="rounded-xl border border-red-200 bg-red-50 px-6 py-6 text-center">
<p class="text-sm font-medium text-red-700">{message}</p>
</div>
