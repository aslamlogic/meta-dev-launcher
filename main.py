from fastapi import FastAPI

app = FastAPI(title="meta-dev", version="14")


@app.get("/")
def root():
    return {"project": "meta-dev", "version": "14", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
