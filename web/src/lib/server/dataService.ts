import { apiFetch } from './http';
import { DATA_SERVICE_URL, REQUEST_TIMEOUT_MS } from './config';

const base = DATA_SERVICE_URL;

export interface HistoricalParams {
provinceCode?: string;
estacionCode?: string;
type: string;
startDate: string;
endDate: string;
}

/** Client for the data-service REST API. */
export const dataService = {
historicalProvincias(params: HistoricalParams) {
return apiFetch({ base, path: '/climate/historical/provincias', query: { ...params } });
},

historicalEstacion(params: HistoricalParams) {
return apiFetch({ base, path: '/climate/historical/estacion', query: { ...params } });
},

retryPending() {
return apiFetch({ base, path: '/climate/historical/reintentar-pendientes', method: 'POST', body: {} });
},

localidades() {
return apiFetch({ base, path: '/climate/pronostico/localidades' });
},

forecast(zona: string, prediccion: string, q: { ccaaId?: string; provinciaId?: string }) {
return apiFetch({ base, path: `/climate/pronostico/${encodeURIComponent(zona)}/${encodeURIComponent(prediccion)}`, query: { ...q } });
},

pestCalendars(q: { grupo?: string; tipo?: string; id?: string }) {
return apiFetch({ base, path: '/climate/plagas', query: { ...q } });
},

async cropNames() {
// /crop/cultivos responde 404 cuando no hay filas propias de cultivo, por lo que los
// nombres de cultivo se derivan del catalogo de variedades (nombre_cultivo).
const raw = await apiFetch({ base, path: '/crop/variedades' });
const names = new Set<string>();
if (Array.isArray(raw)) {
for (const item of raw) {
if (item && typeof item === 'object') {
const name = (item as Record<string, unknown>)['nombre_cultivo'];
if (typeof name === 'string' && name !== '') names.add(name);
}
}
}
return [...names].sort((a, b) => a.localeCompare(b));
},

variedades(cultivo?: string) {
return apiFetch({ base, path: '/crop/variedades', query: cultivo ? { cultivo } : undefined });
},

modelos() {
return apiFetch({ base, path: '/crop/modelos' });
},

etapasFenologicas() {
return apiFetch({ base, path: '/crop/etapas_fenologicas' });
},

variedadUmbrales(nombre: string) {
return apiFetch({ base, path: `/crop/variedades/${encodeURIComponent(nombre)}/umbrales` });
},

variedadHorasFrio(nombre: string) {
return apiFetch({ base, path: `/crop/variedades/${encodeURIComponent(nombre)}/horas_frio` });
},

modeloVariedades(codigo: string) {
return apiFetch({ base, path: `/crop/modelos/${encodeURIComponent(codigo)}/variedades` });
},

cultivoPlagas(cultivos: string, plaga?: string) {
return apiFetch({ base, path: '/crop/plague', query: { cultivos, ...(plaga ? { plaga } : {}) } });
},

cultivoParcelas(cultivo: string, parcela?: string) {
return apiFetch({ base, path: '/crop/parcel', query: { cultivo, ...(parcela ? { parcela } : {}) } });
},

sensores(q: { eui: string; fecha_inicio: string; fecha_fin: string; nombre_predictor: string }) {
return apiFetch({ base, path: '/sensores', query: { ...q } });
},

metadatos(tipo: string) {
return apiFetch({ base, path: `/metadatos/${encodeURIComponent(tipo)}`, timeoutMs: REQUEST_TIMEOUT_MS });
}
};
