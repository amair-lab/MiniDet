from flask import Flask, Response, render_template, jsonify
import cv2
import time
from threading import Thread, Lock
import os
from datetime import datetime

app = Flask(__name__)

# Create directories for storing media
PHOTO_DIR = 'static/photos'
VIDEO_DIR = 'static/videos'
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)


class VideoCamera:
    def __init__(self):
        self.video = cv2.VideoCapture("/dev/video0")
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.lock = Lock()
        self.frame = None
        self.last_access = time.time()
        self.is_recording = False
        self.video_writer = None
        self.current_video_path = None

        Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        while True:
            success, frame = self.video.read()
            if success:
                # Add timestamp to frame
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cv2.putText(frame, timestamp, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                with self.lock:
                    self.frame = frame
                    self.last_access = time.time()

                    # Write frame to video if recording
                    if self.is_recording and self.video_writer:
                        self.video_writer.write(frame)
            else:
                time.sleep(0.1)
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


# Initialize camera
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)