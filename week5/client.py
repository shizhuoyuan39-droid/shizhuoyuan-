#!/usr/bin/env python3
"""
client.py — ROS Service 客户端
Week 5 作业：ROS 服务通信（Service/Client）

功能：向 add_two_ints 服务发送两个整数，打印返回的求和结果

使用方法：
  python3 client.py 3 5
  # 或：rosrun week5_pkg client.py 3 5
"""

import sys
import rospy
from week5_pkg.srv import AddTwoInts


def client_main():
    if len(sys.argv) != 3:
        print("用法: client.py <整数a> <整数b>")
        sys.exit(1)

    a = int(sys.argv[1])
    b = int(sys.argv[2])

    rospy.init_node('add_two_ints_client')

    # 等待服务就绪
    rospy.loginfo("[Client] 等待服务 'add_two_ints' 启动...")
    rospy.wait_for_service('add_two_ints')

    try:
        add = rospy.ServiceProxy('add_two_ints', AddTwoInts)
        resp = add(a, b)
        rospy.loginfo(f"[Client] 请求：{a} + {b} = {resp.sum}")
        print(f"结果：{a} + {b} = {resp.sum}")
    except rospy.ServiceException as e:
        rospy.logerr(f"[Client] 服务调用失败：{e}")


if __name__ == '__main__':
    client_main()
