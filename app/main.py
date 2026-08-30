from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from app.db.session import engine, Base, ensure_database_exists
import app.models.telemetry  # Tabloları SQLAlchemy'ye tanıtmak için
from app.schemas.telemetry import TelemetryPayload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Önce DB'nin var olduğundan emin ol
    await ensure_database_exists()
    
    # 2. Tabloları oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 [DATABASE] Tüm tablolar başarıyla oluşturuldu / senkronize edildi.")
    yield
    # SHUTDOWN
    await engine.dispose()
    print("🛑 [DATABASE] Veritabanı bağlantı havuzu kapatıldı.")


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

@app.post("/api/v1/telemetry/validate", status_code=status.HTTP_200_OK)
async def validate_telemetry(payload: TelemetryPayload):
    return {
        "message": "Telemetri paketi başarıyla doğrulandı.",
        "received_data": payload
    }