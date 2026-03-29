# ROS 2 DDS Scalability Benchmarking Suite

## 1. Overview & Research Objective
This project is an automated benchmarking suite designed to quantitatively evaluate the scalability, latency, and reliability of ROS 2 (Robot Operating System 2) middleware (DDS: Data Distribution Service) under varying system loads.

It objectively identifies OS scheduling overhead and network bottlenecks that occur when the number of nodes increases and large payloads are transmitted, simulating high-load scenarios commonly found in autonomous driving and multi-robot systems.

**Key Comparison Targets:**
* eProsima Fast DDS (ROS 2 Default)
* Eclipse Cyclone DDS

**Core Measurement Metrics:**
* **Mean RTT (Round Trip Time):** Average round-trip latency (ms).
* **Tail Latency (P99):** The 99th percentile latency, used to visualize system non-determinism (Jitter).
* **Success Rate (Reliability):** Packet delivery success rate, used to identify the communication "Breakdown Point."

## 2. Methodology
This benchmark simulates a many-to-many (M:N) background load environment by deploying 1 `Ping` node and $(N-1)$ `Pong` nodes.

* **Controlled Variables:**
  * **Node Count ($N$):** 2, 10, 20, 50, 100
  * **Payload Size:**
    * 32KB (simulating control signals)
    * 2MB (simulating image/LiDAR sensor data)
  * **Duration:** 30 seconds per experiment (published at 10Hz)
* **Reliability Calculation Formula:**
  $$P_{success} = \frac{Received\_Messages}{Expected\_Messages} \times 100$$
  (Data points that are not recorded due to CPU context switching overhead or kernel buffer exhaustion are strictly considered as dropped/lost packets.)

## 3. System Requirements & Prerequisites
To ensure hardware resource isolation and provide a consistent experimental environment, this benchmark runs inside a Docker container (Ubuntu 24.04, ROS 2 Jazzy).

### 3.1. Host Kernel Tuning (Critical)
When DDS (especially Cyclone DDS) processes large packets (2MB) concurrently across multiple nodes, the OS kernel's UDP receive buffer can become exhausted, leading to process crashes or severe packet drops. **The following kernel parameters must be applied on the host system prior to execution:**

```bash
# Expand maximum network buffer sizes (8MB)
sudo sysctl -w net.core.rmem_max=8388608
sudo sysctl -w net.core.wmem_max=8388608
```

### 3.2. Dependencies
- Docker & Docker Compose

- Python 3.10+ (For data visualization on the host)


 ## 4. Installation & Setup
 ```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/ros2-dds-scalability-bench.git
cd ros2-dds-scalability-bench

# 2. Build and launch the isolated research environment via Docker
docker compose up -d

# 3. Enter the container
docker exec -it dds_research_env /bin/zsh

# 4. Build the ROS 2 workspace inside the container
cd /root/workspace
colcon build --symlink-install
source install/setup.zsh
```

## 5. Execution Guide
The benchmark is executed via a Python-based automated launcher (`launcher.py`). This script automatically handles process creation, RTT logging, and resource cleanup based on predefined scenarios.

### 5.1. Running the Benchmark
Set the DDS_TYPE variable at the top of the launcher script to either `"fastdds"` or `"cyclonedds"`, then run the script.

<img width="1249" height="104" alt="image" src="https://github.com/user-attachments/assets/5d5071a0-f924-4f01-abc9-b58537b8eae4" />

<img width="1249" height="104" alt="image" src="https://github.com/user-attachments/assets/9155afc6-4cbc-4ac8-aff5-20b6ba78cf0c" />

<b></b>
```bash
# Execute inside the container terminal
python3 /root/scripts/launcher.py
```

- **Process Flow:** To exclude the overhead of the ROS 2 Discovery phase (PDP/EDP) from the actual measurement data, the launcher enforces a 2-second Warm-up time after spawning all nodes before it begins RTT logging.

- **Data Storage:** All measurements are automatically saved in .csv format with timestamps in the /root/results/ directory.

- ## 6. Data Visualization & Analysis
Once the experiments are complete and the `.csv` files are collected, run the data analysis and graph generation script on the host system.

```bash
# Execute from the project root on the host system
# 1. Install required Python packages
pip install -r requirements.txt

# 2. Generate visualization graphs
cd scripts
python3 visualize.py
```

### 6.1. Expected Outcomes
The visualization script will generate graphs such as `dds_analysis_32768B.png` and `dds_analysis_2097152B.png` in the `results/` directory, categorized by payload size.

The generated figures consist of two panels:
1. **1. [Upper Panel] RTT & Tail Latency (Log Scale):** Contrasts the mean latency (bar) and P99 tail latency (error bar) as $N$ increases. This clearly visualizes the extreme latency spikes (Jitter) that occur when OS scheduling overhead surpasses critical thresholds.
2. **2. [Lower Panel] Reliability:** Tracks the packet delivery success rate. Intervals where the success rate drops below 90% are explicitly annotated as a **Breakdown Point**, objectively demonstrating the maximum capacity limits of each middleware.
