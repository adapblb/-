# type: ignore
# pylint: disable=unknown-word
import pyautogui
import time
from PIL import Image
import cv2
import numpy as np
import os
from enum import Enum
from typing import Tuple, Optional, Dict

class GameState(Enum):
    """游戏状态枚举"""
    ADVENTURE = "adventure"
    CHALLENGE = "challenge"
    UNKNOWN = "unknown"

class ImageMatcher:
    """图像匹配处理类"""
    def __init__(self, confidence: float = 0.8):
        self.confidence = confidence

    def find_on_screen(self, template_path: str) -> Optional[Tuple[int, int]]:
        """
        使用OpenCV在屏幕上查找模板图像，只返回坐标不执行点击
        
        参数：
        - template_path: 模板图片路径
        
        返回：
        - 成功返回坐标元组 (x, y)
        - 失败返回 None
        """
        try:
            if not os.path.exists(template_path):
                print(f"错误：模板文件 {template_path} 不存在")
                return None

            template = cv2.imread(template_path)
            if template is None:
                print(f"错误：无法读取模板图像 {template_path}")
                return None

            screen = np.array(pyautogui.screenshot())
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= self.confidence:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                print(f"找到匹配 {template_path}，位置：({center_x}, {center_y})，匹配度：{max_val:.2f}")
                return (center_x, center_y)

            print(f"未找到匹配 {template_path}，最佳匹配度：{max_val:.2f}")
            return None

        except Exception as e:
            print(f"图像识别过程出错: {str(e)}")
            return None

class MouseController:
    """鼠标控制类"""
    @staticmethod
    def click_at(coordinates: Tuple[int, int], duration: float = 0.5, times: int = 1) -> bool:
        """在指定坐标点击指定次数"""
        try:
            if not coordinates:
                return False

            x, y = coordinates
            print(f"准备在坐标({x}, {y})点击{times}次")

            for i in range(times):
                pyautogui.moveTo(x, y, duration=duration)
                pyautogui.click()
                print(f"完成第{i+1}次点击")
                if i < times - 1:
                    time.sleep(0.8)

            return True

        except Exception as e:
            print(f"点击操作出错: {str(e)}")
            return False

    @staticmethod
    def get_current_position() -> Tuple[int, int]:
        """获取当前鼠标位置"""
        x, y = pyautogui.position()
        print(f"当前鼠标位置：({x}, {y})")
        return (x, y)

class GameAutomation:
    """游戏自动化主类"""
    def __init__(self):
        pyautogui.PAUSE = 1.0
        self.image_matcher = ImageMatcher()
        self.mouse_controller = MouseController()
        self.templates = {
            'adventure': 'adventure.png',
            'adventure_task': 'adventure_task.png',  # 冒险任务标识
            'battle_success': 'battle_success.png',
            'challenge_task': 'challenge_task.png',  # 挑战任务标识
            'battle_lose': 'battle_lose.png',
            'challenge': 'challenge.png',
            'doufa': 'doufa.png',
            'doufa_2': 'doufa_2.png',
            'adventure_ch2': 'adventure_ch2.png',
            'match': 'match.png',  # 如果需要的话
            'match2': 'match2.png',  # 如果需要的话
        }

    def find_and_click(self, template_key: str, times: int = 1, max_attempts: int = 3) -> bool:
        """查找并点击指定模板"""
        for attempt in range(max_attempts):
            coords = self.image_matcher.find_on_screen(self.templates[template_key])
            if coords:
                return self.mouse_controller.click_at(coords, times=times)
            time.sleep(1)
        return False

    def check_battle_status(self, timeout: int = 60) -> bool:
        """检查战斗状态"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            for result in ['battle_success', 'battle_lose']:
                if self.image_matcher.find_on_screen(self.templates[result]):
                    return True
            print(f"战斗进行中... 已等待 {int(time.time() - start_time)} 秒")
            time.sleep(2)
        return False

    def identify_game_state(self) -> GameState:
        """识别当前游戏状态"""
        if self.image_matcher.find_on_screen(self.templates['challenge_task']):
            print("识别到挑战任务")
            return GameState.CHALLENGE
        elif self.image_matcher.find_on_screen(self.templates['adventure_task']):
            print("识别到冒险任务")
            return GameState.ADVENTURE
        print("未识别到任务类型")
        return GameState.UNKNOWN

    def handle_challenge_task(self) -> bool:
        """处理挑战任务"""
        if not self.find_and_click('challenge'):
            return False
        if not self.find_and_click('doufa'):
            return False
        if not self.find_and_click('match'):
            return False
        if not self.find_and_click('doufa_2'):
            return False
        return True

    def handle_adventure_task(self) -> bool:
        """处理冒险任务"""
        if not self.find_and_click('adventure'):
            return False
        if not self.find_and_click('match2'):
            return False
        return True

    def run(self):
        """主运行逻辑"""
        print("程序启动，请在5秒内将鼠标移动到接任务位置...")
        time.sleep(5)
        
        # 获取当前鼠标位置作为接任务位置
        task_coords = self.mouse_controller.get_current_position()
        print(f"已记录接任务位置：{task_coords}")
        
        # 获取adventure按钮位置作为参考点
        adventure_coords = self.image_matcher.find_on_screen(self.templates['adventure'])
        if not adventure_coords:
            print("无法找到adventure按钮，程序退出")
            return

        while True:
            try:
                # 先点击接任务位置
                time.sleep(1)  # 等待任务界面响应
                
                game_state = self.identify_game_state()
                
                if game_state == GameState.CHALLENGE:
                    print("处理挑战任务...")
                    if self.handle_challenge_task() and self.check_battle_status():
                        # 先点击三次
                        self.mouse_controller.click_at(adventure_coords, times=3)
                        time.sleep(1)  # 等待界面响应
                        # 再点击两次task_coordes
                        self.mouse_controller.click_at(task_coords, times=2)

                elif game_state == GameState.ADVENTURE:
                    print("处理冒险任务...")
                    if self.handle_adventure_task() and self.check_battle_status():
                        # 先点击两次
                        self.mouse_controller.click_at(adventure_coords, times=2)
                        time.sleep(1)  # 等待界面响应
                        # 再点击两次task_coordes
                        self.mouse_controller.click_at(task_coords, times=2)

                else:
                    self.mouse_controller.click_at(task_coords, times=2)
                    print("未识别到任务，等待中...")

                time.sleep(5)

            except Exception as e:
                print(f"运行出错: {str(e)}")
                time.sleep(5)

if __name__ == "__main__":
    bot = GameAutomation()
    bot.run()