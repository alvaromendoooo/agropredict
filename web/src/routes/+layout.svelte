<script lang="ts">
import '../app.css';
import Sidebar from '$lib/components/Sidebar.svelte';
import Topbar from '$lib/components/Topbar.svelte';
import Toaster from '$lib/components/Toaster.svelte';
import { setLocale, t, type Locale } from '$lib/i18n';

let { data, children } = $props();

setLocale(data.locale as Locale);

let sidebarOpen = $state(false);
</script>

<svelte:head>
<title>Agro-Predict</title>
</svelte:head>

<div class="min-h-screen lg:flex">
<Sidebar open={sidebarOpen} onclose={() => (sidebarOpen = false)} />

<div class="flex min-w-0 flex-1 flex-col">
<Topbar onmenu={() => (sidebarOpen = true)} />

<main class="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
{@render children()}
</main>

<footer class="px-6 py-4 text-center text-xs text-slate-400">
{$t('common.appName')} · {$t('common.footer')}
</footer>
</div>
</div>

<Toaster />
