import time
import json
import threading
from logger_config import logger


class VideoInfoManager:
    """视频信息管理器，用于在traffic_monitor和video_player之间共享数据"""

    def __init__(self):
        self._video_info = {}
        self._lock = threading.Lock()

    def update_video_info(self, section_id, info):
        """更新视频信息"""
        with self._lock:
            section_id = str(section_id)
            if section_id not in self._video_info:
                self._video_info[section_id] = {}

            self._video_info[section_id].update(info)
            self._video_info[section_id]['last_update'] = time.time()

            logger.info(f"📺 更新视频信息 - 小节 {section_id}")
            if 'total_time' in info:
                logger.info(f"   总时长: {info['total_time']}秒")
            if 'close_time' in info:
                logger.info(f"   当前进度: {info['close_time']}秒")

    def get_video_info(self, section_id):
        """获取视频信息"""
        with self._lock:
            return self._video_info.get(str(section_id), {}).copy()

    def wait_for_total_time(self, section_id, timeout=30):
        """等待获取到视频总时长"""
        section_id = str(section_id)
        start_time = time.time()

        logger.info(f"⏳ 等待获取小节 {section_id} 的视频时长...")

        while time.time() - start_time < timeout:
            info = self.get_video_info(section_id)
            if info.get('total_time', 0) > 0:
                logger.info(f"✅ 获取到视频时长: {info['total_time']}秒")
                return info['total_time']

            time.sleep(0.5)

        logger.warning(f"⏰ 等待超时，未能获取到小节 {section_id} 的视频时长")
        return None

    def has_recent_info(self, section_id, max_age=60):
        """检查是否有最近的视频信息"""
        info = self.get_video_info(section_id)
        if not info:
            return False

        last_update = info.get('last_update', 0)
        return time.time() - last_update <= max_age


# 全局实例
video_info_manager = VideoInfoManager()