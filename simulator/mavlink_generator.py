#Gerçek bir otopilot donanımının (Pixhawk) veya SITL motorunun UDP üzerinden fırlattığı ikili MAVLink paketlerini üreten bir simülatö
import time
import math
from pymavlink import mavutil

# UDP üzerinden MAVLink yayını yapacak yerel hedef (GCS / Bridge Portu)
UDP_TARGET = "udpout:127.0.0.1:14550"

def run_mavlink_sitl():
    print(f"🚁 [MAVLink SITL] Sanal otopilot başlatılıyor...")
    print(f"📡 [MAVLink UDP OUT] Hedef: {UDP_TARGET}")
    
    # 1. UDP Soketi üzerinden MAVLink çıkış hattını aç
    mav_conn = mavutil.mavlink_connection(UDP_TARGET, source_system=1, source_component=1)
    
    lat = 40.7350
    lon = 30.0833
    alt_m = 500.0
    heading_deg = 45.0
    ground_speed = 45.0 # m/s
    battery_pct = 100.0
    boot_time_ms = 0

    print("🚀 [MAVLink SITL] İkili (Binary) telemetri akışı başladı... (Durdurmak için: CTRL+C)\n")

    try:
        while True:
            boot_time_ms += 1000
            
            # Koordinat ve İrtifa güncellemesi (Fizik hesabı)
            rad = math.radians(heading_deg)
            lat += (ground_speed * math.cos(rad) / 111000.0)
            lon += (ground_speed * math.sin(rad) / (111000.0 * math.cos(math.radians(lat))))
            if alt_m < 3000.0:
                alt_m += 5.0
            battery_pct = max(5.0, battery_pct - 0.03)

            # MAVLink Protokol Dönüşümleri:
            # - Lat/Lon: 1e7 ile çarpılmış tamsayı (int)
            # - Alt: Milimetre (mm)
            # - Heading: cdeg (Derece * 100)
            # - Speed: cm/s
            vx_cms = int(ground_speed * math.cos(rad) * 100)
            vy_cms = int(ground_speed * math.sin(rad) * 100)
            
            # 1. GLOBAL_POSITION_INT Mesajı Gönder (Konum, İrtifa, Hız)
            mav_conn.mav.global_position_int_send(
                boot_time_ms,
                int(lat * 1e7),
                int(lon * 1e7),
                int((alt_m + 50.0) * 1000), # Basınç irtifası (AMSL mm)
                int(alt_m * 1000),          # Göreceli irtifa (Relative Alt mm)
                vx_cms,
                vy_cms,
                0,                          # Dikey hız (vz)
                int(heading_deg * 100)      # Heading (cdeg)
            )

            # 2. SYS_STATUS Mesajı Gönder (Batarya, Voltaj)
            mav_conn.mav.sys_status_send(
                onboard_control_sensors_present=0,
                onboard_control_sensors_enabled=0,
                onboard_control_sensors_health=0,
                load=500,                    # %50 CPU yükü
                voltage_battery=12600,       # 12.6V (mV)
                current_battery=1500,        # 15A (cA)
                battery_remaining=int(battery_pct), # Kalan %
                drop_rate_comm=0,
                errors_comm=0,
                errors_count1=0,
                errors_count2=0,
                errors_count3=0,
                errors_count4=0
            )

            print(f"📦 [MAVLink PACKET] Lat: {lat:.5f} | Lon: {lon:.5f} | İrtifa: {alt_m:.1f}m | Batarya: %{battery_pct:.1f}")
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n🛑 [MAVLink SITL] Sanal otopilot yayını durduruldu.")

if __name__ == "__main__":
    run_mavlink_sitl()