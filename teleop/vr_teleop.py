import socket
import numpy as np
import re

# from UR10_RTDE.rtde.rtde import RTDE
from teleop.gripper_request import GripperRequest
from teleop.vr_tracker import VRTracker
from PyDobot.dobot_api import *

def parseResultId(valueRecv):
    # 解析返回值，确保机器人在 TCP 控制模式
    if "Not Tcp" in valueRecv:
        print("Control Mode Is Not Tcp")
        return [1]
    return [int(num) for num in re.findall(r'-?\d+', valueRecv)] or [2]
def main():
    # Create a TCP socket to listen to Unity
    unity_ip = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((unity_ip, port))
    print("Connected to Unity server")

        

    # Initialize the teleoperation class
    # rtde = RTDE("192.168.1.102")
    dobot_ip="192.168.1.54"
    dashboard = DobotApiDashboard(dobot_ip,29999)
    print("Connected to Dobot server")
    feedFour = DobotApiFeedBack(dobot_ip,30004)
    
    print("Connected to Dobot feedback server")
    if parseResultId(dashboard.EnableRobot())[0] != 0:
        print("使能失败: 检查29999端口是否被占用")
        raise Exception("使能失败")
    print("使能成功")

    # dashboard.SetToolPower(0)
    print("设置工具电源成功")
    time.sleep(2)
    ret=dashboard.SetTool485(115200,'N',1)
    print(f"设置485返回值: {ret}")
    ret=dashboard.SetToolPower(1)
    print(f"设置工具电源返回值: {ret}")
    
    dashboard.SpeedFactor(10)
    # for i in range(1, 6):
    #     G=Gripper(port=f'COM{i}')
    #     G.set_vel(100)
    #     G.set_pos(1)
        
    
    

    time.sleep(1)  # 等待夹爪动作完成

    
    # Teleop control
    teleop = VRTracker(
        rtde=dashboard,
        gripper=None,
        rate=0.01,  # Control rate in seconds
        smooth_step=0.05,  # Smoothing step size, smaller is smoother
        pos_mapping=(0.5, 0.5, 0.5),  # x, y, z mapping scaling
    )
    
    
    # # print("ModbusRTUCreate 返回 →", ret)
    # err = ret[0]
    # raw = ret[1]  # 形如 "{3}"、"{3,}" 或者在异常情况下 "{,}"
    # mb_idx = 1

    try:
        start=0
        while True:
            data = client_socket.recv(1024).decode("utf-8").strip()
            # print(teleop.rtde.ToolDI(1))
            print(data)
            if not data:
                break
            # Split the data by newline
            data = data.split('\n')
            if not data or not data[0]:
                continue

            # Parse data: x, y, z, qx, qy, qz, qw, button1, button2
            # Use the latest one
            data = data[0].strip().split(',')
            # partial data, reject
            if len(data) < 9:
                print("Partial data received, skipping...")
                continue

            values = list(map(float, data))
            position = values[:3]
            rotation = values[3:7]
            button1 = bool(values[7])
            button2 = bool(values[8])
            if start == 0:
                teleop.resume(position + rotation)
                start = 1
            # Toggle pause/resume with button1
            if button1:
                if teleop.paused:
                    print("Resuming teleoperation...")
                    teleop.resume(position + rotation)
                else:
                    print("Pausing teleoperation...")
                    teleop.pause()
                    continue

            # Trigger the gripper with button2
            if button2:
                if teleop.gripper_open:
                    print("Closing gripper!")
                else:
                    print("Opening gripper!")
                teleop.trigger_gripper()

            # Track
            
            teleop.track(position + rotation)

    except KeyboardInterrupt:
        print("Closing connection...")
    finally:
        dashboard.Stop()
        # rtde.stop_script()
        client_socket.close()

if __name__ == "__main__":
    main()
