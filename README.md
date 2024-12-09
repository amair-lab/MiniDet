# MiniDetect

A Flask-based web application for camera streaming, photo capture, and video recording. 
This application allows you to access your camera through a web browser, take photos, record videos, and view them in real-time.
Will support object detection. 

## Features

- Live camera streaming
- Full-screen mode
- Real-time timestamp overlay
- Photo capture with timestamp
- Video recording
- Media gallery with photos and videos
- Responsive web interface
- Network accessible within LAN

## Prerequisites

- Python 3.6 or higher
- Web camera device
- Modern web browser

## Installation

1. Clone the repository or download the source code:
```bash
git clone [repository-url]
cd webcam-stream-app
```

2. Create a virtual environment (recommended):
```bash
# For Python 3
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install flask opencv-python
```

## Project Structure
```
webcam-stream-app/
├── app.py
├── static/
│   ├── photos/
│   └── videos/
└── templates/
    └── index.html
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the web interface:
- Local access: `http://localhost:5000`
- LAN access: `http://[your-ip-address]:5000`

### Camera Controls
- Click on the video stream to toggle full-screen mode
- Use "Take Photo" button to capture images
- Use "Start Recording" button to begin video recording
- Click "Stop Recording" to end video recording
- View captured media in the gallery on the right side

## Troubleshooting

### Network Access Issues

#### Ubuntu/Debian Systems
1. Check firewall status:
```bash
sudo ufw status
```

2. Allow port access:
```bash
sudo ufw allow 5000
```

3. If needed, temporarily disable firewall:
```bash
sudo ufw disable
```

#### Manjaro/Arch Systems
1. Check firewall:
```bash
sudo systemctl status firewalld
```

2. Allow port:
```bash
sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

#### CentOS/RHEL Systems
1. Configure SELinux:
```bash
# Check status
sestatus

# Temporarily disable if needed
sudo setenforce 0
```

2. Open port in firewall:
```bash
sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### Camera Access Issues

1. Check camera permissions:
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and log back in for changes to take effect
```

2. List available video devices:
```bash
ls -l /dev/video*
```

3. Test camera access:
```bash
# Install v4l-utils if needed
# Ubuntu/Debian:
sudo apt-get install v4l-utils
# Manjaro/Arch:
sudo pacman -S v4l-utils
# CentOS/RHEL:
sudo yum install v4l-utils

# List devices
v4l2-ctl --list-devices
```

### Port Conflicts

If port 5000 is in use, modify the port in `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
```

## Common Issues and Solutions

1. **Camera Not Found**
   - Ensure camera is properly connected
   - Check device permissions in `/dev/video*`
   - Try running the test script first: `python test_camera.py`

2. **Network Access Denied**
   - Verify firewall settings
   - Check if application is binding to correct network interface
   - Ensure port is not blocked by other applications

3. **Video Stream Not Loading**
   - Check browser compatibility
   - Verify network connectivity
   - Check system resource usage

4. **Performance Issues**
   - Lower video resolution in `app.py`
   - Reduce frame rate
   - Check network bandwidth capacity

## Security Considerations

- This application is designed for LAN use
- No authentication is implemented by default
- Consider adding user authentication for production use
- Use HTTPS for secure communication if needed
- Be cautious when opening ports in your firewall

## Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.