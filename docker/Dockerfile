# 1. Base Image: ROS 2 Jazzy (Ubuntu 24.04 기반)
FROM osrf/ros:jazzy-desktop

# 2. 시스템 패키지 설치 및 DDS 구현체 추가
# - cyclonedds, fastrtps: 두 DDS를 자유롭게 스위칭하기 위해 필수 설치
# - iproute2, iperf3, net-tools: DDS 통신 분석 및 네트워크 부하 측정을 위한 엔지니어 필수 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    iperf3 \
    iproute2 \
    iputils-ping \
    net-tools \
    python3-pip \
    git \
    vim \
    zsh \
    && rm -rf /var/lib/apt/lists/*

# 3. 환경 변수 설정 (DDS 튜닝을 위한 기본값)
# 성능 측정을 위해 기본 RMW를 설정하되, 실행 시점에서 변경 가능하도록 함
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=0

# 4. 개발 편의를 위한 Zsh 및 툴 설정 (선택 사항이나 권장)
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
RUN echo "source /opt/ros/jazzy/setup.zsh" >> ~/.zshrc

# 5. 작업 디렉토리 설정
WORKDIR /root/workspace
ENTRYPOINT ["/bin/zsh"]
