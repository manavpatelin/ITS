import cv2
from ultralytics import YOLO

model = YOLO('yolo12s.pt')  # Replace with your custom model if needed
vehicle_classes = {0: "ambulance", 2: "car", 3: "motorbike", 5: "bus", 7: "truck"}

def generate_frames(video_path):
    try:
        if isinstance(video_path, list):
            video_path = video_path[0]
            
        video_path = str(video_path)
        cap = cv2.VideoCapture(video_path)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            results = model(frame)
            
            for r in results:
                for box in r.boxes:
                    class_id = int(box.cls.item())
                    if class_id in vehicle_classes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        color = (0, 255, 0) if class_id != 0 else (0, 0, 255)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        if class_id == 0:
                            cv2.putText(frame, 'AMBULANCE', (x1, y1-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
            
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
    except Exception as e:
        print(f"Error: {str(e)}")
        yield b''
    finally:
        if 'cap' in locals():
            cap.release()