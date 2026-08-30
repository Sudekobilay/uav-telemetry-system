import json
from aiomqtt import Client
from app.core.config import settings
from app.schemas.command import TelecommandPayload


async def dispatch_telecommand(command: TelecommandPayload) -> bool:
    """
    GCS'ten gelen telekomutu doğrular ve ilgili İHA'nın dinlediği
    'commands/{uav_id}/action' MQTT kanalına basar (Uplink Hattı).
    """
    topic = f"commands/{command.uav_id}/action"
    payload_json = json.dumps({
        "uav_id": command.uav_id,
        "command": command.command_type.value,
        "parameters": command.parameters
    })

    try:
        async with Client(hostname=settings.MQTT_BROKER_HOST, port=settings.MQTT_BROKER_PORT) as client:
            await client.publish(topic, payload=payload_json, qos=1)
            print(f"📡 [C2 UPLINK] Komut fırlatıldı -> Topic: {topic} | Komut: {command.command_type.value}")
            return True
    except Exception as e:
        print(f"❌ [C2 UPLINK HATA] Komut iletilemedi: {e}")
        return False