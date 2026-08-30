import React, { useState } from 'react';
import { Home, RefreshCw, PlaneLanding, Play } from 'lucide-react';

interface Props {
  selectedUavId: string | null;
}

export const C2CommandPanel: React.FC<Props> = ({ selectedUavId }) => {
  const [statusMsg, setStatusMsg] = useState('İHA SEÇİMİ BEKLENİYOR');

  const sendCommand = async (commandType: string) => {
    if (!selectedUavId) return;

    setStatusMsg(`${commandType} İLETİLİYOR...`);
    try {
      const res = await fetch('/api/v1/commands/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uav_id: selectedUavId,
          command_type: commandType,
          parameters: {}
        })
      });

      if (res.ok) {
        setStatusMsg(`[ONAYLANDI] ${commandType}`);
      } else {
        setStatusMsg(`[HATA] Komut reddedildi`);
      }
    } catch {
      setStatusMsg('[BAĞLANTI HATASI]');
    }
  };

  return (
    <div className="bg-mil-card border border-mil-border p-2 rounded">
      <div className="flex justify-between items-center text-[10px] font-semibold text-mil-dim mb-1 pb-1 border-b border-mil-border">
        <span>C2 KOMUTA KONTROL</span>
        <span className="text-mil-green font-mono text-[9px]">UPLINK HAZIR</span>
      </div>

      <div className="grid grid-cols-2 gap-1 my-1">
        <button
          onClick={() => sendCommand('RTH')}
          disabled={!selectedUavId}
          className="flex items-center justify-center gap-1.5 p-1.5 bg-mil-cardInner border border-mil-border hover:bg-mil-hover disabled:opacity-40 text-xs font-semibold text-mil-blue rounded"
        >
          <Home size={12} /> RTH (ÜSSE DÖN)
        </button>
        <button
          onClick={() => sendCommand('LOITER')}
          disabled={!selectedUavId}
          className="flex items-center justify-center gap-1.5 p-1.5 bg-mil-cardInner border border-mil-border hover:bg-mil-hover disabled:opacity-40 text-xs font-semibold text-mil-sand rounded"
        >
          <RefreshCw size={12} /> LOITER (BEKLE)
        </button>
        <button
          onClick={() => sendCommand('LAND')}
          disabled={!selectedUavId}
          className="flex items-center justify-center gap-1.5 p-1.5 bg-mil-cardInner border border-mil-border hover:bg-mil-hover disabled:opacity-40 text-xs font-semibold text-mil-red rounded"
        >
          <PlaneLanding size={12} /> ACİL İNİŞ
        </button>
        <button
          onClick={() => sendCommand('RESUME')}
          disabled={!selectedUavId}
          className="flex items-center justify-center gap-1.5 p-1.5 bg-mil-cardInner border border-mil-border hover:bg-mil-hover disabled:opacity-40 text-xs font-semibold text-mil-green rounded"
        >
          <Play size={12} /> GÖREVE DEVAM
        </button>
      </div>

      <div className="flex justify-between items-center bg-mil-cardInner px-2 py-1 rounded border border-mil-border text-[10px] font-mono mt-1">
        <span className="text-mil-dim">DURUM:</span>
        <span className="text-mil-blue font-bold">{selectedUavId ? statusMsg : 'İHA SEÇİMİ BEKLENİYOR'}</span>
      </div>
    </div>
  );
};