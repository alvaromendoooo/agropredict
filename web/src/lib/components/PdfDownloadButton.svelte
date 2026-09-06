<script lang="ts">
import { t } from '$lib/i18n';
import { toast } from '$lib/stores/toast';

let {
kind,
payload,
filename,
disabled = false
}: {
kind: string;
payload: () => unknown;
filename: string;
disabled?: boolean;
} = $props();

let busy = $state(false);

async function download(): Promise<void> {
if (busy || disabled) return;
busy = true;
try {
const query = new URLSearchParams({
kind,
filename,
payload: JSON.stringify(payload() ?? {})
});
const response = await fetch(`/reports?${query.toString()}`, { headers: { accept: 'application/pdf' } });

const contentType = response.headers.get('content-type') ?? '';
if (contentType.includes('application/pdf')) {
const blob = await response.blob();
const url = URL.createObjectURL(blob);
const anchor = document.createElement('a');
anchor.href = url;
anchor.download = filename;
anchor.click();
URL.revokeObjectURL(url);
toast('success', $t('toast.pdfReady'));
} else {
toast('info', $t('toast.pdfUnavailable'));
}
} catch {
toast('error', $t('toast.pdfError'));
} finally {
busy = false;
}
}
</script>

<button
type="button"
onclick={download}
disabled={disabled || busy}
class="inline-flex items-center gap-2 rounded-lg bg-agro-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-agro-700 disabled:cursor-not-allowed disabled:opacity-60"
>
{#if busy}
<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
</svg>
{$t('common.loading')}
{:else}
<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" />
</svg>
{$t('common.downloadPdf')}
{/if}
</button>
