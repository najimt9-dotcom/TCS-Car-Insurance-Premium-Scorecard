🚗 Car Insurance Premium Scorecard – TCS Use Case

📌 Project Overview

The Car Insurance Premium Scorecard is an AI-driven system designed to analyze driver behavior in real time and calculate insurance risk scores. The project uses computer vision, cloud integration, and AI models to monitor driving patterns and support insurance premium calculation.

This project was developed as part of a TCS team use case, focusing on improving road safety and fair insurance pricing.

🎯 Objectives

Monitor real-time driving behavior using camera input

Detect risky driving patterns such as speeding and abnormal vehicle movement

Generate alerts and store driving data securely in the cloud

Calculate driver risk scores for insurance premium determination

⚙️ System Workflow

Camera Setup: A mobile or vehicle-mounted camera captures road and vehicle data

Vehicle Detection: YOLOv7/YOLOv8 detects vehicle position and movement

Behavior Analysis: Speed, braking patterns, and car movement are analyzed

Alert Generation: Risk events trigger alerts and speed data

Cloud Storage: Data is sent in JSON format to Cloud APIs and stored in MongoDB

AI Scoring: LLaMA/Mistral models analyze stored data to compute driver risk scores

🧠 Key Features

Real-time driver behavior monitoring

Vehicle detection and positioning using YOLOv8

Speed and alert data transmission via Cloud APIs

AI-based risk score calculation for insurance premium modeling

Support for driver safety checks, including drunken driving behavior analysis

🛠️ Technologies Used

Programming Language: Python

Computer Vision: YOLOv7, YOLOv8

Database: MongoDB

Cloud: REST APIs, JSON data exchange

AI/ML Models: LLaMA / Mistral

Concepts: Driver Behavior Analysis, Risk Scoring, Insurance Analytics


🚀 Future Enhancements

Integration with live GPS and telematics data

Enhanced drunken driving detection using sensor fusion

Dashboard for insurers to visualize driver scores

Model optimization for real-time edge deployment
