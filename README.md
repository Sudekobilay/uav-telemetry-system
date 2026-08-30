# 🛰️ UAV Ground Control Station (GCS) & Telemetry System

**Gerçek Zamanlı İHA Telemetri Takip, MAVLink Köprüsü ve Güvenlik İstasyonu**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL_8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MQTT](https://img.shields.io/badge/Mosquitto_MQTT-660066?style=flat-square&logo=eclipse-mosquitto&logoColor=white)](https://mosquitto.org/)
[![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📌 Genel Bakış

Savunma sanayii ve havacılık standartlarında geliştirilmiş; **MAVLink** ikili protokolü, **MQTT** mesaj kuyrukları ve **WebSocket** ile sıfır gecikmeli çoklu İHA takibi sağlayan Yer Kontrol İstasyonu (GCS) mimarisi.

---

## 🏗️ Mimari & Veri Akışı

```text
[ ArduPilot / MAVLink SITL ] (UDP 14550)
            │
            ▼
[ MAVLink ➔ MQTT Bridge ] ──(telemetry/+/data)──► [ Mosquitto Broker ]
                                                            │
                                                            ▼
                                              [ FastAPI Backend ]
                                              ├── Async ORM (MySQL 8.0)
                                              ├── Geofencing & Güvenlik Motoru
                                              └── WebSocket Broadcast
                                                            │
                                                            ▼
                                              [ Leaflet.js Radar Dashboard ]
✨ Temel Özellikler
MAVLink Entegrasyonu: Otopilot ikili paketlerini (HEARTBEAT, ATTITUDE vb.) canlı ayrıştırma.

Dinamik Hava Sahası: Havalanan araçları anında keşfetme, sinyali kesilenleri (6 sn) haritadan otomatik kaldırma.

Uçuş Güvenliği & Geofencing: 45 km yarıçaplı sanal çit ihlali, kritik batarya (<%20) ve aşırı sıcaklık (>45°C) alarmları.

Kara Kutu (Replay API): Geçmiş uçuş oturumlarını zaman sıralı yeniden oynatma.

Konteynerleştirme: Docker Compose ile tüm servisleri tek tuşla başlatma.

🚀 Hızlı Başlangıç
1. Docker Compose ile Çalıştırma
Bash
git clone [https://github.com/kullanici-adiniz/uav-telemetry-system.git](https://github.com/kullanici-adiniz/uav-telemetry-system.git)
cd uav-telemetry-system

docker compose up --build -d
2. Yerel Geliştirme (Local)
Bash
# 1. Bağımlılıkları kur ve sunucuyu aç
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2. Dinamik Hava Trafiği Simülatörünü Başlat (Ayrı Terminal)
python -m simulator.airspace_traffic_generator
🌐 Servis Bağlantıları
GCS Radar Dashboard: http://localhost:8000/dashboard

Swagger API Dokümantasyonu: http://localhost:8000/docs

Kara Kutu Replay Uç Noktası: GET /api/v1/telemetry/replay/{session_code}

Canlı WebSocket Akışı: ws://localhost:8000/ws/telemetry

🛠️ Teknoloji Yığını
Backend & API: FastAPI, Python 3.11, Pydantic V2, Uvicorn

Veritabanı & ORM: MySQL 8.0, SQLAlchemy 2.0 (Async), aiomysql

Mesajlaşma & Dağıtım: Eclipse Mosquitto (MQTT), aiomqtt, WebSockets

Havacılık & Frontend: pymavlink, Leaflet.js, Docker Compose