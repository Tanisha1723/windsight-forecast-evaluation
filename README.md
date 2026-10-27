# WindSight

**Day-ahead wind forecast evaluation for energy-market decisions.**

WindSight is a decision-support dashboard that compares forecast wind generation with actual generation for Great Britain. It evaluates forecasts using information available at a configurable decision cutoff, helping users understand forecast error without using later forecast revisions.

## Problem

Energy-market decisions depend on estimates of future wind generation. Forecasts can change as delivery approaches, so evaluating a forecast using a revision published after the decision time can create misleading results.

WindSight selects the latest eligible forecast published at or before the configured cutoff for each delivery hour, then compares it with observed generation.

## Features

- Forecast-versus-actual generation chart
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Forecast bias
- Weighted Absolute Percentage Error (WAPE)
- Configurable decision cutoff
- Hourly forecast audit table
- CSV export
- Dockerized FastAPI backend

## Data Sources

WindSight uses the Elexon BMRS API:

- **FUELHH** — actual generation, filtered to wind (`fuelType=WIND`)
- **WINDFOR evolution** — forecast revisions for a delivery time

Official documentation:

- [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)
- [WINDFOR latest stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest/stream)
- [WINDFOR evolution](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/evolution)

## Evaluation Methodology

### Decision cutoff

For a delivery timestamp \(t\), the cutoff is:

`delivery timestamp - configured cutoff hours`

For each delivery hour, WindSight selects the forecast revision with the latest `publishTime` that is less than or equal to the cutoff. Revisions published after the cutoff are not eligible.

The default cutoff is 24 hours before delivery. The exact market decision time is not specified by the challenge, so the cutoff is configurable and treated as an explicit modeling assumption.

### Actual generation

The FUELHH source provides half-hourly actual generation. WindSight groups the two half-hourly observations within each UTC delivery hour and averages their generation values to create an hourly comparison value.

### Error convention

`error = forecast generation - actual generation`

- Positive bias indicates overforecasting.
- Negative bias indicates underforecasting.

### Metrics

- **MAE:** average absolute forecast error, in MW.
- **RMSE:** square root of mean squared error, in MW.
- **Bias:** average signed error, in MW.
- **WAPE:** total absolute error divided by total actual generation, expressed as a percentage.

Metrics are calculated using matched, valid forecast/actual pairs. The dashboard reports the number of evaluated and unavailable intervals. WAPE is undefined when total actual generation is zero.

### Scope and limitations

This project evaluates wind-generation forecasts, not total electricity demand or the complete procurement position. Without demand and other supply information, forecast error alone cannot determine the amount of additional electricity that must be purchased.

Results depend on the available source records, hourly aggregation, and the configured cutoff. The evaluation is intended as decision support, not a trading recommendation.

## Architecture

```text
Elexon BMRS API
      |
      v
FastAPI backend
  - Fetch actual wind generation
  - Fetch forecast revisions
  - Select forecast at cutoff
  - Calculate metrics
      |
      v
React + TypeScript frontend
  - KPI cards
  - Forecast comparison chart
  - Audit table
  - CSV export
```

## Project Structure

```text
windsight/
├── backend/
│   ├── elexon.py
│   ├── evaluation.py
│   ├── main.py
│   ├── requirements.txt
│   └── test_evaluation.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── README.md
├── Dockerfile
├── .dockerignore
└── README.md
```

## Run Locally

### Requirements

- Python 3.12 or compatible
- Node.js and npm
- Internet access to the Elexon BMRS API

### Backend

From the project root, create and activate a virtual environment, then install dependencies.

Windows PowerShell:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Health check: `http://127.0.0.1:8000/api/health`

API documentation: `http://127.0.0.1:8000/docs`

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

For local development, the frontend uses `http://127.0.0.1:8000` as the API base by default. To override it, set `VITE_API_BASE_URL` in `frontend/.env.local`.

## Docker

Build the backend image from the project root:

```powershell
docker build -t windsight-api .
```

Run the API container:

```powershell
docker run --rm --name windsight-api -p 8001:8000 windsight-api
```

Health check:

`http://localhost:8001/api/health`

The Docker command above exposes the API on host port 8001. If using the frontend with this container, set `VITE_API_BASE_URL=http://localhost:8001` and restart the frontend development server.

## Tests and Validation

Run the automated evaluation tests from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\test_evaluation.py -v
```

The repository also contains manual scripts for inspecting Elexon responses and validating evaluation consistency. Some scripts require network access to the live API.

## Deployment

Deploy the frontend and backend as separate services:

- Frontend: Vercel or another static hosting provider
- Backend: a Docker-capable hosting provider

Set `VITE_API_BASE_URL` in the frontend hosting environment to the deployed backend's public API URL. Configure backend CORS to permit the deployed frontend origin before deployment.

Deployment URLs will be added after the services are published.

## License

Add a license if you intend to distribute this project under a specific open-source license.
