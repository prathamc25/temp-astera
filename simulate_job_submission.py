# simulate_job_submission.py
import requests
import time

base_url = "http://127.0.0.1:5000"

def submit_jobs():
    job_durations = [
        15, 8, 12, 5, 10,    # Quick jobs
        25, 18, 30, 7, 22,   # Medium jobs  
        40, 35, 28, 12, 45,  # Longer jobs
        6, 20, 15, 8, 32,    # Mixed durations
        50, 18, 10, 25, 38,  # More variety
        12, 28, 15, 42, 7,   # Continuing mix
        22, 35, 8, 18, 30    # Final set
    ] # Simulated seconds of work for each job
    print("Submitting jobs to the queue...")
    
    for i, dur in enumerate(job_durations):
        try:
            response = requests.post(f"{base_url}/submit", json={"job_id": f"job_{i}", "duration": dur})
            print(f"Submitted job_{i} (Duration: {dur}s). Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Could not connect to the control plane server. Is it running?")
            break
        time.sleep(2) # Wait 2 seconds between submissions to simulate intermittent workload

if __name__ == '__main__':
    submit_jobs()
    print("Job submission simulation finished.")