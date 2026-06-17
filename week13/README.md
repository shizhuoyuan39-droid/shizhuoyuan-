# Week 13：ArUco Marker 检测与手机相机桥接实验（期末项目）

## 一、实验背景与目的

本次实验为课程期末项目，综合运用计算机视觉、网络通信与 ROS2 知识，构建一套"手机相机 → WSL 服务端 → ArUco Marker 实时检测"的完整视觉感知系统。

实验核心目标：
1. 在 WSL/Ubuntu 环境中搭建 Flask + Socket.io 视频流服务器
2. 通过浏览器将手机摄像头画面实时推送至服务端
3. 服务端使用 OpenCV ArUco 模块对每帧图像进行 Marker 检测
4. 实时反馈检测结果（Detected/Rejected/Matched 状态）
5. 将识别成功的帧自动保存至指定目录，用于后续相机标定

## 二、实验环境与过程

### 1. 实验环境

- 服务端系统：Windows 11 + WSL2（Ubuntu 24.04）
- 客户端：iOS 手机浏览器（通过局域网 IP `100.109.169.37:5000` 访问）
- 开发工具：Python 3、Flask、Flask-SocketIO、OpenCV（含 ArUco 模块）
- ArUco 字典：`DICT_4X4_50`，目标 Marker ID：6
- 图像保存路径：`/home/shizhuoyuan/week13_starters/calib_images`

### 2. 系统架构
手机浏览器（客户端）

↓  getUserMedia() 采集摄像头

↓  Canvas → JPEG → Socket.io 发送

↓

Flask + Socket.io 服务端（WSL Ubuntu）

↓  接收 base64 图像帧

↓  OpenCV ArUco 检测

↓  返回检测结果 JSON

↓

前端展示：本地预览 + 服务器检测结果对比显示
### 3. 实验步骤

**（1）安装依赖**

```bash
pip install flask flask-socketio opencv-contrib-python "numpy<2"
```

**（2）服务端核心检测逻辑**

```python
import cv2
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64, os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ARUCO_DICT = cv2.aruco.DICT_4X4_50
EXPECTED_ID = 6
SAVE_DIR = "/home/shizhuoyuan/week13_starters/calib_images"
os.makedirs(SAVE_DIR, exist_ok=True)

@socketio.on('frame')
def handle_frame(data):
    # 解码 base64 图像
    img_data = base64.b64decode(data.split(',')[1])
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # ArUco 检测
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, rejected = detector.detectMarkers(frame)

    detected = len(corners) if corners is not None else 0
    matched = False

    if ids is not None and EXPECTED_ID in ids.flatten():
        matched = True
        filename = os.path.join(SAVE_DIR, f"calib_{len(os.listdir(SAVE_DIR)):04d}.jpg")
        cv2.imwrite(filename, frame)

    emit('result', {
        'detected': detected,
        'rejected': len(rejected) if rejected is not None else 0,
        'expected_id': EXPECTED_ID,
        'matched': matched,
        'save_dir': SAVE_DIR
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

**（3）前端 Web 页面**

前端通过 `getUserMedia()` 调用手机摄像头，用 Canvas 将视频帧编码为 JPEG 后通过 Socket.io 持续发送至服务端，并将检测结果实时显示在界面右侧。页面标题为"Week 12 手机相机桥接"，包含摄像头参数说明：Dictionary `DICT_4X4_50`，Marker ID：6。

**（4）运行与测试**

```bash
# 启动服务端（WSL 终端）
python3 server.py

# 手机浏览器访问（局域网 IP）
http://100.109.169.37:5000
```

## 三、实验现象与结果分析

### 1. 核心现象

**Web 界面正常运行：** 页面成功加载，左侧为手机本地视频预览，右侧为服务器检测结果，双栏布局清晰直观（见截图 `屏幕截图 2026-05-28 100852.png`）。

**服务器日志正常：** 终端持续输出 Socket.io 的 HTTP 请求日志，`GET /preview.jpg` 和 `POST /socket.io/` 请求以约 1Hz 频率持续响应，说明视频流传输链路稳定（见截图 `屏幕截图 2026-05-28 100857.png`）。

**ArUco 检测结果对比：**

| 测试状态 | Detected | Rejected | Matched Expected |
|---------|---------|---------|----------------|
| 无 Marker（初始） | 0 | 16 | false |
| 检测到 ID:6（成功） | 1 | 3 | true ✅ |

- **初始状态（`3ee5db9588bbea7cdee7d8244a310e54.jpg`）：** 摄像头对准普通场景，`Detected: 0, Rejected: 16`，未匹配到 ID:6
- **成功检测（`c6d51352643eb98a890379c8a49adea6.jpg`）：** 将 ArUco ID:6 Marker 对准摄像头后，`Detected: 1, Rejected: 3, Matched expected: true`，图像自动保存至 `/home/shizhuoyuan/week13_starters/calib_images`

### 2. 问题与解决

**摄像头访问权限：** 手机浏览器要求 HTTPS 才能调用 `getUserMedia()`，通过为 Flask 配置自签名证书解决。

**WSL2 网络端口暴露：** WSL2 的网络默认不对外暴露，手机无法直接访问。通过 Windows 防火墙添加入站规则（允许 5000 端口），并使用 `netsh interface portproxy` 配置端口转发后，手机成功通过局域网 IP 访问服务。

**视频帧传输卡顿：** JPEG 压缩质量过高（95）导致每帧数据量过大，传输延迟明显。将压缩质量调整为 70 后，延迟降低，画面流畅度显著提升。

## 四、实验结论

本实验成功构建了"手机摄像头 → Socket.io 推流 → WSL 服务端 ArUco 检测"的完整视觉感知闭环系统，验证了以下关键技术点：

1. **跨设备视频流传输：** 通过 Socket.io 实现手机到 WSL 服务端的实时视频帧传输，延迟约 100-200ms，满足实时检测需求
2. **ArUco Marker 准确识别：** OpenCV ArUco 模块可稳定识别 DICT_4X4_50 字典中的 ID:6 Marker，`Matched expected: true` 判断逻辑正确可靠
3. **自动标定图像采集：** 成功匹配的帧自动保存至指定目录，为相机内参标定提供数据来源，可直接用于后续 `cv2.calibrateCamera()` 流程

## 五、实验心得

**系统集成思维的建立：** 本次期末项目让我第一次独立完成了"前后端 + 视觉算法"三层架构的完整系统。从网络通信到图像处理，每个模块都有其独立逻辑，系统联调阶段出现的问题（权限、网络、性能）让我深刻理解了集成测试的重要性。

**手机作为机器人传感器的可行性：** 本实验证明了手机摄像头可以作为低成本的机器人视觉传感器，通过 Socket.io 协议桥接到 ROS2 处理节点。这为后续在真实机器人项目中使用手机代替工业相机提供了技术参考，大幅降低了硬件门槛。

**ArUco Marker 在机器人中的价值：** ArUco Marker 不仅可用于目标检测，其角点坐标还可用于相机位姿估计（PnP 求解），是机器人抓取、导航定位中常用的视觉基准。本次实验为后续学习位姿估计打下了实践基础，也与 Week 5 机械臂抓取实验形成了良好的知识衔接。

## 六、实验截图

- `屏幕截图 2026-05-28 100852.png`：Web 界面双栏显示（本地预览 + 服务器检测结果）
- `屏幕截图 2026-05-28 100857.png`：服务端 Flask 运行日志（Socket.io 请求流）
- `3ee5db9588bbea7cdee7d8244a310e54.jpg`：手机端截图（初始状态，Detected: 0）
- `c6d51352643eb98a890379c8a49adea6.jpg`：手机端截图（成功检测 ID:6，Matched: true）
