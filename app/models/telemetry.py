from datetime import datetime, timezone
import enum
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class FlightStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_FLIGHT = "IN_FLIGHT"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class UAV(Base):
    __tablename__ = "uavs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uav_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="Bayraktar TB2 / ANKA Sim")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 1 İHA -> Çok Uçuş Oturumu
    sessions: Mapped[list["FlightSession"]] = relationship("FlightSession", back_populates="uav", cascade="all, delete-orphan")


class FlightSession(Base):
    __tablename__ = "flight_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    uav_id: Mapped[str] = mapped_column(String(50), ForeignKey("uavs.uav_id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=FlightStatus.IN_FLIGHT.value)

    # İlişkiler
    uav: Mapped["UAV"] = relationship("UAV", back_populates="sessions")
    telemetry_logs: Mapped[list["TelemetryLog"]] = relationship("TelemetryLog", back_populates="flight_session", cascade="all, delete-orphan")
    alerts: Mapped[list["TelemetryAlert"]] = relationship("TelemetryAlert", back_populates="flight_session", cascade="all, delete-orphan")


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("flight_sessions.id"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    battery: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    heading: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="NORMAL")

    flight_session: Mapped["FlightSession"] = relationship("FlightSession", back_populates="telemetry_logs")


class TelemetryAlert(Base):
    """
    Uçuş güvenlik sınırları (Geofence, kritik batarya, irtifa kaybı, aşırı ısınma)
    aşıldığında üretilen denetim (audit) alarmları tablosu.
    """
    __tablename__ = "telemetry_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("flight_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    uav_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # GEOFENCE_BREACH, LOW_BATTERY, OVERHEAT, LOW_ALTITUDE
    severity: Mapped[str] = mapped_column(String(20), nullable=False)    # WARNING, CRITICAL
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    flight_session: Mapped["FlightSession"] = relationship("FlightSession", back_populates="alerts")