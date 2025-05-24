import json
import os
import sys


def get_application_path():
    """获取应用程序根目录路径"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的程序
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是源代码运行
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


def get_default_fiddler_dll_path():
    """获取默认的FiddlerCore4.dll路径"""
    app_path = get_application_path()
    return os.path.join(app_path, 'FiddlerCore4.dll')


class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.app_path = get_application_path()
        self.load_config()

    def load_config(self):
        config_path = os.path.join(self.app_path, self.config_file)

        # 默认配置
        default_config = {
            "api": {
                "base_url": "https://job3.posedu.com.cn/api",
                "headers": {
                    "Host": "job3.posedu.com.cn",
                    "Connection": "keep-alive",
                    "Context-Type": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254032b) XWEB/13655",
                    "xweb_xhr": "1",
                    "Accept": "*/*",
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty",
                    "Referer": "https://servicewechat.com/wx7cac98d3af471bb0/238/page-frame.html",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9"
                }
            },
            "video": {
                "play_speed": 2.0,
                "heartbeat_interval": 5,
                "min_study_time": 30
            },
            "course": {
                "auto_next": True,
                "completion_threshold": 0.9
            },
            "fiddler": {
                "dll_path": get_default_fiddler_dll_path(),
                "proxy_port": 8888,
                "target_domain": "job3.posedu.com.cn",
                "auto_setup_proxy": True,
                "monitor_timeout": 60
            },
            "credentials": {
                "auto_save": True,
                "credentials_file": "credentials.json"
            }
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)

                # 合并用户配置和默认配置
                self.data = self._merge_config(default_config, user_config)

                # 如果用户没有设置dll_path或路径为空，使用默认路径
                if not self.data.get('fiddler', {}).get('dll_path'):
                    self.data['fiddler']['dll_path'] = get_default_fiddler_dll_path()

            except Exception as e:
                print(f"加载配置文件失败，使用默认配置: {e}")
                self.data = default_config
        else:
            # 配置文件不存在，创建默认配置文件
            self.data = default_config
            self.save_config()

    def _merge_config(self, default, user):
        """递归合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def save_config(self):
        """保存配置到文件"""
        config_path = os.path.join(self.app_path, self.config_file)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    @property
    def api_config(self):
        return self.data.get('api', {})

    @property
    def video_config(self):
        return self.data.get('video', {})

    @property
    def course_config(self):
        return self.data.get('course', {})

    @property
    def fiddler_config(self):
        return self.data.get('fiddler', {})

    @property
    def credentials_config(self):
        return self.data.get('credentials', {})


config = Config()
