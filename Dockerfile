# Run the Pytest + Playwright UI smoke tests inside a headless container.
# Base image ships Chromium + all OS libraries Playwright needs.
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

# unixODBC headers let pyodbc (listed in requirements.txt) build. The database
# layer is NOT exercised by this headless smoke skeleton, but the package still
# has to install cleanly so the app imports without error.
RUN apt-get update \
    && apt-get install -y --no-install-recommends unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first so this layer is cached across code edits.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

# Copy the framework source after dependencies are cached.
COPY . .

# Headless, unattended defaults.
#   HEADLESS=True         -> Chromium runs without a display.
#   PAUSE_ON_FAILURE=False -> a failing test never calls page.pause(),
#                             which would otherwise block the container forever.
#   MANUAL_LOGIN=false    -> no interactive SSO; the run fails fast if no
#                             auth_state.json is mounted, and still exports
#                             artifacts (screenshots, reports) to result/.
ENV HEADLESS=True \
    PAUSE_ON_FAILURE=False \
    MANUAL_LOGIN=false \
    PYTHONUNBUFFERED=1

# Single sanity smoke test by default. Override at run time to target another
# suite, e.g. `docker run ... pytest tests/unit/`.
CMD ["pytest", "tests/ui/power_outages_dashboard/", "-m", "sanity"]
