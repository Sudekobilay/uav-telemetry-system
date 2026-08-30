#Yer istasyonunda çalışan, UDP soketinden gelen ikili MAVLink paketlerini ayrıştırıp standart JSON formatına dönüştüren ve Mosquitto MQTT Broker'a fırlatan köprü

import json
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from pymavlink import mavutil

# MAVLink UDP Giriş Portu
MAVLINK_LISTEN_ADDR = "udpin:127.0.0.1:14550"

# MQTT Broker Ayarları
MQTT_BROKER_HOST = "127.0.0.1"
MQTT_BROKER_PORT = 1883
UAV_ID = "BAYRAKTAR-TB2-01"
MQTT_TOPIC = f"telemetry/{UAV_ID}/data"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ [MAVLink BRIDGE] MQTT Broker'a bağlandı -> {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        print(f"🎯 [HEDEF TOPIC] {MQTT_TOPIC} (QoS 1)")
    else:
        print(f"❌ [MAVLink BRIDGE] MQTT Bağlantı Hatası: {rc}")


def run_bridge():
    # 1. MQTT İstemcisini Başlat
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"mavlink_bridge_{UAV_ID}")
    mqtt_client.on_connect = on_connect
    
    try:
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"❌ [MQTT HATA] Broker'a erişilemedi: {e}")
        return

    # 2. MAVLink Dinleyici Bağlantısını Aç
    print(f"📡 [MAVLink BRIDGE] MAVLink UDP portu dinleniyor -> {MAVLINK_LISTEN_ADDR}")
    mav_conn = mavutil.mavlink_connection(MAVLINK_LISTEN_ADDR)

    # Durum değişkenleri (SYS_STATUS ve GLOBAL_POSITION_INT'i harmanlamak için)
    current_battery = 100.0
    packet_count = 0

    print("🚀 [KÖPRÜ AKTİF] MAVLink paketleri bekleniyor...\n")

    try:
        while True:
            # Gelen MAVLink paketini bloklayarak bekle
            msg = mav_conn.recv_match(type=['GLOBAL_POSITION_INT', 'SYS_STATUS'], blocking=True, timeout=3.0)
            
            if msg is None:
                continue

            msg_type = msg.get_type()

            # Batarya durumunu güncelle
            if msg_type == 'SYS_STATUS':
                if msg.battery_remaining != -1:
                    current_battery = float(msg.battery_remaining)

            # Konum verisi geldiğinde telemetri paketini derleyip MQTT'ye yayınla
            elif msg_type == 'GLOBAL_POSITION_INT':
                packet_count += 1
                
                # MAVLink birim dönüşümleri
                lat_deg = msg.lat / 1e7
                lon_deg = msg.lon / 1e7
                alt_m = msg.relative_alt / 1000.0
                speed_mps = round(math.sqrt(msg.vx**2 + msg.vy**2) / 100.0, 2) if hasattr(msg, 'vx') else 0.0
                heading_deg = msg.hdg / 100.0

                # Bizim Pydantic Şemamıza uygun JSON yükü
                telemetry_payload = {
                    "uav_id": UAV_ID,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "latitude": round(lat_deg, 6),
                    "longitude": round(lon_deg, 6),
                    "altitude": round(alt_m, 2),
                    "speed": speed_mps,
                    "battery": round(current_battery, 2),
                    "temperature": 38.5,
                    "heading": round(heading_deg, 1),
                    "status": "NORMAL"
                }

                # MQTT Broker'a yayınla (QoS 1)
                payload_json = json.dumps(telemetry_payload)
                mqtt_client.publish(MQTT_TOPIC, payload_json, qos=1)

                print(
                    f"🌉 [BRIDGE #{packet_count}] MAVLink -> MQTT | "
                    f"İrtifa: {telemetry_payload['altitude']}m | "
                    f"Batarya: %{telemetry_payload['battery']} | "
                    f"Hız: {telemetry_payload['speed']} m/s"
                )

    except KeyboardInterrupt:
        print("\n🛑 [KÖPRÜ DURDURULDU] Kullanıcı köprüyü kapattı.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("🔌 Bağlantılar temizlendi.")


if __name__ == "__main__":
    import math
    run_bridge()