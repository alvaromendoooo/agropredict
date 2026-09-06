import { parse } from 'devalue';

const BASE = 'http://localhost:3000';
const ORIGIN = BASE;

async function call(path, action, payload, { pollMax = 25, delay = 2500 } = {}) {
for (let attempt = 0; ; attempt++) {
const res = await fetch(`${BASE}${path}?/${action}`, {
method: 'POST',
headers: {
'content-type': 'application/x-www-form-urlencoded',
origin: ORIGIN
},
body: new URLSearchParams({ payload: JSON.stringify(payload ?? {}) })
});
const body = await res.json();
if (body.type === 'failure') {
const val = JSON.parse(body.data || '[]')?.[0];
return { status: body.status ?? res.status, ok: false, message: val?.message };
}
const value = parse(body.data);
if (value?.__pending) {
if (attempt >= pollMax) return { status: 200, ok: true, pending: true };
await new Promise((r) => setTimeout(r, delay));
continue;
}
return { status: res.status, ok: true, result: value?.result !== undefined ? value.result : value };
}
}

const out = [];
const log = (name, value) => out.push(`${name}: ${value}`);

const home = await fetch(`${BASE}/`);
log('HOME', home.status);

const maiz = await call('/plagas/calculadas', 'predict', { cultivo: 'Maiz' });
log('CALC-MAIZ', maiz.ok && maiz.result ? `entries=${maiz.result.length} risks=${maiz.result[0].plagas.slice(0, 3).map((p) => p.nivel_riesgo).join('/')}` : JSON.stringify(maiz).slice(0, 140));

const tomate = await call('/plagas/calculadas', 'predict', { cultivo: 'Tomate' });
log('CALC-TOMATE', tomate.ok && tomate.result ? `entries=${tomate.result.length} risks=${tomate.result[0].plagas.slice(0, 2).map((p) => p.nivel_riesgo).join('/')}` : JSON.stringify(tomate).slice(0, 140));

const cal = await call('/calendario-plagas', 'query', { grupo: 'cereales', tipo: 'plaga' });
log('CALENDAR', cal.ok && cal.result ? `rows=${Array.isArray(cal.result) ? cal.result.length : 'obj'}` : JSON.stringify(cal).slice(0, 140));

const clima = await call('/datos/clima', 'query', { source: 'provincia', code: 'CC', type: 'DIA', startDate: '2026-08-01', endDate: '2026-08-31' }, { pollMax: 30 });
const climaRows = clima.ok && clima.result && Array.isArray(clima.result.datos) ? clima.result.datos.length : (clima.pending ? 'PENDING-TIMEOUT' : JSON.stringify(clima).slice(0, 120));
log('CLIMA', `ok=${clima.ok} rows=${climaRows}`);

const sen = await call('/datos/sensores', 'query', { eui: 'a840419a0188cc08', nombre_predictor: 'temperatura_max', fecha_inicio: '2025-06-09', fecha_fin: '2025-07-21' });
const senRes = sen.ok ? sen.result : null;
log('SENSORES', sen.ok ? `shape=${Array.isArray(senRes) ? 'list' : typeof senRes} keys=${senRes && typeof senRes === 'object' ? Object.keys(senRes).slice(0, 4).join(',') : ''}` : JSON.stringify(sen).slice(0, 140));

const obs = await call('/heladas/observadas', 'predict', { tipo: 'Dia', source: 'provincia', code: 'CC', evaluacion: false, variedades: [] }, { pollMax: 30 });
log('OBSERVADAS', obs.ok && obs.result ? `keys=${Object.keys(obs.result).slice(0, 6).join(',')}` : JSON.stringify(obs).slice(0, 160));

const fut = await call('/heladas/futuras', 'predict', { zona: 'provincial', code: 'CC', evaluacion_var: false, evaluacion_loc: false, variedades: [], localidades: [] }, { pollMax: 30 });
log('FUTURAS', fut.ok && fut.result ? `keys=${Object.keys(fut.result).slice(0, 6).join(',')}` : JSON.stringify(fut).slice(0, 160));

const pdfRes = await fetch(`${BASE}/reports?kind=plagas-calculadas&filename=test.pdf&payload=${encodeURIComponent(JSON.stringify({ cultivo: 'Maiz' }))}`, { headers: { origin: ORIGIN, accept: 'application/pdf' } });
log('PDF', `${pdfRes.status} ${pdfRes.headers.get('content-type')}`);

console.log(out.join('\n'));
