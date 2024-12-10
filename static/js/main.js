let isRecording = false;
let detectionCheckInterval;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    updateMediaGallery();
    updateDetections();
    startDetectionCheck();
});

// Handle recording
function toggleRecording() {
    const button = document.getElementById('recordButton');

    if (!isRecording) {
        fetch('/start_recording')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isRecording = true;
                    button.textContent = 'Stop Recording';
                    button.style.backgroundColor = '#f44336';
                }
            });
    } else {
        fetch('/stop_recording')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isRecording = false;
                    button.textContent = 'Start Recording';
                    button.style.backgroundColor = '#4CAF50';
                    updateMediaGallery();
                }
            });
    }
}

// Handle photo capture
function capturePhoto() {
    fetch('/capture')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateMediaGallery();
            }
        });
}

// Update media gallery
function updateMediaGallery() {
    fetch('/list_media')
        .then(response => response.json())
        .then(data => {
            // Update photos
            const photosContainer = document.getElementById('photos');
            photosContainer.innerHTML = data.photos.map(photo => `
                <div class="media-item">
                    <img src="/static/photos/${photo}" alt="${photo}">
                    <p>${photo}</p>
                </div>
            `).join('');

            // Update videos
            const videosContainer = document.getElementById('videos');
            videosContainer.innerHTML = data.videos.map(video => `
                <div class="media-item">
                    <video width="200" controls>
                        <source src="/static/videos/${video}" type="video/avi">
                        Your browser does not support the video tag.
                    </video>
                    <p>${video}</p>
                </div>
            `).join('');
        });
}

// Start periodic detection status check
function startDetectionCheck() {
    checkDetectionStatus();
    detectionCheckInterval = setInterval(checkDetectionStatus, 1000);
}

// Check detection status
function checkDetectionStatus() {
    fetch('/detection_status')
        .then(response => response.json())
        .then(data => {
            const statusElem = document.getElementById('personStatus');
            if (data.person_detected) {
                statusElem.textContent = 'Person Detected';
                statusElem.className = 'detected';
            } else {
                statusElem.textContent = 'No Person Detected';
                statusElem.className = 'not-detected';
            }
        });
}

// Update detections gallery and log
function updateDetections() {
    fetch('/list_detections')
        .then(response => response.json())
        .then(data => {
            // Update detection images
            const detectionsContainer = document.getElementById('detections');
            detectionsContainer.innerHTML = data.detection_images.map(image => `
                <div class="media-item">
                    <img src="/static/detections/${image}" alt="${image}">
                    <p>${image}</p>
                </div>
            `).join('');

            // Update detection log
            const logContainer = document.getElementById('log');
            logContainer.textContent = data.detection_log.join('');
        });

    // Schedule next update
    setTimeout(updateDetections, 1000);
}