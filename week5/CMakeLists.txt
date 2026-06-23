cmake_minimum_required(VERSION 3.0.2)
project(week5_pkg)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  message_generation
)

## 声明自定义服务文件
add_service_files(
  FILES
  AddTwoInts.srv
)

## 生成消息/服务
generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs message_runtime
)

## 安装 Python 脚本
catkin_install_python(PROGRAMS
  scripts/server.py
  scripts/client.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
