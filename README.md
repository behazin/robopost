# Robopost

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