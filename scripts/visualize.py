import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. 실험 메타데이터 및 변수 설정
RESULT_DIR = '../results'  # 결과 CSV 파일이 저장된 디렉토리
DDS_TYPES = ["fastdds", "cyclonedds"]
PAYLOAD_SIZES = [32768, 2097152]    # 32KB, 2MB
NODE_COUNTS = [2, 10, 20, 50, 100]
DURATION = 30  # seconds
HZ = 10 # Ping 발행 주기 (100ms)
EXPECTED_MSGS = DURATION * HZ   # 300 messages expected per test

# 학술적 그래프 스타일 적용
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12, 'axes.labelsize': 14, 'axes.titlesize': 16})

def load_and_preprocess():
    """파일 시스템에서 데이터를 읽어 정규화된 DataFrame으로 반환"""
    records = []

    for payload in PAYLOAD_SIZES:
        for node in NODE_COUNTS:
            for dds in DDS_TYPES:
                file_path = os.path.join(RESULT_DIR, f"{dds}_p{payload}_n{node}.csv")

                mean_rtt = np.nan
                p99_rtt =  np.nan
                success_rate = 0.0

                # 파일이 존재하고, 헤더 외에 데이터가 있는지 확인
                if os.path.exists(file_path) and os.path.getsize(file_path) > 30:
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty and 'rtt_ms' in df.columns:
                            msg_count = len(df)
                            success_rate = (msg_count / EXPECTED_MSGS) * 100.0
                            success_rate = min(success_rate, 100.0)  # 100% 초과 방지

                            mean_rtt = df['rtt_ms'].mean()
                            p99_rtt = df['rtt_ms'].quantile(0.99)
                    except Exception as e:
                        print(f"[Warning] Failed to parse {file_path}: {e}")

                records.append({
                    'middleware': dds,
                    'node_count': node,
                    'payload_size': payload,
                    'mean_rtt': mean_rtt,
                    'p99_rtt': p99_rtt,
                    'success_rate': success_rate
                })

    return pd.DataFrame(records)

def plot_performance(df, payload):
    """특정 페이로드에 대한 RTT 및 성공률 그래프 생성"""
    subset = df[df['payload_size'] == payload].copy()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
    fig.suptitle(f'DDS Scalability Analysis (Payload: {payload // 1024} KB)', fontweight='bold')

    x = np.arange(len(NODE_COUNTS))
    width = 0.35

    fast_data  = subset[subset['middleware'] == 'fastdds']
    cyc_data = subset[subset['middleware'] == 'cyclonedds']

    # --- [Panel 1] RTT & Tail Latency (Log Scale) ---
    # Error bar는 (P99 - Mean)으로 계산하여 위쪽으로만 표시
    fast_err = [max(0, p - m) if pd.notna(p) and pd.notna(m) else 0 for p, m in zip(fast_data['p99_rtt'], fast_data['mean_rtt'])]
    cyc_err = [max(0, p - m) if pd.notna(p) and pd.notna(m) else 0 for p, m in zip(cyc_data['p99_rtt'], cyc_data['mean_rtt'])]

    ax1.bar(x - width/2, fast_data['mean_rtt'], width, label='FastDDS (Mean)', color='#1f77b4', 
            yerr=[[0]*len(fast_err), fast_err], capsize=5, ecolor='black')
    ax1.bar(x + width/2, cyc_data['mean_rtt'], width, label='CycloneDDS (Mean)', color='#ff7f0e',
            yerr=[[0]*len(cyc_err), cyc_err], capsize=5, ecolor='black')
    
    ax1.set_ylabel('Round Trip Time (ms) - Log Scale')
    ax1.set_yscale('log')
    ax1.legend(title='Error bars: 99th Percentile - (P99)')
    ax1.grid(True, which="both", ls="--", linewidth=0.5)

    # --- [Panel 2] Reliability (Success Rate) ---
    ax2.plot(x, fast_data['success_rate'], marker='o', linewidth=2, markersize=8, label='FastDDS', color='#1f77b4')
    ax2.plot(x, cyc_data['success_rate'], marker='s', linewidth=2, markersize=8, label='CycloneDDS', color='#ff7f0e')

    # Breakdown Point 주석 처리 (90% 미만 하락 지점)
    for i, (f_sr, c_sr) in enumerate(zip(fast_data['success_rate'], cyc_data['success_rate'])):
        if f_sr < 90.0:
            ax2.annotate('Breakdown', (x[i], f_sr), textcoords="offset points", xytext=(0,-15), ha='center', color='red', weight='bold')
        if c_sr < 90.0:
            ax2.annotate('Breakdown', (x[i], c_sr), textcoords="offset points", xytext=(0,10), ha='center', color='red', weight='bold')

    ax2.set_ylabel('Success Rate (%)')
    ax2.set_xlabel('Number of Nodes (N)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(NODE_COUNTS)
    ax2.set_ylim(-5, 105)
    ax2.axhline(100, color='gray', linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()
    save_path = os.path.join(RESULT_DIR, f"dds_analysis_{payload}B.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"[INFO] Grapth saved to {save_path}")

if __name__ == "__main__":
    print("Loading data and calculating metrics...")
    df_results = load_and_preprocess()

    # 데이터 요약본 콘솔 출력
    print("\n=== Data Summary ===")
    print(df_results.dropna().to_string(index=False))

    # 페이로드별 그래프 생성
    for p_size in PAYLOAD_SIZES:
        plot_performance(df_results, p_size)