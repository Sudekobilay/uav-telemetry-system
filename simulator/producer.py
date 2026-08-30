import json
import time
import paho.mqtt.client as mqtt
from simulator.uav_simulator import UAVPhysicsSimulator

MQTT_BROKER_HOST = "127.0.0.1"
MQTT_BROKER_PORT = 1883
UAV_ID = "BAYRAKTAR-TB2-01"
MQTT_TOPIC = f"telemetry/{UAV_ID}/data"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ [MQTT PRODUCER] Mosquitto Broker'a başarıyla bağlandı -> {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        print(f"🎯 [HEDEF TOPIC] {MQTT_TOPIC} (QoS 1)")
        print("-" * 75)
    else:
        print(f"❌ [MQTT PRODUCER] Bağlantı başarısız, Hata Kodu: {rc}")


def run_producer(interval_seconds: float = 1.0):
    """
    Fizik simülatöründen sürekli veri üretip Mosquitto Broker'a MQTT Publish (QoS 1) ile basar.
    """
    simulator = UAVPhysicsSimulator(uav_id=UAV_ID)
    
    # 1. MQTT İstemcisini Hazırla
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"producer_{UAV_ID}")
    client.on_connect = on_connect

    print(f"📡 [PRODUCER] MQTT Broker'a bağlanılıyor -> {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        client.loop_start()  # Ağ trafiğini arka planda yönetir
    except Exception as e:
        print(f"⚠️ [BAĞLANTI HATASI] Mosquitto Broker'a ulaşılamıyor: {e}. Docker container ayakta mı?")
        return

    packet_count = 0
    try:
        while True:
            # 2. Fizik Simülatöründen Telemetri Paketi Üret
            telemetry_data = simulator.generate_telemetry_packet(dt=interval_seconds)
            packet_count += 1
            payload_json = json.dumps(telemetry_data)

            # 3. MQTT Topic Üzerine QoS 1 ile Yayınla
            msg_info = client.publish(MQTT_TOPIC, payload_json, qos=1)
            msg_info.wait_for_publish(timeout=2.0)

            print(
                f"📤 [PAKET #{packet_count}] İrtifa: {telemetry_data['altitude']}m | "
                f"Batarya: %{telemetry_data['battery']} | "
                f"Durum: {telemetry_data['status']} -> MQTT OK (Topic: {MQTT_TOPIC})"
            )

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n🛑 [PRODUCER] Telemetri yayını kullanıcı tarafından durduruldu.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("🔌 MQTT bağlantısı kapatıldı.")


if __name__ == "__main__":
    run_producer(interval_seconds=1.0)