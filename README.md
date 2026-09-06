# 🌾 Agro-Predict

**Agro-Predict** is a microservices platform that provides **climate risk prediction for agriculture**: it forecasts **frost risk** (observed historical data + next-day AEMET forecasts) and **pest/disease risk** (ITACyL calendar-based + weather/sensor-based evaluation), and produces **digitally signed PDF reports**.

A **web UI** (SvelteKit) is included in `web/` so the whole platform can be used from the browser.

---

## 🏗️ Architecture

```
                                ┌────────────────┐
                                │   web (UI)     │  SvelteKit · http://localhost:3000
                                └───────┬────────┘
                                        │ REST (BFF proxy)
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
      ┌────────────────────┐                        ┌────────────────────┐
      │   data-service     │                        │ climate_risk_pred  │
      │ Flask · :9002      │                        │ Flask · :10000     │
      │ persistence + API  │                        │ frost/pest models  │
      └──┬───────┬───────┬─┘                        └─────────┬──────────┘
         │       │       │                                    │
         ▼       ▼       ▼                                    │
   ┌────────┐ ┌──────┐ ┌────────┐   ┌───────────────┐         │
   │ AEMET  │ │ SiAR │ │ ITACyL │   │  MCP-IA +     │◄────────┘
   │ Elixir │ │Java  │ │ Java   │   │  Ollama (qwen)│  async (RabbitMQ)
   └────────┘ └──────┘ └────────┘   └───────────────┘

   Infra: MariaDB (:3307) · Redis (:6379) · RabbitMQ (:5672) · Keycloak (:8443)
```

| Service | Tech | Port | Role |
|---|---|---|---|
| `web` | SvelteKit 2 · Svelte 5 · Tailwind 4 | 3000 | Web UI (BFF proxy to the APIs) |
| `data-service` | Flask · SQLAlchemy · Celery · Alembic | 9002 → 5000 | Central persistence + REST API |
| `predictors` (climate_risk_pred) | Flask | 10000 | Frost & pest risk prediction + PDF reports |
| `aemet-service` | Elixir/Phoenix | 4000 | AEMET forecast ingestion |
| `siar-service` | Java/Spring | 8086 | SiAR historical weather |
| `itacyl-service` | Java/Spring | 8087 | ITACyL pest calendars |
| `ia-service` + `mcp-server` + `ollama` | Python · FastMCP · qwen2.5 | 8088 / 9001 / 11434 | AI structuring of raw AEMET text |
| `worker` | Celery | — | Async ingestion retries |
| `keycloak` | Keycloak 26 | 8443 | Authentication (prepared, not enforced yet) |

## 📁 Repository layout

```
├── web/                        # SvelteKit web UI (this repo's front-end)
├── services/
│   ├── data-service/           # Central data API
│   ├── external-services/      # aemet-service · siar-service · itacyl-service
│   └── ia-service/             # MCP-IA server + Ollama worker
├── predictors/
│   └── climate_risk_pred/      # Frost & pest risk predictor + signed PDF reports
├── infra/
│   ├── local/docker/           # docker-compose for local runs (+ .env at repo root)
│   └── prod/                   # Terraform (Azure) deployment
├── doc/                        # Project documentation
└── .env                        # All environment variables (never commit it)
```

## 🚀 Run it locally

**Prerequisites**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) and Git. No local Python/Node needed for the full stack.

1. **Clone and configure**

   ```bash
   git clone https://github.com/alvaromendoooo/agropredict.git
   cd agropredict
   ```

   Create a `.env` file at the repository root (the compose file reads it). Required variables:

   ```ini
   # Databases / infra
   MYSQL_ROOT_PASSWORD=...  MYSQL_DATABASE=tfg  MYSQL_USER=...  MYSQL_PASSWORD=...
   SQLALCHEMY_DATABASE_URL=mysql+pymysql://USER:PASS@mariadb:3306/tfg
   REDIS_PASS=...

   # External providers
   AEMET_API_KEY=...       AEMET_BASE_URL=https://opendata.aemet.es/opendata/api
   SIAR_API_KEY=...
   ITACYL_API_KEY=...

   # Service URLs (inside the docker network)
   SIAR_SERVICE_DATA_URL=http://siar-service:8086/riego/siar/v1/Datos
   SIAR_SERVICE_INFO_URL=http://siar-service:8086/riego/siar/v1/Info
   AEMET_SERVICE_CURRENT_URL=http://aemet-service:4000/api/prediccion/actual
   AEMET_SERVICE_FUTURE_URL=http://aemet-service:4000/api/prediccion/futura
   ITACYL_SERVICE_BASE_URL=http://itacyl-service:8087/plagas/itacyl/v1/Datos
   DATA_SERVICE_HISTORIC_BASE_URL=http://data-service:5000/climate/historical
   DATA_SERVICE_FORECAST_BASE_URL=http://data-service:5000/climate/pronostico
   DATA_SERVICE_CROP_BASE_URL=http://data-service:5000/crop
   DATA_SERVICE_PLAGAS_URL=http://data-service:5000/climate/plagas
   DATA_SERVICE_SENSORES_BASE_URL=http://data-service:5000/sensores
   DATA_SERVICE_CULTIVOS_BASE_URL=http://data-service:5000/crop/cultivos
   DATA_SERVICE_URL=http://data-service:5000
   PREDICTOR_URL=http://predictors:10000

   # AI structuring
   MCP_SERVER_URL=http://mcp-server:9001/mcp
   OLLAMA_HOST=http://ollama:11434  OLLAMA_MODEL=qwen2.5:7b  OLLAMA_NUM_PREDICT=1024
   RABBITMQ_CONNECTION=amqp://USER:PASS@rabbitmq:5672/  RABBITMQ_HOST=rabbitmq
   QUEUE_IN_NAME=aemet.raw  QUEUE_OUT_NAME=aemet.processed  RABBITMQ_USER=...  RABBITMQ_PASS=...

   # Keycloak
   KEYCLOAK_USER=...  KEYCLOAK_PASSWORD=...  KEYCLOAK_URL=localhost  KEYCLOAK_PORT=8443
   KEYCLOAK_STRICT=false  POSTGRES_USER=...  POSTGRES_PASSWORD=...
   ```

2. **Start the whole stack**

   ```bash
   docker compose --env-file .env -f infra/local/docker/compose.yml up -d --build
   ```

3. **Open the UI** → [http://localhost:3000](http://localhost:3000)

   > ⚠️ **First run**: the platform ingests data on demand from AEMET/SiAR/ITACyL. The **first** prediction or historical query of a date range can take **several minutes** (the UI shows a *collecting data…* banner and retries automatically). Later queries of the same range are instant.

### Run only the web UI in development

```bash
cd web
echo "DATA_SERVICE_URL=http://localhost:9002" > .env
echo "PREDICTOR_URL=http://localhost:10000" >> .env
npm install
npm run dev
```

Quality gates: `npm run build` · `npm run check` · `npm test`.

### Run the Python services' tests

```bash
cd services/data-service && python -m pytest app/tests -q
cd predictors/climate_risk_pred && python -m pytest app/tests -q
```

## 🖱️ User manual (web UI)

| Page | What you do there |
|---|---|
| **Dashboard** | Platform overview: registered crops/varieties/sensors and whether frost is expected tomorrow (province CC by default). |
| **Frost risk (observed)** | Pick granularity (hourly/daily/weekly), a province or weather station, optionally evaluate crop varieties → summary, white/black frost events, per-variety assessment, **signed PDF**. |
| **Frost risk (forecast)** | Tomorrow's frost risk from AEMET: sky state, temperature trends, precipitation, snow level, wind gusts, per-locality temperatures, variety stress → **signed PDF**. |
| **Pest risk (calendar)** | Type a crop with ITACyL calendars (e.g. `Maiz`, `Trigo`) → per-pest weekly alert level, causal agent, critical moment, more-info links → **signed PDF**. |
| **Pest risk (weather)** | Crop + pest + date range (sensors optional under *Advanced*) → day-by-day risk timeline with met/pending conditions → **signed PDF**. |
| **Climate history** | Historical weather explorer by province/station with charts and tables. |
| **Weather forecast** | Raw AEMET predictions by zone (national/provincial/community, current/tomorrow). |
| **Crops & varieties** | Catalogue with temperature thresholds per phenological stage and chill-hour models. |
| **Parcels & devices / Sensor measurements** | Metadata browsing and stored sensor measurements (see note below). |
| **Pest calendars** | Weekly alert heat-strips per pest (requires crop group **and** pest type filters). |

The UI is available in **English and Spanish** (switcher in the top bar, persisted in a cookie).

> 📡 **Sensors note**: there is currently no active sensor provider (DTAgro support was removed). The sensor pages serve measurements **already stored** by the platform, and the weather-based pest predictor falls back to SiAR weather data when no sensor data exists. The model/DTO layer is kept provider-agnostic so a future provider can plug in.

## 🤝 Contributing

1. Fork, then create a feature branch from `main`: `git checkout -b feature/my-feature` (or `issue/NN-description`).
2. Follow the existing conventions: typed code, DTO responses, custom `APIException` errors, decorators (`@log`, `@token_required`), tests with pytest (target ≥ 80 % coverage) placed under `tests/` directories.
3. Web conventions: Svelte 5 runes, server-side BFF actions (`+page.server.ts`) — never call the microservices from the browser directly; new UI strings go into **both** `web/src/lib/i18n/en.ts` and `es.ts`.
4. Run the quality gates before opening a PR: service `pytest`, `npm run build && npm run check && npm test` for `web/`.
5. Open a pull request against `main` with a clear description; CI builds and publishes the Docker images.

**Extension points**

- **New sensor provider**: implement a client in `services/data-service/app/clients/`, an ingestion service in `app/ingesta/` (plug it into the `IngestionService` facade) and wire its config in `config/config.py`. The `Sensores`/`MedicionesSensor` models, DTOs and `IngestaDAO.crear_datos_sensores` persistence are already in place.
- **New pest**: register it with the DSL document (`doc/DSL.md`) through the data service.
- **New UI page**: add `web/src/routes/<page>/+page.server.ts` (actions calling the BFF clients) and `+page.svelte`; reuse the components in `web/src/lib/components/`.

## ⚠️ Known weak points (deployment roadmap)

- `ORIGIN` must match the public URL of the web UI (CSRF protection) — set it per environment.
- Signed PDFs require the signing credentials (`clave.key` + `certificado.crt`) to be mounted into the `predictors` container at `/app/app/informe/assets/`; without them, PDF generation returns a clean "not available" error while the JSON prediction keeps working.
- First-run ingestion latency (cold ranges) — background Celery retries mitigate it.
- Keycloak is deployed but not yet enforced on the historical endpoints.
- Secrets live in `.env` — planned migration to a secrets manager (Azure Key Vault).

## 📄 License & contact

Apache 2.0 — see the individual service folders. Contact: `amendoma@alumnos.unex.es`.
