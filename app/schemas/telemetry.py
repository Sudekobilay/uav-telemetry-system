# Guvenlık ve Dogrulama Fıltresı
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

#Basemodel'den mıras alarak bu sınıfı bır pydantıc modelıne donustur
class TelemetryPayload(BaseModel):
    """
    İHA'dan gelen anlık telemetri verisinin doğrulama şeması.
    """
    #IHA Kımlıgı
    uav_id: str = Field(..., description="İHA Çağrı Adı / Benzersiz Kimliği (Örn: UAV-01)")
    #zaman gonderılmezse otomatık UTC saatı basılır
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Telemetri zaman damgası")
    # Enlem degerı
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Enlem koordinatı (-90 ile +90)")
    #Boylam degerı
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Boylam koordinatı (-180 ile +180)")
    #İrtifa 0'ın altına ınemez 
    altitude: float = Field(..., ge=0.0, description="Deniz seviyesi irtifası (metre)")
    speed: float = Field(..., ge=0.0, description="Yer hızı (km/h)")
    battery: float = Field(..., ge=0.0, le=100.0, description="Kalan batarya yüzdesi (%0-100)")
    #Aviyonik sıcaklık degerı 
    temperature: float = Field(..., description="Aviyonik/Motor sıcaklığı (°C)")
    #Pusula yon acısı
    heading: float = Field(..., ge=0.0, le=360.0, description="Pusula yön açısı (0-360 derece)")
    status: Optional[str] = Field(default="NORMAL", description="Uçuş durumu (NORMAL, WARNING, CRITICAL)")

   #Hazır JSON şablonu
    class Config:
        json_schema_extra = {
            "example": {
                "uav_id": "UAV-01",
                "timestamp": "2026-08-29T17:45:00",
                "latitude": 40.7654,
                "longitude": 29.9408,
                "altitude": 520.5,
                "speed": 95.2,
                "battery": 88.0,
                "temperature": 42.3,
                "heading": 180.0,
                "status": "NORMAL"
            }
        }