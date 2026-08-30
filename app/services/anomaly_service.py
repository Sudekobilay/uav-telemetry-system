import math
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.telemetry import TelemetryPayload
from app.models.telemetry import TelemetryAlert

# Geofence Tanımı (Kocaeli Cengiz Topel Merkezli, 45 km Yarıçap Sınırı)
GEOFENCE_CENTER_LAT = 40.7350
GEOFENCE_CENTER_LON = 30.0833
GEOFENCE_MAX_RADIUS_KM = 45.0


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki GPS koordinatı arasındaki mesafeyi Haversine formülü ile km cinsinden hesaplar.
    """
    r = 6371.0  # Dünya yarıçapı (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


async def evaluate_flight_safety(payload: TelemetryPayload, session_id: int, db: AsyncSession) -> List[dict]:
    """
    Gelen telemetri verisini güvenlik kuralları süzgecinden geçirir.
    İhlal varsa veritabanına kaydeder ve üretilen alarmları döner.
    """
    alerts = []

    # 1. Geofence Kontrolü
    distance = calculate_distance_km(GEOFENCE_CENTER_LAT, GEOFENCE_CENTER_LON, payload.latitude, payload.longitude)
    if distance > GEOFENCE_MAX_RADIUS_KM:
        alerts.append({
            "uav_id": payload.uav_id,
            "alert_type": "GEOFENCE_BREACH",
            "severity": "CRITICAL",
            "message": f"Sanal sınır aşıldı! Merkezden mesafe: {distance:.1f} km (Maks Limit: {GEOFENCE_MAX_RADIUS_KM} km)"
        })

    # 2. Kritik Batarya Kontrolü (< %20)
    if payload.battery < 20.0:
        alerts.append({
            "uav_id": payload.uav_id,
            "alert_type": "LOW_BATTERY",
            "severity": "CRITICAL" if payload.battery < 10.0 else "WARNING",
            "message": f"Kritik batarya seviyesi: %{payload.battery:.1f} (Acil iniş planlayın)"
        })

    # 3. Aşırı Aviyonik Sıcaklık Kontrolü (> 45°C)
    if payload.temperature > 45.0:
        alerts.append({
            "uav_id": payload.uav_id,
            "alert_type": "OVERHEAT",
            "severity": "WARNING",
            "message": f"Yüksek aviyonik sıcaklığı: {payload.temperature:.1f}°C"
        })

    # 4. Kritik Düşük İrtifa Kontrolü (< 800m)
    if payload.altitude < 800.0:
        alerts.append({
            "uav_id": payload.uav_id,
            "alert_type": "LOW_ALTITUDE",
            "severity": "WARNING",
            "message": f"Düşük irtifa uyarısı: {payload.altitude:.1f} m"
        })

    # Tespit edilen alarmları DB'ye kalıcı olarak kaydet
    for alert_data in alerts:
        db_alert = TelemetryAlert(
            session_id=session_id,
            uav_id=alert_data["uav_id"],
            alert_type=alert_data["alert_type"],
            severity=alert_data["severity"],
            message=alert_data["message"]
        )
        db.add(db_alert)

    if alerts:
        await db.commit()

    return alerts