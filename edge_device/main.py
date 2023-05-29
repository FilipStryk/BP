import json
from queue import Queue
import threading as mt
import time
from typing import Tuple

import cv2
import numpy as np
import paho.mqtt.client as mqtt

import config
import darknet
from geotools import Point, CoordinatesConverter
from sort import Sort


def track_vehicles(tracker, detections):
    dets = np.empty((0, 5))
    for _, confidence, bbox in detections:
        x1, y1, x2, y2 = darknet.bbox2points(bbox)
        dets = np.append(dets, [[x1, y1, x2, y2, float(confidence)/100]], axis=0)
    tracks = tracker.update(dets)
    return tracks


def convert_tracks_to_gps(converter, tracks, net_shape, frame_shape):
    net_w, net_h = net_shape
    frame_w, frame_h = frame_shape
    tracks_gps = []
    for x1, y1, x2, y2, id in tracks:
        x = x1 + (x2 - x1)/2
        y = y1 + (y2 - y1)/2
        x = int((x/net_w)*frame_w)
        y = int((y2/net_h)*frame_h)
        lat, lon = converter.pixelToGps(x, y)
        p = Point(x, y, lat, lon)
        tracks_gps.append([id, p])
    
    return tracks_gps


def draw_crosshair(img, x: int, y: int, color: Tuple[int, int, int] = (0, 0, 255), width: int = 1) -> None:
    cv2.line(img, (x - 10, y), (x + 10, y), color, width)
    cv2.line(img, (x, y - 10), (x, y + 10), color, width)
    cv2.circle(img, (x, y), 8, color, width)


def draw(frame, tracks, net_shape, frame_shape):
    net_w, net_h = net_shape
    frame_w, frame_h = frame_shape
    for p in config.reference_points:
        draw_crosshair(frame, p.x, p.y)
        cv2.putText(frame, f"({p.x}, {p.y})", (p.x-45, p.y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

    
    for x1, y1, x2, y2, id in tracks:
        x1 = int((x1/net_w)*frame_w)
        y1 = int((y1/net_h)*frame_h)
        x2 = int((x2/net_w)*frame_w)
        y2 = int((y2/net_h)*frame_h)
        x = int(x1 + (x2 - x1)/2)
        y = int(y1 + (y2 - y1)/2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), config.color, 2)
        cv2.putText(frame, f"{id}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.color, 2)
        draw_crosshair(frame, x, y, config.color, 2)


def send_data(tracks_q: Queue):
    client = mqtt.Client()
    client.connect(config.mqtt_host, config.mqtt_port)
    client.loop_start()

    while True:
        cap_time, tracks = tracks_q.get()
        if not tracks: continue

        payload = {
            "device_id": config.device_id,
            "capture_time": cap_time,
            "tracks": {},
        }
        for id, point in tracks:
            payload["tracks"][str(id)] = point.toList()
        client.publish("/tracker",  json.dumps(payload))


def main():
    net, classes, _ = darknet.load_network(
        config_file=config.config_file,
        data_file=config.data_file,
        weights=config.weights,
        batch_size=1
    )
    net_w = darknet.network_width(net)
    net_h = darknet.network_height(net)

    coord_converter: CoordinatesConverter = CoordinatesConverter(config.reference_points)
    tracker: Sort = Sort(max_age=7)

    tracks_q: Queue = Queue()
    mt.Thread(target=send_data, args=(tracks_q, )).start()

    if config.source == "camera":
        pipeline: str = "nvarguscamerasrc sensor-id=0 !"\
            f"video/x-raw(memory:NVMM), width=(int){config.camera_w}, height=(int){config.camera_h}, framerate=(fraction)30/1 !"\
            "nvvidconv flip-method=0 !"\
            f"video/x-raw, width=(int){config.camera_w}, height=(int){config.camera_h}, format=(string)BGRx !"\
            "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    elif config.source == "file":
        cap = cv2.VideoCapture(config.file_path)
    else:
        print("Invalid source.")
        exit(1)

    if config.debug:
        processing_times = []
        frames = 1

    capture_time = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        if config.debug:
            start_time = time.time()
        if config.source == "file":
            capture_time += 1/cap.get(cv2.CAP_PROP_FPS)
        else:
            capture_time = time.time()
        if not ret:
            break

        frame_h, frame_w, _ = frame.shape

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (net_w, net_h), interpolation=cv2.INTER_LINEAR)
        img_darknet = darknet.make_image(net_w, net_h, 3)
        darknet.copy_image_from_bytes(img_darknet, img.tobytes())
        detections = darknet.detect_image(net, classes, img_darknet, thresh=config.thresh)
        darknet.free_image(img_darknet)

        tracks = track_vehicles(tracker, detections)
        tracks_gps = convert_tracks_to_gps(coord_converter, tracks, (net_w, net_h), (frame_w, frame_h))
        tracks_q.put([capture_time, tracks_gps])
        
        if config.display:
            draw(frame, tracks, (net_w, net_h), (frame_w, frame_h))
            image = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
            cv2.namedWindow("Vehicle tracking", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow("Vehicle tracking", image)
            
            if cv2.waitKey(1) == ord('q'):
                break
        
        if config.debug:
            processing_times.append((time.time() - start_time)*1000)
            frames += 1

    cap.release()
    cv2.destroyAllWindows()
    
    if config.debug:
        times = processing_times[1:]
        print("Processing time:")
        print(f"AVG: {np.mean(times)} ms, MIN: {np.min(times)} ms, MAX: {np.max(times)} ms")
        print(f"Frames: {len(times)}")

if __name__ == '__main__':
    main()