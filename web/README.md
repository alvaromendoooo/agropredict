# 🖥️ Agro-Predict — Web UI

SvelteKit front-end for the Agro-Predict platform. It talks to the microservices through a
**BFF (backend-for-frontend) layer**: the browser only ever talks to SvelteKit, and the server
side proxies/normalizes every call to `data-service` and `predictors`.

- **SvelteKit 2 · Svelte 5 (runes) · TypeScript · Tailwind CSS 4 · adapter-node**
- **Bilingual** (English 🇬🇧 / Spanish 🇪🇸), switcher in the top bar (cookie `agro_locale`)
- Charts via Chart.js, unit tests with Vitest

## 🧭 Pages

| Route | Content | Backend endpoints used |
|---|---|---|
| `/` | Dashboard: crops/varieties/sensors counters + frost-tomorrow snapshot (province CC) | `/crop/variedades`, `/metadatos/sensores`, `POST /heladas/futuras/{zona}` |
| `/heladas/observadas` | Observed frost analysis (hour/day/week; province or station; variety evaluation) + PDF | `POST /heladas/observadas/{tipo}` |
| `/heladas/futuras` | Next-day frost risk from AEMET (variety/locality evaluation) + PDF | `POST /heladas/futuras/{zona}` |
| `/plagas/calculadas` | Calendar-based pest risk per crop + PDF | `POST /plagas/calculadas?cultivo=` |
| `/plagas/estimadas` | Weather/sensor-based daily pest risk timeline + PDF | `POST /plagas/estimadas` |
| `/datos/clima` | Historical weather explorer with charts (+ retry pending ingestions) | `GET /climate/historical/{provincias,estacion}`, `POST /climate/historical/reintentar-pendientes` |
| `/datos/pronostico` | Raw AEMET forecast viewer | `GET /climate/pronostico/{zona}/{prediccion}` |
| `/datos/cultivos` | Crops, varieties, phenological thresholds, chill-hour models | `GET /crop/*` |
| `/datos/parcelas` | Parcels/devices/sensors metadata (tabs) | `GET /metadatos/{tipo}` |
| `/datos/sensores` | Stored sensor measurements (chart + table) | `GET /sensores` |
| `/calendario-plagas` | Weekly pest alert heat-strips | `GET /climate/plagas` |
| `/reports` | GET endpoint that streams the **signed PDF reports** | `POST …?format=pdf` on the predictors |

## ⚙️ Environment variables

| Variable | Default (dev) | Docker value |
|---|---|---|
| `DATA_SERVICE_URL` | `http://localhost:9002` | `http://data-service:5000` |
| `PREDICTOR_URL` | `http://localhost:10000` | `http://predictors:10000` |
| `REQUEST_TIMEOUT_MS` | `45000` | — |
| `ORIGIN` | — | `http://localhost:3000` (**must** match the public URL: SvelteKit CSRF checks it) |
| `PORT` | `3000` | `3000` |

## 🚀 Development

```bash
cd web
npm install
npm run dev        # http://localhost:5173
```

## 🏗️ Production build

```bash
npm run build      # adapter-node -> build/
npm start          # node build (respects PORT / ORIGIN)
```

The compose file builds this folder as the `web` service (port 3000).

## 🧪 Quality

```bash
npm test           # Vitest unit tests (utils, i18n)
npm run check      # svelte-check (0 errors expected)
npm run build      # production build must pass
```

## 🧱 How the BFF works (important)

- Pages define **named form actions** in `+page.server.ts`; the client helper
  `callAction()` (`src/lib/client.ts`) posts a form-encoded `payload` field
  (SvelteKit actions reject JSON bodies) and transparently **re-polls while the backend
  reports `PENDING`/`LOADING`** — the UI shows a *collecting data…* banner.
- Action results come back wrapped in Kit's devalue envelope
  (`{ type, status, data }`); `callAction` parses it with **devalue** and normalizes
  errors (`fail(status, { message })`) into `{ ok: false, status, message }`.
- Actions returning `503/504` are treated as *still processing* (pending) instead of
  hard errors, because the platform ingests data on demand.
- PDF reports are **not** form actions: `GET /reports?kind=…&payload=…` streams the
  binary (`application/pdf`) directly to the browser.
- `ORIGIN` env must equal the URL users browse (e.g. `http://localhost:3000`),
  otherwise SvelteKit rejects form posts with 403.

## 📁 Structure

```
web/src/
├── app.html · app.css (Tailwind theme: agro palette) · app.d.ts
├── lib/
│   ├── i18n/{index.ts, en.ts, es.ts}     # typed dictionaries + t() store
│   ├── server/{config,http,dataService,predictor,helpers}.ts   # BFF clients
│   ├── client.ts                          # callAction() + envelope parsing
│   ├── components/                        # design-system components
│   ├── stores/toast.ts · utils/{risk,format}.ts
└── routes/                                # one folder per page (+page.server.ts actions)
    ├── heladas/{observadas,futuras} · plagas/{calculadas,estimadas}
    ├── datos/{clima,pronostico,cultivos,parcelas,sensores}
    ├── calendario-plagas · reports/+server.ts (PDF streaming)
    └── +layout.svelte (sidebar/topbar/i18n) · +page.svelte (dashboard)
```

## ➕ Adding things

- **New page**: create the route folder, actions in `+page.server.ts` (use
  `readActionPayload`, `isPending`, `errorOutcome` from `$lib/server/helpers`),
  view with the shared components, and add nav + i18n keys (`en.ts` + `es.ts`).
- **New language**: add a dictionary file and register it in `lib/i18n/index.ts`.
- **New strings**: always both dictionaries; use `{param}` interpolation when needed.
