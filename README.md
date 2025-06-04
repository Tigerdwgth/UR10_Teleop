# CR5_Teleop
A teleoperation package to control CR robot with VR controller, from elpis-lab/UR10_Teleop.git

![](demo/demo.gif)

## General Description
Git clone this project by

```
git clone --recursive git@github.com:elpis-lab/UR10_Teleop.git
```

This project contains two parts of the codes. One part is for **Unity**, which reads XR/VR controller input and send it out with network Socket. The other part is a python implementation of **UR RTDE** which receives input from network Socket, convert it to a desired target tool pose, and send it to a UR robot.

## Unity Setup
In this project, the XR controller input is read from **Unity** XR Input. The test version is `Unity 2022.3 LTS` but any LTS version should work. Please visit the [official website](https://unity.com/download) to install Unity Hub first, then install a desired Unity Editor.

After installing the Unity Hub and Unity Editor, launch the Unity Hub and press **Add** to add a project from disk. Select **VR-Teleop** folder. Launch the added project.

### VR/XR controller
Theoretically, the code supports arbitrary VR/XR controller as long as they can be read from **Unity**.

Here we provide a simple setup process for **Oculus Quest**.
- Install and connect your Quest with this [tutorial](https://www.meta.com/help/quest/articles/headsets-and-accessories/oculus-link/connect-with-air-link/?srsltid=AfmBOooLBBdxm9uSImv71uAjxEQmfkK0FDfAsZQam951VS9kSAV7cA-q)
- In **Meta Quest Link** software -> Setting -> General, enable Unknown source and OpenXR Runtime.
- After connecting your Quest with either Airlink or Link, run the Unity VR-Teleop project, you should be able to see the controller being tracked properly.

### Customized controller input processing
The key script related to controller input reading and sending is `VRControllerSender.cs`, which is attached to a game object `XR Origin (XR Rig)` in Unity Scene **Main**. You may customize it as desired.

## Python Setup
Once the VR/XR controller is properly connected with the PC and Unity project is launched, Unity will wait for connection to send out the controller input. From the python side, run

```
python -m teleop.vr_teleop
```

The default settings are

- VR/XR Active button to start/stop controller tracking
- VR/XR Select button to open/close gripper
- The default mapping rate for position is (0.5, 0.5, 0.5)
- The default tracking frequency / rate is 100HZ / 0.01s
- The default smoothing factor is 0.05 (The smaller the smoother)

You may update the script `vr_teleop.py` as desired.
