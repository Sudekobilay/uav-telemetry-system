import time
import requests
from simulator.uav_simulator import UAVPhysicsSimulator

API_URL = "http://127.0.0.1:8000/api/v1/telemetry/ingest"

def run_producer(interval_seconds: float = 1.0):
    """
    Fizik simülatöründen sürekli veri üretip FastAPI sunucusuna HTTP POST ile basar.
    """
    simulator = UAVPhysicsSimulator(uav_id="BAYRAKTAR-TB2-01")
    print(f"📡 [PRODUCER] Telemetri aktarımı başlatıldı -> Hedef: {API_URL}")
    print("-" * 75)

    packet_count = 0
    try:
        while True:
            telemetry_data = simulator.generate_telemetry_packet(dt=interval_seconds)
            packet_count += 1

            try:
                response = requests.post(API_URL, json=telemetry_data, timeout=3.0)
                if response.status_code in [200,201]:
                    print(f"✅ [PAKET #{packet_count}] İrtifa: {telemetry_data['altitude']}m | Batarya: %{telemetry_data['battery']} | Durum: {telemetry_data['status']} -> HTTP 200 OK")
                else:
                    print(f"❌ [HATA #{packet_count}] Sunucu Reddi: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                print(f"⚠️ [BAĞLANTI HATASI] FastAPI sunucusuna ulaşılamıyor (127.0.0.1:8000). Sunucu açık mı?")

            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n🛑 [PRODUCER] Telemetri yayını kullanıcı tarafından durduruldu.")


if __name__ == "__main__":
    # requests kütüphanesi yoksa terminalden 'pip install requests' yapabilirsin
    run_producer(interval_seconds=1.0)