import json
import asyncio
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse, Response
from concurrent.futures import ThreadPoolExecutor
from src.core import HistoryManager
from src.core.soap import soap
from src.common import setup_logger

chat = APIRouter(prefix="/chat")
logger = setup_logger("server-chat")
executor = ThreadPoolExecutor()
refs_pool = {}

@chat.get("/")
async def chat_get():
    return "Chat Get!"

@chat.post("/")
def chat_post(
        query: str = Body(...),
        meta: dict = Body(None),
        history: list = Body(...),
        cur_res_id: str = Body(...)):

    history_manager = HistoryManager(history)

    def make_chunk(content, status, history):
        return json.dumps({
            "response": content,
            "history": history,
            "model_name": soap.config.model_name,
            "status": status,
            "meta": meta,
        }, ensure_ascii=False).encode('utf-8') + b"\n"

    def generate_response():

        if meta.get("enable_retrieval"):
            chunk = make_chunk("", "searching", history=None)
            yield chunk

            new_query, refs = soap.retriever(query, history_manager.messages, meta)
            refs_pool[cur_res_id] = refs
        else:
            new_query = query

        messages = history_manager.get_history_with_msg(new_query, max_rounds=meta.get('history_round'))
        history_manager.add_user(query)
        logger.debug(f"Web history: {history_manager.messages}")

        content = ""
        for delta in soap.model.predict(messages, stream=True):
            if not delta.content:
                continue

            if hasattr(delta, 'is_full') and delta.is_full:
                content = delta.content
            else:
                content += delta.content

            chunk = make_chunk(content, "loading", history=history_manager.update_ai(content))
            yield chunk

    return StreamingResponse(generate_response(), media_type='application/json')

@chat.post("/call")
async def call(query: str = Body(...), meta: dict = Body(None)):
    async def predict_async(query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, soap.model.predict, query)

    response = await predict_async(query)
    logger.debug({"query": query, "response": response.content})

    return {"response": response.content}

@chat.get("/refs")
def get_refs(cur_res_id: str):
    global refs_pool
    refs = refs_pool.pop(cur_res_id, None)
    return {"refs": refs}