#include <chrono>
#include <fstream>
#include <iomanip>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/byte_multi_array.hpp"

using namespace std::chrono_literals;

class PerfNode : public rclcpp::Node {
public:
    PerfNode() : Node("perf_node") {
        this->declare_parameter("payload_size", 32768);
        this->declare_parameter("mode", "ping");
        this->declare_parameter("csv_path", "/root/results/rtt_log.csv"); // 저장 경로 파라미터화

        payload_size_ = this->get_parameter("payload_size").as_int();
        mode_ = this->get_parameter("mode").as_string();
        std::string csv_path = this->get_parameter("csv_path").as_string();

        payload_msg_.data.resize(payload_size_, 0);

        if (mode_ == "ping") {
            // CSV 파일 초기화 및 헤더 작성
            csv_file_.open(csv_path, std::ios::out | std::ios::trunc);
            if (csv_file_.is_open()) {
                csv_file_ << "timestamp_ns,rtt_ms\n";
            } else {
                RCLCPP_ERROR(this->get_logger(), "Failed to open CSV file at: %s", csv_path.c_str());
            }

            publisher_ = this->create_publisher<std_msgs::msg::ByteMultiArray>("ping_topic", 10);
            subscriber_ = this->create_subscription<std_msgs::msg::ByteMultiArray>(
                "pong_topic", 10, std::bind(&PerfNode::ping_callback, this, std::placeholders::_1));
            
            timer_ = this->create_wall_timer(100ms, std::bind(&PerfNode::send_ping, this));
            RCLCPP_INFO(this->get_logger(), "Mode: PING | Logging to: %s", csv_path.c_str());
        } 
        else {
            publisher_ = this->create_publisher<std_msgs::msg::ByteMultiArray>("pong_topic", 10);
            subscriber_ = this->create_subscription<std_msgs::msg::ByteMultiArray>(
                "ping_topic", 10, std::bind(&PerfNode::pong_callback, this, std::placeholders::_1));
            RCLCPP_INFO(this->get_logger(), "Mode: PONG | Ready to echo");
        }
    }

    ~PerfNode() {
        if (csv_file_.is_open()) {
            csv_file_.close();
        }
    }

private:
    void send_ping() {
        t_start_ = this->now();
        publisher_->publish(payload_msg_);
    }

    void ping_callback(const std_msgs::msg::ByteMultiArray::SharedPtr msg) {
        (void)msg;
        auto t_end = this->now();
        double rtt_ms = (t_end - t_start_).nanoseconds() / 1000000.0;
        
        // 화면 출력
        RCLCPP_INFO(this->get_logger(), "RTT: %.4f ms", rtt_ms);

        // CSV 파일 기록 (파일이 열려있을 때만)
        if (csv_file_.is_open()) {
            csv_file_ << t_end.nanoseconds() << "," 
                      << std::fixed << std::setprecision(4) << rtt_ms << "\n";
        }
    }

    void pong_callback(const std_msgs::msg::ByteMultiArray::SharedPtr msg) {
        publisher_->publish(*msg);
    }

    int payload_size_;
    std::string mode_;
    std_msgs::msg::ByteMultiArray payload_msg_;
    std::ofstream csv_file_;
    
    rclcpp::Publisher<std_msgs::msg::ByteMultiArray>::SharedPtr publisher_;
    rclcpp::Subscription<std_msgs::msg::ByteMultiArray>::SharedPtr subscriber_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Time t_start_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PerfNode>());
    rclcpp::shutdown();
    return 0;
}
