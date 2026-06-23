#!/usr/bin/env python3
"""
server.py — HTTP 服务器 + ROS turtlesim 控制（常驻程序）
Week 14 作业
平台：ROS + turtlesim

功能：
  1. 启动 HTTP 服务，监听手机网页发来的控制指令
  2. 将指令转换为 geometry_msgs/Twist 发布到 /turtle1/cmd_vel
  3. 同一进程内运行，无需额外节点

使用方法：
  roscore &
  rosrun turtlesim turtlesim_node &
  python3 server.py

然后手机浏览器访问 http://<本机IP>:8888
"""

import rospy
from geometry_msgs.msg import Twist
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import os
import math

PORT = 8888

# ── ROS 发布器（全局）──────────────────────────────────────────────────────
pub = None

# ── 速度指令映射 ───────────────────────────────────────────────────────────
def make_twist(action, speed):
    t = Twist()
    if action == 'forward':
        t.linear.x  =  speed
    elif action == 'back':
        t.linear.x  = -speed
    elif action == 'left':
        t.angular.z =  speed
    elif action == 'right':
        t.angular.z = -speed
    elif action == 'stop':
        pass   # 全零 = 停止
    return t


# ── HTTP 请求处理 ──────────────────────────────────────────────────────────
class TurtleHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # 过滤掉健康检查日志，保持终端整洁
        if '/cmd' in args[0] if args else False:
            rospy.loginfo(f"[HTTP] {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)

        # ── 1. 遥控指令 /cmd?action=xxx&speed=yyy ──────────────────────────
        if parsed.path == '/cmd':
            params = parse_qs(parsed.query)
            action = params.get('action', ['stop'])[0]
            try:
                speed = float(params.get('speed', ['1.5'])[0])
            except ValueError:
                speed = 1.5
            speed = max(0.1, min(speed, 5.0))   # 限幅

            twist = make_twist(action, speed)
            if pub:
                pub.publish(twist)
                rospy.loginfo(f"CMD: {action}  speed={speed:.1f}")

            self._respond(200, f"OK:{action}")

        # ── 2. 获取迷宫地图 /maze ──────────────────────────────────────────
        elif parsed.path == '/maze':
            try:
                from maze import MAZE, START, GOAL
                import json
                body = json.dumps({'maze': MAZE, 'start': START, 'goal': GOAL})
                self._respond(200, body, content_type='application/json')
            except Exception as e:
                self._respond(500, str(e))

        # ── 3. 静态文件（index.html）─────────────────────────────────────
        else:
            file_path = 'index.html' if parsed.path in ('/', '/index.html') else parsed.path.lstrip('/')
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                ct = 'text/html; charset=utf-8'
                self.send_response(200)
                self.send_header('Content-Type', ct)
                self.send_header('Content-Length', len(data))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            else:
                self._respond(404, 'Not Found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

    def _respond(self, code, body='', content_type='text/plain; charset=utf-8'):
        data = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)


# ── 在后台线程运行 HTTP 服务器 ─────────────────────────────────────────────
def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), TurtleHandler)
    rospy.loginfo(f"[HTTP] 服务器已启动，监听端口 {PORT}")
    server.serve_forever()


# ── 主程序 ─────────────────────────────────────────────────────────────────
def main():
    global pub

    rospy.init_node('turtle_remote_server', anonymous=False)
    pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rospy.loginfo("ROS 节点已启动，发布到 /turtle1/cmd_vel")

    # 后台线程运行 HTTP 服务
    t = threading.Thread(target=start_http_server, daemon=True)
    t.start()

    # 获取本机 IP 供用户参考
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = '127.0.0.1'
    rospy.loginfo(f"手机浏览器访问: http://{local_ip}:{PORT}")
    rospy.loginfo("按 Ctrl+C 退出")

    # 保持 ROS 节点运行
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        rate.sleep()


if __name__ == '__main__':
    main()
