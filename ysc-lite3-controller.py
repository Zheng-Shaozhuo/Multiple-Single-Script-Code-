# -*- encoding: utf-8 -*-

# 执行前处理网络
# sudo ip route del default via 192.168.137.120 dev eth1

import sys
import time
import socket
import struct
import threading

import tty
import select
import termios


SERVER_IP = "192.168.1.120"
SERVER_PORT = 43893
HEART_BEAT = 0x21040001

# 简单指令结构体 (CommandHead)
COMMAND_HEAD_STRUCT = struct.Struct('III')  # uint32_t code, parameters_size, type
# ComplexCMD 结构体
COMPLEX_CMD_STRUCT = struct.Struct('iiid')  # int32_t cmd_code, cmd_value, type, double data
# 指令映射标签
CFMAP = {
    '+': lambda: send_easy_command(0x21010D06),     # 移动模式; 移动相关需要预先开启该指令
    '-': lambda: send_easy_command(0x21010D05),     # 原地模式
    'z': lambda: send_easy_command(0x21010202),     # 站立
    'x': lambda: send_easy_command(0x21010D05),     # 原地模式
    'c': lambda: send_easy_command(0x21010507),     # 打招呼
    'v': lambda: send_easy_command(0x21010204),     # 扭身体
    '1': lambda: send_easy_command(0x21010C0A, 1),  # 起立
    '2': lambda: send_easy_command(0x21010C0A, 2),  # 坐下
    '3': lambda: send_easy_command(0x21010C0A, 3),  # 前进
    '4': lambda: send_easy_command(0x21010C0A, 4),  # 后退
    '5': lambda: send_easy_command(0x21010C0A, 5),  # 向左平移
    '6': lambda: send_easy_command(0x21010C0A, 6),  # 向右平移
    '7': lambda: send_easy_command(0x21010C0A, 7),  # 停止
    's': lambda: send_easy_command(0x21010C0A, 7),  # S, 停止
    '8': lambda: send_easy_command(0x21010C0A, 8),  # 低头
    '9': lambda: send_easy_command(0x21010C0A, 9),  # 抬头
    '!': lambda: send_easy_command(0x21010C0A, 11), # 向左看
    '@': lambda: send_easy_command(0x21010C0A, 12), # 向右看
    '#': lambda: send_easy_command(0x21010C0A, 13), # 向左旋转
    '$': lambda: send_easy_command(0x21010C0A, 14), # 向右旋转
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_easy_command(code, psize=0, ctype=0):
    head = COMMAND_HEAD_STRUCT.pack(code, psize, ctype)
    sock.sendto(head, (SERVER_IP, SERVER_PORT))
    if HEART_BEAT == code: return
    print(f"指令 {hex(code)} 发送成功.")

def send_complex_command(code, value, data):
    # 构造 ComplexCMD 数据
    packed = COMPLEX_CMD_STRUCT.pack(code, value, 1, data)
    sock.sendto(packed, (SERVER_IP, SERVER_PORT))
    print("复杂指令发送成功.")

def periodic_task():
    """维持心跳"""
    while True:
        send_easy_command(HEART_BEAT)
        time.sleep(0.2)  # 200ms

# 非阻塞检测键盘输入
def kbhit():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []


def init():
    """初始化"""
    # 初始化连接
    send_easy_command(0x2101030D)  # 关闭扬声器

    # 启动定时任务线程
    thread = threading.Thread(target=periodic_task, daemon=True)
    thread.start()


def exec_action(ch: str):
    """执行具体指令"""
    func = CFMAP.get(ch, None)
    if func is None:
        print (f"key: {ch} not match func, skip")
        return
    func()


def main():
    """主函数"""
    print("按 z 键发送站立模式指令...")
    # 恢复终端设置
    orig_attr = termios.tcgetattr(sys.stdin)
    # 设置非阻塞终端
    tty.setcbreak(sys.stdin.fileno())

    init()
    try:
        while True:
            if kbhit():
                c = sys.stdin.read(1)
                exec_action(c)
            time.sleep(0.1)
    except KeyboardInterrupt:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_attr)
        print("\n程序结束.")


if __name__ == '__main__':
    main()
