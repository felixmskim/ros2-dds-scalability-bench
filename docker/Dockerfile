# 1. Base Image: ROS 2 Jazzy (Ubuntu 24.04 기반)
FROM osrf/ros:jazzy-desktop

# 2. 시스템 패키지 설치 및 DDS 구현체 추가
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. 데이터 시각화 및 분석을 위한 Python 패키지 설치 (PEP 668 정책 우회)
RUN pip3 install pandas matplotlib seaborn --break-system-packages

# 4. 환경 변수 설정 (DDS 튜닝을 위한 기본값)
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=0
# DDS XML 튜닝 파일 경로 지정을 위한 환경변수 (필요시 컨테이너 실행 단계에서 덮어쓰기)
ENV FASTRTPS_DEFAULT_PROFILES_FILE=/root/workspace/profiles/default_fastdds.xml
ENV CYCLONEDDS_URI=file:///root/workspace/profiles/default_cyclonedds.xml

# 5. 개발 편의를 위한 Zsh 및 툴 설정
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
RUN echo "source /opt/ros/jazzy/setup.zsh" >> ~/.zshrc

# 6. 작업 디렉토리 및 XML 프로파일 디렉토리 구성
WORKDIR /root/workspace
RUN mkdir -p /root/workspace/profiles

ENTRYPOINT ["/bin/zsh"]
