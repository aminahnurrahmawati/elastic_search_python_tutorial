from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ApiError, ConnectionError
from datetime import datetime
import logging

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rumus-logger")

# Connect ke Elasticsearch (pakai hostname service Elasticsearch di docker-compose)
es = Elasticsearch("http://elasticsearch:9200")

# Cek koneksi saat startup
@app.on_event("startup")
async def startup_event():
    try:
        if not es.ping():
            logger.error("Elasticsearch tidak bisa dihubungi!")
            raise Exception("Elasticsearch tidak tersedia")
        logger.info("Terhubung ke Elasticsearch")
    except (ApiError, ConnectionError, Exception) as e:
        logger.error(f"Error connect ke ES: {e}")

# Model input user
class Rumus(BaseModel):
    title: str        # contoh: "Luas Lingkaran"
    formula: str      # contoh: "π × r²"
    category: str     # contoh: "matematika" atau "fisika"

# Endpoint untuk menyimpan rumus
@app.post("/rumus")
async def simpan_rumus(rumus: Rumus):
    doc = {
        "timestamp": datetime.utcnow().isoformat(),
        "title": rumus.title,
        "formula": rumus.formula,
        "category": rumus.category,
    }
    try:
        res = es.index(index="rumus-log", document=doc, refresh="wait_for")
        logger.info(f"✔ Rumus '{rumus.title}' disimpan.")
        return {"status": "sukses", "elasticsearch_result": res["result"]}
    except (ApiError, ConnectionError, Exception) as e:
        logger.error(f"Gagal menyimpan rumus: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan ke Elasticsearch")

# Endpoint untuk mengambil daftar rumus
@app.get("/rumus")
async def get_rumus():
    try:
        res = es.search(index="rumus-log", query={"match_all": {}}, size=10)
        results = [hit["_source"] for hit in res["hits"]["hits"]]
        return {"count": len(results), "data": results}
    except (ApiError, ConnectionError, Exception) as e:
        logger.error(f"Gagal mengambil data rumus: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil data dari Elasticsearch")

# Endpoint root untuk tes API
@app.get("/")
async def root():
    return {"message": "FastAPI + Elasticsearch"}
