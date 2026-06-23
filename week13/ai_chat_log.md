# ai_chat_log.md — AI 协作调试记录
**作业：Week 13 PyBullet 四足机器人 Trot 步态调试**
**成员：史卓远、杜泽凝**
**日期：2026 年 6 月 17 日**

---

## 对话记录

---

### 第 1 轮

**我：**
我在用 PyBullet 做四足机器人仿真，想实现 Trot 步态，但不知道从哪里开始。Trot 步态的基本原理是什么？

**AI：**
Trot（对角步态）是四足机器人最常用的步态之一，核心原理是：**对角线上的两条腿同时抬起和落地**，即前左腿（FL）和后右腿（RR）为一组，前右腿（FR）和后左腿（RL）为另一组，两组之间相位差 180°（π rad）。

在代码实现上，通常用正弦函数生成关节角度轨迹：

```python
phase = 2 * pi * freq * t + phase_offset[leg]
hip_angle  = hip_offset  + hip_amplitude  * sin(phase)
knee_angle = knee_offset + knee_amplitude * sin(phase + pi/2)
```

其中 `phase_offset` 决定各腿的相位关系：FL/RR 设为 0，FR/RL 设为 π。

---

### 第 2 轮

**我：**
我加载了 laikago URDF，但运行后机器人直接倒下了，完全没有站立。怎么解决？

**AI：**
机器人倒下通常有以下几个原因，逐一排查：

1. **初始高度不够**：`basePosition` 的 z 值太低，机器人还没站好就落地碰撞了。建议改为 `[0, 0, 0.5]` 或更高。

2. **没有设置初始关节角**：URDF 默认关节角为 0，laikago 在这个姿态下腿是伸直的，重心不稳。需要先用 `resetJointState` 把膝关节设为约 -0.8 rad 的弯曲姿态。

3. **没有预热步骤**：加载后先 `stepSimulation` 100 次，让物理引擎稳定接触面，再开始控制。

修复代码：
```python
for hip_idx, knee_idx in legs:
    p.resetJointState(robot, hip_idx,  0.0)
    p.resetJointState(robot, knee_idx, -0.8)
for _ in range(100):
    p.stepSimulation()
```

---

### 第 3 轮

**我：**
机器人现在能站立了，但步态控制加上去之后腿在抖动，不能向前走。是参数问题还是代码问题？

**AI：**
抖动通常是以下原因造成的：

**1. 幅度太大**：`hip_amplitude` 设置过大会让腿摆角超出物理范围导致抖振。建议从 0.3 rad 开始，逐步增加。

**2. `force` 太小或太大**：`setJointMotorControl2` 的 `force` 参数控制关节扭矩。太小无法克服重力，太大会导致过激响应。laikago 建议从 20 N·m 开始调试。

**3. 膝关节相位不对**：膝关节应该比髋关节超前 90°（π/2），即：
```python
knee_angle = knee_offset + knee_amplitude * sin(phase + pi/2)
```
如果相位写错（比如和髋关节同相），腿会原地抖动而不产生推进力。

**4. 步态频率过高**：1.5 Hz 以上容易失稳，调试时先设为 1.0 Hz。

---

### 第 4 轮

**我：**
调整参数后机器人能走了，但走着走着会偏转方向，不能直走。有什么办法修正吗？

**AI：**
方向偏转是四足仿真的常见问题，原因和解决方法如下：

**原因 1：左右腿参数不对称**
检查 FL/RL 和 FR/RR 的 `phase_offset` 是否完全对称。FL 和 RR 同为 0，FR 和 RL 同为 π，任何细微差异都会造成偏转。

**原因 2：URDF 模型本身存在质量不对称**
laikago 等模型质心可能略有偏移，这是正常的，可以通过在控制层加入偏航角（yaw）反馈补偿：
```python
_, orn = p.getBasePositionAndOrientation(robot)
euler = p.getEulerFromQuaternion(orn)
yaw_error = euler[2]  # 期望 yaw = 0
# 根据 yaw_error 微调左右腿幅度
```

**原因 3：摩擦力设置**
默认地面摩擦力可能不足，可以修改：
```python
p.changeDynamics(plane_id, -1, lateralFriction=0.8)
```

对于本次作业，直走能走出 1 m 以上即视为调试成功，轻微偏转可接受。

---

### 第 5 轮

**我：**
仿真完成后怎么判断步态调试是否成功？有没有量化指标？

**AI：**
可以用以下几个量化指标评估 Trot 步态调试效果：

**1. 总位移（最直观）**
仿真结束时记录起终点距离，10 秒内能走出 0.3 m 以上说明步态基本可行。

**2. 平均前进速度**
`速度 = 总位移 / 时间`，laikago 在 Trot 步态下实际速度约 0.1～0.5 m/s。

**3. 机体高度稳定性**
记录 z 轴高度变化，理想情况应在初始值附近小幅波动（±0.05 m 以内）。

**4. 是否摔倒**
可以检测 z 高度是否低于阈值（如 0.1 m）判断是否跌倒。

在代码中加入统计：
```python
end_pos = p.getBasePositionAndOrientation(robot)[0]
dist = math.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2)
print(f"总位移: {dist:.3f} m，平均速度: {dist/SIM_DURATION:.3f} m/s")
```

---

### 第 6 轮

**我：**
如果老师提供的模型关节名字和 laikago 不一样，代码怎么兼容？

**AI：**
可以在代码里加一个自动识别关节的函数，通过关键词匹配关节名称，而不写死索引：

```python
def get_joint_map(robot):
    jmap = {}
    for i in range(p.getNumJoints(robot)):
        name = p.getJointInfo(robot, i)[1].decode('utf-8')
        jmap[name] = i
    return jmap

def find_leg_joints(jmap):
    legs = []
    for prefix in ['FL', 'FR', 'RL', 'RR']:
        hip_idx, knee_idx = None, None
        for name, idx in jmap.items():
            nu = name.upper()
            if prefix in nu and any(k in nu for k in ['HIP','SHOULDER','ABDUCTOR']):
                hip_idx = idx
            if prefix in nu and any(k in nu for k in ['KNEE','THIGH','UPPER','CALF']):
                knee_idx = idx
        if hip_idx and knee_idx:
            legs.append((hip_idx, knee_idx))
    return legs
```

这样无论老师的模型关节叫什么名字，只要含有 FL/FR/RL/RR 和 hip/knee 关键词就能自动识别。

---

*以上为与 AI 协作调试的完整对话记录，共 6 轮。*
