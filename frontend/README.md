# WindSight Frontend

The WindSight frontend is a React and TypeScript dashboard for evaluating day-ahead wind-generation forecasts against actual generation data.

## Tech Stack

- React
- TypeScript
- Vite
- Recharts
- Lucide React
- CSS

## Features

- Forecast-versus-actual generation chart
- Forecast error metrics: MAE, RMSE, bias, and WAPE
- Configurable decision cutoff
- Forecast evaluation audit table
- CSV export of evaluation results

## Local Development

From the project root, install dependencies and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The development server normally runs at `http://localhost:5173`.

The backend API must also be running. Configure `VITE_API_BASE_URL` in `frontend/.env.local` to point to the backend API. For local development, the default is `http://127.0.0.1:8000`.

## Production Build

```bash
npm run build
```

The production files are generated in `frontend/dist/`.

## Related Documentation

See the root-level `README.md` for the overall project architecture, evaluation methodology, backend setup, Docker instructions, and deployment configuration.
