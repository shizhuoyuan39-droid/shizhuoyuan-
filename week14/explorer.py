#!/usr/bin/env python3
"""
explorer.py — 小乌龟自动迷宫探索（BFS 寻路 + ROS 控制）
Week 14 作业
平台：ROS + turtlesim

功能：
  - 读取 maze.py 中的地图，用 BFS 算法求最短路径
  - 控制 turtlesim 小乌龟自动走出迷宫
  - 到达终点后停止并打印成功信息

使用方法：
  roscore &
  rosrun turtlesim turtlesim_node &
  python3 explorer.py
"""

import rospy
import math
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from collections import deque

from maze import (MAZE, START, GOAL, ROWS, COLS,
                  maze_to_turtle, turtle_to_maze,
                  is_wall, get_neighbors, print_maze)

# ── 参数 ────────────────────────────────────────────────────────────────────
LINEAR_SPEED  = 1.0   # 直线速度（单位/秒）
ANGULAR_SPEED = 1.5   # 旋转速度（rad/s）
GOAL_THRESH   = 0.15  # 到达格子中心的距离阈值
ANGLE_THRESH  = 0.05  # 角度对齐阈值（rad）

# ── 全局 Pose ────────────────────────────────────────────────────────────────
current_pose = Pose()


def pose_callback(msg):
    global current_pose
    current_pose = msg


# ── BFS 寻路 ─────────────────────────────────────────────────────────────────
def bfs(start, goal):
    """返回从 start 到 goal 的格子路径（含起点和终点）"""
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        cur = path[-1]
        if cur == goal:
            return path
        for nb in get_neighbors(*cur):
            if nb not in visited:
                visited.add(nb)
                queue.append(path + [nb])
    return []   # 无路可走


# ── 角度归一化 ───────────────────────────────────────────────────────────────
def normalize_angle(a):
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


# ── 旋转到目标角度 ────────────────────────────────────────────────────────────
def rotate_to(pub, target_angle, rate):
    while not rospy.is_shutdown():
        err = normalize_angle(target_angle - current_pose.theta)
        if abs(err) < ANGLE_THRESH:
            break
        cmd = Twist()
        cmd.angular.z = ANGULAR_SPEED if err > 0 else -ANGULAR_SPEED
        pub.publish(cmd)
        rate.sleep()
    pub.publish(Twist())   # 停止旋转


# ── 直线前进到目标点 ──────────────────────────────────────────────────────────
def move_to(pub, tx, ty, rate):
    while not rospy.is_shutdown():
        dx = tx - current_pose.x
        dy = ty - current_pose.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < GOAL_THRESH:
            break
        cmd = Twist()
        cmd.linear.x = min(LINEAR_SPEED, dist * 2)
        pub.publish(cmd)
        rate.sleep()
    pub.publish(Twist())   # 停止


# ── 主控制循环 ────────────────────────────────────────────────────────────────
def main():
    rospy.init_node('turtle_explorer', anonymous=False)

    pub  = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rospy.Subscriber('/turtle1/pose', Pose, pose_callback)

    rospy.loginfo("等待 turtlesim 就绪…")
    rospy.sleep(1.0)

    # ── 打印迷宫 ──────────────────────────────────────────────────────────
    rospy.loginfo("当前迷宫地图：")
    path_cells = []   # 先空

    # ── BFS 求路径 ────────────────────────────────────────────────────────
    rospy.loginfo("BFS 寻路中…")
    path = bfs(START, GOAL)
    if not path:
        rospy.logerr("BFS 无法找到路径！请检查迷宫配置。")
        return

    rospy.loginfo(f"找到路径，共 {len(path)} 步：{path}")
    print_maze(path)

    rate = rospy.Rate(20)

    # ── 逐格走路径 ────────────────────────────────────────────────────────
    for i, (row, col) in enumerate(path):
        if rospy.is_shutdown():
            break

        tx, ty = maze_to_turtle(row, col)
        rospy.loginfo(f"[{i+1}/{len(path)}] 前往格子({row},{col}) → turtle({tx:.2f},{ty:.2f})")

        # 先旋转到正确方向
        target_angle = math.atan2(ty - current_pose.y, tx - current_pose.x)
        rotate_to(pub, target_angle, rate)

        # 再直线前进
        move_to(pub, tx, ty, rate)

    rospy.loginfo("🎉 成功到达终点！迷宫探索完成。")
    pub.publish(Twist())   # 确保停止


if __name__ == '__main__':
    main()
