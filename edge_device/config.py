from geotools import Point

device_id: int      = 1
config_file: str    = 'yolov4-tiny-detrac.cfg'
data_file: str      = 'obj.data'
weights: str        = 'yolov4-tiny-detrac_best.weights'
source: str         = "file" # "camera" or "file"
file_path: str      = "test_video.mp4"
camera_w: int       = 1920
camera_h: int       = 1080
display: bool       = False
debug: bool         = True
thresh: float       = 0.5
color               = (0, 0, 255)
mqtt_host: str      = "192.168.1.132"
mqtt_port: int      = 1883

reference_points = [
    Point(1028, 850, 49.2241922, 16.5798447),
    Point(1770, 716, 49.2241500, 16.5797239),
    Point(527, 356, 49.2233417, 16.5802336),
    Point(297, 354, 49.2234064, 16.5803944),
]