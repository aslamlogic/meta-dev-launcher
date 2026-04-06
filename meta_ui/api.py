from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import Any
import os

app = FastAPI()


@app.get("/")
def root():
    return FileResponse("meta_ui/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/runs")
def runs():
    return {"status": "ready"}


@app.get("/env")
def env():
    return {
        "META_GITHUB_TOKEN": bool(os.getenv("META_GITHUB_TOKEN"))
    }


@app.post("/run")
async def run_system(request: Request) -> Any:
    try:
        body = await request.json()
        repo = body.get("repo")

        if not repo:
            return {"status": "error", "error": "repo not provided"}

        from iteration.controller import main

        result = main(repo)

        return {
            "status": "executed",
            "repo": repo,
            "result": result
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )
