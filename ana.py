from flask import Blueprint, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

app = Blueprint('analytics', __name__)
CORS(app)

# Database connection parameters
DB_NAME = "traffic_analytics"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"

# Initialize vehicle types
vehicle_types = ["Cars", "Trucks", "Motorcycles", "Buses", "Emergency"]
vehicle_counts = {"Cars": 0, "Trucks": 0, "Motorcycles": 0, "Buses": 0, "Emergency": 0}

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

def init_analytics_database():
    """Ensure the database exists and has the required tables"""
    try:
        # Try to connect to the database
        try:
            conn = get_db_connection()
        except psycopg2.OperationalError as e:
            # If database doesn't exist, it will be created by app2.py
            # Just return and wait for app2.py to create it
            print(f"Waiting for main application to create database: {e}")
            return False
            
        # If we get here, the database exists
        # Check if our table exists
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'traffic_data'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("Table 'traffic_data' does not exist. Waiting for main application to create it.")
            cur.close()
            conn.close()
            return False
            
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Analytics database initialization error: {e}")
        return False

# Initialize database when module is loaded
database_ready = init_analytics_database()

def update_vehicle_counts():
    """Update vehicle counts from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        for vehicle_type in vehicle_types:
            cur.execute("SELECT COUNT(*) FROM traffic_data WHERE vehicle_type = %s", (vehicle_type,))
            count = cur.fetchone()['count']
            vehicle_counts[vehicle_type] = count
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error in update_vehicle_counts: {e}")
        # Fallback to default values if database connection fails
        for vehicle_type in vehicle_types:
            vehicle_counts[vehicle_type] = 0

@app.route('/analytics')
def index():
    return render_template('ana.html')

@app.route('/api/traffic-data')
def get_traffic_data():
    """Get traffic data from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get last 20 records
        cur.execute("""
            SELECT * FROM traffic_data 
            ORDER BY id DESC 
            LIMIT 20
        """)
        traffic_data = cur.fetchall()
        
        formatted_data = []
        for item in traffic_data:
            formatted_item = {
                "Time": item["time"],
                "Lane1": item["lane1"],
                "Lane2": item["lane2"],
                "Lane3": item["lane3"],
                "Lane4": item["lane4"],
                "Count": item["count"],
                "ProcessingTime": item["processing_time"],
                "VehicleType": item["vehicle_type"],
                "VehicleCount": item["vehicle_count"],
                "Precision": item["precision"],
                "Recall": item["recall"],
                "F1Score": item["f1_score"],
                "Action": item["action"],
                "Priority": item["priority"]
            }
            formatted_data.append(formatted_item)
        
        # Update vehicle counts
        update_vehicle_counts()
        
        # Calculate confusion matrix from latest data
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action = 'Ambulance'")
        true_positive = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action = 'Ambulance' AND priority != 'TRUE'")
        false_positive = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action != 'Ambulance'")
        true_negative = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action != 'Ambulance' AND priority = 'TRUE'")
        false_negative = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        confusion_matrix = {
            "True Positive": true_positive,
            "False Positive": false_positive,
            "True Negative": true_negative,
            "False Negative": false_negative
        }
        
        matrix_data = [{"name": k, "value": v} for k, v in confusion_matrix.items()]
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return jsonify({
            "trafficData": formatted_data,
            "vehicleTypes": vehicle_counts,
            "confusionMatrix": matrix_data,
            "currentTime": current_time
        })
    except Exception as e:
        print(f"Database error in get_traffic_data: {e}")
        return jsonify({
            "trafficData": [],
            "vehicleTypes": vehicle_counts,
            "confusionMatrix": [],
            "currentTime": datetime.now().strftime("%H:%M:%S")
        })

@app.route('/api/vehicle-types')
def get_vehicle_types():
    """Get vehicle type distribution"""
    update_vehicle_counts()
    result = []
    for vehicle_type, count in vehicle_counts.items():
        result.append({"name": vehicle_type, "value": count})
    return jsonify(result)

@app.route('/api/confusion-matrix')
def get_confusion_matrix():
    """Get confusion matrix data"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action = 'Ambulance'")
        true_positive = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action = 'Ambulance' AND priority != 'TRUE'")
        false_positive = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action != 'Ambulance'")
        true_negative = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) FROM traffic_data WHERE action != 'Ambulance' AND priority = 'TRUE'")
        false_negative = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        result = [
            {"name": "True Positive", "value": true_positive},
            {"name": "False Positive", "value": false_positive},
            {"name": "True Negative", "value": true_negative},
            {"name": "False Negative", "value": false_negative}
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Database error in get_confusion_matrix: {e}")
        return jsonify([
            {"name": "True Positive", "value": 0},
            {"name": "False Positive", "value": 0},
            {"name": "True Negative", "value": 0},
            {"name": "False Negative", "value": 0}
        ])
