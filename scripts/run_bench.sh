#!/bin/bash

# 사용법 안내
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 [fastdds|cyclonedds] [ros2_command]"
    echo "Example: $0 fastdds ros2 run demo_nodes_cpp talker"
    exit 1
fi

DDS_TYPE=$1
shift # 첫 번째 인자(DDS_TYPE)를 제거하고 나머지를 ROS2 명령어로 취급
COMMAND=$@

# 설정 파일 경로 (컨테이너 내부 기준)
FAST_CONFIG="/root/configs/fastdds_profiles.xml"
CYCLONE_CONFIG="/root/configs/cyclonedds.xml"

case $DDS_TYPE in
    "fastdds")
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        export FASTRTPS_DEFAULT_PROFILES_FILE=$FAST_CONFIG
        echo "[INFO] Running with FastDDS using $FAST_CONFIG"
        ;;
    "cyclonedds")
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI="file://$CYCLONE_CONFIG"
        echo "[INFO] Running with CycloneDDS using $CYCLONE_CONFIG"
        ;;
    *)
        echo "[ERROR] Unknown DDS type: $DDS_TYPE"
        exit 1
        ;;
esac

# ROS 2 명령어 실행
exec $COMMAND
