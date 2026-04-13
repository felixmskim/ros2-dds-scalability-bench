# 1개의 Ping 노드와 N-1개의 Pong 노드를 띄워 전체 시스템 부하 속에서 RTT를 측정하는 스크립트
import subprocess
import time
import os

# Phase 1: Transport Layer 실험 설정
DDS_TYPE = "cyclonedds" # 사용할 DDS 구현체 ("fastdds", "cyclonedds")

# [추가] 실험할 버퍼 설정 파일들
# fast_dds
# BUFFER_CONFIGS = {
#     "64k": "/root/configs/fast_64k.xml",
#     "2m": "/root/configs/fast_2m.xml",
#     "8m": "/root/configs/fast_8m.xml"
# }

# cyclone_dds
BUFFER_CONFIGS = {
    "64k": "/root/configs/cyc_64k.xml",
    "2m": "/root/configs/cyc_2m.xml",
    "8m": "/root/configs/cyc_8m.xml"
}


PAYLOAD_SIZES = [32768, 2097152]  # 32KB, 2MB
NODE_COUNTS = [2, 10, 20, 50, 100]  # 총 노드 수 (1 Ping + N-1 Pong) / N=1 제외
DURATION = 30  # 각 실험당 실행 시간 (초)

def run_experiment(node_count, payload_size, buf_label, xml_path):
    processes = []
    # 결과 파일명에 버퍼 정보 추가
    csv_name = f"/root/results/{DDS_TYPE}_b{buf_label}_p{payload_size}_n{node_count}.csv"
    
    print(f"\n[START] Buffer: {buf_label}, Nodes: {node_count}, Payload: {payload_size}B")
    # 1. (N-1)개의 Pong 노드 실행 (배경 부하 및 에코 역할)
    for i in range(node_count - 1):
        cmd = [
            "/root/scripts/run_bench.sh", DDS_TYPE, xml_path, # XML 경로 전달
            "ros2", "run", "dds_bench", "perf_node",
            "--ros-args", "-p", "mode:=pong", "-r", f"__node:=pong_node_{i}"
        ]
        processes.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL))
        # [수정] 노드가 너무 많을 때 한꺼번에 띄우면 커널 스케줄러가 마비됨
        if node_count > 50:
            time.sleep(0.1)

    # 2. Discovery 대기 시간 대폭 상향
    # [수정] 노드 수에 비례하여 대기 시간을 늘려야 합니다. (N=100일 때 2초는 턱없이 부족)
    wait_time = 5 if node_count < 50 else 15 
    print(f"Waiting {wait_time}s for Discovery...")
    time.sleep(wait_time)

    # 2. 1개의 Ping 노드 실행 (실제 RTT 측정 및 로깅)
    ping_cmd = [
        "/root/scripts/run_bench.sh", DDS_TYPE, xml_path, # XML 경로 전달
        "ros2", "run", "dds_bench", "perf_node",
        "--ros-args", "-p", "mode:=ping", "-p", f"payload_size:={payload_size}", 
        "-p", f"csv_path:={csv_name}", "-r", "__node:=ping_node_main"
    ]
    # ping_p = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE, text=True)
    ping_p = subprocess.Popen(ping_cmd) # 에러 확인을 위해 stdout 열어둠
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
        # 버퍼 설정 -> 노드 수 -> 페이로드 순으로 실험 순회
        for buf_label, xml_path in BUFFER_CONFIGS.items():
            for n in NODE_COUNTS:
                for size in PAYLOAD_SIZES:
                    run_experiment(n, size, buf_label, xml_path)
                    time.sleep(5) # 시스템 안정화
    except KeyboardInterrupt:
        subprocess.run(["pkill", "-f", "perf_node"])
        print("\nExperiment interrupted.")
