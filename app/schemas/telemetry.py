# Güvenlik ve Doğrulama Filtresi
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


# BaseModel'den miras alarak bu sınıfı bir pydantic modeline dönüştür
class TelemetryPayload(BaseModel):
    """
    İHA'dan gelen anlık telemetri verisinin doğrulama şeması.
    """
    # İHA Kimliği
    uav_id: str = Field(..., description="İHA Çağrı Adı / Benzersiz Kimliği (Örn: UAV-01)")
    # Zaman gönderilmezse otomatik UTC saati basılır
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Telemetri zaman damgası"
    )
    # Enlem değeri
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Enlem koordinatı (-90 ile +90)")
    # Boylam değeri
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Boylam koordinatı (-180 ile +180)")
    # İrtifa 0'ın altına inemez 
    altitude: float = Field(..., ge=0.0, description="Deniz seviyesi irtifası (metre)")
    speed: float = Field(..., ge=0.0, description="Yer hızı (km/h veya m/s)")
    battery: float = Field(..., ge=0.0, le=100.0, description="Kalan batarya yüzdesi (%0-100)")
    # Aviyonik sıcaklık değeri 
    temperature: float = Field(..., description="Aviyonik/Motor sıcaklığı (°C)")
    # Pusula yön açısı
    heading: float = Field(..., ge=0.0, le=360.0, description="Pusula yön açısı (0-360 derece)")
    # Glass Cockpit / PFD Uçuş Dinamikleri
    roll: Optional[float] = Field(default=0.0, description="Yatış açısı - Roll (-180 ile +180 derece)")
    pitch: Optional[float] = Field(default=0.0, description="Yunuslama açısı - Pitch (-90 ile +90 derece)")
    status: Optional[str] = Field(default="NORMAL", description="Uçuş durumu (NORMAL, WARNING, CRITICAL)")

    # Hazır JSON şablonu (Pydantic V2 uyumlu)
    model_config = {
        "json_schema_extra": {
            "example": {
                "uav_id": "UAV-01",
                "timestamp": "2026-08-30T17:45:00Z",
                "latitude": 40.7654,
                "longitude": 29.9408,
                "altitude": 520.5,
                "speed": 95.2,
                "battery": 88.0,
                "temperature": 42.3,
                "heading": 180.0,
                "roll": -4.5,
                "pitch": 2.1,
                "status": "NORMAL"
            }
        }
    }