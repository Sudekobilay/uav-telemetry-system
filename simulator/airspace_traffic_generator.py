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

class ActiveMission:
    """Hava sahasında o an görev yapan dinamik bir İHA nesnesi"""
    def __init__(self, uav_id: str):
        self.uav_id = uav_id
        
        # 1. Simülatörü uav_id ile başlat
        self.sim = UAVPhysicsSimulator(uav_id=uav_id)
        
        # 2. Rastgele konum ve uçuş değerlerini doğrudan simülatör nesnesine ata
        base_lat, base_lon = 40.7350, 30.0833
        self.sim.latitude = base_lat + random.uniform(-0.6, 0.6)
        self.sim.longitude = base_lon + random.uniform(-0.9, 0.9)
        self.sim.altitude = random.uniform(1500.0, 7000.0)
        self.sim.speed = random.uniform(40.0, 110.0) if "KIZILELMA" not in uav_id else random.uniform(180.0, 250.0)
        self.sim.battery = random.uniform(85.0, 100.0)
        self.sim.heading = random.uniform(0.0, 360.0)
        
        # Görev süresi (30 ile 90 saniye arasında rastgele aktif kalma süresi)
        self.flight_duration_sec = random.randint(30, 90)
        self.start_time = time.time()

    def is_mission_completed(self) -> bool:
        """Görev süresi bitti mi veya batarya tükendi mi?"""
        return (time.time() - self.start_time > self.flight_duration_sec)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="airspace_traffic_manager")
    print(f"📡 [HAVA SAHASI RADARI] MQTT Broker'a bağlanılıyor -> {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"❌ [MQTT HATA] Broker'a ulaşılamadı: {e}")
        return

    active_missions = []
    mission_counter = 1

    print("🚀 [DİNAMİK HAVA SAHASI YAYINDA] İHA'lar kalkış/iniş yapacak. Sabit sayı yok!\n")

    try:
        while True:
            # 1. Hava Sahasına Rastgele Yeni İHA Girişi (Kalkış / Spawn)
            if len(active_missions) < 4 or (random.random() < 0.4 and len(active_missions) < 15):
                model = random.choice(CALLSIGNS)
                uav_id = f"{model}-{mission_counter:03d}"
                mission_counter += 1
                
                mission = ActiveMission(uav_id)
                active_missions.append(mission)
                print(f"🛫 [KALKIŞ / AIRBORNE] Yeni İHA hava sahasına girdi -> {uav_id} (Aktif İHA Sayısı: {len(active_missions)})")

            # 2. Havada Olan Tüm Aktif İHA'ların Telemetrisini Üret ve MQTT'ye Bas
            still_active = []
            for mission in active_missions:
                if mission.is_mission_completed():
                    print(f"🛬 [İNİŞ / LANDED] {mission.uav_id} görevini tamamlayıp üsse indi.")
                    continue

                # Canlı telemetri paketini üret
                telemetry = mission.sim.generate_telemetry_packet(dt=1.0)
                topic = f"telemetry/{mission.uav_id}/data"
                payload_json = json.dumps(telemetry)
                client.publish(topic, payload_json, qos=0)
                still_active.append(mission)

            active_missions = still_active

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n🛑 [HAVA SAHASI DURDURULDU] Simülasyon kapatıldı.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()