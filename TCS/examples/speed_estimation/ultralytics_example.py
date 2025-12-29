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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ======================= EMAIL CONFIGURATION =======================
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "email",
    "sender_password": "password",
    "timeout": 30
}

# ======================= DOCUMENT GENERATION FUNCTIONS =======================
def generate_nodejs_output_txt(analysis_id, stats, violations_data):
    """Generate TXT file with Node.js style output"""
    try:
        filename = f"nodejs_output_{analysis_id}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"🚗 TRAFFIC ANALYSIS REPORT - {analysis_id}\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("📊 EXECUTIVE SUMMARY\n")
            f.write("-" * 50 + "\n")
            f.write(f"Total Vehicles Detected: {stats.get('total_vehicles_detected', 0)}\n")
            f.write(f"Vehicles in Monitoring Zone: {stats.get('vehicles_in_zone', 0)}\n")
            f.write(f"Total Violations Recorded: {stats.get('total_unique_violations', 0)}\n")
            f.write(f"Vehicles with Violations: {stats.get('vehicles_with_violations', 0)}\n")
            f.write(f"Maximum Speed Detected: {stats.get('max_speed', 0)} km/h\n")
            f.write(f"Average Speed: {stats.get('avg_speed', 0):.2f} km/h\n")
            f.write(f"Processing Duration: {stats.get('processing_duration', 0):.2f} seconds\n\n")
            
            f.write("🚦 VEHICLE DISTRIBUTION ANALYSIS\n")
            f.write("-" * 50 + "\n")
            vehicle_dist = stats.get('vehicle_class_distribution', {})
            if vehicle_dist:
                total_vehicles = stats.get('total_vehicles_detected', 1)
                for vehicle_type, count in vehicle_dist.items():
                    percentage = (count / total_vehicles) * 100
                    f.write(f"• {vehicle_type}: {count} vehicles ({percentage:.1f}%)\n")
            else:
                f.write("No vehicle distribution data available\n")
            f.write("\n")
            
            f.write("⚠️ TRAFFIC VIOLATIONS ANALYSIS\n")
            f.write("-" * 50 + "\n")
            speeding_count = sum(1 for violations_list in violations_data.values() 
                               for v in violations_list if v.get('speed_kmh', 0) > 100)
            high_severity = sum(1 for violations_list in violations_data.values() 
                              for v in violations_list if v.get('speed_kmh', 0) > 120)
            
            f.write(f"Total Violations: {stats.get('total_unique_violations', 0)}\n")
            f.write(f"Speeding Violations (>100 km/h): {speeding_count}\n")
            f.write(f"High Severity Violations (>120 km/h): {high_severity}\n")
            f.write(f"Vehicles with Multiple Violations: {stats.get('vehicles_with_violations', 0)}\n\n")
            
            f.write("📈 PERFORMANCE METRICS\n")
            f.write("-" * 50 + "\n")
            
            # Calculate performance scores
            total_vehicles = stats.get('total_vehicles_detected', 1)
            violation_rate = (stats.get('total_unique_violations', 0) / total_vehicles) * 100
            avg_speed = stats.get('avg_speed', 0)
            max_speed = stats.get('max_speed', 0)
            
            safety_score = max(0, 100 - violation_rate * 2)
            efficiency_score = min(100, (avg_speed / 80) * 100) if avg_speed > 0 else 0
            compliance_score = 100 if max_speed <= 100 else max(0, 100 - (max_speed - 100))
            overall_score = (safety_score + efficiency_score + compliance_score) / 3
            
            f.write(f"Safety Score: {safety_score:.1f}% - {'Excellent' if safety_score >= 90 else 'Good' if safety_score >= 70 else 'Needs Improvement'}\n")
            f.write(f"Efficiency Score: {efficiency_score:.1f}% - {'Optimal' if efficiency_score >= 80 else 'Good' if efficiency_score >= 60 else 'Low'}\n")
            f.write(f"Compliance Score: {compliance_score:.1f}% - {'High' if compliance_score >= 90 else 'Medium' if compliance_score >= 70 else 'Low'}\n")
            f.write(f"Overall Score: {overall_score:.1f}% - {'Excellent' if overall_score >= 85 else 'Good' if overall_score >= 70 else 'Needs Attention'}\n\n")
            
            f.write("💡 RECOMMENDATIONS\n")
            f.write("-" * 50 + "\n")
            
            recommendations = []
            if violation_rate > 20:
                recommendations.append("• Implement stricter speed enforcement measures")
            if max_speed > 120:
                recommendations.append("• Consider speed calming infrastructure")
            if avg_speed < 40:
                recommendations.append("• Review traffic flow optimization")
            if stats.get('vehicles_with_violations', 0) > 10:
                recommendations.append("• Enhance driver awareness campaigns")
            
            if not recommendations:
                recommendations.append("• Current traffic management appears effective")
                recommendations.append("• Continue monitoring and maintenance")
            
            for rec in recommendations:
                f.write(rec + "\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("Generated by Traffic Analysis System | Professional Report\n")
            f.write("=" * 70 + "\n")
        
        print(f"✅ Node.js Output TXT generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error generating Node.js output TXT: {e}")
        return None

def generate_premium_scorecard_txt(scorecard_text, analysis_id, stats):
    """Generate TXT file for premium scorecard"""
    try:
        filename = f"premium_scorecard_{analysis_id}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("🏆 PREMIUM MANAGEMENT SCORECARD 🏆\n")
            f.write("=" * 70 + "\n")
            f.write(f"Analysis ID: {analysis_id}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("EXECUTIVE ANALYSIS\n")
            f.write("-" * 50 + "\n")
            
            # Split scorecard text into paragraphs
            paragraphs = scorecard_text.split('\n')
            for para in paragraphs:
                if para.strip():  # Skip empty lines
                    f.write(para.strip() + "\n")
            
            f.write("\n")
            f.write("📈 PERFORMANCE METRICS\n")
            f.write("-" * 50 + "\n")
            
            # Calculate performance scores
            total_vehicles = stats.get('total_vehicles_detected', 1)
            violation_rate = (stats.get('total_unique_violations', 0) / total_vehicles) * 100
            avg_speed = stats.get('avg_speed', 0)
            max_speed = stats.get('max_speed', 0)
            
            # Performance scoring
            safety_score = max(0, 100 - violation_rate * 2)
            efficiency_score = min(100, (avg_speed / 80) * 100) if avg_speed > 0 else 0
            compliance_score = 100 if max_speed <= 100 else max(0, 100 - (max_speed - 100))
            overall_score = (safety_score + efficiency_score + compliance_score) / 3
            
            f.write(f"Safety Score: {safety_score:.1f}% - {'Excellent' if safety_score >= 90 else 'Good' if safety_score >= 70 else 'Needs Improvement'}\n")
            f.write(f"Efficiency Score: {efficiency_score:.1f}% - {'Optimal' if efficiency_score >= 80 else 'Good' if efficiency_score >= 60 else 'Low'}\n")
            f.write(f"Compliance Score: {compliance_score:.1f}% - {'High' if compliance_score >= 90 else 'Medium' if compliance_score >= 70 else 'Low'}\n")
            f.write(f"Overall Score: {overall_score:.1f}% - {'Excellent' if overall_score >= 85 else 'Good' if overall_score >= 70 else 'Needs Attention'}\n\n")
            
            f.write("💡 MANAGEMENT RECOMMENDATIONS\n")
            f.write("-" * 50 + "\n")
            
            recommendations = []
            if violation_rate > 20:
                recommendations.append("• Implement stricter speed enforcement measures")
            if max_speed > 120:
                recommendations.append("• Consider speed calming infrastructure")
            if avg_speed < 40:
                recommendations.append("• Review traffic flow optimization")
            if stats.get('vehicles_with_violations', 0) > 10:
                recommendations.append("• Enhance driver awareness campaigns")
            
            if not recommendations:
                recommendations.append("• Current traffic management appears effective")
                recommendations.append("• Continue monitoring and maintenance")
            
            for rec in recommendations:
                f.write(rec + "\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("Generated by Traffic Analysis System | Premium Analytics Suite\n")
            f.write("=" * 70 + "\n")
        
        print(f"✅ Premium Scorecard TXT generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error generating premium scorecard TXT: {e}")
        return None

def generate_html_report(analysis_id, stats, violations_data, scorecard_text):
    """Generate HTML report"""
    try:
        filename = f"traffic_report_{analysis_id}.html"
        
        # Calculate additional statistics
        total_violations = stats.get('total_unique_violations', 0)
        speeding_count = sum(1 for violations_list in violations_data.values() 
                           for v in violations_list if v.get('speed_kmh', 0) > 100)
        high_severity = sum(1 for violations_list in violations_data.values() 
                          for v in violations_list if v.get('speed_kmh', 0) > 120)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Traffic Analysis Report - {analysis_id}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                    font-size: 2.5em;
                }}
                .section {{
                    margin: 30px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }}
                .section h2 {{
                    color: #2c3e50;
                    margin-top: 0;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 10px 0;
                }}
                .stat-label {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
                .vehicle-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin: 15px 0;
                }}
                .vehicle-item {{
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                    border-left: 3px solid #3498db;
                }}
                .recommendations {{
                    background: #e8f4fc;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
                .warning {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .success {{
                    color: #27ae60;
                    font-weight: bold;
                }}
                .info {{
                    color: #3498db;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Traffic Analysis Report</h1>
                    <p><strong>Analysis ID:</strong> {analysis_id}</p>
                    <p><strong>Generated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="section">
                    <h2>📊 Executive Summary</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('total_vehicles_detected', 0)}</div>
                            <div class="stat-label">Total Vehicles</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{total_violations}</div>
                            <div class="stat-label">Total Violations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('max_speed', 0)} km/h</div>
                            <div class="stat-label">Max Speed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{speeding_count}</div>
                            <div class="stat-label">Speeding Cases</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🚦 Vehicle Distribution</h2>
                    <div class="vehicle-list">
        """
        
        # Add vehicle distribution
        vehicle_dist = stats.get('vehicle_class_distribution', {})
        for vehicle_type, count in vehicle_dist.items():
            html_content += f"""
                        <div class="vehicle-item">
                            <strong>{vehicle_type}</strong><br>
                            {count} vehicles
                        </div>
            """
        
        html_content += f"""
                    </div>
                </div>
                
                <div class="section">
                    <h2>⚠️ Violations Analysis</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('vehicles_with_violations', 0)}</div>
                            <div class="stat-label">Vehicles with Violations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{speeding_count}</div>
                            <div class="stat-label">Speeding Violations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{high_severity}</div>
                            <div class="stat-label">High Severity</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('avg_speed', 0):.1f} km/h</div>
                            <div class="stat-label">Average Speed</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📈 Performance Metrics</h2>
        """
        
        # Calculate performance scores
        total_vehicles = stats.get('total_vehicles_detected', 1)
        violation_rate = (stats.get('total_unique_violations', 0) / total_vehicles) * 100
        avg_speed = stats.get('avg_speed', 0)
        max_speed = stats.get('max_speed', 0)
        
        safety_score = max(0, 100 - violation_rate * 2)
        efficiency_score = min(100, (avg_speed / 80) * 100) if avg_speed > 0 else 0
        compliance_score = 100 if max_speed <= 100 else max(0, 100 - (max_speed - 100))
        overall_score = (safety_score + efficiency_score + compliance_score) / 3
        
        html_content += f"""
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value { 'success' if safety_score >= 80 else 'warning' if safety_score >= 60 else 'warning' }">{safety_score:.1f}%</div>
                            <div class="stat-label">Safety Score</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value { 'success' if efficiency_score >= 70 else 'warning' if efficiency_score >= 50 else 'warning' }">{efficiency_score:.1f}%</div>
                            <div class="stat-label">Efficiency Score</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value { 'success' if compliance_score >= 80 else 'warning' if compliance_score >= 60 else 'warning' }">{compliance_score:.1f}%</div>
                            <div class="stat-label">Compliance Score</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value { 'success' if overall_score >= 70 else 'warning' if overall_score >= 50 else 'warning' }">{overall_score:.1f}%</div>
                            <div class="stat-label">Overall Score</div>
                        </div>
                    </div>
                </div>
                
                <div class="recommendations">
                    <h2>💡 Management Recommendations</h2>
                    <ul>
        """
        
        recommendations = []
        if violation_rate > 20:
            recommendations.append("<li>Implement stricter speed enforcement measures</li>")
        if max_speed > 120:
            recommendations.append("<li>Consider speed calming infrastructure</li>")
        if avg_speed < 40:
            recommendations.append("<li>Review traffic flow optimization</li>")
        if stats.get('vehicles_with_violations', 0) > 10:
            recommendations.append("<li>Enhance driver awareness campaigns</li>")
        
        if not recommendations:
            recommendations.append("<li>Current traffic management appears effective</li>")
            recommendations.append("<li>Continue monitoring and maintenance</li>")
        
        for rec in recommendations:
            html_content += rec
        
        html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🏆 Executive Scorecard</h2>
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 15px 0;">
                        <pre style="white-space: pre-wrap; font-family: inherit;">{scorecard_text}</pre>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This report was automatically generated by the Traffic Analysis System</p>
                    <p>For detailed analytics and real-time monitoring, access the dashboard system</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML Report generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error generating HTML report: {e}")
        return None

def send_email_with_documents(receiver_email, analysis_id, stats, violations_data, scorecard_text):
    """Send email with document attachments"""
    json_filename = None
    nodejs_txt_filename = None
    scorecard_txt_filename = None
    html_filename = None
    
    try:
        print(f"📧 Preparing comprehensive email report to {receiver_email}...")
        
        # Validate email parameters
        if not receiver_email or "@" not in receiver_email:
            print("❌ Invalid recipient email address")
            return False
            
        # Generate documents
        print("📄 Generating document reports...")
        nodejs_txt_filename = generate_nodejs_output_txt(analysis_id, stats, violations_data)
        scorecard_txt_filename = generate_premium_scorecard_txt(scorecard_text, analysis_id, stats)
        html_filename = generate_html_report(analysis_id, stats, violations_data, scorecard_text)
        
        if not nodejs_txt_filename or not scorecard_txt_filename:
            print("❌ Document generation failed, sending email without documents")
            # Fallback to regular email without documents
            return send_email_report(receiver_email, analysis_id, stats, violations_data)
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = receiver_email
        msg['Subject'] = f"🚗 Comprehensive Traffic Analysis Report - {analysis_id}"
        
        # Calculate additional statistics for email
        total_violations = stats.get('total_unique_violations', 0)
        speeding_count = sum(1 for violations_list in violations_data.values() 
                           for v in violations_list if v.get('speed_kmh', 0) > 100)
        
        # Enhanced Email Body
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 15px; 
                    text-align: center;
                }}
                .section {{ 
                    margin: 25px 0; 
                    padding: 20px; 
                    background-color: #f8f9fa; 
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(2, 1fr); 
                    gap: 15px; 
                    margin-top: 15px;
                }}
                .stat-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-top: 5px;
                }}
                .warning {{ color: #e74c3c; font-weight: bold; }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .info {{ color: #3498db; font-weight: bold; }}
                .attachments {{
                    background: #e8f4fc;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Comprehensive Traffic Analysis Report</h1>
                    <p><strong>Analysis ID:</strong> {analysis_id}</p>
                    <p><strong>Generated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="section">
                    <h2>📊 Executive Summary</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('total_vehicles_detected', 0)}</div>
                            <div class="stat-label">Total Vehicles</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{total_violations}</div>
                            <div class="stat-label">Total Violations</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{stats.get('max_speed', 0)} km/h</div>
                            <div class="stat-label">Max Speed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{speeding_count}</div>
                            <div class="stat-label">Speeding Cases</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📎 Report Attachments</h2>
                    <div class="attachments">
                        <p><strong>📄 Detailed Analysis Report (TXT):</strong> Comprehensive statistics and violation data</p>
                        <p><strong>🏆 Premium Management Scorecard (TXT):</strong> Executive summary with performance metrics</p>
                        <p><strong>🌐 Interactive HTML Report:</strong> Visual report with charts and analysis</p>
                        <p><strong>📊 JSON Data File:</strong> Complete dataset for further analysis</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🚦 Key Findings</h2>
                    <ul>
                        <li><strong>Vehicle Distribution:</strong> {len(stats.get('vehicle_class_distribution', {}))} different vehicle types detected</li>
                        <li><strong>Violation Rate:</strong> {(total_violations / max(1, stats.get('total_vehicles_detected', 1)) * 100):.1f}% of vehicles had violations</li>
                        <li><strong>Average Speed:</strong> {stats.get('avg_speed', 0):.1f} km/h across all vehicles</li>
                        <li><strong>Processing Efficiency:</strong> Analysis completed in {stats.get('processing_duration', 0):.2f} seconds</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>This report was automatically generated by the Traffic Analysis System</p>
                    <p>For detailed analytics and real-time monitoring, access the dashboard system</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Create JSON attachment
        json_data = {
            'analysis_id': analysis_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'statistics': stats,
            'violations': violations_data,
            'vehicle_distribution': stats.get('vehicle_class_distribution', {}),
            'email_sent_to': receiver_email,
            'email_sent_at': datetime.datetime.now().isoformat(),
            'document_reports_generated': True
        }
        
        json_filename = f"traffic_data_{analysis_id}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, cls=NumpyEncoder)
            print(f"✅ JSON data saved: {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {e}")
            return False
        
        # Attach all files
        attachments = [
            (nodejs_txt_filename, "Detailed_Analysis_Report.txt"),
            (scorecard_txt_filename, "Premium_Management_Scorecard.txt"),
            (html_filename, "Interactive_Report.html"),
            (json_filename, "Complete_Analysis_Data.json")
        ]
        
        for file_path, display_name in attachments:
            try:
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={display_name}",
                    )
                    msg.attach(part)
                    print(f"✅ Attached: {display_name}")
            except Exception as e:
                print(f"❌ Error attaching {display_name}: {e}")
                continue
        
        # Send email
        print("🚀 Connecting to SMTP server...")
        try:
            server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=EMAIL_CONFIG["timeout"])
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            print("🔐 Logging in to email account...")
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            
            print("📤 Sending comprehensive email report...")
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG["sender_email"], receiver_email, text)
            server.quit()
            
            print("✅ Comprehensive email with documents sent successfully!")
            
            # Clean up temporary files
            files_to_clean = [json_filename, nodejs_txt_filename, scorecard_txt_filename, html_filename]
            for file_path in files_to_clean:
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"🗑️ Cleaned up: {file_path}")
                except Exception as e:
                    print(f"⚠️ Could not remove {file_path}: {e}")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("💡 Please check your email and password (use App Password for Gmail)")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Unexpected error in email function: {e}")
        # Clean up temporary files in case of error
        files_to_clean = [json_filename, nodejs_txt_filename, scorecard_txt_filename, html_filename]
        for file_path in files_to_clean:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        return False

def send_email_report(receiver_email, analysis_id, stats, violations_data):
    """Send email with JSON and statistics reports (fallback function)"""
    json_filename = None
    try:
        print(f"📧 Preparing email report to {receiver_email}...")
        
        # Validate email parameters
        if not receiver_email or "@" not in receiver_email:
            print("❌ Invalid recipient email address")
            return False
            
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = receiver_email
        msg['Subject'] = f"Traffic Analysis Report - {analysis_id}"
        
        # Calculate additional statistics for email
        total_violations = stats.get('total_unique_violations', 0)
        speeding_count = sum(1 for violations_list in violations_data.values() 
                           for v in violations_list if v.get('speed_kmh', 0) > 100)
        
        # Email body with improved formatting
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
                <p><strong>Analysis ID:</strong> {analysis_id}</p>
                <p><strong>Timestamp:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 Summary Statistics:</h2>
                <div class="stats">
                    <div class="stat-item"><strong>Total Vehicles:</strong> {stats.get('total_vehicles_detected', 0)}</div>
                    <div class="stat-item"><strong>Total Violations:</strong> {total_violations}</div>
                    <div class="stat-item"><strong>Speeding Violations:</strong> {speeding_count}</div>
                    <div class="stat-item"><strong>Max Speed:</strong> {stats.get('max_speed', 0)} km/h</div>
                    <div class="stat-item"><strong>Average Speed:</strong> {stats.get('avg_speed', 0):.2f} km/h</div>
                    <div class="stat-item"><strong>Processing Duration:</strong> {stats.get('processing_duration', 0):.2f} seconds</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🚦 Vehicle Distribution:</h2>
                <ul>
        """
        
        # Add vehicle distribution
        vehicle_dist = stats.get('vehicle_class_distribution', {})
        for vehicle_type, count in vehicle_dist.items():
            body += f"<li><strong>{vehicle_type}:</strong> {count} vehicles</li>"
        
        body += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>⚠️ Violations Overview</h2>
                <p><strong>Vehicles with Violations:</strong> {stats.get('vehicles_with_violations', 0)}</p>
                <p><strong>Risk Level:</strong> <span class="{'warning' if total_violations > 200 else 'success'}">
                    {'High' if total_violations > 200 else 'Medium' if total_violations > 100 else 'Low'}
                </span></p>
            </div>
            
            <div class="section">
                <p>Complete analysis data is attached as a JSON file.</p>
                <p>For detailed analytics, please access the Traffic Analytics Dashboard.</p>
            </div>
            
            <footer>
                <p>Best regards,<br><strong>Traffic Analysis System</strong></p>
            </footer>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Create JSON attachment
        json_data = {
            'analysis_id': analysis_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'statistics': stats,
            'violations': violations_data,
            'vehicle_distribution': stats.get('vehicle_class_distribution', {}),
            'email_sent_to': receiver_email,
            'email_sent_at': datetime.datetime.now().isoformat()
        }
        
        json_filename = f"traffic_data_{analysis_id}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, cls=NumpyEncoder)
            print(f"✅ JSON data saved: {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON file: {e}")
            return False
        
        # Attach JSON file
        try:
            with open(json_filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={json_filename}",
            )
            msg.attach(part)
            print(f"✅ Attached: {json_filename}")
        except Exception as e:
            print(f"❌ Error attaching {json_filename}: {e}")
            return False
        
        # Send email with better error handling
        print("🚀 Connecting to SMTP server...")
        try:
            server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=EMAIL_CONFIG["timeout"])
            server.ehlo()  # Identify ourselves to the SMTP server
            server.starttls()  # Secure the connection
            server.ehlo()  # Re-identify ourselves over TLS connection
            
            print("🔐 Logging in to email account...")
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            
            print("📤 Sending email...")
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG["sender_email"], receiver_email, text)
            server.quit()
            
            print("✅ Email sent successfully!")
            
            # Clean up temporary file
            try:
                if json_filename and os.path.exists(json_filename):
                    os.remove(json_filename)
                    print(f"🗑️ Temporary file cleaned up: {json_filename}")
            except Exception as e:
                print(f"⚠️ Could not remove temporary file: {e}")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("💡 Please check your email and password (use App Password for Gmail)")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Unexpected error in email function: {e}")
        # Clean up temporary file in case of error
        try:
            if json_filename and os.path.exists(json_filename):
                os.remove(json_filename)
        except:
            pass
        return False

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
TWILIO_ACCOUNT_SID = "Twilo_account_sid"
TWILIO_AUTH_TOKEN = "Twilio_Token"
TWILIO_PHONE_NUMBER = "Twilo no"
MY_PHONE_NUMBER = "+91phone no"
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
            "Authorization": "api_key"
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
    working_connection = "working connection string"
    
    dashboard_code = '''import streamlit as st
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
    "sender_email": "email",
    "sender_password": "password",
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
MONGODB_CONNECTION_STRING = "''' + working_connection + '''"
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
'''
    
    with open("auto_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("✅ Dashboard generated with CORRECT MongoDB connection and Email feature")

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
        print("📧 NEW FEATURE: Email reports directly from the dashboard!")
        print("🎨 Features: Real-time stats, Speed analysis, Risk assessment, Violations tracking, Email reports")
        
        # Give user instructions
        print("\n💡 If the browser doesn't open automatically, please visit:")
        print("   🌐 http://localhost:8501")
        print("\n📧 To send email reports:")
        print("   1. Look for 'Email Report' section in the dashboard")
        print("   2. Enter recipient email address")
        print("   3. Click 'Send Email Report' button")
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
    parser.add_argument("--send_email", action="store_true", default=False, help="Send email report with documents")
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
    scorecard_text = ""
    if args.generate_scorecard:
        scorecard_text = generate_accurate_scorecard(final_stats)
        if args.mongodb and mongodb_connected:
            save_premium_scorecard(scorecard_text, analysis_id, final_stats)

    # Send email report with documents
    if args.send_email:
        receiver_email = input("Enter email address to send comprehensive document report: ")
        if receiver_email:
            print(f"\n📧 Sending comprehensive email report with documents to {receiver_email}...")
            email_success = send_email_with_documents(receiver_email, analysis_id, final_stats, analyzer.violations, scorecard_text)
            if email_success:
                print("✅ Comprehensive email with documents sent successfully!")
            else:
                print("⚠️ Email report could not be sent")

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