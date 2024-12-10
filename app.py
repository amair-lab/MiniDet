from flask import Flask, Response, render_template, jsonify
import cv2
import time
from threading import Thread, Lock
import os
from datetime import datetime
import torch
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog

app = Flask(__name__)

# Create directories for storing media
PHOTO_DIR = 'static/photos'
VIDEO_DIR = 'static/videos'
DETECTION_DIR = 'static/detections'
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(DETECTION_DIR, exist_ok=True)

# Initialize detection log file
DETECTION_LOG = os.path.join(DETECTION_DIR, 'detection_log.txt')


class DetectionPredictor:
    def __init__(self):
        self.cfg = get_cfg()
        self.cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml"))
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml")
        self.cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.predictor = DefaultPredictor(self.cfg)
        self.person_class_id = MetadataCatalog.get(self.cfg.DATASETS.TRAIN[0]).thing_classes.index('person')

    def detect_person(self, frame):
        outputs = self.predictor(frame)
        pred_classes = outputs["instances"].pred_classes.cpu().numpy()
        pred_boxes = outputs["instances"].pred_boxes.tensor.cpu().numpy()
        scores = outputs["instances"].scores.cpu().numpy()

        person_indices = pred_classes == self.person_class_id
        person_boxes = pred_boxes[person_indices]
        person_scores = scores[person_indices]

        return len(person_boxes) > 0, person_boxes, person_scores


class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture("/dev/video0")  # Changed to 0 for default camera
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.lock = Lock()
        self.frame = None
        self.last_access = time.time()
        self.is_recording = False
        self.video_writer = None
        self.current_video_path = None

        self.detector = DetectionPredictor()
        self.last_detection_time = None
        self.person_detected = False
        self.detection_cooldown = 5.0

        Thread(target=self._capture_loop, daemon=True).start()

    def log_detection(self, detected, timestamp, scores):
        with open(DETECTION_LOG, 'a') as f:
            status = "Person detected" if detected else "Person left"
            f.write(f"{timestamp}: {status}\tconfidence: {scores}\n")

    def save_detection_frame(self, frame, boxes=None):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'detection_{timestamp}.jpg'
        filepath = os.path.join(DETECTION_DIR, filename)

        if boxes is not None:
            frame_with_boxes = frame.copy()
            for box in boxes:
                x1, y1, x2, y2 = box.astype(int)
                cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.imwrite(filepath, frame_with_boxes)
        else:
            cv2.imwrite(filepath, frame)

        return filename

    def _capture_loop(self):
        while True:
            success, frame = self.video.read()
            if success:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cv2.putText(frame, timestamp, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                current_time = time.time()
                if self.last_detection_time is None or \
                        (current_time - self.last_detection_time) >= self.detection_cooldown:

                    detected, boxes, scores = self.detector.detect_person(frame)

                    if detected != self.person_detected:
                        self.person_detected = detected
                        self.log_detection(detected, timestamp, scores)

                        if detected:
                            self.save_detection_frame(frame, boxes)
                        else:
                            self.save_detection_frame(frame)

                    elif detected:
                        self.save_detection_frame(frame, boxes)

                    self.last_detection_time = current_time

                with self.lock:
                    self.frame = frame
                    self.last_access = current_time

                    if self.is_recording and self.video_writer:
                        self.video_writer.write(frame)
            else:
                time.sleep(0.5)
                self.video.release()
                self.video = cv2.VideoCapture("/dev/video0")

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return jpeg.tobytes() if ret else None

    def capture_photo(self):
        with self.lock:
            if self.frame is None:
                return None
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'photo_{timestamp}.jpg'
            filepath = os.path.join(PHOTO_DIR, filename)
            cv2.imwrite(filepath, self.frame)
            return filename

    def start_recording(self):
        with self.lock:
            if not self.is_recording and self.frame is not None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'video_{timestamp}.avi'
                filepath = os.path.join(VIDEO_DIR, filename)

                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                frame_size = (self.frame.shape[1], self.frame.shape[0])
                self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, frame_size)
                self.is_recording = True
                self.current_video_path = filepath
                return filename
        return None

    def stop_recording(self):
        with self.lock:
            if self.is_recording and self.video_writer:
                self.is_recording = False
                self.video_writer.release()
                self.video_writer = None
                return os.path.basename(self.current_video_path)
        return None

    def __del__(self):
        self.video.release()
        if self.video_writer:
            self.video_writer.release()


# Camera singleton
camera = None


def get_camera():
    global camera
    if camera is None:
        camera = VideoCamera()
    return camera


def generate_frames():
    cam = get_camera()
    while True:
        frame = cam.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            time.sleep(0.1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture')
def capture():
    cam = get_camera()
    filename = cam.capture_photo()
    if filename:
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error'})


@app.route('/start_recording')
def start_recording():
    cam = get_camera()
    filename = cam.start_recording()
    if filename:
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error'})


@app.route('/stop_recording')
def stop_recording():
    cam = get_camera()
    filename = cam.stop_recording()
    if filename:
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error'})


@app.route('/list_media')
def list_media():
    photos = [f for f in os.listdir(PHOTO_DIR) if f.endswith('.jpg')]
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.avi')]
    return jsonify({
        'photos': sorted(photos, reverse=True),
        'videos': sorted(videos, reverse=True)
    })


@app.route('/detection_status')
def detection_status():
    cam = get_camera()
    return jsonify({
        'person_detected': cam.person_detected,
        'last_detection_time': cam.last_detection_time
    })


@app.route('/list_detections')
def list_detections():
    detections = [f for f in os.listdir(DETECTION_DIR) if f.endswith('.jpg')]

    log_entries = []
    if os.path.exists(DETECTION_LOG):
        with open(DETECTION_LOG, 'r') as f:
            log_entries = f.readlines()

    return jsonify({
        'detection_images': sorted(detections, reverse=True),
        'detection_log': log_entries
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12512, threaded=True, debug=False)