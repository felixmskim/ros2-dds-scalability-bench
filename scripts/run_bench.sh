#!/bin/bash

# 사용법 안내
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 [fastdds|cyclonedds] [ros2_command]"
    echo "Example: $0 fastdds ros2 run demo_nodes_cpp talker"
    exit 1
fi

DDS_TYPE=$1
CONFIG_PATH=$2  # 두 번째 인자로 XML 경로를 받음
shift 2        # 앞의 두 인자를 제거
COMMAND=$@

# 설정 파일 경로 (컨테이너 내부 기준)
FAST_CONFIG="/root/configs/fastdds_profiles.xml"
CYCLONE_CONFIG="/root/configs/cyclonedds.xml"

case $DDS_TYPE in
    "fastdds")
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export FASTRTPS_DEFAULT_PROFILES_FILE=$CONFIG_PATH # 가변 경로 적용
        echo "[INFO] Running with FastDDS using $CONFIG_PATH"
        ;;
    "cyclonedds")
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI="file://$CONFIG_PATH"
        echo "[INFO] Running with CycloneDDS using $CONFIG_PATH"
        ;;
    *)
        echo "[ERROR] Unknown DDS type: $DDS_TYPE"
        exit 1
        ;;
esac

# ROS 2 명령어 실행
exec $COMMAND
