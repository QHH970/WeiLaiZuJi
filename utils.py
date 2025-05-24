import time
import random
from logger_config import logger

def safe_request(func, *args, **kwargs):
    """安全的请求包装器，包含重试机制"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(1, 3))
            else:
                raise e

def format_time(seconds):
    """格式化时间显示"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def random_delay(min_delay=1, max_delay=3):
    """随机延迟，模拟人类行为"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def calculate_progress(current, total):
    """计算进度百分比"""
    if total == 0:
        return 0
    return min(100, (current / total) * 100)
