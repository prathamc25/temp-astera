# dashboard.py
import requests
import time
import os
from datetime import datetime

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_system_status():
    """Fetch current system status from control plane"""
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=2)
        return response.json()
    except:
        return None

def display_dashboard():
    """Display a dynamic monitoring dashboard"""
    while True:
        clear_screen()
        status = get_system_status()
        
        if not status:
            print("❌ Cannot connect to control plane. Is it running?")
            time.sleep(2)
            continue
        
        current_time = datetime.now().strftime("%H:%M:%S")
        print("=" * 80)
        print(f"🚀 GPU CLUSTER MONITORING DASHBOARD - {current_time}")
        print("=" * 80)
        
        # Display queue status
        print(f"\n📊 QUEUE STATUS: {status['job_queue_length']} jobs waiting")
        print("-" * 40)
        
        # Display GPU status
        print("\n🔧 GPU STATUS:")
        print("-" * 40)
        for gpu_id, gpu_info in status['gpus'].items():
            state_icon = "🟢" if gpu_info['state'] == 'idle' else "🔴"
            job_info = f"job: {gpu_info['current_job']}" if gpu_info['current_job'] else "idle"
            temp = gpu_info['telemetry']['temperature']
            power = gpu_info['telemetry']['power_draw']
            util = gpu_info['telemetry']['utilization']
            
            print(f"{state_icon} {gpu_id}: {job_info:20} | 🌡{temp:5.1f}°C | ⚡{power:4}W | 📈{util:3}%")
        
        # Display summary
        idle_gpus = sum(1 for gpu in status['gpus'].values() if gpu['state'] == 'idle')
        busy_gpus = len(status['gpus']) - idle_gpus
        
        print(f"\n📈 SUMMARY: {busy_gpus} busy, {idle_gpus} idle, {status['job_queue_length']} queued")
        print("=" * 80)
        print("🔄 Auto-refreshing every 2 seconds... (Ctrl+C to stop)")
        
        time.sleep(2)  # Refresh every 2 seconds

if __name__ == '__main__':
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")