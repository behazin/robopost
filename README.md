# Robopost
## Environment Variables

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to a Google Cloud service account JSON key file.
- `GOOGLE_PROJECT_ID`: Identifier of the Google Cloud project used by Vertex AI.
- `CRAWLER_INTERVAL_SECONDS`: Interval in seconds for the source crawler scheduler.

## Running Tests

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Run the test suite:
   ```bash
   pytest
   ```

To measure code coverage:
```bash
coverage run -m pytest
coverage report
```
The pytest configuration enables asyncio support and coverage settings.

## Rebuilding Containers

After making changes, rebuild the service containers so that code and dependency updates are reflected:

```bash
docker compose build
# or
docker compose up --build
```
