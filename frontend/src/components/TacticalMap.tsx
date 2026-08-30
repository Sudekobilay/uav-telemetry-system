import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { TelemetryPacket } from '../types/telemetry';

interface Props {
  fleet: Record<string, TelemetryPacket>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export const TacticalMap: React.FC<Props> = ({ fleet, selectedId, onSelect }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Record<string, L.Marker>>({});
  const polylinesRef = useRef<Record<string, L.Polyline>>({});

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

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Telemetri Güncellemelerini Haritaya Yansıtma
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
          .on('click', () => onSelect(uav.uav_id));

        const polyline = L.polyline([latLng], {
          color,
          weight: 1.2,
          opacity: 0.5,
          dashArray: '2, 4',
        }).addTo(map);

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
  }, [fleet, selectedId, onSelect]);

  return <div ref={mapContainerRef} className="w-full h-full bg-black" />;
};