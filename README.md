# meta-dev

FastAPI service for Railway deployment.

## Endpoints
- `GET /`
- `GET /health`

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port  
```
