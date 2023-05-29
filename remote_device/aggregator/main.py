import datetime as dt
import json
import math
import signal
import time

import numpy as np
import paho.mqtt.client as mqtt
import psycopg2

import config

from pprint import pprint
client = mqtt.Client()

db_conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    user=config.db_user,
    password=config.db_pass,
    dbname=config.db_dbname,
)
db_cursor = db_conn.cursor()

if config.debug:
    delays = []


def haversine_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    dlat = math.radians(p1[0]) - math.radians(p2[0])
    dlon = math.radians(p1[1]) - math.radians(p2[1])
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1[0]) * math.cos(p2[0]) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371e3


def on_connect(client, userdata, flags, rc):
    client.subscribe("/tracker")


def on_message(client, userdata, msg: mqtt.MQTTMessage):
    payload = json.loads(msg.payload)

    device_id = payload["device_id"]
    capture_time = payload["capture_time"]
    tracks_ids = list(payload["tracks"].keys())

    db_cursor.execute("SELECT id FROM tracks WHERE id IN %s", (tuple(tracks_ids), ))
    existing_tracks = [t[0] for t in db_cursor.fetchall()]
    new_tracks_ids = list(set(tracks_ids).difference(existing_tracks))

    for new_track in new_tracks_ids:
        sql = "INSERT INTO tracks (id, device_id) VALUES(%s, %s)"
        db_cursor.execute(sql, (new_track, device_id, ))

    db_cursor.execute("UPDATE tracks SET active = id IN %s WHERE 1=1", (tuple(tracks_ids), ))


    for id, p in payload["tracks"].items():
        db_cursor.execute("SELECT latitude, longitude, captured_at FROM points WHERE track_id = %s ORDER BY captured_at DESC", (id, ))
        prev_position = db_cursor.fetchone()

        if prev_position:
            dist = haversine_distance((p[2], p[3]), (prev_position[0], prev_position[1]))
        else:
            dist = 0
        
        db_cursor.execute("SELECT distance, captured_at FROM points WHERE track_id = %s ORDER BY captured_at DESC", (id, ))
        prev_positions = db_cursor.fetchmany(20)
        if len(prev_positions) > 0:
            t = [dt.datetime.timestamp(dt.datetime.utcfromtimestamp(capture_time)), ]
            d = [dist, ]
            for prev_pos in prev_positions:
                t.append(prev_pos[1].timestamp())
                d.append(prev_pos[0])
            
            time_delta = np.mean(np.abs(np.diff(np.array(t))))
            avg_dist = np.mean(d)
            speed = (avg_dist/time_delta)*3.6
        else:
            dist = 0
            speed = 0
        
        sql = "INSERT INTO points (track_id, captured_at, latitude, longitude, x, y, distance, speed) VALUES(%s, to_timestamp(%s), %s, %s, %s, %s, %s, %s)"
        db_cursor.execute(sql, (id, capture_time, p[2], p[3], p[0], p[1], dist, speed))

    if config.debug:
        delays.append(time.time() - capture_time)
    
    db_conn.commit()


def sigint_exit(signum, frame):
    if config.debug:
        print(f"AVG: {np.mean(delays)}, MIN: {np.min(delays)}, MAX: {np.max(delays)}, MEDIAN: {np.median(delays)}")
    client.disconnect()
    exit()


def main():
    signal.signal(signal.SIGINT, sigint_exit)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(config.mqtt_host, config.mqtt_port)
    client.loop_forever()
    

if __name__ == "__main__":
    main()