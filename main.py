from collections import defaultdict
import cv2
from ultralytics import YOLO


# Load the pretrained YOLO11 model
model = YOLO("models\hardhat_detection_yolo11_200_epochs_best_02032025.pt")

# Path to the video file
# To use webcam: video_path = 0
video_path = "input_files\hardhat_input_video.mp4"

# Open the video capture and load settings for the output video file
cap = cv2.VideoCapture(video_path)
codec = cv2.VideoWriter_fourcc(*"AVC1")
out = cv2.VideoWriter('./output_files/processed.mp4' , codec, 30, (640, 640))

# Prepare dictionaries for storing the track history
track_history = defaultdict(lambda: [])
track_history_xy = defaultdict(lambda: [])

# Loop through the video frames
while cap.isOpened():
    # Read a frame from the input video
    success, frame = cap.read()
    if success:
        # Resize the input video frames to 640x640px for the better performance
        frame = cv2.resize(frame, (640, 640), interpolation=cv2.INTER_AREA)
        # Run YOLO11 tracking on the frame, persisting tracks between frames
        results = model.track(frame, conf=0.3, persist=True)
        # Prepare lists for the objects tracking IDs
        persons = []
        heads = []
        hardhats = []
        try:
            # Get the boxes, track IDs, object names and classes
            boxes = results[0].boxes.xywh.cpu()
            boxes_xy = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            id_names = results[0].names
            clss = results[0].boxes.cls.int().cpu().tolist()
            # Set default colors for the classes
            colors = [
                (0, 255, 0),
                (255, 0, 0),
                (0, 0, 255)
            ]
            # Get the objects boxes
            for box, box_xy, track_id, cls in zip(boxes, boxes_xy, track_ids, clss):
                x, y, w, h = box
                x1, y1, x2, y2 = box_xy
                # Store the tracking history
                track = track_history[track_id]
                track_xy = track_history_xy[track_id]
                # x, y center point, height and width of the box
                track.append((float(x), float(y), float(w), float(h)))
                # x, y top left and x, y bottom right point of the box
                track_xy.append((float(x1), float(y1), float(x2), float(y2))) 
                # Store the tracking IDs for the object classes
                if cls == 2:
                    persons.append(track_id)
                elif cls == 1:
                    heads.append(track_id)
                elif cls == 0:
                    hardhats.append(track_id)
                # Draw the boxes in the frame only if the object appears for 10 times
                # Exclude false detections
                if len(track) >= 10:
                    if len(track) > 10:
                        track.pop(0)
                        track_xy.pop(0)
                if len(track) == 10:
                    x1, y1, x2, y2 = track_history_xy[track_id][-1]
                    cv2.putText(frame, f"{id_names[cls]} ID: {track_id}", (int(box_xy[0]), int(box_xy[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[cls], 2)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), colors[cls], 2)
            # For every person in the frame find the nearest head and hard hat
            # Detect if the hard hat is at the persons head
            for person in persons:
                for head in heads:
                    x, y, w, h = track_history[person][-1]
                    x1, y1, w1, h1 = track_history[head][-1]
                    if abs(x - x1) < (w + w1) and abs(y - y1) < (h + h1):
                        for hardhat in hardhats:
                            x2, y2, w2, h2 = track_history[hardhat][-1]
                            if abs(x1 - x2) < (w1 + w2) and abs(y1 - y2) < (h1 + h2):
                                cv2.putText(frame, f"person ID: {person}", (int(x - w/2), int(y - h/2 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)
                                cv2.rectangle(frame, (int(x - w/2), int(y + h/2)), (int(x + w/2), int(y - h/2)), colors[0], 2)
                                break
            # Write the frame to the output video
            out.write(frame)
            # Visualize the results on the frame
            cv2.imshow("YOLO11 Tracking", frame)
        except:
            # Write the frame to the output video
            out.write(frame)
            # Visualize the results on the frame
            cv2.imshow("YOLO11 Tracking", frame)
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
out.release()
cap.release()
cv2.destroyAllWindows()