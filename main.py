from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI(title="meta-dev", version="14")


@app.get("/")
def root():
    return JSONResponse({"service": "meta-dev", "version": "14", "status": "ok"})


@app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
