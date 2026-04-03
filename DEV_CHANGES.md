# Dev Version Change Notes

## UI
- Dev mode indicator controlled by `MPT_MODE=dev`.
- Streamlit title shows `MoneyPrinterTurbo DEV v<version>`.
- Dev mode applies a subtle background/header tint to visually distinguish it from prod.

## Job execution model (important)
- WebUI no longer runs video generation in the Streamlit session.
- WebUI now submits work to the FastAPI backend:
  - Create task: `POST /api/v1/videos`
  - Poll status: `GET /api/v1/tasks/{task_id}`
- This allows video generation to continue even if the browser disconnects (e.g., mobile tab switching).

## Dev Docker Compose
- `moneyprinterturbo-dev.yml` now runs two services:
  - `moneyprinterturbo-dev-api` (FastAPI)
  - `moneyprinterturbo-dev-webui` (Streamlit)
- Dev WebUI uses `MPT_API_BASE_URL=http://moneyprinterturbo-dev-api:8080`.
- Host ports:
  - WebUI: `8502 -> 8501`
  - API: `8089 -> 8080`

## Security / API auth
- FastAPI endpoints under `/api/v1/*` require `x-api-key` matching `config.toml` `app.api_key`.

## Notes
- Task status is stored in memory unless Redis mode is enabled; API container restarts can lose task state.
