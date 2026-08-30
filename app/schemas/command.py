from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    RTH = "RTH"                    # Return to Home (Kalkış Üssüne Dön)
    LOITER = "LOITER"              # Havada Sabit Daire Çiz / Bekle
    LAND = "LAND"                  # Acil İniş Yap
    SET_ALTITUDE = "SET_ALTITUDE"  # İrtifa Değiştir
    RESUME_MISSION = "RESUME"      # Normal Göreve Devam Et


class TelecommandPayload(BaseModel):
    uav_id: str = Field(..., description="Komutun iletileceği hedef İHA çağrı adı")
    command_type: CommandType = Field(..., description="Gönderilecek C2 komutu")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Ek parametreler (örn: hedef irtifa)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "uav_id": "BAYRAKTAR-TB2-01",
                "command_type": "RTH",
                "parameters": {}
            }
        }
    }