# simulate_gpu_nodes.py
import requests
import time

base_url = "http://127.0.0.1:5000"

def register_gpus():
    print("Registering GPUs with the control plane...")
    for i in range(8): # Register 4 GPUs
        try:
            response = requests.post(f"{base_url}/register", json={"node_id": f"gpu_{i}"})
            print(f"Status: {response.status_code}, Response: {response.json()}")
        except requests.exceptions.ConnectionError:
            print("Could not connect to the control plane server. Is it running?")
            break
        time.sleep(0.5) # Small delay between registrations

if __name__ == '__main__':
    register_gpus()
    print("GPU registration simulation finished.")