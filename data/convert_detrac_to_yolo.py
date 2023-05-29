import os
import re
import lxml.etree as ET
from typing import List, Dict, Tuple
from sklearn.model_selection import train_test_split
import shutil

# https://github.com/AlexeyAB/Yolo_mark/issues/60

DATASET_PATH: str = "Train_Data"
ANNOTATIONS_PATH: str = "Train_Annotations"
IMAGE_WIDTH = 960
IMAGE_HEIGHT = 540
IMG_PATTERN = re.compile("^img\d{5}\.jpg$")
RELATIVE_TO = "../.."

class_ids = {
    "car": 0,
    "bus": 1,
    "van": 2,
    "others": 3,
}

#*******************************************************************************
# convert_frame
#*******************************************************************************

def convert_frame(frame: os.DirEntry, f_annotations) -> Dict:
    bboxes = []
    stats = {
        "car": 0,
        "bus": 0,
        "van": 0,
        "others": 0,
    }

    for target in f_annotations.xpath("target"):
        box = target.xpath("box")[0]
        attributes = target.xpath("attribute")[0]

        width = float(box.get("width"))
        height = float(box.get("height"))
        x = (float(box.get("left")) + width / 2) / IMAGE_WIDTH
        y = (float(box.get("top")) + height / 2) / IMAGE_HEIGHT
        width /= IMAGE_WIDTH
        height /= IMAGE_HEIGHT

        vehicle_type = attributes.get("vehicle_type")
        stats[vehicle_type] = stats[vehicle_type] + 1

        label = f"{class_ids[vehicle_type]} {x:.6} {y:.6} {width:.6} {height:.6}"
        bboxes.append(label)

    split_path = frame.path.split('/')
    split_path[-1] = split_path[-2] + "_" + split_path[-1]
    split_path.insert(0, "converted")
    new_path = '/'.join(split_path)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.copy(frame.path, new_path)
    with open(new_path.replace(f"jpg", 'txt'), "w") as fr_an:
        fr_an.write('\n'.join(bboxes))

    return stats

#*******************************************************************************
# convert_video
#*******************************************************************************

def convert_video(video: os.DirEntry) -> Tuple[Dict, List]:
    video_name = video.name
    stats = {
        "car": 0,
        "bus": 0,
        "van": 0,
        "others": 0,
        "frames": 0,
    }
    frames = []

    annotations_file = f"{ANNOTATIONS_PATH}/{video_name}.xml"
    if os.path.isfile(annotations_file):
        annotations = ET.parse(annotations_file)

        images: List[os.DirEntry] = [
            f for f in os.scandir(f"{DATASET_PATH}/{video_name}") if
            f.is_file() and IMG_PATTERN.match(f.name)
        ]

        for img in images:
            frame_number = int(img.name.replace("img", "").replace(".jpg", ""))
            frame_annotations = annotations.xpath(
                f"/sequence/frame[@num=\"{frame_number}\"]/target_list"
            )

            if frame_annotations:
                frame_annotations = frame_annotations[0]
                frame_stats = convert_frame(img, frame_annotations)
                stats = {key: stats.get(key, 0) + frame_stats.get(key, 0) for key in set(stats) | set(frame_stats)}
                frames.append(f"converted/{DATASET_PATH}/{video_name}/{video_name}_{img.name}")
                stats["frames"] += 1

    print(f"{video_name} ({stats['frames']} frames) - Car: {stats['car']}, Bus: {stats['bus']}, Van: {stats['van']}, Others: {stats['others']}")

    return stats, frames

#*******************************************************************************
# convert_set
#*******************************************************************************

def convert_set(videos: List[os.DirEntry], filename: str):
    stats = {}
    frames = []
    print("=============================================================")
    for c, v in enumerate(videos):
        print(f"{c+1}/{len(videos)}")
        video_stats, video_frames = convert_video(v)
        frames += video_frames
        stats = {key: stats.get(key, 0) + video_stats.get(key, 0) for key in set(stats) | set(video_stats)}

    print(f"{stats['frames']} frames - Car: {stats['car']}, Bus: {stats['bus']}, Van: {stats['van']}, Others: {stats['others']}")
    print("=============================================================\n")

    frames = [f"{os.path.relpath(f, RELATIVE_TO)}" for f in frames]

    with open(filename, "w") as f:
        f.write('\n'.join(frames))

#*******************************************************************************
# main
#*******************************************************************************

def main():
    f: os.DirEntry
    videos: List[os.DirEntry] = [f for f in os.scandir(DATASET_PATH) if f.is_dir()]
    train, test = train_test_split(videos, test_size=0.2, random_state=23)

    print(f"Processing training videos ({len(train)})...")
    convert_set(train, "train_frames.txt")

    print(f"Processing testing videos ({len(test)})...")
    convert_set(test, "test_frames.txt")

if __name__ == "__main__":
    main()
