import datetime as dt
import urllib.parse

import gpxpy.gpx
import matplotlib.pyplot as plt
import requests

import seaborn as sns


sns.set_theme()

api_url = "http://127.0.0.1:8000"
device_id = 1
active = None
since = None
to = dt.datetime.now()

tracks_endpoint = f"/tracks/{device_id}?"
if active is not None:
    tracks_endpoint += f"active={str(active)}&"
if since is not None:
    tracks_endpoint += f"since={urllib.parse.quote(since.isoformat())}&"
if to is not None:
    tracks_endpoint += f"to={urllib.parse.quote(to.isoformat())}"
tracks = requests.get(api_url + tracks_endpoint).json()

gpx = gpxpy.gpx.GPX()


paths = {}
plt.figure(1)
plt.title("Speed of the vehicles over time")
plt.xlabel("Time")
plt.ylabel("Speed (km/h)")
for t in tracks:
    path_endpoint = f"/track/{t['id']}/path"
    path = requests.get(api_url + path_endpoint).json()
    paths[t["id"]] = path

    x = []
    y = []
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    for p in path:
        if p["speed"] != 0:
            x.append(dt.datetime.fromisoformat(p["captured_at"]))
            y.append(p["speed"])
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
            latitude=p["lat"],
            longitude=p["lon"],
            time=dt.datetime.fromisoformat(p["captured_at"])
        ))
    
    sns.lineplot(x=x, y=y)


with open('paths.gpx', 'w') as f:
    f.write(gpx.to_xml())

plt.show()