# control_plane_server.py
from flask import Flask, request, jsonify
import simpy
import threading
import time
from enum import Enum
import random

# --- SimPy GPU Simulator Definition ---
class GPUState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"

class GPUSimulator:
    def __init__(self, env, node_id, base_temp=30, base_power=50):
        self.env = env
        self.node_id = node_id
        self.state = GPUState.IDLE
        self.current_job = None

        # Base telemetry values
        self.temperature = base_temp
        self.power_draw = base_power
        self.utilization = 0
        self.memory_allocated = 0
        self.memory_total = 16 * 1024  # 16 GB

        # Start the telemetry update process
        self.action = env.process(self.update_telemetry())

    def update_telemetry(self):
        """A process that simulates changing telemetry over time."""
        while True:
            # Simulate telemetry changes based on state
            if self.state == GPUState.BUSY:
                self.temperature = min(95, self.temperature + random.uniform(0.5, 2.0))
                self.power_draw = random.randint(200, 300)
                self.utilization = random.randint(80, 100)
                self.memory_allocated = self.memory_total * 0.8  # 80% allocated
            else:
                self.temperature = max(25, self.temperature - random.uniform(0.1, 0.5))
                self.power_draw = random.randint(40, 60)
                self.utilization = 0
                self.memory_allocated = 0

            # Wait for a simulated second before updating again
            yield self.env.timeout(1)

    def execute_job(self, job_id, duration):
        """Simulates executing a job for a given duration."""
        if self.state == GPUState.BUSY:
            return False  # Failed to start job

        self.state = GPUState.BUSY
        self.current_job = job_id
        print(f"GPU {self.node_id}: Started job {job_id} at time {self.env.now}")

        # This is the core execution: wait for the 'duration' of the job
        yield self.env.timeout(duration)

        # Job is finished
        self.state = GPUState.IDLE
        self.current_job = None
        print(f"GPU {self.node_id}: Finished job {job_id} at time {self.env.now}")
        return True

# --- Flask Control Plane Server ---
app = Flask(__name__)

# Global structures
job_queue = []  # Simple list acting as a FIFO queue
gpu_registry = {}  # Maps GPU ID to its simulator object and info
env = simpy.Environment()  # The core SimPy environment

# Start the simulation environment in a separate thread
def sim_thread(env):
    print("SimPy environment started.")
    env.run(until=1000)  # Run for a long simulated time

sim_thread = threading.Thread(target=sim_thread, args=(env,))
sim_thread.daemon = True
sim_thread.start()

# --- REST API Endpoints ---
@app.route('/register', methods=['POST'])
def register_gpu():
    data = request.get_json()
    node_id = data['node_id']

    # Create a new simulator instance for this GPU
    gpu_sim = GPUSimulator(env, node_id)
    gpu_registry[node_id] = {
        'sim_obj': gpu_sim,
        'state': gpu_sim.state,
        'telemetry': {
            'temperature': gpu_sim.temperature,
            'power_draw': gpu_sim.power_draw,
            'utilization': gpu_sim.utilization
        }
    }
    print(f"GPU {node_id} registered successfully.")
    return jsonify({"message": f"GPU {node_id} registered successfully"}), 201

@app.route('/submit', methods=['POST'])
def submit_job():
    data = request.get_json()
    job_id = data['job_id']
    duration = data['duration']  # Simulated job length

    # Add job to the queue
    job_queue.append({'job_id': job_id, 'duration': duration})
    print(f"Job {job_id} added to queue. Queue length: {len(job_queue)}")
    return jsonify({"message": "Job submitted"}), 202

@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint to get the current system status (queue and GPU states)"""
    status = {
        'job_queue_length': len(job_queue),
        'gpus': {}
    }
    for gpu_id, gpu_info in gpu_registry.items():
        status['gpus'][gpu_id] = {
            'state': gpu_info['sim_obj'].state.value,
            'current_job': gpu_info['sim_obj'].current_job,
            'telemetry': {
                'temperature': gpu_info['sim_obj'].temperature,
                'power_draw': gpu_info['sim_obj'].power_draw,
                'utilization': gpu_info['sim_obj'].utilization
            }
        }
    return jsonify(status), 200

# --- Core FIFO Scheduler Loop ---
def scheduler_loop():
    print("FIFO Scheduler loop started.")
    while True:
        if job_queue and gpu_registry:
            # 1. Find the next job
            next_job = job_queue[0]

            # 2. Find an idle GPU (FIFO = first available)
            idle_gpu_id = None
            for gpu_id, gpu_info in gpu_registry.items():
                if gpu_info['sim_obj'].state == GPUState.IDLE:
                    idle_gpu_id = gpu_id
                    break  # Found one!

            # 3. If we found an idle GPU, assign the job
            if idle_gpu_id:
                job = job_queue.pop(0)  # Remove the job from the queue
                gpu_sim = gpu_registry[idle_gpu_id]['sim_obj']

                # Start the job execution process in the SimPy environment
                env.process(gpu_sim.execute_job(job['job_id'], job['duration']))
                print(f"Scheduler: Assigned job {job['job_id']} to GPU {idle_gpu_id}")

        # Be kind to the CPU - don't run in a tight, endless loop
        time.sleep(1)  # Check every second

# Start the scheduler loop in its own thread
scheduler_thread = threading.Thread(target=scheduler_loop)
scheduler_thread.daemon = True
scheduler_thread.start()

if __name__ == '__main__':
    print("Starting Control Plane Server on http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)  # use_reloader=False avoids double-threading