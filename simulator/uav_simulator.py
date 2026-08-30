import math
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any


class UAVPhysicsSimulator:
    """
    Savunma sanayii standartlarında otonom İHA uçuş ve telemetri simülatörü.
    """
    def __init__(
        self,
        uav_id: str = "BAYRAKTAR-TB2-01",
        start_lat: float = 40.7654,
        start_lon: float = 29.9408,
        start_alt: float = 500.0
    ):
        self.uav_id = uav_id
        self.latitude = start_lat
        self.longitude = start_lon
        self.altitude = start_alt
        
        self.speed = 120.0  # km/h
        self.heading = 45.0  # Pusula yönü (0-360 derece)
        self.battery = 100.0  # Yüzde (%)
        self.temperature = 35.0  # Aviyonik / Motor sıcaklığı (°C)
        self.status = "NORMAL"
        
        # Uçuş profili hedefleri
        self.target_altitude = 2500.0
        self.is_climbing = True

    def _update_kinematics(self, dt: float = 1.0):
        """
        Zamana bağlı kinematik hareket ve GPS gürültüsü (noise) hesaplaması.
        """
        distance_km = (self.speed / 3600.0) * dt
        lat_step = (distance_km / 111.0) * math.cos(math.radians(self.heading))
        lon_step = (distance_km / (111.0 * math.cos(math.radians(self.latitude)))) * math.sin(math.radians(self.heading))

        # Gauss GPS sapması (~2 metre)
        gps_noise_lat = random.gauss(0, 0.00002)
        gps_noise_lon = random.gauss(0, 0.00002)

        self.latitude += lat_step + gps_noise_lat
        self.longitude += lon_step + gps_noise_lon

        # Pusula yönünde doğal salınım
        self.heading = (self.heading + random.uniform(-1.5, 1.5)) % 360.0

    def _update_avionics(self, dt: float = 1.0):
        """
        İrtifa tırmanışı, dinamik batarya tüketimi ve motor ısı dengesi.
        """
        if self.is_climbing:
            climb_rate = 8.0 * dt  # 8 m/s tırmanış
            self.altitude += climb_rate
            if self.altitude >= self.target_altitude:
                self.is_climbing = False
        else:
            self.altitude += random.uniform(-1.0, 1.0)

        # Batarya tüketimi
        drain_rate = 0.03 if self.is_climbing else 0.01
        self.battery = max(0.0, self.battery - (drain_rate * dt))

        # Isıl dinamik
        target_temp = 55.0 if self.is_climbing else 42.0
        self.temperature += (target_temp - self.temperature) * 0.05 + random.uniform(-0.2, 0.2)

        # Uçuş emniyet durum makinesi (FSM)
        if self.battery < 15.0 or self.temperature > 75.0:
            self.status = "CRITICAL"
        elif self.battery < 30.0 or self.temperature > 60.0:
            self.status = "WARNING"
        else:
            self.status = "NORMAL"

    def generate_telemetry_packet(self, dt: float = 1.0) -> Dict[str, Any]:
        """
        Bir saniyelik uçuş çevrimini simüle eder ve telemetri JSON paketi üretir.
        """
        self._update_kinematics(dt)
        self._update_avionics(dt)

        return {
            "uav_id": self.uav_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 2),
            "speed": round(self.speed + random.uniform(-1.0, 1.0), 2),
            "battery": round(self.battery, 2),
            "temperature": round(self.temperature, 2),
            "heading": round(self.heading, 1),
            "status": self.status
        }