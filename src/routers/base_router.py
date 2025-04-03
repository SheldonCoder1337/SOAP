from fastapi import APIRouter

base = APIRouter()

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request, Body
from src.core import HistoryManager
from src.common import setup_logger
from src.core.soap import soap

logger = setup_logger("server-base")

@base.get("/")
async def route_index():
    return {"message": "You Got It!"}

@base.get("/config")
def get_config():
    return soap.config

@base.post("/config")
async def update_config(key = Body(...), value = Body(...)):
    soap.config[key] = value
    soap.config.save()
    return soap.config

@base.post("/restart")
async def restart():
    soap.restart()
    return {"message": "Restarted!"}

@base.get("/log")
def get_log():
    from src.common.logger import LOG_FILE
    from collections import deque

    with open(LOG_FILE, 'r') as f:
        last_lines = deque(f, maxlen=1000)

    log = ''.join(last_lines)
    return {"log": log}


