import React from 'react';
import type { TelemetryPacket } from '../types/telemetry';
import { Plane } from 'lucide-react';

interface Props {
  fleet: Record<string, TelemetryPacket>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export const FleetTable: React.FC<Props> = ({ fleet, selectedId, onSelect }) => {
  const uavs = Object.values(fleet);

  return (
    <div className="w-[290px] bg-mil-panel border-r border-mil-border flex flex-col h-full">
      <div className="p-2 border-b border-mil-border flex justify-between items-center bg-[#0b0e14]">
        <span className="text-xs font-semibold text-mil-dim">AKTİF HAVA UNSURLARI</span>
        <span className="text-[10px] font-mono text-mil-blue bg-[#121721] px-1.5 py-0.5 rounded border border-mil-border">
          {uavs.length} ARAÇ
        </span>
      </div>

      <div className="grid grid-cols-[20px_1fr_50px_40px] gap-1 px-2 py-1 bg-[#0d1118] border-b border-mil-border text-[10px] font-semibold text-mil-dim">
        <span />
        <span>ÇAĞRI KODU</span>
        <span className="text-right">İRTİFA</span>
        <span className="text-center">MOD</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {uavs.map((uav) => {
          const isSelected = selectedId === uav.uav_id;
          const isWarn = uav.status === 'CRITICAL' || uav.status === 'WARNING';

          return (
            <div
              key={uav.uav_id}
              onClick={() => onSelect(uav.uav_id)}
              className={`grid grid-cols-[20px_1fr_50px_40px] gap-1 px-2 py-1.5 border-b border-[#141a24] text-xs cursor-pointer items-center transition-colors ${
                isSelected
                  ? 'bg-mil-selected border-l-2 border-l-mil-sand text-white font-semibold'
                  : isWarn
                  ? 'bg-[#1c1414] border-l-2 border-l-mil-red'
                  : 'bg-mil-card hover:bg-mil-hover'
              }`}
            >
              <Plane size={12} className={isSelected ? 'text-mil-sand' : isWarn ? 'text-mil-red' : 'text-mil-blue'} />
              <span className="font-mono truncate">{uav.uav_id}</span>
              <span className="font-mono text-right text-mil-dim">{Math.round(uav.altitude)}m</span>
              <span className={`font-mono text-[9px] text-center px-1 py-0.5 rounded ${
                isWarn ? 'bg-[#2b1717] text-mil-red' : 'bg-[#1a222f] text-mil-blue'
              }`}>
                {uav.status === 'NORMAL' ? 'NAV' : uav.status.substring(0, 3)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};