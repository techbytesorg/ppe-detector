import cv2
from ultralytics import YOLO
import time
import os
import numpy as np
import signal
import sys

# Configure unbuffered output for immediate logging
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # Line buffered
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)  # Line buffered

print("OpenCV version:", cv2.__version__)
print("Has GStreamer:", "GStreamer" in cv2.getBuildInformation())

# Performance optimizations
os.environ['OMP_NUM_THREADS'] = '4'  # Optimize CPU threads
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use specific GPU

# Global flag for graceful shutdown
shutdown_flag = False
unclutter_process = None

def signal_handler(sig, frame):
    global shutdown_flag
    print('\nKeyboard interrupt received. Shutting down gracefully...')
    shutdown_flag = True

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Load the pretrained YOLO11 model with optimizations
model = YOLO("models/hardhat_detection_yolo11_200_epochs_best_02032025.pt")

# Optimize model for inference
model.fuse()  # Fuse Conv2d and BatchNorm2d layers for faster inference

# Warm up the model with a dummy frame
print("Warming up model...")
dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
_ = model.predict(dummy_frame, conf=0.85)
print("Model warmed up")

# Camera settings
video_path = 0
is_jetson = True
detection_width = 640
detection_height = 640

# Get actual screen dimensions for fullscreen display
try:
    # Try to get screen resolution from system
    import subprocess
    result = subprocess.run(['xrandr'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if '*' in line:  # Current resolution has asterisk
            resolution = line.split()[0]
            screen_width, screen_height = map(int, resolution.split('x'))
            print(f"Detected screen resolution: {screen_width}x{screen_height}")
            break
    else:
        raise Exception("Could not detect resolution from xrandr")
except:
    # Fallback to common resolutions or try OpenCV method
    print("Could not detect screen resolution, using fallback method...")
    # Create a temporary window to get screen size
    temp_window = cv2.namedWindow("temp", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("temp", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # Get the window size (this should be screen size in fullscreen)
    try:
        # This is a workaround - we'll use common Jetson display sizes
        screen_width = 1920  # Common for many displays
        screen_height = 1080
        print(f"Using fallback resolution: {screen_width}x{screen_height}")
    except:
        screen_width = 1920
        screen_height = 1080
    cv2.destroyWindow("temp")

# Performance settings
SKIP_FRAMES = 3  # Process every 4th frame for better performance
frame_count = 0
last_inference_time = 0
INFERENCE_INTERVAL = 0.2  # Check every 200ms

if is_jetson and isinstance(video_path, int):
    print("Using Jetson camera with optimized GStreamer pipeline")
    # Try different configurations in order of preference
    camera_configs = [
        # Config 1: 1280x720 without sensor mode
        {
            "width": 1280, "height": 720, "fps": 30,
            "pipeline": lambda w, h, fps: (
                f"nvarguscamerasrc sensor-id={video_path} ! "
                f"video/x-raw(memory:NVMM), width={w}, height={h}, "
                f"format=NV12, framerate={fps}/1 ! "
                "nvvidconv flip-method=2 ! "
                "video/x-raw, format=BGRx ! "
                "videoconvert ! "
                "video/x-raw, format=BGR ! "
                "appsink drop=true max-buffers=2"
            )
        },
        # Config 2: 640x480 fallback
        {
            "width": 640, "height": 480, "fps": 30,
            "pipeline": lambda w, h, fps: (
                f"nvarguscamerasrc sensor-id={video_path} ! "
                f"video/x-raw(memory:NVMM), width={w}, height={h}, "
                f"format=NV12, framerate={fps}/1 ! "
                "nvvidconv flip-method=2 ! "
                "video/x-raw, format=BGRx ! "
                "videoconvert ! "
                "video/x-raw, format=BGR ! "
                "appsink drop=true max-buffers=2"
            )
        }
    ]
    
    cap = None
    for i, config in enumerate(camera_configs):
        try:
            print(f"Trying camera config {i+1}: {config['width']}x{config['height']} @ {config['fps']}fps")
            gst_pipeline = config["pipeline"](config["width"], config["height"], config["fps"])
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    print(f"Success! Using {config['width']}x{config['height']} configuration")
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    break
                else:
                    cap.release()
                    cap = None
            else:
                if cap:
                    cap.release()
                cap = None
                    
        except Exception as e:
            print(f"Config {i+1} failed: {e}")
            if cap:
                cap.release()
            cap = None
    
    if cap is None:
        print("All Jetson camera configs failed, falling back to standard VideoCapture")
        cap = cv2.VideoCapture(video_path)
else:
    print("Using OpenCV VideoCapture")
    cap = cv2.VideoCapture(video_path)

assert cap.isOpened(), "Failed to open camera"
print("Camera opened successfully, proceeding to window setup...")

# Create fullscreen window with proper configuration
window_name = "PPE Status"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Move window to top-left corner to ensure full coverage
cv2.moveWindow(window_name, 0, 0)
print("Window setup complete, attempting cursor management...")

# Hide mouse cursor using unclutter
try:
    import subprocess
    print("Checking for existing unclutter process...")
    # Check if unclutter is already running
    try:
        result = subprocess.run(['pgrep', '-x', 'unclutter'], capture_output=True)
        print(f"pgrep result: returncode={result.returncode}")
        if result.returncode == 0:
            print("Found existing unclutter process, killing it to start fresh...")
            subprocess.run(['pkill', '-x', 'unclutter'], check=False)
            time.sleep(0.5)  # Give it time to die
            print("Starting fresh unclutter with our parameters...")
            unclutter_process = subprocess.Popen(['unclutter', '-idle', '0.01', '-root'])
            print("Mouse cursor hidden using unclutter (background process)")
        else:
            print("No existing unclutter found, starting new instance...")
            # Run unclutter in background so it doesn't block the main application
            unclutter_process = subprocess.Popen(['unclutter', '-idle', '0.01', '-root'])
            print("Mouse cursor hidden using unclutter (background process)")
    except FileNotFoundError:
        print("pgrep not available, starting unclutter anyway")
        unclutter_process = subprocess.Popen(['unclutter', '-idle', '0.01', '-root'])
        print("Mouse cursor hidden using unclutter (background process)")
except Exception as e:
    print(f"Could not hide mouse cursor with unclutter: {e} - continuing with visible cursor")

# Create status screens
green_screen = np.full((screen_height, screen_width, 3), (0, 255, 0), dtype=np.uint8)  # Green screen
red_screen = np.full((screen_height, screen_width, 3), (0, 0, 255), dtype=np.uint8)    # Red screen
yellow_screen = np.full((screen_height, screen_width, 3), (0, 255, 255), dtype=np.uint8)  # Yellow screen

# Add text to screens with better visibility
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 5
thickness = 12  # Increased thickness for bolder text
outline_color = (0, 0, 0)  # Black text for better contrast
text_color = (255, 255, 255)  # White outline
outline_thickness = 25  # Thick white outline

# Add "SAFE" text to green screen with outline
text = "SAFE"
text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
text_x = (screen_width - text_size[0]) // 2
text_y = (screen_height + text_size[1]) // 2
# Draw white outline first
cv2.putText(green_screen, text, (text_x, text_y), font, font_scale, outline_color, outline_thickness)
# Draw black text on top
cv2.putText(green_screen, text, (text_x, text_y), font, font_scale, text_color, thickness)

# Add "DANGER" text to red screen with outline
text = "DANGER"
text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
text_x = (screen_width - text_size[0]) // 2
text_y = (screen_height + text_size[1]) // 2
# Draw white outline first
cv2.putText(red_screen, text, (text_x, text_y), font, font_scale, outline_color, outline_thickness)
# Draw black text on top
cv2.putText(red_screen, text, (text_x, text_y), font, font_scale, text_color, thickness)

# Add "STANDBY" text to yellow screen with outline
text = "STANDBY"
text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
text_x = (screen_width - text_size[0]) // 2
text_y = (screen_height + text_size[1]) // 2
# Draw white outline first
cv2.putText(yellow_screen, text, (text_x, text_y), font, font_scale, outline_color, outline_thickness)
# Draw black text on top
cv2.putText(yellow_screen, text, (text_x, text_y), font, font_scale, text_color, thickness)

# Detection state
hardhat_detected = False
person_detected = False
last_detection_time = time.time()

print("Starting PPE detection... Press 'q' or Ctrl+C to exit")

# Main detection loop
while cap.isOpened() and not shutdown_flag:
    success, frame = cap.read()
    if success and not shutdown_flag:
        frame_count += 1
        current_time = time.time()
        
        # Skip frames for better performance
        should_run_inference = (frame_count % (SKIP_FRAMES + 1) == 0 and 
                               current_time - last_inference_time >= INFERENCE_INTERVAL)
        
        if should_run_inference:
            last_inference_time = current_time
            
            # Resize frame for detection
            detection_frame = cv2.resize(frame, (detection_width, detection_height))
            
            # Run YOLO detection
            results = model.predict(detection_frame, conf=0.85, verbose=False)
            
            # Reset detection flags
            hardhat_detected = False
            person_detected = False
            
            # Check detections
            if results[0].boxes is not None:
                classes = results[0].boxes.cls.cpu().numpy()
                
                # Check for person (class 2) and hardhat (class 0)
                for cls in classes:
                    if cls == 2:  # Person
                        person_detected = True
                    elif cls == 0:  # Hardhat
                        hardhat_detected = True
                
                last_detection_time = current_time
        
        # Determine status and display appropriate screen
        # Show green if hardhat is detected, red if person without hardhat, yellow if no person
        if hardhat_detected:
            cv2.imshow(window_name, green_screen)
            status = "SAFE - Hardhat detected"
        elif person_detected:
            cv2.imshow(window_name, red_screen)
            status = "DANGER - No hardhat detected"
        else:
            # No person detected, show yellow standby screen
            cv2.imshow(window_name, yellow_screen)
            status = "STANDBY - No person in view"
        
        # Print status every 30 frames
        if frame_count % 30 == 0:
            print(f"Status: {status}")
        
        # Handle exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or shutdown_flag:
            break
    else:
        if shutdown_flag:
            print("Shutdown requested during processing")
        break

# Cleanup
print("Cleaning up resources...")

# Clean up unclutter process
if unclutter_process and unclutter_process.poll() is None:
    try:
        unclutter_process.terminate()
        unclutter_process.wait(timeout=5)
        print("Unclutter process terminated")
    except subprocess.TimeoutExpired:
        unclutter_process.kill()
        print("Unclutter process killed (forced)")
    except Exception as e:
        print(f"Error cleaning up unclutter: {e}")

cap.release()
cv2.destroyAllWindows()
print("PPE detection stopped")