#!/usr/bin/env python3
"""
server.py — ROS Service 服务端
Week 5 作业：ROS 服务通信（Service/Client）

功能：提供 AddTwoInts 服务，接收两个整数并返回求和结果

使用方法：
  roscore &
  python3 server.py
  # 或：rosrun week5_pkg server.py
"""

import rospy
from week5_pkg.srv import AddTwoInts, AddTwoIntsResponse


def handle_add(req):
    result = req.a + req.b
    rospy.loginfo(f"[Server] 收到请求：{req.a} + {req.b} = {result}")
    return AddTwoIntsResponse(result)


def server_main():
    rospy.init_node('add_two_ints_server')
    # 注册服务，服务名为 'add_two_ints'
    s = rospy.Service('add_two_ints', AddTwoInts, handle_add)
    rospy.loginfo("[Server] 服务已启动，等待请求...")
    rospy.spin()


if __name__ == '__main__':
    server_main()
