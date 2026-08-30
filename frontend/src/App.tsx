import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Crosshair, Clock, ShieldAlert, Plane, Home, RefreshCw, PlaneLanding, Play } from 'lucide-react';
import type { TelemetryPacket, AlertPacket } from './types/telemetry';

export const App: React.FC = () => {
  const [fleet, setFleet] = useState<Record<string, TelemetryPacket>>({});
  const [alerts, setAlerts] = useState<AlertPacket[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [utcTime, setUtcTime] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [c2Status, setC2Status] = useState('İHA SEÇİMİ BEKLENİYOR');

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Record<string, L.Marker>>({});
  const polylinesRef = useRef<Record<string, L.Polyline>>({});

  // UTC Saat
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setUtcTime(now.toUTCString().substring(17, 25));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // WebSocket Entegrasyonu
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
    const socket = new WebSocket(`${protocol}//${host}/ws/telemetry`);

    socket.onopen = () => setIsConnected(true);
    socket.onclose = () => setIsConnected(false);

    socket.onmessage = (event) => {
      const packet = JSON.parse(event.data);
      if (packet.uav_id) {
        setFleet((prev) => {
          const next = { ...prev, [packet.uav_id]: packet };
          if (!selectedId) {
            setSelectedId(packet.uav_id);
            setC2Status(`${packet.uav_id} BAĞLANDI`);
          }
          return next;
        });
      } else if (packet.type === 'ALERT') {
        setAlerts((prev) => [packet, ...prev.slice(0, 19)]);
      }
    };

    return () => socket.close();
  }, [selectedId]);

  // Leaflet Harita Başlatma (Güvenli DOM Kontrolü)
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, { attributionControl: false }).setView([40.7350, 30.0833], 9);
    
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 18,
    }).addTo(map);

    L.circle([40.7350, 30.0833], {
      radius: 45000,
      color: '#6c94b8',
      weight: 1,
      dashArray: '4, 6',
      fillColor: '#6c94b8',
      fillOpacity: 0.03,
    }).addTo(map);

    mapRef.current = map;

    // Harita oturduktan sonra boyutunu güncelle
    setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Harita Marker Güncellemeleri
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    Object.values(fleet).forEach((uav) => {
      const latLng: [number, number] = [uav.latitude, uav.longitude];
      const isSelected = uav.uav_id === selectedId;
      const isWarn = uav.status === 'CRITICAL' || uav.status === 'WARNING';
      const color = isSelected ? '#b89c68' : isWarn ? '#9e4444' : '#6c94b8';

      if (!markersRef.current[uav.uav_id]) {
        const icon = L.divIcon({
          className: 'custom-uav-icon',
          html: `<div style="transform: rotate(${uav.heading - 45}deg); color: ${color}; font-size: 16px; transition: transform 0.3s ease;">
                  ✈
                 </div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        });

        const marker = L.marker(latLng, { icon })
          .addTo(map)
          .on('click', () => {
            setSelectedId(uav.uav_id);
            setC2Status(`${uav.uav_id} BAĞLANDI`);
          });

        const polyline = L.polyline([latLng], { color, weight: 1.2, opacity: 0.5, dashArray: '2, 4' }).addTo(map);

        markersRef.current[uav.uav_id] = marker;
        polylinesRef.current[uav.uav_id] = polyline;
      } else {
        const marker = markersRef.current[uav.uav_id];
        const polyline = polylinesRef.current[uav.uav_id];

        marker.setLatLng(latLng);
        polyline.addLatLng(latLng);

        const iconEl = marker.getElement()?.firstElementChild as HTMLElement;
        if (iconEl) {
          iconEl.style.transform = `rotate(${uav.heading - 45}deg)`;
          iconEl.style.color = color;
        }
      }
    });
  }, [fleet, selectedId]);

  const selectedUav = selectedId ? fleet[selectedId] : null;
  const roll = selectedUav?.roll ?? 0;
  const pitch = selectedUav?.pitch ?? 0;
  const heading = selectedUav?.heading ?? 0;

  const sendCommand = async (type: string) => {
    if (!selectedId) return;
    setC2Status(`${type} İLETİLİYOR...`);
    try {
      const res = await fetch('/api/v1/commands/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uav_id: selectedId, command_type: type, parameters: {} })
      });
      if (res.ok) setC2Status(`[ONAYLANDI] ${type}`);
      else setC2Status(`[HATA] Reddedildi`);
    } catch {
      setC2Status('[BAĞLANTI HATASI]');
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', backgroundColor: '#0a0c10', color: '#b2bac2', fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden', userSelect: 'none' }}>
      
      {/* ÜST HEADER */}
      <header style={{ height: '42px', minHeight: '42px', backgroundColor: '#0f131a', borderBottom: '1px solid #1e2633', padding: '0 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 1000 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Crosshair size={16} color="#6c94b8" />
          <h1 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e6edf3', letterSpacing: '0.3px' }}>İHA HAREKÂT KONTROL MERKEZİ & TAKTİK C2</h1>
          <span style={{ fontSize: '0.55rem', color: '#606d7d', fontFamily: 'JetBrains Mono, monospace', marginLeft: '10px' }}>SYS_VER: 3.0.0 | SECURE GCS</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem', color: '#b89c68' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={12} color="#606d7d" />
            <span>{utcTime || '17:42:14'}</span>
            <span style={{ fontSize: '9px', color: '#606d7d', border: '1px solid #1e2633', padding: '1px 3px', borderRadius: '2px' }}>UTC/ZULU</span>
          </div>
          <span style={{ fontSize: '9px', color: '#606d7d', border: '1px solid #1e2633', padding: '1px 3px', borderRadius: '2px' }}>WGS-84</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.68rem' }}>
          <span style={{ color: '#606d7d' }}>LINK PING: <span style={{ color: '#488255', fontWeight: 600 }}>14ms</span></span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: isConnected ? '#111a13' : '#1a1212', color: isConnected ? '#488255' : '#9e4444', border: `1px solid ${isConnected ? '#1f3323' : '#361f1f'}`, padding: '3px 8px', borderRadius: '2px', fontWeight: 600 }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: 'currentColor' }} />
            <span>{isConnected ? 'C2 & TELEMETRİ AKTİF' : 'BAĞLANTI KESİLDİ'}</span>
          </div>
        </div>
      </header>

      {/* ANA İZGARA */}
      <div style={{ display: 'grid', gridTemplateColumns: '290px 1fr 370px', width: '100%', flex: 1, overflow: 'hidden', position: 'relative' }}>
        
        {/* SOL: FİLO TABLOSU */}
        <div style={{ backgroundColor: '#0f131a', borderRight: '1px solid #1e2633', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', zIndex: 10 }}>
          <div style={{ padding: '8px 10px', borderBottom: '1px solid #1e2633', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0b0e14' }}>
            <span style={{ fontSize: '0.65rem', color: '#606d7d', fontWeight: 600 }}>AKTİF HAVA UNSURLARI</span>
            <span style={{ fontSize: '0.62rem', fontFamily: 'JetBrains Mono, monospace', color: '#6c94b8', backgroundColor: '#121721', padding: '1px 5px', borderRadius: '2px', border: '1px solid #1e2633' }}>
              {Object.keys(fleet).length} ARAÇ
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '18px 1fr 55px 40px', gap: '6px', padding: '5px 10px', backgroundColor: '#0d1118', borderBottom: '1px solid #1e2633', fontSize: '0.6rem', color: '#606d7d', fontWeight: 600 }}>
            <span />
            <span>ÇAĞRI KODU</span>
            <span style={{ textAlign: 'right' }}>İRTİFA</span>
            <span style={{ textAlign: 'center' }}>MOD</span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {Object.keys(fleet).length === 0 ? (
              <div style={{ padding: '15px', textAlign: 'center', fontSize: '0.65rem', color: '#606d7d' }}>Hava araçları bekleniyor...</div>
            ) : (
              Object.values(fleet).map((uav) => {
                const isSelected = selectedId === uav.uav_id;
                const isWarn = uav.status === 'CRITICAL' || uav.status === 'WARNING';

                return (
                  <div
                    key={uav.uav_id}
                    onClick={() => {
                      setSelectedId(uav.uav_id);
                      setC2Status(`${uav.uav_id} BAĞLANDI`);
                      if (mapRef.current) mapRef.current.panTo([uav.latitude, uav.longitude]);
                    }}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '18px 1fr 55px 40px',
                      gap: '6px',
                      padding: '6px 10px',
                      borderBottom: '1px solid #141a24',
                      backgroundColor: isSelected ? '#242e3f' : isWarn ? '#1c1414' : '#151a24',
                      borderLeft: isSelected ? '2px solid #b89c68' : isWarn ? '2px solid #9e4444' : 'none',
                      cursor: 'pointer',
                      alignItems: 'center',
                      fontSize: '0.7rem'
                    }}
                  >
                    <Plane size={11} color={isSelected ? '#b89c68' : isWarn ? '#9e4444' : '#6c94b8'} />
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: isSelected ? 600 : 500, color: isSelected ? '#e6edf3' : '#b2bac2', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{uav.uav_id}</span>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', textAlign: 'right', color: '#606d7d' }}>{Math.round(uav.altitude)}m</span>
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.58rem', textAlign: 'center', padding: '1px 3px', borderRadius: '2px', backgroundColor: isWarn ? '#2b1717' : '#1a222f', color: isWarn ? '#9e4444' : '#6c94b8', fontWeight: 600 }}>
                      {uav.status === 'NORMAL' ? 'NAV' : uav.status.substring(0, 3)}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ORTA: HARİTA (Mutlak Konumlandırma ile Kararma Sorunu Çözüldü) */}
        <div style={{ position: 'relative', width: '100%', height: '100%', backgroundColor: '#000' }}>
          <div ref={mapContainerRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', zIndex: 1 }} />
        </div>

        {/* SAĞ: TAKTİK PANEL */}
        <div style={{ backgroundColor: '#0f131a', borderLeft: '1px solid #1e2633', padding: '8px', display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', zIndex: 10, height: '100%' }}>
          
          {/* PFD GÖSTERGESİ */}
          <div style={{ backgroundColor: '#151a24', border: '1px solid #2c374a', borderRadius: '2px', padding: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.68rem', fontWeight: 600, color: '#e6edf3', marginBottom: '4px', paddingBottom: '3px', borderBottom: '1px solid #1e2633' }}>
              <span>{selectedUav?.uav_id || 'HAVA ARACI SEÇİLMEDİ'}</span>
              <span style={{ color: '#b89c68' }}>R:{roll.toFixed(1)}° P:{pitch.toFixed(1)}°</span>
            </div>

            <div style={{ width: '100%', height: '150px', borderRadius: '2px', overflow: 'hidden', position: 'relative', border: '1px solid #1e2633', backgroundColor: '#10151f' }}>
              <div style={{ width: '500px', height: '500px', position: 'absolute', top: '-175px', left: '-75px', transform: `rotate(${-roll}deg) translateY(${pitch * 1.8}px)`, transition: 'transform 0.1s linear' }}>
                <div style={{ height: '250px', backgroundColor: '#131d2b' }} />
                <div style={{ height: '250px', backgroundColor: '#261c16', borderTop: '1px solid #707e8c' }} />
              </div>

              {/* Sol Hız */}
              <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '40px', backgroundColor: 'rgba(13, 17, 24, 0.94)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', fontFamily: 'JetBrains Mono, monospace', zIndex: 6, borderRight: '1px solid #1e2633' }}>
                <span style={{ fontSize: '0.48rem', color: '#606d7d' }}>IAS</span>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#488255' }}>{selectedUav ? Math.round(selectedUav.speed) : '--'}</span>
                <span style={{ fontSize: '0.48rem', color: '#606d7d' }}>km/h</span>
              </div>

              {/* Sağ İrtifa */}
              <div style={{ position: 'absolute', top: 0, bottom: 0, right: 0, width: '40px', backgroundColor: 'rgba(13, 17, 24, 0.94)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', fontFamily: 'JetBrains Mono, monospace', zIndex: 6, borderLeft: '1px solid #1e2633' }}>
                <span style={{ fontSize: '0.48rem', color: '#606d7d' }}>ALT</span>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#6c94b8' }}>{selectedUav ? Math.round(selectedUav.altitude) : '--'}</span>
                <span style={{ fontSize: '0.48rem', color: '#606d7d' }}>m</span>
              </div>

              {/* Nişangah */}
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none', zIndex: 10 }}>
                <svg style={{ width: '80px', height: '25px' }} viewBox="0 0 120 40">
                  <path d="M 20 20 L 45 20 L 45 25" stroke="#b89c68" strokeWidth="1.5" fill="none" />
                  <circle cx="60" cy="20" r="2.5" fill="#b89c68" />
                  <path d="M 75 25 L 75 20 L 100 20" stroke="#b89c68" strokeWidth="1.5" fill="none" />
                </svg>
              </div>
            </div>
          </div>

          {/* C2 KOMUTA KONTROL */}
          <div style={{ backgroundColor: '#151a24', border: '1px solid #1e2633', borderRadius: '2px', padding: '6px 8px' }}>
            <div style={{ fontSize: '0.62rem', color: '#606d7d', fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '4px', marginBottom: '4px', borderBottom: '1px solid #1e2633' }}>
              <span>C2 KOMUTA KONTROL</span>
              <span style={{ color: '#488255', fontSize: '0.55rem', fontFamily: 'JetBrains Mono, monospace' }}>UPLINK HAZIR</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
              <button onClick={() => sendCommand('RTH')} disabled={!selectedId} style={{ padding: '7px 4px', border: '1px solid #1e2633', borderRadius: '2px', fontSize: '0.65rem', fontWeight: 500, cursor: selectedId ? 'pointer' : 'not-allowed', opacity: selectedId ? 1 : 0.4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#6c94b8', backgroundColor: '#0d1117' }}>
                <Home size={11} /> RTH (ÜSSE DÖN)
              </button>
              <button onClick={() => sendCommand('LOITER')} disabled={!selectedId} style={{ padding: '7px 4px', border: '1px solid #1e2633', borderRadius: '2px', fontSize: '0.65rem', fontWeight: 500, cursor: selectedId ? 'pointer' : 'not-allowed', opacity: selectedId ? 1 : 0.4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#b89c68', backgroundColor: '#0d1117' }}>
                <RefreshCw size={11} /> LOITER (BEKLE)
              </button>
              <button onClick={() => sendCommand('LAND')} disabled={!selectedId} style={{ padding: '7px 4px', border: '1px solid #1e2633', borderRadius: '2px', fontSize: '0.65rem', fontWeight: 500, cursor: selectedId ? 'pointer' : 'not-allowed', opacity: selectedId ? 1 : 0.4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#9e4444', backgroundColor: '#0d1117' }}>
                <PlaneLanding size={11} /> ACİL İNİŞ
              </button>
              <button onClick={() => sendCommand('RESUME')} disabled={!selectedId} style={{ padding: '7px 4px', border: '1px solid #1e2633', borderRadius: '2px', fontSize: '0.65rem', fontWeight: 500, cursor: selectedId ? 'pointer' : 'not-allowed', opacity: selectedId ? 1 : 0.4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#488255', backgroundColor: '#0d1117' }}>
                <Play size={11} /> GÖREVE DEVAM
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0d1117', padding: '4px 6px', borderRadius: '2px', border: '1px solid #1e2633', marginTop: '4px', fontSize: '0.6rem', fontFamily: 'JetBrains Mono, monospace' }}>
              <span style={{ color: '#606d7d' }}>DURUM:</span>
              <span style={{ color: '#6c94b8', fontWeight: 600 }}>{selectedId ? c2Status : 'İHA SEÇİMİ BEKLENİYOR'}</span>
            </div>
          </div>

          {/* AVİYONİK VERİ & PUSULA */}
          <div style={{ backgroundColor: '#151a24', border: '1px solid #1e2633', borderRadius: '2px', padding: '6px 8px' }}>
            <div style={{ fontSize: '0.62rem', color: '#606d7d', fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '4px', marginBottom: '4px', borderBottom: '1px solid #1e2633' }}>
              <span>AVİYONİK VERİ</span>
              <span style={{ color: '#b89c68', fontSize: '0.6rem', fontFamily: 'JetBrains Mono, monospace' }}>{selectedUav?.status || 'NORMAL'}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '6px' }}>
              <div style={{ backgroundColor: '#0d1117', border: '1px solid #1e2633', borderRadius: '2px', padding: '4px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', border: '1px solid #2c374a', backgroundColor: '#0b0e14', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', transform: `rotate(${-heading}deg)`, transition: 'transform 0.2s linear' }}>
                  <div style={{ width: 0, height: 0, borderLeft: '3px solid transparent', borderRight: '3px solid transparent', borderBottom: '10px solid #9e4444', position: 'absolute', top: '2px' }} />
                </div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', fontWeight: 600, color: '#6c94b8', marginTop: '2px' }}>{Math.round(heading)}°</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                <div style={{ backgroundColor: '#0d1117', border: '1px solid #1e2633', borderRadius: '2px', padding: '3px 6px' }}>
                  <div style={{ fontSize: '0.52rem', color: '#606d7d', fontWeight: 500 }}>BATARYA</div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.78rem', fontWeight: 600, color: '#e6edf3', marginTop: '1px' }}>{selectedUav?.battery?.toFixed(1) ?? '--'}%</div>
                  <div style={{ width: '100%', height: '3px', backgroundColor: '#1b222d', borderRadius: '1px', overflow: 'hidden', marginTop: '3px' }}>
                    <div style={{ height: '100%', width: `${selectedUav?.battery ?? 0}%`, backgroundColor: '#488255' }} />
                  </div>
                </div>
                <div style={{ backgroundColor: '#0d1117', border: '1px solid #1e2633', borderRadius: '2px', padding: '3px 6px' }}>
                  <div style={{ fontSize: '0.52rem', color: '#606d7d', fontWeight: 500 }}>AVİYONİK ISI</div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.78rem', fontWeight: 600, color: '#e6edf3', marginTop: '1px' }}>{selectedUav?.temperature?.toFixed(1) ?? '--'}°C</div>
                </div>
                <div style={{ backgroundColor: '#0d1117', border: '1px solid #1e2633', borderRadius: '2px', padding: '3px 6px' }}>
                  <div style={{ fontSize: '0.52rem', color: '#606d7d', fontWeight: 500 }}>ENLEM (LAT)</div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.65rem', fontWeight: 600, color: '#e6edf3', marginTop: '1px' }}>{selectedUav?.latitude?.toFixed(5) ?? '--'}</div>
                </div>
                <div style={{ backgroundColor: '#0d1117', border: '1px solid #1e2633', borderRadius: '2px', padding: '3px 6px' }}>
                  <div style={{ fontSize: '0.52rem', color: '#606d7d', fontWeight: 500 }}>BOYLAM (LON)</div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.65rem', fontWeight: 600, color: '#e6edf3', marginTop: '1px' }}>{selectedUav?.longitude?.toFixed(5) ?? '--'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* GÜVENLİK ALARM GÜNLÜĞÜ */}
          <div style={{ backgroundColor: '#151a24', border: '1px solid #1e2633', borderRadius: '2px', padding: '6px 8px', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '0.62rem', color: '#9e4444', fontWeight: 600, paddingBottom: '4px', marginBottom: '4px', borderBottom: '1px solid #1e2633', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={12} /> GÜVENLİK ALARM GÜNLÜĞÜ
            </div>
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px', maxHeight: '130px' }}>
              {alerts.length === 0 ? (
                <div style={{ fontSize: '0.6rem', color: '#606d7d', textAlign: 'center', marginTop: '6px' }}>Aktif alarm yok.</div>
              ) : (
                alerts.map((a, i) => (
                  <div key={i} style={{ backgroundColor: '#171112', borderLeft: '2px solid #9e4444', padding: '4px 6px', borderRadius: '1px', fontSize: '0.58rem', fontFamily: 'JetBrains Mono, monospace' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9e4444', fontWeight: 600 }}>
                      <span>[{a.alert_type}] {a.uav_id}</span>
                      <span style={{ color: '#606d7d', fontSize: '0.5rem' }}>{new Date(a.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div style={{ color: '#b2bac2', fontSize: '0.58rem', marginTop: '2px' }}>{a.message}</div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default App;