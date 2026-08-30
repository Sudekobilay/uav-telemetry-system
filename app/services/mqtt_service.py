import json
import asyncio
from aiomqtt import Client
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.telemetry import TelemetryPayload
from app.services.telemetry_service import save_telemetry_data
from app.services.websocket_manager import ws_manager


async def start_mqtt_listener():
    """
    FastAPI yaşam döngüsünde arka planda çalışan MQTT Subscriber.
    Broker üzerindeki 'telemetry/+/data' kanalını dinler,
    veriyi MySQL'e kaydeder ve WebSocket ile bağlı tüm haritalara anında dağıtır.
    """
    print(f"📡 [MQTT SUBSCRIBER] Broker'a bağlanılıyor -> {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
    
    while True:
        try:
            async with Client(hostname=settings.MQTT_BROKER_HOST, port=settings.MQTT_BROKER_PORT) as client:
                await client.subscribe(settings.MQTT_TELEMETRY_TOPIC, qos=1)
                print(f"✅ [MQTT SUBSCRIBER] Abone olundu: '{settings.MQTT_TELEMETRY_TOPIC}' (QoS 1)")

                async for message in client.messages:
                    try:
                        # 1. Ham JSON mesajını ayrıştır
                        payload_dict = json.loads(message.payload.decode("utf-8"))
                        
                        # 2. Pydantic şeması ile doğrula
                        telemetry_payload = TelemetryPayload(**payload_dict)

                        # 3. Asenkron DB oturumu açıp MySQL'e kaydet
                        async with AsyncSessionLocal() as db_session:
                            saved_record = await save_telemetry_data(payload=telemetry_payload, db=db_session)
                        
                        # 4. WebSocket üzerinden bağlı tüm istemcilere (Harita / Dashboard) canlı ilet
                        broadcast_data = telemetry_payload.model_dump()
                        broadcast_data["timestamp"] = broadcast_data["timestamp"].isoformat()
                        broadcast_data["log_id"] = saved_record.id
                        await ws_manager.broadcast(broadcast_data)

                        print(f"📥 [MQTT RECV & WS BROADCAST] İHA: {telemetry_payload.uav_id} | Log ID: {saved_record.id} | İrtifa: {telemetry_payload.altitude}m | Batarya: %{telemetry_payload.battery}")

                    except json.JSONDecodeError:
                        print("⚠️ [MQTT HATA] Geçersiz JSON paketi alındı.")
                    except Exception as parse_err:
                        print(f"⚠️ [MQTT DOĞRULAMA HATASI] {parse_err}")

        except asyncio.CancelledError:
            print("🛑 [MQTT SUBSCRIBER] Dinleyici görevi durduruldu.")
            break
        except Exception as conn_err:
            print(f"❌ [MQTT BAĞLANTI HATASI] Broker bağlantısı kesildi: {conn_err}. 3 saniye sonra yeniden denenecek...")
            await asyncio.sleep(3)