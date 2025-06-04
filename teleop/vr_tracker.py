import time
import numpy as np
from collections import deque

from teleop.gripper import *
from teleop.utils import eular_to_quat, quat_to_eular
from teleop.utils import interpolate_quat, quat_multiply, quat_conjugate
from PyDobot.dobot_api import *

class VRTracker:
    def __init__(
        self,
        rtde=None,
        gripper=None,
        rate=0.008,
        smooth_step=0.1,  # Smoothing step size, smaller is smoother
        pos_mapping=(0.1, 0.1, 0.1),  # x, y, z scaling
    ):
        self.rtde = rtde
        self.gripper = gripper
        self.rate = rate
        self.paused = True
        self.gripper_open = False

        self.input_anchor = None  # [x, y, z, *quat]
        self.tool_anchor = None  # [x, y, z, *quat]
        self.target = None # [x, y, z, *quat]
        self.smooth_step = smooth_step

        self.pos_mapping = np.array(pos_mapping)
        # self.input_anchor=self.rtde.GetPose()
        # self.input_anchor= np.zeros(7)
        # self.tool_anchor = np.zeros(7)
        # self.target = np.zeros(7)
        # tmp=self.extract_pose(self.rtde.GetPose())
        # print("tmp:",tmp)
        # self.target[:3] = tmp[:3]
        # self.target[3:] = rotvec_to_quat(tmp[3:])
        # # self.input_anchor=self.target
        # self.tool_anchor=self.target
        modbus_rtu_over_tcp.connect(( "192.168.1.54", 60000))
        modbus_rtu_over_tcp_status = True
        print("Connected to AG95 server")
        print(AG95_getStatus(None))
        # self.gripper_open= True if AG95_GetPos(1)[0] > 90 else False
    def extract_pose(self,data):
            # 使用正则表达式提取花括号中的内容
                match = re.search(r'\{([-\d.,\s]+)\}', data)
                if match:
                    # 将提取的字符串分割并转换为浮点数列表
                    pose = [float(x) for x in match.group(1).split(',')]
                    return pose
                return None
    def resume(self, input_anchor):
        print("resume at pose",input_anchor)
        # Assume input is [x, y, z, *quat]
        self.input_anchor = np.array(input_anchor)
        # Tool pose is [x, y, z, *quat]
        # tool_anchor = self.rtde.get_tool_pose()
        # GetPose(self, user=-1, tool=-1):
        tool_anchor = self.rtde.GetPose()
       
        # print(tool_anchor)
        # print(extract_pose(tool_anchor))
        tool_anchor = self.extract_pose(tool_anchor)
        # print("tool_anchor:",tool_anchor)
        self.tool_anchor = np.zeros(7)
        self.tool_anchor[:3] = tool_anchor[:3]
        self.tool_anchor[3:] = eular_to_quat(tool_anchor[3:])

        self.target = np.copy(self.tool_anchor)
        self.paused = False

    def pause(self):
        self.paused = True

    def track(self, user_input):
        # Assume input is [x, y, z, *quat]
        if self.paused:
            return
       
        user_input = np.array(user_input)

        # The relative input value is the difference 
        # between the user input and the anchor
       
       
        rel_translation = user_input[:3] - self.input_anchor[:3]
        
        rel_quat = quat_multiply(
            user_input[3:], quat_conjugate(self.input_anchor[3:])
        )
        # print("rel_quat:", rel_quat)
        # Scale the relative translation
        rel_translation = rel_translation * self.pos_mapping
        # print("rel_translation:", rel_translation)
        # The actual required tool pose is the sum of the anchor and the input
        global_translation = self.tool_anchor[:3] + rel_translation
        global_quat = quat_multiply( self.tool_anchor[3:],rel_quat)
        
        # print("rot",self.extract_pose(self.rtde.GetPose())[3:])
        # print("cur pose rot quat",eular_to_quat(self.extract_pose(self.rtde.GetPose())[3:]))
        # print("reverse",quat_to_eular(eular_to_quat(self.extract_pose(self.rtde.GetPose())[3:])))
        
        # Smooth the target by interpolating 
        # between the current target and the new target
        self.target[:3] += (
            self.smooth_step * (global_translation - self.target[:3])
        )
        
        self.target[3:] = interpolate_quat(
            self.target[3:], global_quat, self.smooth_step
        )
    

        # Send the smoothed target [x, y, z, *rotvec] to the robot
        target = np.zeros(6)
        target[:3] = self.target[:3]
        # print("quat2rot",quat_to_rotvec(self.target[3:]))
        # print("global quat2rot",quat_to_rotvec(global_quat))
        target[3:] = quat_to_eular(self.target[3:])
        # print("target",target[3:])
        
        # print("Current pose:", self.extract_pose(self.rtde.GetPose()))
        # print("target",target)
        # dashboard.ServoP(p[0], p[1], p[2], p[3], p[4], p[5])
        print(f"ServoP({target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f}, {target[3]:.2f}, {target[4]:.2f}, {target[5]:.2f})")
        self.rtde.ServoP(*target)
        # self.rtde.servo_tool(target, time=self.rate)

        return target

    def trigger_gripper(self):
        if self.gripper_open:
            AG95_Pos(1,0)  # 关闭夹爪
        else:
            AG95_Pos(1,100)  # 打开夹爪
        self.gripper_open = not self.gripper_open
