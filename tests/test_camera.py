import cv2
import os
import subprocess
import time


def list_video_devices():
    """List all available video devices in /dev/video*"""
    video_devices = []
    try:
        # List all video devices
        devices = subprocess.check_output(['v4l2-ctl', '--list-devices'], universal_newlines=True)
        print("\nAvailable Video Devices:")
        print(devices)

        # Get a simple list of /dev/video* devices
        dev_videos = sorted([d for d in os.listdir('/dev') if d.startswith('video')])
        print("\nSimple device list:", dev_videos)
        return [f'/dev/{d}' for d in dev_videos]
    except FileNotFoundError:
        print("v4l2-ctl not found. Installing v4l-utils might help.")
        # Fallback to just listing /dev/video* devices
        return [f'/dev/{d}' for d in os.listdir('/dev') if d.startswith('video')]
    except Exception as e:
        print(f"Error listing devices: {e}")
        return []


def test_camera(device_path):
    """Test if a camera can be opened and capture frames"""
    print(f"\nTesting camera: {device_path}")

    # Try opening with direct device path
    cap = cv2.VideoCapture(device_path)
    if not cap.isOpened():
        # If direct path fails, try with device index
        try:
            device_num = int(device_path.split('video')[-1])
            cap = cv2.VideoCapture(device_num)
        except:
            print(f"Failed to open camera with index")
            return False

    if not cap.isOpened():
        print(f"Failed to open camera: {device_path}")
        return False

    # Try reading a frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        cap.release()
        return False

    # Get camera properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Success! Camera properties:")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")

    # Show the frame for 2 seconds
    window_name = f"Testing {device_path}"
    cv2.imshow(window_name, frame)
    cv2.waitKey(2000)
    cv2.destroyWindow(window_name)

    cap.release()
    return True


def main():
    # First, list all video devices
    devices = list_video_devices()

    if not devices:
        print("No video devices found!")
        return

    print("\nTesting each camera device...")
    working_devices = []

    for device in ["/dev/video0"]:
        if test_camera(device):
            working_devices.append(device)

    print("\nSummary:")
    print(f"Found {len(devices)} devices, {len(working_devices)} working")
    if working_devices:
        print("\nWorking devices:")
        for device in working_devices:
            print(f"- {device}")

        # Demonstrate how to use in the Flask app
        print("\nTo use a working camera in the Flask app, modify the camera initialization line to:")
        print('camera = cv2.VideoCapture("' + working_devices[0] + '")  # Use the first working camera')
        print('# OR use the device index:')
        print('camera = cv2.VideoCapture(' + working_devices[0].split('video')[-1] + ')')
    else:
        print("\nNo working cameras found!")
        print("\nTroubleshooting tips:")
        print("1. Check if you have permission to access the camera devices")
        print("2. Try running: sudo usermod -a -G video $USER")
        print("3. Install v4l2-utils: sudo apt-get install v4l-utils")
        print("4. Check camera connections and drivers")


if __name__ == "__main__":
    main()