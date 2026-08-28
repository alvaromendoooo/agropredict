28/08/2026

<task_progress>
- [x] Map all DTAgro references across data-service, climate_risk_pred, infra, docs
- [x] Understand sensor data flow (DTAgro → ingestion → DB → /sensores → predictor)
- [x] Decide what stays (models/DTOs/DAO, /sensores endpoint) vs. what goes (DTAgro fetch layer)
- [x] Present plan for approval
- [x] Delete DTAgro files + update services/config/infra/docs
- [x] Validate: grep sweep (clean), compile checks (OK), pytest both services (no regressions vs. baseline)
</task_progress>

# ✅ DTAgro removal complete — final summary

**19 files changed: 44 insertions(+), 14,917 deletions(−)** — exactly as approved in the plan.

## What was deleted
| File | Why |
|---|---|
| `services/data-service/app/external_services/dtagro_service.py` | 100% DTAgro fetch logic |
| `services/data-service/app/clients/sensor_client.py` | 100% DTAgroClient (HTTP + token) |
| `services/data-service/app/ingesta/sensor_ingestion_service.py` | Only wrapped DTAgroService → DB |
| `app/data/dispositivos/dt_devices.csv`, `parcelas/dt_plots.csv`, `sensores/dt_markers.csv` | DTAgro-exported sample metadata (zero code references) |
| `services/data-service/repomix-output.xml` | Generated bundle containing stale DTAgro source |
| `DTAGRO_SERVICE_BASE_URL` / `DTAGRO_API_TOKEN` | From `config.py`, `infra/local/docker/.env`, `orchestator.env.tpl` |

## What was updated
- **`sensores_service.py` / `routes.py` (data-service)**: `/sensores` is now a provider-agnostic **DB-read endpoint** — no `nombre_dt_agro` param, no on-demand ingestion; 404 for unknown sensors or unstored ranges (also fixed a latent crash: `None` results from sensors without data were appended and would break DTO building).
- **`ingesta_service.py`**: removed `SensorIngestionService` from the facade mixin (SIAR/AEMET/ITACyL/Metadata intact).
- **Predictor**: `get_datos_sensores()` client without the DTAgro param; dtagro-branded identifiers renamed to generic sensor terms; **`datos_sensores` now optional** in `POST /plagas/estimadas` (SiAR-only estimated predictions work); added **None-safety** in `_transformar_datos_sensores` — without DTAgro backfill, 404s become common and previously crashed with `AttributeError`.
- **Swagger (both services), data-service README, AGENTS.md**: DTAgro wording removed/neutralized; `.gitkeep` keeps the metadata upload dirs alive.

## Explicitly preserved (per your instruction)
`models.py` (Sensores, MedicionesSensor, Dispositivos, Parcelas, Metadatos), all DTOs, `IngestaDAO.crear_datos_sensores`, the metadata CSV-upload system, and `EvaluarPlaga`'s SiAR fallback — a future provider only needs to re-add a client + ingestion service class.

## Validation results
- **Sweep**: zero `dtagro` references left (only the intentional historical note in AGENTS.md).
- **`compileall`**: OK on both services.
- **data-service tests: 75 passed / 13 failed** — I verified via `git stash` that the **pre-change baseline is identical** (13 pre-existing failures in `historicos` tests: fixtures use `MedicionClimatica(temperatura=...)` columns that no longer exist in the model — unrelated to sensors).
- **predictor tests: 33 passed / 7 failed** — baseline also identical (pre-existing outdated expectations vs. `evaluar_plaga_generica` signature, plus an `UnboundLocalError` at `prediction_service.py:1393` in heladas code).
- Note: the local env was missing the declared dependencies (`pyHanko`, `reportlab`, etc.) — I installed them so the suites could run; no repo files were changed for that.

⚠️ One heads-up: the two pre-existing test failure groups are worth fixing separately (they're stale tests, not infra problems). Also, the tracked runtime log `fichero_salida.json` keeps getting modified by test runs — consider adding it to `.gitignore` in a future cleanup.