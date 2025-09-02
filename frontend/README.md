# Frontend for Latest News Agent

## Run (Dev)

- From `frontend/`:

```
npm install
NEXT_PUBLIC_BACKEND_URL=http://localhost:12001 npm run dev
```

The app starts at http://localhost:12000. It sets permissive headers to allow iframes and CORS.

Two-host setup for this environment:
- Frontend: https://work-1-gkenubufgwosjdnq.prod-runtime.all-hands.dev (port 12000)
- Backend: https://work-2-gkenubufgwosjdnq.prod-runtime.all-hands.dev (port 12001)

Pass the backend URL via env variable as shown above.
