import json
import time
import random
import math
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from simulator.uav_simulator import UAVPhysicsSimulator

MQTT_BROKER_HOST = "127.0.0.1"
MQTT_BROKER_PORT = 1883

# Gerçekçi İHA Çağrı Kodları ve Modelleri
CALLSIGNS = ["BAYRAKTAR-TB2", "BAYRAKTAR-AKINCI", "TUSAS-ANKA", "TUSAS-AKSUNGUR", "BAYRAKTAR-KIZILELMA"]

# Aktif görevdeki İHA nesnelerinin referans havuzu
active_missions_dict = {}


class ActiveMission:
    """Hava sahasında o an görev yapan dinamik bir İHA nesnesi"""
    def __init__(self, uav_id: str):
        self.uav_id = uav_id
        
        # 1. Simülatörü uav_id ile başlat
        base_lat, base_lon = 40.7350, 30.0833
        start_lat = base_lat + random.uniform(-0.4, 0.4)
        start_lon = base_lon + random.uniform(-0.6, 0.6)
        start_alt = random.uniform(1500.0, 6000.0)

        self.sim = UAVPhysicsSimulator(
            uav_id=uav_id,
            start_lat=start_lat,
            start_lon=start_lon,
            start_alt=start_alt
        )
        
        # 2. Rastgele uçuş dinamikleri ata
        self.sim.speed = random.uniform(80.0, 140.0) if "KIZILELMA" not in uav_id else random.uniform(220.0, 320.0)
        self.sim.battery = random.uniform(85.0, 100.0)
        self.sim.heading = random.uniform(0.0, 360.0)
        
        # Görev süresi (60 ile 180 saniye arasında rastgele aktif kalma süresi)
        self.flight_duration_sec = random.randint(60, 180)
        self.start_time = time.time()

    def is_mission_completed(self) -> bool:
        """Görev süresi bitti mi, iniş tamamlandı mı veya batarya tükendi mi?"""
        if self.sim.status == "LANDED":
            return True
        # C2 komutu ile RTH/LOITER modunda ise süreden dolayı düşürme
        if self.sim.flight_mode in ["RTH", "LOITER"]:
            return False
        return (time.time() - self.start_time > self.flight_duration_sec)


def on_connect(client, userdata, flags, rc, properties=None):
    """Broker bağlantısı kurulduğunda C2 komut kanalına abone ol"""
    print("✅ [TRAFİK SİMÜLATÖRÜ] Broker'a bağlandı. C2 Komut kanalları dinleniyor (commands/+/action)...")
    client.subscribe("commands/+/action", qos=1)


def on_message(client, userdata, msg):
    """GCS Yer İstasyonundan gelen C2 komutunu yakala ve hedef İHA'ya uygula"""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        uav_id = payload.get("uav_id")
        command = payload.get("command")
        params = payload.get("parameters", {})

        if uav_id in active_missions_dict:
            mission = active_missions_dict[uav_id]
            mission.sim.process_command(command, params)
            print(f"⚡ [C2 UPLINK ALINDI] {uav_id} -> Komut: {command}")
        else:
            print(f"⚠️ [C2 UYARI] Komut gönderilen İHA hava sahasında bulunamadı: {uav_id}")
    except Exception as e:
        print(f"⚠️ [C2 PARSE HATA] {e}")


def main():
    global active_missions_dict

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="airspace_traffic_manager")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"📡 [HAVA SAHASI RADARI] MQTT Broker'a bağlanılıyor -> {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"❌ [MQTT HATA] Broker'a ulaşılamadı: {e}")
        return

    mission_counter = 1
    print("🚀 [DİNAMİK HAVA SAHASI YAYINDA] İHA'lar kalkış/iniş yapacak. C2 Komuta Hazır!\n")

    try:
        while True:
            # 1. Hava Sahasına Rastgele Yeni İHA Girişi (Kalkış / Spawn)
            if len(active_missions_dict) < 4 or (random.random() < 0.35 and len(active_missions_dict) < 12):
                model = random.choice(CALLSIGNS)
                uav_id = f"{model}-{mission_counter:03d}"
                mission_counter += 1
                
                mission = ActiveMission(uav_id)
                active_missions_dict[uav_id] = mission
                print(f"🛫 [KALKIŞ / AIRBORNE] Yeni İHA hava sahasına girdi -> {uav_id} (Aktif İHA Sayısı: {len(active_missions_dict)})")

            # 2. Havada Olan Tüm Aktif İHA'ların Telemetrisini Üret ve MQTT'ye Bas
            completed_uavs = []
            for uav_id, mission in active_missions_dict.items():
                if mission.is_mission_completed():
                    print(f"🛬 [İNİŞ / LANDED] {uav_id} görevini tamamlayıp üsse indi.")
                    completed_uavs.append(uav_id)
                    continue

                # Canlı telemetri paketini üret
                telemetry = mission.sim.generate_telemetry_packet(dt=1.0)
                topic = f"telemetry/{uav_id}/data"
                payload_json = json.dumps(telemetry)
                client.publish(topic, payload_json, qos=0)

            # İniş yapanları havuzdan temizle
            for uav_id in completed_uavs:
                del active_missions_dict[uav_id]

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n🛑 [HAVA SAHASI DURDURULDU] Simülasyon kapatıldı.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()