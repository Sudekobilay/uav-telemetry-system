from typing import List
from fastapi import WebSocket
import json

class ConnectionManager:
    """
    FastAPI üzerinde açık olan tüm WebSocket istemcilerini (tarayıcıları)
    yöneten ve canlı veri dağıtımı (broadcast) yapan servis.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🌐 [WEBSOCKET] Yeni bir yer istasyonu bağlandı. Toplam İstemci: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 [WEBSOCKET] İstemci ayrıldı. Kalan İstemci: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Gelen telemetri paketini bağlı tüm harita ve dashboard istemcilerine anında iletir.
        """
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected_clients.append(connection)

        # Hata veren (kapanmış) istemcileri listeden temizle
        for dead_client in disconnected_clients:
            self.disconnect(dead_client)

# Tekil (Singleton) yönetici örneği
ws_manager = ConnectionManager()