一、实验背景与目的
本次实验基于 Docker 容器化 ROS2 环境，完成pybullet、OpenCV、NumPy等依赖库的安装，并通过docker commit命令将配置好的容器保存为自定义镜像，实现 ROS2 开发环境的持久化与复用，掌握 Docker 容器镜像定制的核心流程，解决 OpenCV 与 NumPy 的版本兼容性问题。
二、实验环境与过程
1. 实验环境
宿主系统：Windows 11 + PowerShell
容器环境：基于ghcr.io/tiryoh/ros2-desktop-vnc:humble的 ROS2 Humble 容器，支持 VNC / 浏览器桌面访问
核心工具：Docker、pip包管理器、docker commit命令
2. 实验步骤
启动基础容器：在 PowerShell 中运行docker run命令启动 ROS2 容器，通过docker ps查看运行中的容器。
进入容器安装依赖：
bash
运行
# 进入容器终端
docker exec -it ee0b197cc16c /bin/bash
# 安装兼容版本的NumPy（解决OpenCV依赖冲突）
pip install "numpy<2"
# 安装OpenCV及扩展模块
pip install opencv-python opencv-contrib-python
# 安装PyBullet物理仿真库
pip install pybullet
解决依赖冲突：处理opencv-python与numpy<2的版本兼容性报错，通过调整安装顺序和版本限制完成配置。
提交容器为自定义镜像：
powershell
# 提交容器为镜像，添加描述信息
docker commit -m "install pybullet and opencv" -a "shizhuoyuan1" ee0b197cc16c my-ros2-full:v1.0
# 查看生成的自定义镜像
docker images
备份与复用镜像：将配置好的容器84436b8f83fc提交为addog:shi镜像，实现多环境配置的持久化。
三、实验现象与问题分析
1. 核心现象
依赖安装与冲突解决：安装numpy<2后，opencv-python提示依赖numpy>=2的冲突，但通过强制安装兼容版本的 OpenCV（适配旧版 NumPy），最终完成安装。
容器镜像成功生成：docker commit命令执行后，生成了大小为12.4GB的my-ros2-full:v1.0镜像，相比基础镜像10.8GB增加了依赖库的占用空间。
容器内 Docker 命令不可用：在容器终端执行docker ps时提示command not found，说明容器内未安装 Docker 客户端，无法在容器内直接管理 Docker。
2. 原理与问题分析
docker commit的工作原理：该命令将容器的文件系统变更（如安装的依赖、配置的环境）保存为一个新的只读镜像层，保留容器的运行状态，实现环境的持久化。相比 Dockerfile 构建，commit更适合快速保存已配置好的临时环境。
OpenCV 与 NumPy 版本冲突的根源：新版opencv-python（4.13+）要求numpy>=2，但 ROS2 容器内的 Python 3.10 环境中，numpy<2的旧版本更稳定，通过安装适配旧版 NumPy 的 OpenCV 版本（如 4.5.x）或降级 OpenCV 可解决冲突。
容器内 Docker 命令不可用的原因：ghcr.io/tiryoh/ros2-desktop-vnc镜像仅包含 ROS2 运行环境，未预装 Docker 客户端，因此无法在容器内执行 Docker 相关命令，如需容器内 Docker 功能需使用 Docker-in-Docker 方案。
四、实验结论
通过docker commit命令可将配置好依赖的 ROS2 容器保存为自定义镜像，实现开发环境的快速复用，避免重复安装依赖的繁琐流程。
OpenCV 与 NumPy 的版本兼容性是计算机视觉开发中的常见问题，需根据 Python 版本和 ROS 环境选择适配的依赖版本。
容器化环境下的开发流程需注意镜像的分层存储机制，commit生成的镜像会包含所有容器变更，体积较大，后续可通过 Dockerfile 优化构建流程，减小镜像体积。
五、实验心得（补充版）
容器镜像定制的价值：本次实验让我体会到 Docker 镜像定制的便捷性 —— 原本需要重复配置的 ROS2+OpenCV+PyBullet 环境，通过一次commit即可保存为镜像，后续开发直接运行镜像即可，大大提升了开发效率，也保证了团队环境的一致性。
依赖冲突的调试思路：解决 OpenCV 与 NumPy 的版本冲突时，我意识到依赖版本管理的重要性。在复杂开发环境中，需先梳理依赖关系，再通过调整版本限制、分步安装等方式解决冲突，而不是盲目安装最新版本。
容器化开发的局限性与优化方向：docker commit生成的镜像体积较大，且无法追溯构建过程，后续应学习使用 Dockerfile 构建镜像，通过分层构建减少镜像体积，同时实现构建流程的可复用与可维护。
后续拓展方向：可基于自定义镜像，开发 ROS2+OpenCV 的视觉目标检测节点，或结合 PyBullet 实现四足机器人的物理仿真，将容器化环境与实际机器人项目开发结合起来，进一步验证环境的可用性。
