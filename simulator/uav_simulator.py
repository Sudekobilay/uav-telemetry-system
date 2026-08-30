import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any


class UAVPhysicsSimulator:
    """
    Savunma sanayii standartlarında otonom İHA uçuş, C2 telecommand ve telemetri simülatörü.
    """
    def __init__(
        self,
        uav_id: str = "BAYRAKTAR-TB2-01",
        start_lat: float = 40.7654,
        start_lon: float = 29.9408,
        start_alt: float = 500.0
    ):
        self.uav_id = uav_id
        self.home_lat = start_lat
        self.home_lon = start_lon
        
        self.latitude = start_lat
        self.longitude = start_lon
        self.altitude = start_alt
        
        self.speed = 120.0  # km/h
        self.heading = random.uniform(0.0, 360.0)  # Pusula yönü (0-360 derece)
        self.battery = 100.0  # Yüzde (%)
        self.temperature = 35.0  # Aviyonik / Motor sıcaklığı (°C)
        self.status = "NORMAL"  # NORMAL, RTH, LOITER, LANDING, LANDED, WARNING, CRITICAL
        
        # PFD Uçuş Dinamikleri (Glass Cockpit)
        self.roll = 0.0   # Derece (-30° sağ / +30° sol yatış)
        self.pitch = 0.0  # Derece (-15° alçalış / +15° tırmanış)
        
        # Uçuş profili hedefleri & C2 Modları
        self.target_altitude = 2500.0
        self.is_climbing = True
        self.flight_mode = "MISSION"  # MISSION, RTH, LOITER, LAND

    def process_command(self, command_type: str, params: dict = None):
        """
        GCS'ten gelen C2 Telekomutunu (Uplink) işler ve uçuş modunu değiştirir.
        """
        print(f"🎯 [{self.uav_id}] C2 Komutu Alındı: {command_type}")
        if command_type == "RTH":
            self.flight_mode = "RTH"
            self.status = "RTH"
        elif command_type == "LOITER":
            self.flight_mode = "LOITER"
            self.status = "LOITER"
        elif command_type == "LAND":
            self.flight_mode = "LAND"
            self.status = "LANDING"
        elif command_type == "RESUME":
            self.flight_mode = "MISSION"
            self.status = "NORMAL"

    def _calculate_bearing_to(self, target_lat: float, target_lon: float) -> float:
        """
        İki koordinat arasındaki pusula açısını (bearing) küresel trigonometri ile hesaplar.
        """
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(target_lat)
        diff_lon = math.radians(target_lon - self.longitude)

        x = math.sin(diff_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_lon))
        initial_bearing = math.atan2(x, y)
        return (math.degrees(initial_bearing) + 360.0) % 360.0

    def _update_kinematics(self, dt: float = 1.0):
        """
        Uçuş moduna göre yön, otopilot açı dönüşü, Roll açısı ve haritada net ilerleme adımı hesaplar.
        """
        turn_rate = 0.0

        if self.flight_mode == "RTH":
            # Kalkış üssüne (Home) yönel
            target_heading = self._calculate_bearing_to(self.home_lat, self.home_lon)
            diff = (target_heading - self.heading + 180.0) % 360.0 - 180.0
            turn_rate = max(-4.0, min(4.0, diff * 0.2))
            self.heading = (self.heading + turn_rate) % 360.0

        elif self.flight_mode == "LOITER":
            # Havada sabit daire çiz (bekleme paterni)
            turn_rate = 4.0  # Sabit 4°/sn dönüş
            self.heading = (self.heading + turn_rate) % 360.0

        elif self.flight_mode == "LAND":
            # İniş rotasında sabit devam et
            turn_rate = 0.0

        else:  # MISSION (Normal otonom devriye)
            # Her saniye sağa-sola zikzak yapmaması için nadir ve kararlı rota sapması
            if random.random() < 0.12:
                turn_rate = random.uniform(-6.0, 6.0)
                self.heading = (self.heading + turn_rate) % 360.0

        # Roll Dinamiği (Dönüş açısına göre kanat yatışı)
        target_roll = turn_rate * 6.0
        self.roll += (target_roll - self.roll) * 0.35

        # RADARDA VE HARİTADA İLERLEMEYİ NET GÖRMEK İÇİN KİNEMATİK ADIM:
        # Saniyede ~0.0055 derece (~600m) belirgin koordinat ötelenmesi
        visual_step_deg = 0.0055 * dt
        heading_rad = math.radians(self.heading)

        lat_step = visual_step_deg * math.cos(heading_rad)
        lon_step = visual_step_deg * math.sin(heading_rad) / math.cos(math.radians(self.latitude))

        self.latitude += lat_step
        self.longitude += lon_step

    def _update_avionics(self, dt: float = 1.0):
        """
        Uçuş moduna göre irtifa, batarya, motor sıcaklığı ve Pitch açısını yönetir.
        """
        if self.flight_mode == "LAND":
            # Kademeli iniş protokolü (6 m/s alçalış)
            self.altitude = max(0.0, self.altitude - 6.0 * dt)
            target_pitch = -4.0
            if self.altitude <= 5.0:
                self.speed = 0.0
                self.status = "LANDED"
        elif self.is_climbing and self.flight_mode == "MISSION":
            climb_rate = 8.0 * dt
            self.altitude += climb_rate
            target_pitch = 6.5
            if self.altitude >= self.target_altitude:
                self.is_climbing = False
        else:
            altitude_delta = random.uniform(-0.5, 0.5)
            self.altitude += altitude_delta
            target_pitch = altitude_delta * 2.0

        # Yumuşak Pitch geçişi
        self.pitch += (target_pitch - self.pitch) * 0.3

        # Batarya tüketimi
        drain_rate = 0.03 if self.is_climbing else 0.01
        self.battery = max(0.0, self.battery - (drain_rate * dt))

        # Isıl dinamik
        target_temp = 55.0 if self.is_climbing else 42.0
        self.temperature += (target_temp - self.temperature) * 0.05 + random.uniform(-0.2, 0.2)

        # Durum denetimi (C2 özel modunda değilse FSM işlet)
        if self.flight_mode not in ["RTH", "LOITER", "LAND"]:
            if self.battery < 15.0 or self.temperature > 75.0:
                self.status = "CRITICAL"
            elif self.battery < 30.0 or self.temperature > 60.0:
                self.status = "WARNING"
            else:
                self.status = "NORMAL"

    def generate_telemetry_packet(self, dt: float = 1.0) -> Dict[str, Any]:
        """
        Bir saniyelik çevrim işletip PFD ve C2 destekli telemetri paketi döner.
        """
        self._update_kinematics(dt)
        self._update_avionics(dt)

        return {
            "uav_id": self.uav_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 2),
            "speed": round(self.speed + random.uniform(-0.5, 0.5), 2),
            "battery": round(self.battery, 2),
            "temperature": round(self.temperature, 2),
            "heading": round(self.heading, 1),
            "roll": round(self.roll, 1),
            "pitch": round(self.pitch, 1),
            "status": self.status
        }