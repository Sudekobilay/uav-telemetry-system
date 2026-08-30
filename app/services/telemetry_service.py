from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.telemetry import UAV, FlightSession, TelemetryLog, FlightStatus
from app.schemas.telemetry import TelemetryPayload


async def save_telemetry_data(payload: TelemetryPayload, db: AsyncSession) -> TelemetryLog:
    # 1. İHA kontrolü
    stmt_uav = select(UAV).where(UAV.uav_id == payload.uav_id)
    result_uav = await db.execute(stmt_uav)
    uav = result_uav.scalar_one_or_none()

    if not uav:
        uav = UAV(uav_id=payload.uav_id, model_name="Bayraktar TB2 Simülatör")
        db.add(uav)
        await db.flush()

    # 2. Aktif uçuş oturumu kontrolü
    stmt_session = select(FlightSession).where(
        FlightSession.uav_id == payload.uav_id,
        FlightSession.status == FlightStatus.IN_FLIGHT
    ).order_by(FlightSession.id.desc())
    
    result_session = await db.execute(stmt_session)
    flight_session = result_session.scalars().first()

    if not flight_session:
        session_code = f"FLIGHT-{payload.uav_id}-{int(datetime.now(timezone.utc).timestamp())}"
        flight_session = FlightSession(
            session_code=session_code,
            uav_id=payload.uav_id,
            status=FlightStatus.IN_FLIGHT
        )
        db.add(flight_session)
        await db.flush()

    # 3. Naive UTC zaman dönüşümü
    record_timestamp = payload.timestamp
    if record_timestamp.tzinfo is not None:
        record_timestamp = record_timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    # 4. Telemetri kaydı
    telemetry_record = TelemetryLog(
        session_id=flight_session.id,
        timestamp=record_timestamp,
        latitude=payload.latitude,
        longitude=payload.longitude,
        altitude=payload.altitude,
        speed=payload.speed,
        battery=payload.battery,
        temperature=payload.temperature,
        heading=payload.heading,
        status=payload.status or "NORMAL"
    )
    
    db.add(telemetry_record)
    await db.commit()

    return telemetry_record