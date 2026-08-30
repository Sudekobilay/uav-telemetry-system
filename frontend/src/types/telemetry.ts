export type FlightStatus = 'NORMAL' | 'RTH' | 'LOITER' | 'LANDING' | 'LANDED' | 'WARNING' | 'CRITICAL';

export interface TelemetryPacket {
  uav_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude: number;
  speed: number;
  battery: number;
  temperature: number;
  heading: number;
  roll: number;
  pitch: number;
  status: FlightStatus;
}

export interface AlertPacket {
  alert_type: string;
  uav_id: string;
  message: string;
  severity: 'WARNING' | 'CRITICAL';
  timestamp: string;
}