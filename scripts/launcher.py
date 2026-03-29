# 1개의 Ping 노드와 N-1개의 Pong 노드를 띄워 전체 시스템 부하 속에서 RTT를 측정하는 스크립트
import subprocess
import time
import os

# 실험 설정 
DDS_TYPE = "cyclonedds"  # 사용할 DDS 구현체 ("fastdds", "cyclonedds")
PAYLOAD_SIZES = [32768, 2097152]  # 32KB, 2MB
NODE_COUNTS = [2, 10, 20, 50, 100]  # 총 노드 수 (1 Ping + N-1 Pong) / N=1 제외
DURATION = 30  # 각 실험당 실행 시간 (초)

def run_experiment(node_count, payload_size):
    processes = []
    csv_name = f"/root/results/{DDS_TYPE}_p{payload_size}_n{node_count}.csv"
    
    print(f"\n[START] Nodes: {node_count}, Payload: {payload_size} bytes")

    # 1. (N-1)개의 Pong 노드 실행 (배경 부하 및 에코 역할)
    for i in range(node_count - 1):
        cmd = [
            "/root/scripts/run_bench.sh", DDS_TYPE,
            "ros2", "run", "dds_bench", "perf_node",
            "--ros-args", 
            "-p", "mode:=pong", 
            "-r", f"__node:=pong_node_{i}"
        ]
        processes.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL))

    time.sleep(2)  # 노드 탐색(Discovery)을 위한 대기 시간

    # 2. 1개의 Ping 노드 실행 (실제 RTT 측정 및 로깅)
    ping_cmd = [
        "/root/scripts/run_bench.sh", DDS_TYPE,
        "ros2", "run", "dds_bench", "perf_node",
        "--ros-args", 
        "-p", "mode:=ping", 
        "-p", f"payload_size:={payload_size}",
        "-p", f"csv_path:={csv_name}",
        "-r", f"__node:=ping_node_main"
    ]
    # ping_p = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE, text=True)
    ping_p = subprocess.Popen(ping_cmd, stdout=subprocess.DEVNULL)
    processes.append(ping_p)

    time.sleep(DURATION)

    # 3. Cleanup
    print("\nFinishing experiment...")
    for p in processes:
        p.terminate() # SIGTERM 전송
        
    # 프로세스가 완전히 죽을 때까지 대기
    time.sleep(2)
    subprocess.run(["pkill", "-f", "perf_node"], stderr=subprocess.DEVNULL)
    
    if os.path.exists(csv_name) and os.path.getsize(csv_name) > 20: # 헤더 크기 이상인지 확인
        print(f"[SUCCESS] Data saved: {csv_name}")
    else:
        print(f"[FAIL] No data recorded in {csv_name}")

if __name__ == "__main__":
    # 결과 폴더 확인
    if not os.path.exists("/root/results"):
        os.makedirs("/root/results")
    try:
        for n in NODE_COUNTS:
            for size in PAYLOAD_SIZES:
                run_experiment(n, size)
    except KeyboardInterrupt:
        subprocess.run(["pkill", "-f", "perf_node"])
        print("\nExperiment interrupted.")
