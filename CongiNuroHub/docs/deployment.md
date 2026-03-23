# CongiNuroHub Deployment

CongiNuroHub now has a concrete deployment target for a stable browser URL.

## Container target

Build locally:

```powershell
docker build -t conginurohub .\CongiNuroHub
docker run --rm -p 8877:8877 conginurohub
```

The container starts the built-in HTTP server on `0.0.0.0` and reads the `PORT` environment variable.

## Render target

`render.yaml` is included for a simple web-service deployment.

Expected flow:

1. Push the repository to GitHub.
2. Create a new Render Blueprint deployment from the repository.
3. Render will build the `Dockerfile` and expose a stable `onrender.com` URL.
4. Educators can use that URL directly in class.

## Notes

- CongiNuroHub serves NeoWakeUP workspace assets from the same repository checkout. If you deploy CongiNuroHub independently, keep the `NeoWakeUP/assets/recraft/gui_pass_600` asset tree present alongside the app.
- For fully self-contained public deployment, the next step is copying the selected NeoWakeUP assets into a CongiNuroHub-owned static asset directory.