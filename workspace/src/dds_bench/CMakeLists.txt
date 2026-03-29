cmake_minimum_required(VERSION 3.8)
project(dds_bench)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 의존성 찾기
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# 실행 파일 생성
add_executable(perf_node src/perf_node.cpp)

# 의존성 연결
ament_target_dependencies(perf_node rclcpp std_msgs)

# 설치 경로 설정 (ros2 run 명령어가 인식하게 함)
install(TARGETS
  perf_node
  DESTINATION lib/${PROJECT_NAME})

ament_package()
