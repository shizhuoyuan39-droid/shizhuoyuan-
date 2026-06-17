# Week 12：视觉感知与 PyBullet 物理仿真综合实验

## 一、实验背景与目的

本次实验在 Docker 容器化 ROS2 环境的基础上，综合运用 PyBullet 物理仿真引擎与 OpenCV 视觉库，完成机器人物理仿真场景的搭建与视觉感知模块的集成验证。实验目标是掌握 PyBullet 仿真环境的基本操作，理解物理引擎在机器人仿真中的应用，并结合 OpenCV 实现视觉数据的采集与处理，为后续视觉引导机器人运动控制奠定基础。

## 二、实验环境与过程

### 1. 实验环境

- 宿主系统：Windows 11 + WSL2（Ubuntu 24.04）
- 容器环境：Docker + 自定义 ROS2 镜像（`my-ros2-full:v1.0`，已预装 PyBullet、OpenCV、NumPy）
- 核心工具：PyBullet 物理仿真库、OpenCV 计算机视觉库、Python 3、Docker 容器桌面（127.0.0.1:16080）

### 2. 实验步骤

**（1）启动已配置的 Docker 容器**

使用上周（Week 11）保存的自定义镜像启动容器，无需重复安装依赖：

```bash
docker run -p 16080:80 -p 16006:6006 --shm-size=512m my-ros2-full:v1.0
```

通过浏览器访问 `127.0.0.1:16080` 进入容器桌面环境。

**（2）PyBullet 仿真环境初始化**

在容器终端中启动 PyBullet ExampleBrowser，选择 OpenGL3+ 渲染模式：

```bash
python3 -c "import pybullet as p; import pybullet_data; \
  p.connect(p.GUI); p.setAdditionalSearchPath(pybullet_data.getDataPath()); \
  p.loadURDF('plane.urdf'); p.loadURDF('r2d2.urdf', [0,0,1]); \
  p.setGravity(0,0,-9.8); \
  [p.stepSimulation() for _ in range(10000)]"
```

**（3）物理仿真场景观察**

通过 ExampleBrowser 运行内置仿真示例，观察刚体动力学、碰撞检测、关节控制等核心功能，记录仿真器运行过程（已录制为 MP4 视频）。

**（4）OpenCV 视觉模块集成测试**

结合 Week 10 的 OpenCV 基础，验证 PyBullet 渲染图像与 OpenCV 的数据交互：

```python
import pybullet as p
import pybullet_data
import cv2
import numpy as np

p.connect(p.DIRECT)  # 离屏渲染模式（无 GUI）
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")
p.loadURDF("r2d2.urdf", [0, 0, 1])
p.setGravity(0, 0, -9.8)

for _ in range(100):
    p.stepSimulation()

# 获取仿真渲染图像
width, height = 640, 480
view_matrix = p.computeViewMatrix([3, 3, 3], [0, 0, 0], [0, 0, 1])
proj_matrix = p.computeProjectionMatrixFOV(60, width/height, 0.1, 100)
_, _, img, _, _ = p.getCameraImage(width, height, view_matrix, proj_matrix)

# 转为 OpenCV 格式并保存
img_array = np.array(img, dtype=np.uint8).reshape(height, width, 4)
img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
cv2.imwrite("pybullet_frame.png", img_bgr)

p.disconnect()
print("仿真帧已保存为 pybullet_frame.png")
```

## 三、实验现象与问题分析

### 1. 核心现象

**PyBullet 物理仿真正常运行：** Bullet Physics ExampleBrowser 成功在 Ubuntu 24.04 容器环境中以 OpenGL3+ 渲染模式启动（Release Build），仿真场景包含重力、刚体碰撞、关节驱动等物理效果，机器人模型在重力作用下表现出真实的动力学响应。

**视频记录：** 录制了 PyBullet ExampleBrowser 的完整运行过程，记录了仿真场景初始化、物体自由落体、碰撞弹跳等关键物理现象（见 `Bullet Physics ExampleBrowser using OpenGL3+ [btgl] Release build (Ubuntu-24.04) 2026-05-21 11-37-55.mp4`）。

**离屏渲染与 OpenCV 集成：** PyBullet 的 `DIRECT` 模式支持无 GUI 的离屏渲染，`getCameraImage()` 返回的 RGBA 数组可直接转换为 OpenCV 可处理的 BGR 格式，两者的数据交互流程顺畅。

### 2. 问题与解决

**OpenGL 渲染依赖：** 容器内首次运行 PyBullet GUI 模式时提示缺少 OpenGL 相关库，通过安装 `libgl1-mesa-glx` 解决，并保存到自定义镜像中避免重复安装。

**NumPy 数组维度：** `getCameraImage()` 返回一维扁平数组，需通过 `reshape(height, width, 4)` 重组为标准图像格式，初期因维度错误导致 OpenCV 处理失败，调整后正常运行。

**仿真步长与实时性：** 默认仿真步长（1/240s）在 Docker 容器内因 CPU 资源限制存在轻微卡顿，通过减少每帧渲染分辨率（从 1080p 降至 720p）后，仿真帧率明显提升，达到流畅运行标准。

## 四、实验结论

PyBullet 物理引擎可在 Docker 容器化 Ubuntu 环境中稳定运行，支持 OpenGL3+ 渲染，能够真实模拟刚体动力学、碰撞检测与关节驱动等机器人核心物理过程，是低成本机器人算法验证的高效平台。

PyBullet 的离屏渲染功能与 OpenCV 数据格式兼容良好，两者集成为视觉感知模块提供了完整的数据通路，可支持后续相机位姿估计、目标检测等视觉任务在仿真环境中的验证。

## 五、实验心得

**仿真与现实的桥梁：** 在真实硬件投入之前，PyBullet 可以快速验证控制算法的物理可行性，大幅降低开发成本和风险。这个思路在工业机器人开发中被广泛采用——先仿真调优，再部署硬件。

**视觉-物理联合仿真的潜力：** PyBullet 渲染图像与 OpenCV 的结合，让我看到了视觉引导机器人控制的完整闭环：仿真环境提供视觉输入，视觉算法提取特征，控制算法驱动仿真机器人响应。这种模式是现代机器人学研究的主流范式，也是 Week 13 期末项目的理论基础。

**容器化镜像的跨周复用价值：** 直接使用 Week 11 保存的自定义镜像，无需重新安装任何依赖，1 分钟内即可恢复完整实验环境。容器化开发在跨周次实验延续性上的优势非常显著。

## 六、实验资料

- 📹 仿真运行视频：`Bullet Physics ExampleBrowser using OpenGL3+ [btgl] Release build (Ubuntu-24.04) 2026-05-21 11-37-55.mp4`
