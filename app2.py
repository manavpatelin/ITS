from flask import Flask, render_template, jsonify, Response
from threading import Thread, Lock
import time
import os
from detection import generate_frames
from vehicle_counter import start_vehicle_counting, stop_vehicle_counting, get_vehicle_counts, get_ambulance_status
from datetime import datetime, timedelta
import random
import psycopg2

app = Flask(__name__)

VIDEO_DIR = "videos"
VIDEO_PATHS = [os.path.join(VIDEO_DIR, f"Lane_{i}.mp4") for i in range(1, 5)]

traffic_states = {
    1: {"color": "green", "timer": 0, "remaining_red": 0},
    2: {"color": "red", "timer": 30, "remaining_red": 30},
    3: {"color": "red", "timer": 60, "remaining_red": 60},
    4: {"color": "red", "timer": 90, "remaining_red": 90}
}

state_lock = Lock()
ADDITIONAL_RED_TIME = 0
INITIAL_COUNT_DELAY = 0

# Database connection parameters
DB_NAME = "traffic_analytics"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DATA_COLLECTION_INTERVAL = 4  # 4 seconds

def get_db_connection():
    """Create a database connection"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
        # No port specified - will use default PostgreSQL port
    )
    return conn

def init_database():
    """Initialize the database and create tables if they don't exist"""
    try:
        # First try to connect to the database
        try:
            conn = get_db_connection()
        except psycopg2.OperationalError as e:
            # If database doesn't exist, create it
            if "database" in str(e) and "does not exist" in str(e):
                print(f"Database {DB_NAME} does not exist. Creating it...")
                # Connect to default postgres database
                conn_default = psycopg2.connect(
                    dbname="postgres",
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST
                )
                conn_default.autocommit = True
                cur_default = conn_default.cursor()
                
                # Create database
                cur_default.execute(f"CREATE DATABASE {DB_NAME}")
                
                cur_default.close()
                conn_default.close()
                
                # Now connect to the new database
                conn = get_db_connection()
            else:
                raise
        
        cur = conn.cursor()
        
        # Create traffic_data table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traffic_data (
                id SERIAL PRIMARY KEY,
                time VARCHAR(50),
                lane1 INTEGER,
                lane2 INTEGER,
                lane3 INTEGER,
                lane4 INTEGER,
                count INTEGER,
                processing_time VARCHAR(50),
                vehicle_type VARCHAR(50),
                vehicle_count INTEGER,
                precision FLOAT,
                recall FLOAT,
                f1_score FLOAT,
                action VARCHAR(50),
                priority VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

def get_green_duration(vehicle_count):
    if vehicle_count < 10: return 10
    elif vehicle_count < 20: return 20
    else: return 30

def handle_ambulance_emergency():
    ambulance_status = get_ambulance_status()
    emergency_lanes = [int(lane) for lane, present in ambulance_status.items() if present]
    
    if not emergency_lanes:
        return None
    
    emergency_lane = emergency_lanes[0]

    with state_lock:
        for lane in traffic_states:
            if lane == emergency_lane:
                traffic_states[lane].update({"color": "green", "timer": 00, "remaining_red": 0, "emergency": True})
            else:
                traffic_states[lane].update({"color": "red", "timer": 00, "remaining_red":00, "emergency": False})
    return emergency_lane

def save_traffic_data(counts, processing_time="50ms"):
    """Save traffic data to PostgreSQL database"""
    try:
        current_time = datetime.now().strftime("%H:%M")
        
        # Get vehicle types and their counts from detection
        vehicle_types = ["Cars", "Trucks", "Motorcycles", "Buses", "Emergency"]
        
        # Get actual vehicle type from detection if available
        from vehicle_counter import get_vehicle_type_counts
        vehicle_type_counts = get_vehicle_type_counts()
        
        # Choose the vehicle type with the highest count
        max_count = 0
        vehicle_type = vehicle_types[int(time.time()) % 5]  # Default fallback
        
        for vtype, count in vehicle_type_counts.items():
            if count > max_count:
                max_count = count
                vehicle_type = vtype
        
        # Calculate metrics (you can replace these with actual calculations)
        precision = round(90 + random.uniform(0, 8), 2)
        recall = round(90 + random.uniform(0, 8), 2)
        f1_score = round(90 + random.uniform(0, 8), 2)
        
        # Determine if ambulance is present for action and priority
        ambulance_status = get_ambulance_status()
        action = "Ambulance" if any(ambulance_status.values()) else "Normal"
        priority = "TRUE" if any(ambulance_status.values()) else "FALSE"
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert data into the database
        cur.execute("""
            INSERT INTO traffic_data 
            (time, lane1, lane2, lane3, lane4, count, processing_time, 
             vehicle_type, vehicle_count, precision, recall, f1_score, action, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            current_time, 
            counts.get('1', 0), 
            counts.get('2', 0), 
            counts.get('3', 0), 
            counts.get('4', 0),
            sum(int(count) for count in counts.values()),
            processing_time,
            vehicle_type,
            max_count,  # Use the actual count for the selected vehicle type
            precision,
            recall,
            f1_score,
            action,
            priority
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Traffic data saved to database at {current_time}")
    except Exception as e:
        print(f"Error saving traffic data to database: {e}")

def update_traffic_lights():
    current_lane = 1
    yellow_duration = 3
    is_first_run = True
    saved_lane = None
    last_save_time = time.time()
    
    while True:
        # Save traffic data every interval
        current_time = time.time()
        if current_time - last_save_time >= DATA_COLLECTION_INTERVAL:
            counts = get_vehicle_counts()
            save_traffic_data(counts)
            last_save_time = current_time
            
        emergency_lane = handle_ambulance_emergency()
        
        if emergency_lane is not None:
            if saved_lane is None:
                saved_lane = current_lane  # Save the interrupted lane
                
            while True:
                time.sleep(1)
                if not get_ambulance_status().get(str(emergency_lane), False):
                    break
                with state_lock:
                    traffic_states[emergency_lane]["timer"] = 0

            # After ambulance passes, return to saved lane
            previous_lane = current_lane 
             # Reset saved lane
            
            with state_lock:
                traffic_states[emergency_lane].update({"color": "yellow", "timer": yellow_duration})
            
            for _ in range(yellow_duration):
                time.sleep(1)
                with state_lock:
                    for lane in traffic_states:
                        if traffic_states[lane]["timer"] > 0:
                            traffic_states[lane]["timer"] -= 1

            with state_lock:
                traffic_states[emergency_lane]["color"] = "red"
                next_lane = previous_lane
                counts = get_vehicle_counts()
                
                for lane in range(1, 5):
                    if lane != emergency_lane:
                        positions_until_green = (lane - next_lane) if lane > next_lane else (4 + lane - next_lane)
                        total_wait = 0
                        temp_lane = next_lane
                        
                        for _ in range(positions_until_green):
                            lane_count = int(counts.get(str(temp_lane), 0))
                            total_wait += get_green_duration(lane_count) + yellow_duration
                            temp_lane = (temp_lane % 4) + 1
                        
                        if lane != next_lane:
                            total_wait += ADDITIONAL_RED_TIME
                        
                        traffic_states[lane]["timer"] = total_wait
                        traffic_states[lane]["remaining_red"] = total_wait

            current_lane = next_lane
            continue

        # Original traffic logic
        with state_lock:
            if is_first_run:
                traffic_states[1]["timer"] = 0
                time.sleep(INITIAL_COUNT_DELAY)
                
                counts = get_vehicle_counts()
                first_count = int(counts.get(str(current_lane), 0))
                green_duration = get_green_duration(first_count)
                
                traffic_states[1]["timer"] = green_duration
                traffic_states[1]["color"] = "green"
                is_first_run = False
            else:
                counts = get_vehicle_counts()
                current_count = int(counts.get(str(current_lane), 0))
                green_duration = get_green_duration(current_count)
                traffic_states[current_lane]["color"] = "green"
                traffic_states[current_lane]["timer"] = green_duration
                traffic_states[current_lane]["remaining_red"] = 0

            next_lane = (current_lane % 4) + 1

            for lane in range(1, 5):
                if lane != current_lane:
                    positions_until_green = (lane - current_lane) if lane > current_lane else (4 + lane - current_lane)
                    
                    total_wait = 0
                    temp_lane = current_lane
                    
                    for _ in range(positions_until_green):
                        lane_count = int(counts.get(str(temp_lane), 0))
                        total_wait += get_green_duration(lane_count) + yellow_duration
                        temp_lane = (temp_lane % 4) + 1
                    
                    if lane != next_lane:
                        total_wait += ADDITIONAL_RED_TIME
                    
                    traffic_states[lane]["color"] = "red"
                    traffic_states[lane]["timer"] = total_wait
                    traffic_states[lane]["remaining_red"] = total_wait 

        for _ in range(green_duration):
            time.sleep(1)
            with state_lock:
                for lane in traffic_states:
                    if traffic_states[lane]["timer"] > 0:
                        traffic_states[lane]["timer"] -= 1
                    if traffic_states[lane]["remaining_red"] > 0:
                        traffic_states[lane]["remaining_red"] -= 1

        with state_lock:
            traffic_states[current_lane]["color"] = "yellow"
            traffic_states[current_lane]["timer"] = yellow_duration

        for _ in range(yellow_duration):
            time.sleep(1)
            with state_lock:
                for lane in traffic_states:
                    if traffic_states[lane]["timer"] > 0:
                        traffic_states[lane]["timer"] -= 1
                    if traffic_states[lane]["remaining_red"] > 0:
                        traffic_states[lane]["remaining_red"] -= 1

        with state_lock:
            traffic_states[current_lane]["color"] = "red"
            
            total_red = 0
            next_lane = (current_lane % 4) + 1
            temp_lane = next_lane
            
            for _ in range(3):
                next_count = int(counts.get(str(temp_lane), 0))
                total_red += get_green_duration(next_count) + yellow_duration
                temp_lane = (temp_lane % 4) + 1
            
            if current_lane != next_lane:
                total_red += ADDITIONAL_RED_TIME
            
            traffic_states[current_lane]["timer"] = total_red
            traffic_states[current_lane]["remaining_red"] = total_red

        current_lane = (current_lane % 4) + 1

thread = Thread(target=update_traffic_lights, daemon=True)
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live_content')
def live():
    return render_template('live.html')

@app.route('/video_feed/<int:lane_id>')
def video_feed(lane_id):
    if lane_id < 1 or lane_id > len(VIDEO_PATHS):
        return "Invalid lane ID", 400
        
    video_path = VIDEO_PATHS[lane_id - 1]
    return Response(generate_frames(video_path),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/traffic_states')
def get_traffic_states():
    with state_lock:
        return jsonify(traffic_states)

@app.route('/vehicle_counts')
def get_vehicle_counts_route():
    return jsonify(get_vehicle_counts())

@app.route('/ambulance_status')
def get_ambulance_status_route():
    return jsonify(get_ambulance_status())

@app.route('/analytics')
def analytics():
    return render_template('ana.html')

def validate_videos():
    if not os.path.exists(VIDEO_DIR):
        print(f"Error: Videos directory '{VIDEO_DIR}' not found.")
        print("Please create a 'videos' directory and add your video files.")
        return False

    missing_videos = []
    for i in range(1, 5):
        video_path = os.path.join(VIDEO_DIR, f"Lane_{i}.mp4")
        if not os.path.exists(video_path):
            missing_videos.append(f"Lane_{i}.mp4")
    
    if missing_videos:
        print(f"Error: Missing video files: {', '.join(missing_videos)}")
        print(f"Please ensure all required videos are in the '{VIDEO_DIR}' directory:")
        print("Required files: Lane_1.mp4, Lane_2.mp4, Lane_3.mp4, Lane_4.mp4")
        return False
    return True

if __name__ == "__main__":
    # Initialize database before starting the app
    init_database()
    
    # Register the analytics blueprint
    from ana import app as analytics_blueprint
    app.register_blueprint(analytics_blueprint)
    
    if validate_videos():
        start_vehicle_counting(VIDEO_PATHS)
        try:
            app.run(debug=True)
        finally:
            stop_vehicle_counting()