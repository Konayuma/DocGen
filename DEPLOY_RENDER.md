# Deploying DocGen to Render

This file describes how to deploy the `DocGen` FastAPI app to Render using the included `render.yaml` manifest.

1. Create a new Render account or sign in to your existing account.
2. Connect your GitHub repository to Render (Render will request access to the repository).
3. In Render, click **New** -> **From Repo**, and select your repository and the `main` branch.
4. Choose the "Use a render.yaml or Dockerfile" option; your `render.yaml` will be used for configuration.
5. Complete the service setup and create the web service.

Important settings:
- Ensure you set `GEMINI_API_KEY` and any other necessary API keys in the **Environment** > **Secrets** section of the Render dashboard.
- If you use the optional GitHub Action deploy workflow, create the repository secrets `RENDER_API_KEY` and `RENDER_SERVICE_ID`.
- If you want to scale to production, change the plan from `free` to the appropriate paid plan in the Render dashboard.

Troubleshooting:
- If the build fails with Tesseract or system packages, check Render logs and ensure the Docker image installs dependencies correctly.
- If the app is unreachable, ensure it is listening on `$PORT` (the Dockerfile sets `PORT` default to 8000 and uses `$PORT` at runtime).
- Use the Render logs for `build` and `service` to diagnose errors.
