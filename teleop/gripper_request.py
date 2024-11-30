import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor


class GripperRequest:

    def __init__(self, host):
        self.host = host
        self.gripper_api_url = "http://" + host + ":8005"

    async def control_gripper(self, action):
        """Control the gripper through its API"""
        try:
            with ThreadPoolExecutor() as executor:
                response = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda: requests.post(f"{self.gripper_api_url}/{action}"),
                )
            return response.json()
        except Exception as e:
            print(f"Error controlling gripper: {e}")
            return None

    async def open_gripper(self):
        res = await self.control_gripper("open")
        return res

    async def close_gripper(self):
        res = await self.control_gripper("close")
        return res


if __name__ == "__main__":
    import time

    gripper = GripperRequest("130.215.216.42")
    res = asyncio.run(gripper.open_gripper())
    print(f"Open gripper response: {res}")
    time.sleep(3.0)
    res = asyncio.run(gripper.close_gripper())
    print(f"Close gripper response: {res}")
    time.sleep(3.0)
    res = asyncio.run(gripper.open_gripper())
    print(f"Open gripper response: {res}")
