#!/usr/bin/env python3
"""
Restart script for sentiment analyzer and dashboard
"""

import subprocess
import os
import time
import psutil

def kill_python_processes():
    """Kill existing Python processes running our services"""
    print("🔄 Stopping existing Python processes...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(script in cmdline for script in ['sentiment_analyzer.py', 'comment_summarizer.py', 'dashboard.py']):
                    print(f"   Stopping {proc.info['pid']}: {cmdline}")
                    proc.kill()
                    time.sleep(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def restart_services():
    """Restart the sentiment analyzer and other services"""
    print("🚀 Starting services...")
    
    # Start sentiment analyzer
    subprocess.Popen(['python', 'youtube_api.py'], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.getcwd())
    print("   ✅ Started Api")
    
    subprocess.Popen(['python', 'sentiment_analyzer.py'], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.getcwd())
    print("   ✅ Started sentiment analyzer")
    
    # Start comment summarizer  
    subprocess.Popen(['python', 'comment_summarizer.py'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE, 
                    cwd=os.getcwd())
    print("   ✅ Started comment summarizer")
    
    # Start dashboard
    subprocess.Popen(['streamlit', 'run', 'dashboard.py'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.getcwd())
    print("   ✅ Started Streamlit dashboard")
    
    print("\n🎯 Services restarted successfully!")
    print("   Dashboard: http://localhost:8501")

if __name__ == "__main__":
    kill_python_processes()
    time.sleep(2)
    restart_services()
