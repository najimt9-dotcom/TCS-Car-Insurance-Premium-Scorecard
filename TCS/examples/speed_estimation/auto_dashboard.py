import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pymongo import MongoClient
import time
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import os

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
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .warning {
        color: #ff4b4b;
        font-weight: bold;
    }
    .success {
        color: #00cc96;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #1f77b4;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .email-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Email Configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "saifkumbay@gmail.com",
    "sender_password": "xbtazshmdrdvfwei",
    "timeout": 30
}

def send_email_from_dashboard(receiver_email, analysis_data):
    """Send email report from dashboard"""
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = receiver_email
        msg['Subject'] = f"Traffic Analysis Report - {analysis_data.get('analysis_id', 'N/A')}"
        
        # Email body
        vehicles_with_violations = analysis_data.get('vehicles_with_violations', 0)
        speeding_count = analysis_data.get('speeding_count', 0)
        high_severity_count = analysis_data.get('high_severity_count', 0)
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                .stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
                .stat-item {{ padding: 8px; background: white; border-radius: 3px; }}
                .warning {{ color: #e74c3c; font-weight: bold; }}
                .success {{ color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚗 Traffic Analysis Report</h1>
                <p><strong>Analysis ID:</strong> {analysis_data.get('analysis_id', 'N/A')}</p>
                <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 Key Statistics</h2>
                <div class="stats">
                    <div class="stat-item"><strong>Total Vehicles:</strong> {analysis_data.get('total_vehicles', 0)}</div>
                    <div class="stat-item"><strong>Zone Vehicles:</strong> {analysis_data.get('vehicles_in_zone', 0)}</div>
                    <div class="stat-item"><strong>Total Violations:</strong> {analysis_data.get('total_violations', 0)}</div>
                    <div class="stat-item"><strong>Max Speed:</strong> {analysis_data.get('max_speed', 0)} km/h</div>
                    <div class="stat-item"><strong>Average Speed:</strong> {analysis_data.get('avg_speed', 0):.2f} km/h</div>
                    <div class="stat-item"><strong>Speeding Violations:</strong> {speeding_count}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🚦 Vehicle Distribution</h2>
                <ul>
        """
        
        # Add vehicle distribution
        vehicle_dist = analysis_data.get('vehicle_distribution', {})
        for vehicle_type, count in vehicle_dist.items():
            body += f"<li><strong>{vehicle_type}:</strong> {count} vehicles</li>"
        
        body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>⚠️ Violations Summary</h2>
                <ul>
                    <li><strong>Vehicles with Violations:</strong> {vehicles_with_violations}</li>
                    <li><strong>Speeding Violations:</strong> {speeding_count}</li>
                    <li><strong>High Severity Violations:</strong> {high_severity_count}</li>
                </ul>
            </div>
            
            <div class="section">
                <p>This report was generated automatically from the Traffic Analytics Dashboard.</p>
                <p>For detailed analysis, please log in to the dashboard system.</p>
            </div>
            
            <footer>
                <p>Best regards,<br><strong>Traffic Analytics System</strong></p>
            </footer>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=EMAIL_CONFIG["timeout"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG["sender_email"], receiver_email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"Email sending failed: {str(e)}")
        return False

# MongoDB Configuration - USING CORRECT WORKING CONNECTION
MONGODB_CONNECTION_STRING = "mongodb+srv://mohammmadsaif22210003_db_user:YaQAoJfXrthGtlu0@cluster0.easchkc.mongodb.net/traffic_analysis?retryWrites=true&w=majority&appName=Cluster0"
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
        st.error(f"❌ MongoDB Connection Failed: {str(e)}")
        return None

def get_latest_statistics(_db):
    """Get the latest traffic statistics"""
    try:
        if _db is None:
            return None
        collection = _db["traffic_statistics"]
        return collection.find_one(sort=[("timestamp", -1)])
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
        return None

def get_violations_data(_db, limit=100):
    """Get violations data"""
    try:
        if _db is None:
            return []
        collection = _db["vehicle_violations"]
        return list(collection.find().sort("timestamp", -1).limit(limit))
    except Exception as e:
        st.error(f"Error fetching violations: {e}")
        return []

def get_analytics_trend(_db, hours=24):
    """Get analytics trend for the last N hours"""
    try:
        if _db is None:
            return []
        collection = _db["real_time_analytics"]
        time_threshold = datetime.now() - timedelta(hours=hours)
        return list(collection.find({"timestamp": {"$gte": time_threshold.isoformat()}}).sort("timestamp", 1))
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")
        return []

def get_vehicle_distribution(_db):
    """Get vehicle distribution data"""
    try:
        if _db is None:
            return {}
        collection = _db["traffic_statistics"]
        latest = collection.find_one(sort=[("timestamp", -1)])
        return latest.get('vehicle_distribution', {}) if latest else {}
    except Exception as e:
        st.error(f"Error fetching vehicle distribution: {e}")
        return {}

def get_speed_analysis(_db):
    """Get speed analysis data"""
    try:
        if _db is None:
            return []
        collection = _db["vehicle_violations"]
        pipeline = [
            {"$group": {
                "_id": "$vehicle_type",
                "avg_speed": {"$avg": "$speed_kmh"},
                "max_speed": {"$max": "$speed_kmh"},
                "min_speed": {"$min": "$speed_kmh"},
                "count": {"$sum": 1}
            }}
        ]
        return list(collection.aggregate(pipeline))
    except Exception as e:
        st.error(f"Error fetching speed analysis: {e}")
        return []

def get_database_stats(_db):
    """Get database statistics"""
    try:
        if _db is None:
            return {}
        stats = {
            "total_statistics": _db.traffic_statistics.count_documents({}),
            "total_violations": _db.vehicle_violations.count_documents({}),
            "total_analytics": _db.real_time_analytics.count_documents({}),
            "total_scorecards": _db.premium_scorecards.count_documents({}),
        }
        return stats
    except Exception as e:
        st.error(f"Error fetching database stats: {e}")
        return {}

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
                f"{max_speed} km/h",
                delta=f"{max_speed - 100} km/h over limit" if max_speed > 100 else None,
                delta_color="inverse" if max_speed > 100 else "normal",
                help="Highest speed detected"
            )
        
        # Email Report Section
        st.markdown("---")
        st.markdown('<div class="section-header">📧 Email Report</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            email_address = st.text_input(
                "📨 Enter email address to send report:",
                placeholder="example@gmail.com",
                help="Enter a valid email address to receive the traffic analysis report"
            )
            
            # Prepare analysis data for email
            analysis_data = {
                'analysis_id': latest_stats.get('analysis_id', 'N/A'),
                'total_vehicles': latest_stats.get('total_vehicles', 0),
                'vehicles_in_zone': latest_stats.get('vehicles_in_zone', 0),
                'total_violations': total_violations,
                'max_speed': max_speed,
                'avg_speed': latest_stats.get('avg_speed', 0),
                'vehicle_distribution': vehicle_distribution,
                'vehicles_with_violations': len(set(v['vehicle_id'] for v in violations_data)),
                'speeding_count': speeding_count,
                'high_severity_count': len([v for v in violations_data if v.get('severity') == 'high'])
            }
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🚀 Send Email Report", use_container_width=True, type="primary"):
                if email_address and "@" in email_address and "." in email_address:
                    with st.spinner("Sending email report..."):
                        success = send_email_from_dashboard(email_address, analysis_data)
                        if success:
                            st.success(f"✅ Report sent successfully to {email_address}!")
                        else:
                            st.error("❌ Failed to send email. Please check email configuration.")
                else:
                    st.warning("⚠️ Please enter a valid email address")
        
        st.info("💡 The email will include key statistics, vehicle distribution, and violations summary.")
        
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
                    df_speed = df_speed.rename(columns={'_id': 'Vehicle Type'})
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
                    labels={'x': 'Severity Level', 'y': 'Count'},
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
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Risk Level: {risk_level}", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': risk_color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 30], 'color': 'lightgreen'},
                        {'range': [30, 70], 'color': 'yellow'},
                        {'range': [70, 100], 'color': 'lightcoral'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
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
                st.write(f"**Analysis ID:** {latest_stats.get('analysis_id', 'N/A')}")
                st.write(f"**Processing Time:** {latest_stats.get('processing_time', 'N/A')}")
                st.write(f"**Status:** {latest_stats.get('status', 'N/A')}")
                st.write(f"**Database Records:**")
                st.write(f"  - Statistics: {db_stats.get('total_statistics', 0)}")
                st.write(f"  - Violations: {db_stats.get('total_violations', 0)}")
                st.write(f"  - Analytics: {db_stats.get('total_analytics', 0)}")
                st.write(f"  - Scorecards: {db_stats.get('total_scorecards', 0)}")
    
    else:
        st.error("❌ No data found in the database. Please run the traffic analysis first.")
        
else:
    # Fallback to local data when MongoDB is not available
    st.warning("⚠️ Running in offline mode with local data")
    
    try:
        with open('ultimate_traffic_data.json', 'r') as f:
            local_data = json.load(f)
            stats = local_data.get('statistics', {})
            violations = local_data.get('violations', {})
        
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
            st.metric("Max Speed", f"{stats.get('max_speed', 0)} km/h")
        
        # Email section for local data
        st.markdown("---")
        st.markdown('<div class="section-header">📧 Email Report</div>', unsafe_allow_html=True)
        
        email_address = st.text_input(
            "📨 Enter email address to send report:",
            placeholder="example@gmail.com",
            help="Enter a valid email address to receive the traffic analysis report"
        )
        
        if st.button("🚀 Send Email Report", type="primary"):
            if email_address and "@" in email_address and "." in email_address:
                st.info("📧 Email feature requires MongoDB connection for full functionality")
                st.warning("Please ensure MongoDB is connected for email reports")
            else:
                st.warning("⚠️ Please enter a valid email address")
        
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

# Email configuration instructions
with st.sidebar.expander("📧 Email Setup"):
    st.markdown("""
    **To enable email reports:**
    
    1. Update `EMAIL_CONFIG` in the dashboard code:
    ```python
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_gmail_app_password",
    ```
    
    2. Use Gmail App Password (not regular password)
    3. Enable 2-factor authentication in Gmail
    4. Generate App Password from Google Account settings
    """)
