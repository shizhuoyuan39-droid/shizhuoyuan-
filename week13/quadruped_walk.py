#!/usr/bin/env python3
"""
quadruped_walk.py — PyBullet 四足机器人 Trot 步态调试
Week 13 作业
成员：史卓远、杜泽凝

功能：
  - 加载四足机器人 URDF 模型
  - 实现 Trot（对角步态）行走
  - 使用正弦函数生成髋关节/膝关节轨迹
  - 可视化仿真并记录机器人位移

使用方法：
  pip install pybullet
  python3 quadruped_walk.py
"""

import pybullet as p
import pybullet_data
import time
import math
import os

# ── 仿真参数 ──────────────────────────────────────────────────────────────────
SIM_FREQ      = 240       # 仿真频率 Hz
SIM_DURATION  = 10.0      # 仿真时长（秒）
REAL_TIME     = True      # 是否实时仿真

# ── 步态参数（Trot） ───────────────────────────────────────────────────────────
GAIT_FREQ     = 1.5       # 步态频率 Hz（每秒完成 1.5 个步态周期）
HIP_AMPLITUDE = 0.4       # 髋关节摆动幅度（rad）
KNEE_AMPLITUDE = 0.6      # 膝关节摆动幅度（rad）
HIP_OFFSET    = 0.0       # 髋关节偏置角
KNEE_OFFSET   = -0.8      # 膝关节偏置角（站立姿态）

# Trot 步态相位偏移（对角腿同相，相邻腿反相）
# 腿序：0=前左(FL) 1=前右(FR) 2=后左(RL) 3=后右(RR)
PHASE_OFFSET = [0.0, math.pi, math.pi, 0.0]   # FL/RR 同相，FR/RL 同相


def load_robot(client):
    """加载四足机器人模型，优先使用 pybullet_data 中的 ANYmal，
    若不存在则使用 laikago，再不行则用内置简化模型路径。"""
    p.setAdditionalSearchPath(pybullet_data.getDataPath())

    # 候选 URDF（pybullet_data 内置）
    candidates = [
        "laikago/laikago.urdf",
        "a1/a1.urdf",
    ]
    for urdf in candidates:
        full = os.path.join(pybullet_data.getDataPath(), urdf)
        if os.path.exists(full):
            robot = p.loadURDF(urdf,
                               basePosition=[0, 0, 0.5],
                               baseOrientation=p.getQuaternionFromEuler([0, 0, 0]),
                               physicsClientId=client)
            print(f"[加载] 使用模型：{urdf}")
            return robot

    # 最终回退：使用 URDF 字符串内联创建最简四足模型
    print("[加载] 未找到内置四足模型，使用简化 URDF")
    import tempfile, textwrap
    urdf_str = textwrap.dedent("""
    <?xml version="1.0"?>
    <robot name="simple_quad">
      <link name="base"><inertial><mass value="5"/><inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/></inertial>
        <visual><geometry><box size="0.4 0.2 0.08"/></geometry></visual>
        <collision><geometry><box size="0.4 0.2 0.08"/></geometry></collision></link>
      <!-- 前左腿 -->
      <link name="FL_hip"><inertial><mass value="0.5"/><inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
        <visual><geometry><cylinder radius="0.02" length="0.1"/></geometry></visual></link>
      <joint name="FL_hip_joint" type="revolute"><parent link="base"/><child link="FL_hip"/>
        <origin xyz="0.15 0.1 0"/><axis xyz="1 0 0"/><limit lower="-1.5" upper="1.5" effort="20" velocity="5"/></joint>
      <link name="FL_knee"><inertial><mass value="0.3"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.005"/></inertial>
        <visual><geometry><cylinder radius="0.015" length="0.15"/></geometry></visual></link>
      <joint name="FL_knee_joint" type="revolute"><parent link="FL_hip"/><child link="FL_knee"/>
        <origin xyz="0 0 -0.1"/><axis xyz="1 0 0"/><limit lower="-2.5" upper="0" effort="20" velocity="5"/></joint>
      <!-- 前右腿 -->
      <link name="FR_hip"><inertial><mass value="0.5"/><inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
        <visual><geometry><cylinder radius="0.02" length="0.1"/></geometry></visual></link>
      <joint name="FR_hip_joint" type="revolute"><parent link="base"/><child link="FR_hip"/>
        <origin xyz="0.15 -0.1 0"/><axis xyz="1 0 0"/><limit lower="-1.5" upper="1.5" effort="20" velocity="5"/></joint>
      <link name="FR_knee"><inertial><mass value="0.3"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.005"/></inertial>
        <visual><geometry><cylinder radius="0.015" length="0.15"/></geometry></visual></link>
      <joint name="FR_knee_joint" type="revolute"><parent link="FR_hip"/><child link="FR_knee"/>
        <origin xyz="0 0 -0.1"/><axis xyz="1 0 0"/><limit lower="-2.5" upper="0" effort="20" velocity="5"/></joint>
      <!-- 后左腿 -->
      <link name="RL_hip"><inertial><mass value="0.5"/><inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
        <visual><geometry><cylinder radius="0.02" length="0.1"/></geometry></visual></link>
      <joint name="RL_hip_joint" type="revolute"><parent link="base"/><child link="RL_hip"/>
        <origin xyz="-0.15 0.1 0"/><axis xyz="1 0 0"/><limit lower="-1.5" upper="1.5" effort="20" velocity="5"/></joint>
      <link name="RL_knee"><inertial><mass value="0.3"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.005"/></inertial>
        <visual><geometry><cylinder radius="0.015" length="0.15"/></geometry></visual></link>
      <joint name="RL_knee_joint" type="revolute"><parent link="RL_hip"/><child link="RL_knee"/>
        <origin xyz="0 0 -0.1"/><axis xyz="1 0 0"/><limit lower="-2.5" upper="0" effort="20" velocity="5"/></joint>
      <!-- 后右腿 -->
      <link name="RR_hip"><inertial><mass value="0.5"/><inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/></inertial>
        <visual><geometry><cylinder radius="0.02" length="0.1"/></geometry></visual></link>
      <joint name="RR_hip_joint" type="revolute"><parent link="base"/><child link="RR_hip"/>
        <origin xyz="-0.15 -0.1 0"/><axis xyz="1 0 0"/><limit lower="-1.5" upper="1.5" effort="20" velocity="5"/></joint>
      <link name="RR_knee"><inertial><mass value="0.3"/><inertia ixx="0.005" ixy="0" ixz="0" iyy="0.005" iyz="0" izz="0.005"/></inertial>
        <visual><geometry><cylinder radius="0.015" length="0.15"/></geometry></visual></link>
      <joint name="RR_knee_joint" type="revolute"><parent link="RR_hip"/><child link="RR_knee"/>
        <origin xyz="0 0 -0.1"/><axis xyz="1 0 0"/><limit lower="-2.5" upper="0" effort="20" velocity="5"/></joint>
    </robot>
    """)
    with tempfile.NamedTemporaryFile(suffix='.urdf', mode='w', delete=False) as f:
        f.write(urdf_str)
        tmp_path = f.name
    robot = p.loadURDF(tmp_path, basePosition=[0, 0, 0.5],
                       physicsClientId=client)
    return robot


def get_joint_map(robot, client):
    """返回关节名称 → 关节索引的映射"""
    jmap = {}
    for i in range(p.getNumJoints(robot, physicsClientId=client)):
        info = p.getJointInfo(robot, i, physicsClientId=client)
        name = info[1].decode('utf-8')
        jmap[name] = i
    return jmap


def find_leg_joints(jmap):
    """
    自动识别四条腿的髋关节和膝关节索引。
    返回：[(hip_idx, knee_idx), ...] 顺序为 FL, FR, RL, RR
    """
    # 常见关键词映射
    hip_kw  = [['FL','hip'], ['FR','hip'], ['RL','hip'], ['RR','hip'],
               ['fl','hip'], ['fr','hip'], ['rl','hip'], ['rr','hip'],
               ['0','hip'],  ['1','hip'],  ['2','hip'],  ['3','hip']]
    knee_kw = [['FL','knee','thigh','upper'], ['FR','knee','thigh','upper'],
               ['RL','knee','thigh','upper'], ['RR','knee','thigh','upper']]

    legs = []
    for leg_prefix in ['FL', 'FR', 'RL', 'RR']:
        hip_idx  = None
        knee_idx = None
        for name, idx in jmap.items():
            nu = name.upper()
            if leg_prefix in nu and ('HIP' in nu or 'SHOULDER' in nu or 'ABDUCTOR' in nu):
                hip_idx = idx
            if leg_prefix in nu and ('KNEE' in nu or 'THIGH' in nu or 'UPPER' in nu or 'CALF' in nu):
                knee_idx = idx
        if hip_idx is not None and knee_idx is not None:
            legs.append((hip_idx, knee_idx))

    # 若自动识别失败，按顺序取前8个旋转关节
    if len(legs) < 4:
        revolute = [idx for name, idx in jmap.items()]
        revolute = revolute[:8]
        legs = [(revolute[i*2], revolute[i*2+1]) for i in range(4) if i*2+1 < len(revolute)]

    return legs[:4]


def trot_angles(t, leg_idx):
    """计算第 leg_idx 条腿在时刻 t 的 (髋关节角, 膝关节角)"""
    phase = 2 * math.pi * GAIT_FREQ * t + PHASE_OFFSET[leg_idx]
    hip   = HIP_OFFSET  + HIP_AMPLITUDE  * math.sin(phase)
    knee  = KNEE_OFFSET + KNEE_AMPLITUDE * math.sin(phase + math.pi / 2)
    return hip, knee


def main():
    # ── 连接 PyBullet ────────────────────────────────────────────────────────
    client = p.connect(p.GUI)
    p.setGravity(0, 0, -9.8, physicsClientId=client)
    p.setTimeStep(1.0 / SIM_FREQ, physicsClientId=client)
    p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraYaw=45,
                                  cameraPitch=-20, cameraTargetPosition=[0,0,0.3])

    # ── 加载地面 ─────────────────────────────────────────────────────────────
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.loadURDF("plane.urdf", physicsClientId=client)

    # ── 加载机器人 ────────────────────────────────────────────────────────────
    robot = load_robot(client)
    jmap  = get_joint_map(robot, client)
    print(f"[关节] 共 {len(jmap)} 个关节：{list(jmap.keys())}")

    legs = find_leg_joints(jmap)
    print(f"[步态] 识别腿部关节（FL/FR/RL/RR）：{legs}")

    if len(legs) < 4:
        print("[警告] 关节识别不足4条腿，仿真继续但步态可能不完整")

    # ── 初始站立姿态 ─────────────────────────────────────────────────────────
    for hip_idx, knee_idx in legs:
        p.resetJointState(robot, hip_idx,  HIP_OFFSET,  physicsClientId=client)
        p.resetJointState(robot, knee_idx, KNEE_OFFSET, physicsClientId=client)
    for _ in range(100):
        p.stepSimulation(physicsClientId=client)

    # ── 主仿真循环 ────────────────────────────────────────────────────────────
    steps = int(SIM_DURATION * SIM_FREQ)
    start_pos = p.getBasePositionAndOrientation(robot, physicsClientId=client)[0]
    print(f"[仿真] 开始，共 {steps} 步，时长 {SIM_DURATION}s")

    for step in range(steps):
        t = step / SIM_FREQ

        for i, (hip_idx, knee_idx) in enumerate(legs):
            if i >= 4:
                break
            hip_angle, knee_angle = trot_angles(t, i)

            p.setJointMotorControl2(
                robot, hip_idx,
                controlMode=p.POSITION_CONTROL,
                targetPosition=hip_angle,
                force=20, maxVelocity=5,
                physicsClientId=client)

            p.setJointMotorControl2(
                robot, knee_idx,
                controlMode=p.POSITION_CONTROL,
                targetPosition=knee_angle,
                force=20, maxVelocity=5,
                physicsClientId=client)

        p.stepSimulation(physicsClientId=client)

        if REAL_TIME:
            time.sleep(1.0 / SIM_FREQ)

        # 每 2 秒打印一次位置
        if step % (SIM_FREQ * 2) == 0:
            pos, _ = p.getBasePositionAndOrientation(robot, physicsClientId=client)
            print(f"  t={t:.1f}s  位置: x={pos[0]:.3f}, y={pos[1]:.3f}, z={pos[2]:.3f}")

    # ── 统计结果 ─────────────────────────────────────────────────────────────
    end_pos = p.getBasePositionAndOrientation(robot, physicsClientId=client)[0]
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    dist = math.sqrt(dx*dx + dy*dy)
    print(f"\n[结果] 仿真结束")
    print(f"  起始位置: {start_pos}")
    print(f"  终止位置: {end_pos}")
    print(f"  总位移:   {dist:.3f} m")
    print(f"  平均速度: {dist/SIM_DURATION:.3f} m/s")

    time.sleep(2)
    p.disconnect(client)


if __name__ == '__main__':
    main()
