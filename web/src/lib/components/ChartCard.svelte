<script lang="ts">
import Chart from 'chart.js/auto';
import { CHART_COLORS } from '$lib/utils/risk';

interface Dataset {
label: string;
data: (number | null)[];
color?: string;
type?: 'line' | 'bar';
}

let {
title,
labels,
datasets,
height = 260,
yBeginAtZero = false
}: {
title?: string;
labels: (string | number)[];
datasets: Dataset[];
height?: number;
yBeginAtZero?: boolean;
} = $props();

let canvas: HTMLCanvasElement | undefined = $state();
let chart: Chart | undefined;

$effect(() => {
if (!canvas || labels.length === 0) return;

chart?.destroy();
chart = new Chart(canvas, {
type: 'line',
data: {
labels: [...labels],
datasets: datasets.map((dataset, i) => ({
label: dataset.label,
data: [...dataset.data],
type: dataset.type,
borderColor: dataset.color ?? CHART_COLORS[i % CHART_COLORS.length],
backgroundColor: (dataset.color ?? CHART_COLORS[i % CHART_COLORS.length]) + '33',
fill: false,
tension: 0.3,
spanGaps: true,
pointRadius: labels.length > 60 ? 0 : 2
}))
},
options: {
responsive: true,
maintainAspectRatio: false,
interaction: { mode: 'index', intersect: false },
plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } },
scales: { y: { beginAtZero: yBeginAtZero } }
}
});

return () => {
chart?.destroy();
chart = undefined;
};
});
</script>

<div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
{#if title}<h3 class="mb-3 text-sm font-semibold text-slate-700">{title}</h3>{/if}
{#if labels.length > 0}
<div style="height: {height}px"><canvas bind:this={canvas}></canvas></div>
{:else}
<p class="py-10 text-center text-sm text-slate-400">—</p>
{/if}
</div>
