import React from 'react';
import type { TelemetryPacket } from '../types/telemetry';
interface Props {
  telemetry: TelemetryPacket | null;
}

export const PrimaryFlightDisplay: React.FC<Props> = ({ telemetry }) => {
  const roll = telemetry?.roll ?? 0;
  const pitch = telemetry?.pitch ?? 0;
  const speed = telemetry?.speed ? Math.round(telemetry.speed) : '--';
  const altitude = telemetry?.altitude ? Math.round(telemetry.altitude) : '--';

  return (
    <div className="bg-mil-card border border-mil-borderLight p-2 rounded">
      <div className="flex justify-between items-center font-mono text-xs text-white border-b border-mil-border pb-1 mb-2">
        <span>{telemetry?.uav_id || 'HAVA ARACI SEÇİLMEDİ'}</span>
        <span className="text-mil-sand">R:{roll.toFixed(1)}° P:{pitch.toFixed(1)}°</span>
      </div>

      <div className="w-full h-36 bg-[#10151f] border border-mil-border relative overflow-hidden rounded">
        {/* Yapay Ufuk */}
        <div 
          className="absolute w-[500px] h-[500px] -top-[175px] -left-[75px] transition-transform duration-100 linear"
          style={{ transform: `rotate(${-roll}deg) translateY(${pitch * 1.8}px)` }}
        >
          <div className="h-[250px] bg-[#131d2b]" />
          <div className="h-[250px] bg-[#261c16] border-t border-[#707e8c]" />
        </div>

        {/* Hız Göstergesi */}
        <div className="absolute left-0 top-0 bottom-0 w-11 bg-mil-cardInner/90 border-r border-mil-border flex flex-col items-center justify-center font-mono z-10">
          <span className="text-[9px] text-mil-dim">IAS</span>
          <span className="text-sm font-bold text-mil-green">{speed}</span>
          <span className="text-[9px] text-mil-dim">km/h</span>
        </div>

        {/* İrtifa Göstergesi */}
        <div className="absolute right-0 top-0 bottom-0 w-11 bg-mil-cardInner/90 border-l border-mil-border flex flex-col items-center justify-center font-mono z-10">
          <span className="text-[9px] text-mil-dim">ALT</span>
          <span className="text-sm font-bold text-mil-blue">{altitude}</span>
          <span className="text-[9px] text-mil-dim">m</span>
        </div>

        {/* Nişangah */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <svg className="w-20 h-8" viewBox="0 0 120 40">
            <path d="M 20 20 L 45 20 L 45 25" stroke="#b89c68" strokeWidth="2" fill="none" />
            <circle cx="60" cy="20" r="3" fill="#b89c68" />
            <path d="M 75 25 L 75 20 L 100 20" stroke="#b89c68" strokeWidth="2" fill="none" />
          </svg>
        </div>
      </div>
    </div>
  );
};