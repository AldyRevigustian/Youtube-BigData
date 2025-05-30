#!/usr/bin/env python3
"""
Main launcher script for the YouTube Sentiment Analysis System
Run this from the root directory to start all services
"""

import subprocess
import os
import time
import sys

def start_services():
    """Start all system services"""
    print("🚀 Starting YouTube Sentiment Analysis System...")
    print("=" * 50)
    
    # Get current directory (should be root)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    services = [
        ("YouTube API", os.path.join(root_dir, "ingestion", "youtube_api.py")),
        ("Sentiment Analyzer", os.path.join(root_dir, "processing", "sentiment_analyzer.py")),
        ("Comment Summarizer", os.path.join(root_dir, "processing", "comment_summarizer.py")),
    ]
    
    processes = []
    
    # Start Python services
    for service_name, script_path in services:
        try:
            if os.name == 'nt':  # Windows
                proc = subprocess.Popen(
                    [sys.executable, script_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=root_dir
                )
            else:  # Unix/Linux
                proc = subprocess.Popen(
                    [sys.executable, script_path],
                    cwd=root_dir
                )
            processes.append((service_name, proc))
            print(f"   ✅ Started {service_name}")
            time.sleep(2)  # Give each service time to start
        except Exception as e:
            print(f"   ❌ Failed to start {service_name}: {e}")
    
    # Start Streamlit Dashboard
    try:
        dashboard_path = os.path.join(root_dir, "dashboard", "dashboard.py")
        if os.name == 'nt':  # Windows
            dashboard_proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=root_dir
            )
        else:  # Unix/Linux
            dashboard_proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_path],
                cwd=root_dir
            )
        processes.append(("Streamlit Dashboard", dashboard_proc))
        print("   ✅ Started Streamlit Dashboard")
    except Exception as e:
        print(f"   ❌ Failed to start Dashboard: {e}")
    
    print("\n🎯 All services started successfully!")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:8501")
    print("⚡ Storm UI: http://localhost:8080")
    print("🔧 To stop services, close the console windows or press Ctrl+C")
    
    return processes

if __name__ == "__main__":
    try:
        processes = start_services()
        
        # Keep main script running
        print("\n⏳ System running... Press Ctrl+C to exit")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        for service_name, proc in processes:
            try:
                proc.terminate()
                print(f"   ✅ Stopped {service_name}")
            except:
                pass
        print("🔴 System shutdown complete")
