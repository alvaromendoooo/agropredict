import { apiFetch, fetchPdf } from './http';
import { PREDICTOR_URL, REQUEST_TIMEOUT_MS } from './config';

const base = PREDICTOR_URL;

/** Client for the climate risks predictor REST API. */
export const predictor = {
heladasObservadas(tipo: string, body: Record<string, unknown>) {
return apiFetch({
base,
path: `/heladas/observadas/${encodeURIComponent(tipo)}`,
method: 'POST',
body,
timeoutMs: REQUEST_TIMEOUT_MS
});
},

heladasObservadasPdf(tipo: string, body: Record<string, unknown>, filename: string) {
return fetchPdf({
base,
path: `/heladas/observadas/${encodeURIComponent(tipo)}`,
method: 'POST',
body,
query: { format: 'pdf' },
fallbackName: filename
});
},

heladasFuturas(zona: string, body: Record<string, unknown>) {
return apiFetch({
base,
path: `/heladas/futuras/${encodeURIComponent(zona)}`,
method: 'POST',
body,
timeoutMs: REQUEST_TIMEOUT_MS
});
},

heladasFuturasPdf(zona: string, body: Record<string, unknown>, filename: string) {
return fetchPdf({
base,
path: `/heladas/futuras/${encodeURIComponent(zona)}`,
method: 'POST',
body,
query: { format: 'pdf' },
fallbackName: filename
});
},

plagasCalculadas(cultivo: string) {
return apiFetch({
base,
path: '/plagas/calculadas',
method: 'POST',
query: { cultivo },
body: {},
timeoutMs: REQUEST_TIMEOUT_MS
});
},

plagasCalculadasPdf(cultivo: string, filename: string) {
return fetchPdf({
base,
path: '/plagas/calculadas',
method: 'POST',
query: { cultivo, format: 'pdf' },
body: {},
fallbackName: filename
});
},

plagasEstimadas(body: Record<string, unknown>) {
return apiFetch({
base,
path: '/plagas/estimadas',
method: 'POST',
body,
timeoutMs: REQUEST_TIMEOUT_MS
});
},

plagasEstimadasPdf(body: Record<string, unknown>, filename: string) {
return fetchPdf({
base,
path: '/plagas/estimadas',
method: 'POST',
query: { format: 'pdf' },
body,
fallbackName: filename
});
}
};
