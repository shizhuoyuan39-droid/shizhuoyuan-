#!/usr/bin/env python3
"""
maze.py — 自定义迷宫地图定义
Week 14 作业
平台：ROS + turtlesim

迷宫坐标系：turtlesim 窗口为 11x11 单位
0=通道，1=墙壁
起点：(1,1)，终点：(9,9)（turtlesim 坐标）
"""

# ────────────────────────────────────────────
# 迷宫地图（行 0 在顶部，列 0 在左侧）
# 行数=ROW，列数=COL
# ────────────────────────────────────────────
MAZE = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

ROWS = len(MAZE)
COLS = len(MAZE[0])

# turtlesim 坐标原点在左下角，y 轴向上
# 迷宫行列 → turtlesim 坐标换算（每格 = 1 单位）
CELL_SIZE = 1.0          # 每个格子对应的 turtlesim 单位长度
ORIGIN_X  = 0.5          # 地图左下角在 turtlesim 中的 x
ORIGIN_Y  = 0.5          # 地图左下角在 turtlesim 中的 y

# 起点和终点（行, 列）
START = (9, 1)   # 迷宫左下通道
GOAL  = (1, 9)   # 迷宫右上通道


def maze_to_turtle(row, col):
    """将迷宫行列坐标转换为 turtlesim (x, y)"""
    x = ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
    y = ORIGIN_Y + (ROWS - 1 - row) * CELL_SIZE + CELL_SIZE / 2
    return x, y


def turtle_to_maze(x, y):
    """将 turtlesim (x, y) 转换为迷宫行列坐标（取整）"""
    col = int((x - ORIGIN_X) / CELL_SIZE)
    row = int(ROWS - 1 - (y - ORIGIN_Y) / CELL_SIZE)
    return row, col


def is_wall(row, col):
    """判断该格子是否为墙壁"""
    if row < 0 or row >= ROWS or col < 0 or col >= COLS:
        return True
    return MAZE[row][col] == 1


def get_neighbors(row, col):
    """返回四方向可走的邻居格子列表"""
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if not is_wall(nr, nc):
            neighbors.append((nr, nc))
    return neighbors


def print_maze(path=None):
    """在终端打印迷宫，可选高亮路径"""
    path_set = set(path) if path else set()
    for r, row in enumerate(MAZE):
        line = ''
        for c, cell in enumerate(row):
            pos = (r, c)
            if pos == START:
                line += 'S '
            elif pos == GOAL:
                line += 'G '
            elif pos in path_set:
                line += '· '
            elif cell == 1:
                line += '██'
            else:
                line += '  '
        print(line)


if __name__ == '__main__':
    print("迷宫地图预览（S=起点，G=终点，██=墙壁）：")
    print_maze()
    print(f"\n起点 turtlesim 坐标: {maze_to_turtle(*START)}")
    print(f"终点 turtlesim 坐标: {maze_to_turtle(*GOAL)}")
