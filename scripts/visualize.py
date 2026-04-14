import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. 실험 메타데이터 및 변수 설정
RESULT_DIR = '../results'
DDS_TYPES = ["fastdds", "cyclonedds"]
BUFFER_SIZES = ["64k", "2m", "8m"]  # Phase 1 변수 추가
PAYLOAD_SIZES = [32768, 2097152]    # 32KB, 2MB
NODE_COUNTS = [2, 10, 20, 50, 100]
DURATION = 30  # seconds
HZ = 10 
EXPECTED_MSGS = DURATION * HZ   

# 학술적 그래프 스타일 적용
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12, 'axes.labelsize': 14, 'axes.titlesize': 16})

def load_and_preprocess():
    """파일 시스템에서 데이터를 읽어 정규화된 DataFrame으로 반환"""
    records = []

    for payload in PAYLOAD_SIZES:
        for node in NODE_COUNTS:
            for dds in DDS_TYPES:
                for buf in BUFFER_SIZES:
                    # 변경된 파일 명명 규칙 반영 (_b{buf}_ 추가)
                    file_path = os.path.join(RESULT_DIR, f"{dds}_b{buf}_p{payload}_n{node}.csv")

                    mean_rtt = np.nan
                    p99_rtt =  np.nan
                    success_rate = 0.0

                    if os.path.exists(file_path) and os.path.getsize(file_path) > 30:
                        try:
                            df = pd.read_csv(file_path)
                            if not df.empty and 'rtt_ms' in df.columns:
                                msg_count = len(df)
                                success_rate = (msg_count / EXPECTED_MSGS) * 100.0
                                success_rate = min(success_rate, 100.0)

                                mean_rtt = df['rtt_ms'].mean()
                                p99_rtt = df['rtt_ms'].quantile(0.99)
                        except Exception as e:
                            print(f"[Warning] Failed to parse {file_path}: {e}")

                    records.append({
                        'middleware': dds,
                        'buffer_size': buf,
                        'node_count': node,
                        'payload_size': payload,
                        'mean_rtt': mean_rtt,
                        'p99_rtt': p99_rtt,
                        'success_rate': success_rate
                    })

    return pd.DataFrame(records)

def plot_buffer_analysis(df, middleware, payload):
    """특정 미들웨어와 페이로드에 대해 버퍼 크기별 성능을 대조하는 그래프 생성"""
    subset = df[(df['middleware'] == middleware) & (df['payload_size'] == payload)].copy()
    
    # 해당 조합의 데이터가 전혀 없으면 그래프 생성 스킵
    if subset['mean_rtt'].isna().all() and (subset['success_rate'] == 0).all():
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
    fig.suptitle(f'[{middleware.upper()}] Buffer Tuning Analysis (Payload: {payload // 1024} KB)', fontweight='bold')

    x = np.arange(len(NODE_COUNTS))
    width = 0.25  # 3개의 막대를 나란히 배치하기 위해 너비 축소

    # 버퍼 크기별 색상 및 X축 오프셋 지정
    colors = {'64k': '#1f77b4', '2m': '#ff7f0e', '8m': '#2ca02c'}
    offsets = {'64k': -width, '2m': 0, '8m': width}

    # --- [Panel 1] RTT & Tail Latency (Log Scale) ---
    for buf in BUFFER_SIZES:
        buf_data = subset[subset['buffer_size'] == buf]
        if buf_data.empty: continue
        
        # Error bar 계산 (상위 99% Tail Latency)
        err = [max(0, p - m) if pd.notna(p) and pd.notna(m) else 0 for p, m in zip(buf_data['p99_rtt'], buf_data['mean_rtt'])]
        
        ax1.bar(x + offsets[buf], buf_data['mean_rtt'], width, label=f'Buffer: {buf}', color=colors[buf],
                yerr=[[0]*len(err), err], capsize=5, ecolor='black')

    ax1.set_ylabel('Round Trip Time (ms) - Log Scale')
    ax1.set_yscale('log')
    ax1.legend(title='Error bars: 99th Percentile (P99)')
    ax1.grid(True, which="both", ls="--", linewidth=0.5)

    # --- [Panel 2] Reliability (Success Rate) ---
    markers = {'64k': 'o', '2m': 's', '8m': '^'}
    for buf in BUFFER_SIZES:
        buf_data = subset[subset['buffer_size'] == buf]
        if buf_data.empty: continue
        
        ax2.plot(x, buf_data['success_rate'], marker=markers[buf], linewidth=2, markersize=8, label=f'Buffer: {buf}', color=colors[buf])

        # Breakdown Point 주석 처리
        for i, sr in enumerate(buf_data['success_rate']):
            if sr < 90.0:
                y_offset = 15 if offsets[buf] >= 0 else -20
                ax2.annotate('Breakdown', (x[i], sr), textcoords="offset points", xytext=(0, y_offset), ha='center', color='red', weight='bold', fontsize=9)

    ax2.set_ylabel('Success Rate (%)')
    ax2.set_xlabel('Number of Nodes (N)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(NODE_COUNTS)
    ax2.set_ylim(-5, 105)
    ax2.axhline(100, color='gray', linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()
    save_path = os.path.join(RESULT_DIR, f"{middleware}_buffer_analysis_{payload}B.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"[INFO] Graph saved to {save_path}")

if __name__ == "__main__":
    print("Loading data and calculating metrics...")
    df_results = load_and_preprocess()

    print("\n=== Data Summary ===")
    # 결측치를 제외한 유효 데이터만 출력
    print(df_results.dropna(subset=['mean_rtt']).to_string(index=False))

    # 미들웨어 및 페이로드 조합별로 독립된 그래프 생성
    for dds in DDS_TYPES:
        for p_size in PAYLOAD_SIZES:
            plot_buffer_analysis(df_results, dds, p_size)