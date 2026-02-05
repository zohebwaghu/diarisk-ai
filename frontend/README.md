# DiaRisk AI Frontend

Minimal static client to call the FastAPI backend.

## Run

Open `index.html` in your browser. For best results, run a local static server:

```
python -m http.server 5173
```

Then visit `http://localhost:5173/frontend/`.

## Vercel Proxy

The Vercel deployment uses a serverless proxy under `/api/*` to forward requests
to your FastAPI backend. Set the backend URL in Vercel:

```
BACKEND_URL=https://your-backend.example.com
```

If `BACKEND_URL` is unset, the proxy returns a 500 error.
