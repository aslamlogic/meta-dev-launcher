from fastapi import FastAPI
from iteration.controller import main

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/runs")
def run():
    main()
    return {"status": "started"}
