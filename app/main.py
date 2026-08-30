import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, Base, ensure_database_exists, get_db
import app.models.telemetry
from app.schemas.telemetry import TelemetryPayload
from app.services.telemetry_service import save_telemetry_data
from app.services.mqtt_service import start_mqtt_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Veritabanı ve tabloları hazırla
    await ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 [DATABASE] Tüm tablolar başarıyla oluşturuldu / senkronize edildi.")
    
    # 2. MQTT Dinleyici görevini arka planda başlat
    mqtt_task = asyncio.create_task(start_mqtt_listener())
    
    yield
    
    # 3. Kapanırken görevi iptal et ve bağlantıları kapat
    mqtt_task.cancel()
    await engine.dispose()
    print("🛑 [DATABASE & MQTT] Bağlantılar ve arka plan görevleri kapatıldı.")


app = FastAPI(
    title="UAV Telemetry & Analytics System",
    description="Savunma Sanayii Odaklı Gerçek Zamanlı İHA Telemetri Takip ve Analiz API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "status": "online",
        "service": "UAV Telemetry API",
        "version": "1.0.0"
    }


@app.post("/api/v1/telemetry/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(payload: TelemetryPayload, db: AsyncSession = Depends(get_db)):
    """
    Gelen telemetri paketini doğrular ve MySQL veritabanına kalıcı olarak kaydeder (HTTP Hattı).
    """
    record = await save_telemetry_data(payload=payload, db=db)
    return {
        "message": "Telemetri verisi başarıyla kaydedildi.",
        "log_id": record.id,
        "session_id": record.session_id,
        "uav_id": payload.uav_id,
        "status": record.status
    }