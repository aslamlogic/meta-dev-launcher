from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from iteration.controller import run_iteration_loop


app = FastAPI()


class Endpoint(BaseModel):
    method: str
    path: str


class Spec(BaseModel):
    endpoints: List[Endpoint]


@app.get("/")
def root():
    return {"status": "meta_dev_launcher_running"}


@app.post("/run")
def run(spec: Spec):
    try:
        spec_dict = spec.dict()

        print("[DEBUG SPEC RECEIVED]", spec_dict)

        result = run_iteration_loop(spec_dict)

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
