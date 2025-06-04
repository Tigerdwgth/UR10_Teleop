from dobot_api import DobotApiDashboard, DobotApiFeedBack
import threading
from time import sleep
from pynput import keyboard, mouse

class TeleopDobotServoP:
    def __init__(self, ip='192.168.1.54'):
        self.ip = ip
        self.dashboardPort = 29999
        self.feedPort = 30004
        self.dashboard = DobotApiDashboard(self.ip, self.dashboardPort)
        self.feed = DobotApiFeedBack(self.ip, self.feedPort)
        self.running = True
        self.step_xyz = 2.0     # mm
        self.step_r = 1      # deg
        self.servo_time = 0.005  # ServoP命令时间参数
        self.current_pose = self.get_current_pose()
        self.lock = threading.Lock()
        self.gripper_status = 0

    def enable_robot(self):
        result = self.dashboard.EnableRobot()
        print("使能结果：", result)
        sleep(1)
        
    def get_current_pose(self):
        pose_str = self.dashboard.GetPose()
        try:
            vals = pose_str.split("{")[1].split("}")[0].split(",")
            pose = [float(v) for v in vals]
            return pose  # [x, y, z, rx, ry, rz]
        except Exception as e:
            print("GetPose解析失败", e, pose_str)
            return [0,0,0,0,0,0]

    def send_servo_p(self):
        # 多线程安全
        p = self.current_pose
        msg = self.dashboard.ServoP(p[0], p[1], p[2], p[3], p[4], p[5])
        # msg = self.dashboard.MoveJ([p[0], p[1], p[2], p[3], p[4], p[5]], t=self.servo_time)
        print(f"ServoP({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}, {p[3]:.2f}, {p[4]:.2f}, {p[5]:.2f}, t={self.servo_time}): {msg}")

    def update_pose(self, idx, delta):
        with self.lock:
            self.current_pose[idx] += delta
            self.send_servo_p()

    def set_gripper(self, status):
        msg = self.dashboard.ToolDOInstant(1, status)
        print(f"ToolDOInstant(1, {status}) -> {msg}")
        self.gripper_status = status

    def on_press(self, key):
        try:
            if key.char == 'w':
                self.update_pose(1, -self.step_xyz)    # Y+
            elif key.char == 's':
                self.update_pose(1, self.step_xyz)   # Y-
            elif key.char == 'a':
                self.update_pose(0, self.step_xyz)   # X-
            elif key.char == 'd':
                self.update_pose(0, -self.step_xyz)    # X+
            elif key.char == 'q':
                self.update_pose(3, self.step_r)      # Rx+
            elif key.char == 'e':
                self.update_pose(3, -self.step_r)     # Rx-
            elif key.char == 'z':
                self.update_pose(4, self.step_r)      # Ry+
            elif key.char == 'x':
                self.update_pose(4, -self.step_r)     # Ry-
            elif key.char == 'c':
                self.update_pose(5, self.step_r)      # Rz+
            elif key.char == 'v':
                self.update_pose(5, -self.step_r)     # Rz-
        except AttributeError:
            if key == keyboard.Key.shift:
                self.update_pose(2, -self.step_xyz)    # Z+
            elif key == keyboard.Key.space:
                self.update_pose(2, self.step_xyz)   # Z-
            elif key == keyboard.Key.esc:
                print("退出遥操作")
                self.running = False
                return False

    def on_click(self, x, y, button, pressed):
        if not pressed:
            return
        if button == mouse.Button.left:
            self.set_gripper(1)   # 夹爪闭合
        elif button == mouse.Button.right:
            self.set_gripper(0)   # 夹爪张开

    def pose_update_thread(self):
        """用于定期同步实际末端位置（防止累积漂移）。"""
        while self.running:
            sleep(2)
            with self.lock:
                self.current_pose = self.get_current_pose()

    def run(self):
        print("启用机器人…")
        self.enable_robot()
        print("遥操作ServoP模式开始！按 ESC 退出。")
        self.current_pose = self.get_current_pose()
        # 开一个线程定时刷新实际末端位姿，防止漂移
        threading.Thread(target=self.pose_update_thread, daemon=True).start()
        key_listener = keyboard.Listener(on_press=self.on_press)
        mouse_listener = mouse.Listener(on_click=self.on_click)
        key_listener.start()
        mouse_listener.start()
        while self.running:
            sleep(0.1)
        key_listener.stop()
        mouse_listener.stop()
        print("遥操作已结束。")

if __name__ == '__main__':
    teleop = TeleopDobotServoP()
    teleop.run()
