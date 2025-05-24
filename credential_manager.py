import json
import os
import time
from logger_config import logger
from config import config


class CredentialManager:
    def __init__(self):
        self.credentials_file = config.credentials_config.get('credentials_file', 'credentials.json')
        self.auto_save = config.credentials_config.get('auto_save', True)

        # 确保凭据文件路径是相对于程序根目录的
        if not os.path.isabs(self.credentials_file):
            self.credentials_file = os.path.join(config.app_path, self.credentials_file)

    def save_credentials(self, socket_id, school_id, user_id, token, referer=None):
        """保存凭据到文件"""
        if not self.auto_save:
            return False

        credentials = {
            'socketId': socket_id,
            'schoolId': school_id,
            'userId': user_id,
            'token': token,
            'referer': referer,
            'timestamp': time.time()
        }

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)

            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, ensure_ascii=False, indent=2)
            logger.info(f"凭据已保存到: {self.credentials_file}")
            return True
        except Exception as e:
            logger.error(f"保存凭据失败: {e}")
            return False

    def load_credentials(self):
        """从文件加载凭据"""
        if not os.path.exists(self.credentials_file):
            return None

        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                credentials = json.load(f)

            # 检查凭据是否完整
            required_fields = ['socketId', 'schoolId', 'userId', 'token']
            if all(credentials.get(field) for field in required_fields):
                # 如果没有referer字段，使用默认值
                if not credentials.get('referer'):
                    credentials['referer'] = "https://servicewechat.com/wx7cac98d3af471bb0/238/page-frame.html"
                    logger.warning("凭据文件中没有Referer字段，使用默认值")

                logger.info("从文件加载凭据成功")
                return credentials
            else:
                logger.warning("凭据文件不完整")
                return None

        except Exception as e:
            logger.error(f"加载凭据失败: {e}")
            return None

    def delete_credentials(self):
        """删除凭据文件"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                logger.info("凭据文件已删除")
            return True
        except Exception as e:
            logger.error(f"删除凭据文件失败: {e}")
            return False

    def is_token_valid(self, credentials):
        """简单检查token是否可能有效（基于时间戳）"""
        if not credentials or 'timestamp' not in credentials:
            return False

        # 假设token有效期为24小时
        current_time = time.time()
        credential_time = credentials['timestamp']

        # 24小时 = 86400秒
        return (current_time - credential_time) < 86400