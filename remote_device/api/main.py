import datetime as dt
from typing import Optional, List
from uuid import UUID
from zoneinfo import ZoneInfo

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import config


db_conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    user=config.db_user,
    password=config.db_pass,
    dbname=config.db_dbname,
)
db_cursor = db_conn.cursor()

app = FastAPI()


class Point(BaseModel):
    captured_at: dt.datetime
    lat: float
    lon: float
    distance: Optional[float] = None
    speed: Optional[float] = None


class Track(BaseModel):
    id: UUID
    device_id: int
    created_at: dt.datetime
    active: bool
    last_position: Optional[Point] = None


@app.get("/tracks/{device_id}", response_model=List[Track], response_model_exclude_unset=True)
async def tracks_active(device_id: int, active: Optional[bool] = None, since: Optional[dt.datetime] = None, to: Optional[dt.datetime] = None) -> List[Track]:
    sql = "SELECT id, device_id, created_at, active FROM tracks WHERE device_id = %(device_id)s"
    params = {
        "device_id": device_id,
    }

    if active is not None:
        sql+= " AND active = %(active)s"
        params["active"] = active
    if since is not None:
        sql += " AND created_at >= to_timestamp(%(since)s)"
        params["since"] = dt.datetime.timestamp(since)
    if to is not None:
        sql += " AND created_at <= to_timestamp(%(to)s)"
        params["to"] = dt.datetime.timestamp(to)

    db_cursor.execute(sql, params)
    res = db_cursor.fetchall()
    tracks = []
    for r in res:
        db_cursor.execute("SELECT captured_at, latitude, longitude FROM points WHERE track_id = %s ORDER BY captured_at ASC", (r[0], ))
        pos = db_cursor.fetchone()
        tracks.append(Track(
            id=UUID(r[0]),
            device_id=int(r[1]),
            created_at=r[2].replace(tzinfo=dt.timezone.utc).astimezone(tz=ZoneInfo("Europe/Prague")),
            active=bool(r[3]),
            last_position=Point(captured_at=pos[0].replace(tzinfo=dt.timezone.utc).astimezone(tz=ZoneInfo("Europe/Prague")), lat=pos[1], lon=pos[2]),
        ))

    return tracks


@app.get("/track/{track_id}/path", response_model=List[Point])
async def track_path(track_id: UUID) -> List[Point]:
    db_cursor.execute("SELECT id, device_id, created_at, active FROM tracks where id = %s", (track_id.hex, ))
    track = db_cursor.fetchone()
    if track == None:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db_cursor.execute("SELECT captured_at, latitude, longitude, distance, speed FROM points where track_id = %s ORDER BY captured_at ASC", (track_id.hex, ))
    path = db_cursor.fetchall()
    points = []
    for i in range(len(path)):
        cap, lat, lon, dist, speed = path[i]
        p = Point(captured_at=cap, lat=lat, lon=lon, distance=dist, speed=speed)
        points.append(p)

    return points