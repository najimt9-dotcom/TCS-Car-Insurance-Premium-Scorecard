import argparse
from collections import defaultdict, deque, Counter
import datetime
import json
import requests
import os
import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from twilio.rest import Client
import subprocess
import sys
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# ======================= MONGODB ATLAS CONFIGURATION =======================
MONGODB_CONNECTION_STRING = "mongodb_string"
DATABASE_NAME = "traffic_analysis"
COLLECTIONS = {
    "statistics": "traffic_statistics",
    "violations": "vehicle_violations", 
    "scorecards": "premium_scorecards",
    "analytics": "real_time_analytics"
}

# Global MongoDB client
mongo_client = None
db = None

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    global mongo_client, db
    try:
        print("🔗 Connecting to MongoDB Atlas...")
        mongo_client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=15000)
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[DATABASE_NAME]
        print("✅ Successfully connected to MongoDB Atlas")
        
        # Verify collections exist
        existing_collections = db.list_collection_names()
        for collection in COLLECTIONS.values():
            if collection not in existing_collections:
                print(f"📁 Creating collection: {collection}")
                db.create_collection(collection)
        
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ MongoDB Atlas connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ MongoDB Atlas error: {e}")
        return False

def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("🔌 MongoDB connection closed")

def save_to_mongodb(collection_name, data):
    """Save data to MongoDB Atlas"""
    try:
        if db is None:
            print("❌ No database connection")
            return False
        
        collection = db[COLLECTIONS[collection_name]]
        result = collection.insert_one(data)
        print(f"✅ Data saved to MongoDB - {collection_name} - ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving to MongoDB {collection_name}: {e}")
        return False

def save_traffic_statistics(stats, analysis_id):
    """Save traffic statistics to MongoDB"""
    statistics_data = {
        "analysis_id": analysis_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_vehicles": stats.get('total_vehicles_detected', 0),
        "vehicles_in_zone": stats.get('vehicles_in_zone', 0),
        "total_violations": stats.get('total_unique_violations', 0),
        "vehicles_with_violations": stats.get('vehicles_with_violations', 0),
        "max_speed": stats.get('max_speed', 0),
        "avg_speed": stats.get('avg_speed', 0),
        "vehicle_distribution": stats.get('vehicle_class_distribution', {}),
        "processing_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": "completed"
    }
    
    return save_to_mongodb("statistics", statistics_data)

def save_individual_violations(violations_data, analysis_id):
    """Save individual violations to MongoDB"""
    violations_list = []
    
    for vehicle_key, violations in violations_data.items():
        for violation in violations:
            violation_record = {
                "analysis_id": analysis_id,
                "timestamp": violation['timestamp'],
                "vehicle_id": violation['tracker_id'],
                "vehicle_type": violation['class'],
                "speed_kmh": violation['speed_kmh'],
                "violation_number": violation['violation_number'],
                "is_speeding": violation['speed_kmh'] > 100,
                "severity": "high" if violation['speed_kmh'] > 120 else "medium" if violation['speed_kmh'] > 100 else "low"
            }
            violations_list.append(violation_record)
    
    if violations_list:
        # Save violations in batches
        batch_size = 50
        success_count = 0
        for i in range(0, len(violations_list), batch_size):
            batch = violations_list[i:i + batch_size]
            for violation in batch:
                if save_to_mongodb("violations", violation):
                    success_count += 1
        print(f"✅ Saved {success_count}/{len(violations_list)} violations to MongoDB")
        return success_count > 0
    return False

def save_premium_scorecard(scorecard_text, analysis_id, stats):
    """Save premium scorecard to MongoDB"""
    scorecard_data = {
        "analysis_id": analysis_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "scorecard_text": scorecard_text,
        "summary": {
            "total_vehicles": stats.get('total_vehicles_detected', 0),
            "total_violations": stats.get('total_unique_violations', 0),
            "max_speed": stats.get('max_speed', 0),
            "risk_level": "high" if stats.get('total_unique_violations', 0) > 200 else "medium" if stats.get('total_unique_violations', 0) > 100 else "low"
        }
    }
    
    return save_to_mongodb("scorecards", scorecard_data)

def save_real_time_analytics(frame_data, analysis_id):
    """Save real-time analytics during processing"""
    analytics_data = {
        "analysis_id": analysis_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "frame_number": frame_data.get('frame_number', 0),
        "vehicles_detected": frame_data.get('vehicles_detected', 0),
        "violations_count": frame_data.get('violations_count', 0),
        "processing_time": frame_data.get('processing_time', 0)
    }
    
    return save_to_mongodb("analytics", analytics_data)

def get_analysis_id():
    """Generate unique analysis ID"""
    return f"analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ======================= CONFIGURATION =======================
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Twilio Setup
TWILIO_ACCOUNT_SID = "TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "TWILIO_AUTH_TOKEN"
TWILIO_PHONE_NUMBER = "+TWILIO_PHONE_NUMBER"
MY_PHONE_NUMBER = "+91Phone_No"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(message: str):
    try:
        client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=MY_PHONE_NUMBER)
    except Exception as e:
        print("SMS sending error:", e)

# Vehicle & Speed Setup
VEHICLE_ID = "CAR123"
SOURCE = np.array([[1252, 787], [2298, 803], [5039, 2159], [-550, 2159]])
TARGET_WIDTH = 25
TARGET_HEIGHT = 250
TARGET = np.array([[0, 0], [TARGET_WIDTH - 1, 0], [TARGET_WIDTH - 1, TARGET_HEIGHT - 1], [0, TARGET_HEIGHT - 1]])
SPEED_LIMIT = 100

# ======================= VIEW TRANSFORMER =======================
class ViewTransformer:
    def __init__(self, source: np.ndarray, target: np.ndarray) -> None:
        source = source.astype(np.float32)
        target = target.astype(np.float32)
        self.m = cv2.getPerspectiveTransform(source, target)

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        if points.size == 0:
            return points
        reshaped_points = points.reshape(-1, 1, 2).astype(np.float32)
        transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
        return transformed_points.reshape(-1, 2)

# ======================= TRAFFIC ANALYZER =======================
class UltimateTrafficAnalyzer:
    def __init__(self, analysis_id):
        self.all_vehicles_seen = set()
        self.zone_vehicles_seen = set()
        self.violations = defaultdict(list)
        self.vehicle_states = {}
        self.unique_vehicle_classes = Counter()
        self.analysis_id = analysis_id
        self.start_time = datetime.datetime.now()
        
    def record_vehicle(self, tracker_id, class_name, in_zone=False):
        if tracker_id is None:
            return
        vehicle_key = f"{tracker_id}_{class_name}"
        if vehicle_key not in self.all_vehicles_seen:
            self.all_vehicles_seen.add(vehicle_key)
            self.unique_vehicle_classes[class_name] += 1
        if in_zone:
            self.zone_vehicles_seen.add(vehicle_key)
            
    def record_violation(self, tracker_id, class_name, speed_kmh, timestamp):
        if tracker_id is None or speed_kmh < 5:
            return None
        vehicle_key = f"{tracker_id}_{class_name}"
        
        if vehicle_key not in self.vehicle_states:
            self.vehicle_states[vehicle_key] = {
                'last_speed': speed_kmh, 'last_time': timestamp, 
                'violation_count': 1, 'max_speed': speed_kmh
            }
            violation_data = {
                "tracker_id": int(tracker_id), "class": class_name, 
                "speed_kmh": int(speed_kmh), "timestamp": timestamp, "violation_number": 1
            }
            self.violations[vehicle_key].append(violation_data)
            return violation_data
        else:
            state = self.vehicle_states[vehicle_key]
            time_diff = (datetime.datetime.fromisoformat(timestamp) - 
                        datetime.datetime.fromisoformat(state['last_time'])).total_seconds()
            speed_diff = abs(speed_kmh - state['last_speed'])
            
            if speed_diff > 10 or time_diff > 5:
                state['violation_count'] += 1
                state['last_speed'] = speed_kmh
                state['last_time'] = timestamp
                state['max_speed'] = max(state['max_speed'], speed_kmh)
                
                violation_data = {
                    "tracker_id": int(tracker_id), "class": class_name,
                    "speed_kmh": int(speed_kmh), "timestamp": timestamp,
                    "violation_number": state['violation_count']
                }
                self.violations[vehicle_key].append(violation_data)
                
                if speed_kmh > SPEED_LIMIT:
                    alert_msg = f"ALERT! {class_name} #{tracker_id} at {int(speed_kmh)} km/h"
                    print(alert_msg)
                    send_sms(alert_msg)
                return violation_data
        return None

    def get_statistics(self):
        total_vehicles = len(self.all_vehicles_seen)
        zone_vehicles = len(self.zone_vehicles_seen)
        total_violations = sum(len(v) for v in self.violations.values())
        all_speeds = [v['speed_kmh'] for violations_list in self.violations.values() for v in violations_list]
        
        stats = {
            'analysis_id': self.analysis_id,
            'total_vehicles_detected': total_vehicles,
            'vehicles_in_zone': zone_vehicles,
            'total_unique_violations': total_violations,
            'vehicle_class_distribution': dict(self.unique_vehicle_classes),
            'max_speed': max(all_speeds) if all_speeds else 0,
            'avg_speed': sum(all_speeds) / len(all_speeds) if all_speeds else 0,
            'vehicles_with_violations': len(self.violations),
            'processing_duration': (datetime.datetime.now() - self.start_time).total_seconds()
        }
        return stats

# ======================= SCORECARD GENERATION =======================
def generate_accurate_scorecard(analyzer_stats):
    analysis_prompt = f"""
    Create premium management scorecard:
    Vehicles: {analyzer_stats['total_vehicles_detected']}
    Violations: {analyzer_stats['total_unique_violations']}
    Max Speed: {analyzer_stats['max_speed']} km/h
    Vehicle Types: {analyzer_stats['vehicle_class_distribution']}
    """
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Api_Key"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": analysis_prompt}],
            "temperature": 0.3, "max_tokens": 1000
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            scorecard = result['choices'][0]['message']['content']
            with open("ultimate_scorecard.txt", "w") as f:
                f.write("PREMIUM MANAGEMENT SCORECARD\n" + "="*50 + "\n" + scorecard)
            print("✅ Scorecard generated!")
            return scorecard
    except Exception as e:
        print(f"Scorecard error: {e}")
    
    # Fallback local scorecard
    scorecard = f"""
LOCAL SCORECARD
Total Vehicles: {analyzer_stats['total_vehicles_detected']}
Violations: {analyzer_stats['total_unique_violations']}
Max Speed: {analyzer_stats['max_speed']} km/h
Analysis ID: {analyzer_stats['analysis_id']}
"""
    with open("ultimate_scorecard.txt", "w") as f:
        f.write(scorecard)
    return scorecard

# ======================= ENHANCED DASHBOARD =======================
def create_auto_dashboard():
    print("🔄 Generating dashboard with CORRECT MongoDB connection...")
    
    # Delete old dashboard file first
    if os.path.exists("auto_dashboard.py"):
        os.remove("auto_dashboard.py")
        print("🗑️ Deleted old dashboard file")
    
    # Use the SAME working connection string as main script
    working_connection = "mongodb+srv://mohammmadsaif22210003_db_user:YaQAoJfXrthGtlu0@cluster0.easchkc.mongodb.net/traffic_analysis?retryWrites=true&w=majority&appName=Cluster0"
    
    dashboard_code = f'''import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pymongo import MongoClient
import time
import json

# Page configuration
st.set_page_config(
    page_title="Traffic Analytics Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {{
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }}
    .metric-card {{
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .warning {{
        color: #ff4b4b;
        font-weight: bold;
    }}
    .success {{
        color: #00cc96;
        font-weight: bold;
    }}
    .section-header {{
        font-size: 1.5rem;
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }}
</style>
""", unsafe_allow_html=True)

# MongoDB Configuration - USING CORRECT WORKING CONNECTION
MONGODB_CONNECTION_STRING = "{working_connection}"
DATABASE_NAME = "traffic_analysis"

@st.cache_resource(show_spinner="Connecting to MongoDB Atlas...")
def init_connection():
    """Initialize MongoDB connection"""
    try:
        client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=15000)
        # Test connection
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        
        # Test collection access
        db.traffic_statistics.find_one()
        return db
    except Exception as e:
        st.error(f"❌ MongoDB Connection Failed: {{str(e)}}")
        return None

def get_latest_statistics(_db):
    """Get the latest traffic statistics"""
    try:
        if _db is None:
            return None
        collection = _db["traffic_statistics"]
        return collection.find_one(sort=[("timestamp", -1)])
    except Exception as e:
        st.error(f"Error fetching statistics: {{e}}")
        return None

def get_violations_data(_db, limit=100):
    """Get violations data"""
    try:
        if _db is None:
            return []
        collection = _db["vehicle_violations"]
        return list(collection.find().sort("timestamp", -1).limit(limit))
    except Exception as e:
        st.error(f"Error fetching violations: {{e}}")
        return []

def get_analytics_trend(_db, hours=24):
    """Get analytics trend for the last N hours"""
    try:
        if _db is None:
            return []
        collection = _db["real_time_analytics"]
        time_threshold = datetime.now() - timedelta(hours=hours)
        return list(collection.find({{"timestamp": {{"$gte": time_threshold.isoformat()}}}}).sort("timestamp", 1))
    except Exception as e:
        st.error(f"Error fetching analytics: {{e}}")
        return []

def get_vehicle_distribution(_db):
    """Get vehicle distribution data"""
    try:
        if _db is None:
            return {{}}
        collection = _db["traffic_statistics"]
        latest = collection.find_one(sort=[("timestamp", -1)])
        return latest.get('vehicle_distribution', {{}}) if latest else {{}}
    except Exception as e:
        st.error(f"Error fetching vehicle distribution: {{e}}")
        return {{}}

def get_speed_analysis(_db):
    """Get speed analysis data"""
    try:
        if _db is None:
            return []
        collection = _db["vehicle_violations"]
        pipeline = [
            {{"$group": {{
                "_id": "$vehicle_type",
                "avg_speed": {{"$avg": "$speed_kmh"}},
                "max_speed": {{"$max": "$speed_kmh"}},
                "min_speed": {{"$min": "$speed_kmh"}},
                "count": {{"$sum": 1}}
            }}}}
        ]
        return list(collection.aggregate(pipeline))
    except Exception as e:
        st.error(f"Error fetching speed analysis: {{e}}")
        return []

def get_database_stats(_db):
    """Get database statistics"""
    try:
        if _db is None:
            return {{}}
        stats = {{
            "total_statistics": _db.traffic_statistics.count_documents({{}}),
            "total_violations": _db.vehicle_violations.count_documents({{}}),
            "total_analytics": _db.real_time_analytics.count_documents({{}}),
            "total_scorecards": _db.premium_scorecards.count_documents({{}}),
        }}
        return stats
    except Exception as e:
        st.error(f"Error fetching database stats: {{e}}")
        return {{}}

# Main Dashboard
st.markdown('<h1 class="main-header">🚗 Traffic Analytics Dashboard</h1>', unsafe_allow_html=True)

# Initialize connection with spinner
with st.spinner("🔄 Connecting to MongoDB Atlas..."):
    db = init_connection()

# Check if connection is successful (using proper None comparison)
if db is not None:
    st.sidebar.success("✅ Connected to MongoDB Atlas")
    
    # Sidebar Controls
    st.sidebar.title("📊 Dashboard Controls")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh every 30 seconds", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Data filters
    st.sidebar.subheader("📅 Data Filters")
    time_filter = st.sidebar.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
    )
    
    # Database Statistics
    st.sidebar.subheader("💾 Database Info")
    db_stats = get_database_stats(db)
    if db_stats:
        st.sidebar.metric("Total Records", sum(db_stats.values()))
        st.sidebar.metric("Statistics", db_stats.get("total_statistics", 0))
        st.sidebar.metric("Violations", db_stats.get("total_violations", 0))
        st.sidebar.metric("Analytics", db_stats.get("total_analytics", 0))
    
    # Get data
    latest_stats = get_latest_statistics(db)
    violations_data = get_violations_data(db, 100)
    analytics_trend = get_analytics_trend(db)
    vehicle_distribution = get_vehicle_distribution(db)
    speed_analysis = get_speed_analysis(db)
    
    if latest_stats is not None:
        # Key Metrics Row
        st.markdown('<div class="section-header">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Vehicles", 
                latest_stats.get('total_vehicles', 0),
                help="Total vehicles detected in the analysis"
            )
        
        with col2:
            st.metric(
                "Zone Vehicles", 
                latest_stats.get('vehicles_in_zone', 0),
                help="Vehicles detected in the monitoring zone"
            )
        
        with col3:
            total_violations = len(violations_data)
            st.metric(
                "Total Violations", 
                total_violations,
                help="Total traffic violations recorded"
            )
        
        with col4:
            speeding_count = len([v for v in violations_data if v.get('is_speeding', False)])
            st.metric(
                "Speeding Violations", 
                speeding_count,
                help="Number of speeding violations"
            )
        
        with col5:
            max_speed = latest_stats.get('max_speed', 0)
            st.metric(
                "Max Speed", 
                f"{{max_speed}} km/h",
                delta=f"{{max_speed - 100}} km/h over limit" if max_speed > 100 else None,
                delta_color="inverse" if max_speed > 100 else "normal",
                help="Highest speed detected"
            )
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚦 Vehicle Distribution")
            if vehicle_distribution:
                df_vehicles = pd.DataFrame(
                    list(vehicle_distribution.items()), 
                    columns=['Vehicle Type', 'Count']
                )
                fig_pie = px.pie(
                    df_vehicles, 
                    values='Count', 
                    names='Vehicle Type',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("📊 No vehicle distribution data available")
        
        with col2:
            st.subheader("📈 Speed Analysis by Vehicle Type")
            if speed_analysis:
                df_speed = pd.DataFrame(speed_analysis)
                if not df_speed.empty:
                    df_speed = df_speed.rename(columns={{'_id': 'Vehicle Type'}})
                    fig_bar = px.bar(
                        df_speed,
                        x='Vehicle Type',
                        y='avg_speed',
                        title='Average Speed by Vehicle Type',
                        color='avg_speed',
                        color_continuous_scale='Viridis'
                    )
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("📊 No speed analysis data available")
            else:
                st.info("📊 No speed analysis data available")
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚠️ Violations Severity")
            if violations_data:
                severity_counts = pd.DataFrame(violations_data)['severity'].value_counts()
                fig_severity = px.bar(
                    x=severity_counts.index,
                    y=severity_counts.values,
                    labels={{'x': 'Severity Level', 'y': 'Count'}},
                    color=severity_counts.index,
                    color_discrete_sequence=['#00cc96', '#ffa15a', '#ff4b4b']
                )
                fig_severity.update_layout(height=400)
                st.plotly_chart(fig_severity, use_container_width=True)
            else:
                st.info("📊 No violations data available")
        
        with col2:
            st.subheader("🎯 Risk Assessment")
            risk_score = 75 if total_violations > 200 else 45 if total_violations > 100 else 25
            risk_level = "High" if risk_score > 70 else "Medium" if risk_score > 40 else "Low"
            risk_color = "red" if risk_score > 70 else "orange" if risk_score > 40 else "green"
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=risk_score,
                domain={{'x': [0, 1], 'y': [0, 1]}},
                title={{'text': f"Risk Level: {{risk_level}}", 'font': {{'size': 20}}}},
                gauge={{
                    'axis': {{'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"}},
                    'bar': {{'color': risk_color}},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {{'range': [0, 30], 'color': 'lightgreen'}},
                        {{'range': [30, 70], 'color': 'yellow'}},
                        {{'range': [70, 100], 'color': 'lightcoral'}}
                    ],
                    'threshold': {{
                        'line': {{'color': "red", 'width': 4}},
                        'thickness': 0.75,
                        'value': 90
                    }}
                }}
            ))
            fig_gauge.update_layout(height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Recent Violations Table
        st.markdown('<div class="section-header">🚨 Recent Violations</div>', unsafe_allow_html=True)
        
        if violations_data:
            df_violations = pd.DataFrame(violations_data)
            # Convert timestamp to readable format
            df_violations['timestamp'] = pd.to_datetime(df_violations['timestamp'])
            df_violations['time'] = df_violations['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Display relevant columns
            display_columns = ['vehicle_id', 'vehicle_type', 'speed_kmh', 'severity', 'time']
            available_columns = [col for col in display_columns if col in df_violations.columns]
            
            # Color code severity
            def color_severity(val):
                if val == 'high':
                    return 'color: red; font-weight: bold'
                elif val == 'medium':
                    return 'color: orange'
                else:
                    return 'color: green'
            
            styled_df = df_violations[available_columns].style.applymap(
                color_severity, subset=['severity']
            )
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400
            )
        else:
            st.info("📋 No recent violations to display")
        
        # System Information
        with st.expander("🔧 System Information & Raw Data"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Latest Statistics")
                st.json(latest_stats)
            
            with col2:
                st.subheader("Analysis Information")
                st.write(f"**Analysis ID:** {{latest_stats.get('analysis_id', 'N/A')}}")
                st.write(f"**Processing Time:** {{latest_stats.get('processing_time', 'N/A')}}")
                st.write(f"**Status:** {{latest_stats.get('status', 'N/A')}}")
                st.write(f"**Database Records:**")
                st.write(f"  - Statistics: {{db_stats.get('total_statistics', 0)}}")
                st.write(f"  - Violations: {{db_stats.get('total_violations', 0)}}")
                st.write(f"  - Analytics: {{db_stats.get('total_analytics', 0)}}")
                st.write(f"  - Scorecards: {{db_stats.get('total_scorecards', 0)}}")
    
    else:
        st.error("❌ No data found in the database. Please run the traffic analysis first.")
        
else:
    # Fallback to local data when MongoDB is not available
    st.warning("⚠️ Running in offline mode with local data")
    
    try:
        with open('ultimate_traffic_data.json', 'r') as f:
            local_data = json.load(f)
            stats = local_data.get('statistics', {{}})
            violations = local_data.get('violations', {{}})
        
        # Convert violations dict to list for display
        violations_list = []
        for vehicle_key, v_list in violations.items():
            for violation in v_list:
                violations_list.append(violation)
        
        # Display local data
        st.subheader("📊 Local Analysis Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Vehicles", stats.get('total_vehicles_detected', 0))
        
        with col2:
            st.metric("Total Violations", stats.get('total_unique_violations', 0))
        
        with col3:
            st.metric("Max Speed", f"{{stats.get('max_speed', 0)}} km/h")
        
        # Show vehicle distribution
        if stats.get('vehicle_class_distribution'):
            st.subheader("🚦 Vehicle Distribution (Local Data)")
            df_vehicles = pd.DataFrame(
                list(stats['vehicle_class_distribution'].items()), 
                columns=['Vehicle Type', 'Count']
            )
            fig_pie = px.pie(df_vehicles, values='Count', names='Vehicle Type')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Show recent violations
        if violations_list:
            st.subheader("🚨 Recent Violations (Local Data)")
            df_violations = pd.DataFrame(violations_list)
            st.dataframe(df_violations, use_container_width=True)
            
    except FileNotFoundError:
        st.error("❌ No local data file found. Please run the traffic analysis first.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🚗 Traffic Analytics Dashboard • Powered by MongoDB Atlas • Real-time Monitoring System"
    "</div>",
    unsafe_allow_html=True
)
'''
    
    with open("auto_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("✅ Dashboard generated with CORRECT MongoDB connection")

def launch_gui():
    print("\n" + "="*60)
    print("🚀 AUTO-LAUNCHING ENHANCED DASHBOARD GUI...")
    print("="*60)
    
    create_auto_dashboard()
    
    # Force kill all Streamlit processes
    try:
        subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
        time.sleep(3)
        print("✅ Killed all existing Streamlit processes")
    except:
        pass
    
    try:
        # Launch new dashboard
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "auto_dashboard.py", 
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.serverAddress", "localhost",
            "--server.address", "localhost"
        ])
        
        print("✅ Enhanced Dashboard launched: http://localhost:8501")
        print("📊 GUI should open automatically in your browser")
        print("🎨 Features: Real-time stats, Speed analysis, Risk assessment, Violations tracking")
        
        # Give user instructions
        print("\n💡 If the browser doesn't open automatically, please visit:")
        print("   🌐 http://localhost:8501")
        print("\n🛑 To stop the dashboard, press Ctrl+C in this terminal")
        
        return process
        
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Manual command: streamlit run auto_dashboard.py")
        return None

# ======================= VIDEO FILE VALIDATION =======================
def check_video_file(video_path):
    """Check if video file is accessible and get info"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        cap.release()
        return False
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"✅ Video loaded successfully:")
    print(f"   📏 Resolution: {width}x{height}")
    print(f"   🎞️  FPS: {fps:.2f}")
    print(f"   📊 Total frames: {frame_count}")
    
    cap.release()
    return True

# ======================= MAIN VIDEO PROCESSING =======================
def main():
    parser = argparse.ArgumentParser(description="Traffic Analysis with MongoDB Atlas & Auto-GUI")
    parser.add_argument("--source_video_path", required=True, type=str)
    parser.add_argument("--target_video_path", default=None, type=str)
    parser.add_argument("--confidence_threshold", default=0.3, type=float)
    parser.add_argument("--iou_threshold", default=0.7, type=float)
    parser.add_argument("--generate_scorecard", action="store_true")
    parser.add_argument("--auto_gui", action="store_true", default=True)
    parser.add_argument("--mongodb", action="store_true", default=True, help="Save data to MongoDB Atlas")
    args = parser.parse_args()

    # Generate analysis ID
    analysis_id = get_analysis_id()
    print(f"📋 Analysis ID: {analysis_id}")

    # Check video file first
    if not check_video_file(args.source_video_path):
        print("🚨 Please check the video file path and format")
        print("💡 Try using absolute path or check if file exists")
        return

    # Connect to MongoDB Atlas
    mongodb_connected = False
    if args.mongodb:
        mongodb_connected = connect_to_mongodb()
        if not mongodb_connected:
            print("⚠️  Continuing without MongoDB Atlas connection")

    # Video setup
    try:
        video_info = sv.VideoInfo.from_video_path(video_path=args.source_video_path)
    except Exception as e:
        print(f"❌ Error loading video: {e}")
        if mongodb_connected:
            close_mongodb_connection()
        return

    model = YOLO("yolov8s.pt")
    byte_track = sv.ByteTrack(frame_rate=video_info.fps, track_activation_threshold=args.confidence_threshold)

    thickness = sv.calculate_optimal_line_thickness(resolution_wh=video_info.resolution_wh)
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)
    box_annotator = sv.BoxAnnotator(thickness=thickness)
    label_annotator = sv.LabelAnnotator(text_scale=text_scale, text_thickness=thickness, text_position=sv.Position.BOTTOM_CENTER)
    trace_annotator = sv.TraceAnnotator(thickness=thickness, trace_length=video_info.fps*2, position=sv.Position.BOTTOM_CENTER)

    frame_generator = sv.get_video_frames_generator(source_path=args.source_video_path)
    polygon_zone = sv.PolygonZone(polygon=SOURCE)
    view_transformer = ViewTransformer(source=SOURCE, target=TARGET)
    coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))

    analyzer = UltimateTrafficAnalyzer(analysis_id)

    print("🎯 Starting video processing...")
    print(f"📹 Video: {video_info.width}x{video_info.height}, {video_info.fps} FPS")
    if mongodb_connected:
        print("☁️  MongoDB Atlas: Connected (data will be saved to cloud)")
    
    # Frame processing
    for frame_num, frame in enumerate(frame_generator):
        result = model(frame)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = detections[detections.confidence > args.confidence_threshold]
        
        # Count all vehicles
        if hasattr(detections, 'tracker_id') and detections.tracker_id is not None:
            for i, tracker_id in enumerate(detections.tracker_id):
                if tracker_id is not None:
                    class_name = model.names[detections.class_id[i]]
                    analyzer.record_vehicle(tracker_id, class_name)
        
        # Process zone vehicles
        zone_detections = detections[polygon_zone.trigger(detections)]
        zone_detections = zone_detections.with_nms(threshold=args.iou_threshold)
        zone_detections = byte_track.update_with_detections(detections=zone_detections)

        labels = []
        if hasattr(zone_detections, 'tracker_id') and zone_detections.tracker_id is not None:
            points = zone_detections.get_anchors_coordinates(anchor=sv.Position.BOTTOM_CENTER)
            points = view_transformer.transform_points(points=points).astype(int)

            for i, tracker_id in enumerate(zone_detections.tracker_id):
                if tracker_id is None: 
                    continue
                    
                coordinates[tracker_id].append(points[i][1])
                class_name = model.names[zone_detections.class_id[i]]
                analyzer.record_vehicle(tracker_id, class_name, in_zone=True)

                if len(coordinates[tracker_id]) < video_info.fps / 2:
                    speed_kmh = 0
                else:
                    coordinate_start = coordinates[tracker_id][-1]
                    coordinate_end = coordinates[tracker_id][0]
                    distance = abs(coordinate_start - coordinate_end)
                    time = len(coordinates[tracker_id]) / video_info.fps
                    speed_kmh = distance / time * 3.6

                # Create label with speed
                label = f"#{tracker_id} {class_name} {int(speed_kmh)} km/h"
                if speed_kmh > SPEED_LIMIT:
                    label += " ⚠️"
                labels.append(label)

                if speed_kmh > 5:
                    timestamp = datetime.datetime.now().isoformat()
                    violation_data = analyzer.record_violation(tracker_id, class_name, speed_kmh, timestamp)
                    
                    # Save real-time analytics to MongoDB
                    if mongodb_connected and frame_num % 50 == 0:
                        analytics_data = {
                            'frame_number': frame_num,
                            'vehicles_detected': len(analyzer.all_vehicles_seen),
                            'violations_count': sum(len(v) for v in analyzer.violations.values()),
                            'processing_time': datetime.datetime.now().isoformat()
                        }
                        save_real_time_analytics(analytics_data, analysis_id)

        # Display frame with labels
        annotated_frame = frame.copy()
        if hasattr(zone_detections, 'tracker_id') and zone_detections.tracker_id is not None:
            annotated_frame = trace_annotator.annotate(scene=annotated_frame, detections=zone_detections)
            annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=zone_detections)
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=zone_detections, labels=labels)
        
        # Add header info
        cv2.putText(annotated_frame, f"Vehicles: {len(analyzer.all_vehicles_seen)} | Violations: {sum(len(v) for v in analyzer.violations.values())}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Traffic Analysis - MongoDB Atlas", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if frame_num % 100 == 0:
            stats = analyzer.get_statistics()
            print(f"📊 Frame {frame_num}: {stats['total_vehicles_detected']} vehicles, {stats['total_unique_violations']} violations")

    cv2.destroyAllWindows()

    # Final processing
    print("\n" + "="*60)
    print("✅ VIDEO PROCESSING COMPLETE!")
    print("="*60)

    final_stats = analyzer.get_statistics()
    print(f"📈 Final Results:")
    print(f"   • Total Vehicles: {final_stats['total_vehicles_detected']}")
    print(f"   • Total Violations: {final_stats['total_unique_violations']}")
    print(f"   • Max Speed: {final_stats['max_speed']} km/h")
    print(f"   • Processing Time: {final_stats['processing_duration']:.2f} seconds")

    # Save data locally
    with open("ultimate_traffic_data.json", "w") as f:
        json.dump({'statistics': final_stats, 'violations': analyzer.violations}, f, indent=4, cls=NumpyEncoder)
    print("💾 Local data saved")

    # Save to MongoDB Atlas
    if args.mongodb and mongodb_connected:
        print("\n💾 Finalizing MongoDB data storage...")
        
        # Save final statistics
        stats_success = save_traffic_statistics(final_stats, analysis_id)
        
        # Save violations
        violations_success = save_individual_violations(analyzer.violations, analysis_id)
        
        # Save one final analytics record
        final_analytics = {
            'frame_number': frame_num,
            'vehicles_detected': len(analyzer.all_vehicles_seen),
            'violations_count': sum(len(v) for v in analyzer.violations.values()),
            'processing_time': datetime.datetime.now().isoformat(),
            'status': 'completed'
        }
        save_real_time_analytics(final_analytics, analysis_id)
        
        if stats_success and violations_success:
            print("✅ All final data saved to MongoDB Atlas Cloud")
        else:
            print("⚠️ Some data may not have been saved to MongoDB Atlas")

    # Generate scorecard
    if args.generate_scorecard:
        scorecard_text = generate_accurate_scorecard(final_stats)
        if args.mongodb and mongodb_connected:
            save_premium_scorecard(scorecard_text, analysis_id, final_stats)

    # Auto-launch GUI
    gui_process = None
    if args.auto_gui:
        gui_process = launch_gui()

    # Close MongoDB connection
    if mongodb_connected:
        close_mongodb_connection()

    print("\n🎉 All tasks completed!")
    
    # Keep the script running if GUI is launched
    if gui_process:
        try:
            gui_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped by user")

if __name__ == "__main__":
    main()