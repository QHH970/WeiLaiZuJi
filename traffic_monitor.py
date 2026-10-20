import clr
import sys
import os
import json
import time
import threading
from urllib.parse import urlparse, parse_qs
from logger_config import logger
from config import config

# 全局变量用于存储Fiddler相关类
FiddlerApplication = None
CONFIG = None
CertMaker = None

# 导入视频信息管理器
try:
    from video_info_manager import video_info_manager
except ImportError:
    video_info_manager = None
    logger.warning("无法导入视频信息管理器")


class WeChatTrafficMonitor:
    def __init__(self):
        self.target_domain = config.fiddler_config.get('target_domain', 'job3.posedu.com.cn')
        self.proxy_port = config.fiddler_config.get('proxy_port', 8888)
        self.dll_path = config.fiddler_config.get('dll_path', '')
        self.extracted_data = []
        self.is_running = False
        self.credentials_found = False
        self.latest_credentials = {}
        self.video_info = {}  # 存储视频信息
        self.monitor_thread = None
        self.fiddler_loaded = False

        # 检查并加载FiddlerCore
        self._load_fiddler_core()

    def _find_fiddler_dll(self):
        """查找FiddlerCore4.dll文件"""
        # 可能的路径列表
        possible_paths = [
            self.dll_path,  # 配置文件中指定的路径
            os.path.join(config.app_path, 'FiddlerCore4.dll'),  # 程序根目录
            os.path.join(os.path.dirname(__file__), 'FiddlerCore4.dll'),  # 当前文件目录
            'FiddlerCore4.dll',  # 当前工作目录
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                logger.info(f"找到 FiddlerCore4.dll: {path}")
                return path

        return None

    def _load_fiddler_core(self):
        """加载FiddlerCore DLL"""
        global FiddlerApplication, CONFIG, CertMaker

        try:
            # 查找DLL文件
            dll_path = self._find_fiddler_dll()
            if not dll_path:
                logger.warning("未找到 FiddlerCore4.dll 文件")
                logger.info("请将 FiddlerCore4.dll 放置在以下任一位置:")
                logger.info(f"1. 程序根目录: {config.app_path}")
                logger.info(f"2. 配置文件指定路径: {self.dll_path}")
                logger.info("3. 当前工作目录")
                self.fiddler_loaded = False
                return False

            # 更新实际使用的路径
            self.dll_path = dll_path

            clr.AddReference(os.path.abspath(dll_path))   # 按完整路径加载，绕开程序集名解析


            # 导入Fiddler相关类
            import Fiddler
            FiddlerApplication = Fiddler.FiddlerApplication
            CONFIG = Fiddler.CONFIG
            CertMaker = Fiddler.CertMaker

            self.fiddler_loaded = True
            logger.info("FiddlerCore DLL 加载成功")
            return True

        except Exception as e:
            logger.error(f"加载FiddlerCore失败: {e}")
            logger.info("可能的解决方案:")
            logger.info("1. 确保 FiddlerCore4.dll 文件存在")
            logger.info("2. 确保运行在Windows系统上")
            logger.info("3. 确保安装了 pythonnet: pip install pythonnet")
            self.fiddler_loaded = False
            return False

    def setup_fiddler(self):
        """配置FiddlerCore"""
        if not self.fiddler_loaded:
            logger.error("FiddlerCore未正确加载")
            return False

        try:
            # 设置FiddlerCore配置
            CONFIG.IgnoreServerCertErrors = True
            CONFIG.bMITM_HTTPS = True  # 启用HTTPS解密

            # 设置证书
            CertMaker.createRootCert()
            CertMaker.trustRootCert()

            # 配置代理端口
            FiddlerApplication.Startup(self.proxy_port, True, True, True)

            # 注册事件处理器
            FiddlerApplication.BeforeRequest += self.on_before_request
            FiddlerApplication.AfterSessionComplete += self.on_after_session_complete

            logger.info(f"FiddlerCore启动成功，监听端口: {self.proxy_port}")
            logger.info(f"请确保系统代理设置为: 127.0.0.1:{self.proxy_port}")
            return True

        except Exception as e:
            logger.error(f"FiddlerCore启动失败: {e}")
            return False

    def on_before_request(self, session):
        """请求前处理 - 不拦截，只监控"""
        try:
            # 检查是否是目标域名
            if self.target_domain in session.hostname:
                logger.debug(f"检测到目标流量: {session.fullUrl}")
        except Exception as e:
            logger.error(f"处理请求时出错: {e}")

    def on_after_session_complete(self, session):
        """会话完成后处理"""
        try:
            # 只处理目标域名的流量
            if self.target_domain not in session.hostname:
                return

            # 提取请求头信息
            headers = {}
            try:
                for header in session.oRequest.headers:
                    headers[header.Name] = header.Value
            except:
                # 如果无法获取headers，跳过
                return

            # 检查是否是心跳包请求
            if '/api/app/course/video_play_back' in session.fullUrl:
                self._process_heartbeat_request(session, headers)

            # 提取目标字段
            extracted_info = self.extract_target_fields(headers, session)

            if any(extracted_info.values()):
                self.extracted_data.append({
                    'timestamp': time.time(),
                    'url': session.fullUrl,
                    'method': session.RequestMethod,
                    'extracted_fields': extracted_info,
                    'all_headers': headers
                })

                # 更新最新凭据
                self.latest_credentials.update({k: v for k, v in extracted_info.items() if v})

                # 检查是否获取到完整凭据
                required_fields = ['socketId', 'schoolId', 'userId', 'token', 'referer']
                if all(self.latest_credentials.get(key) for key in required_fields):
                    self.credentials_found = True
                    logger.info("✅ 完整凭据已获取!")
                    logger.info(f"Socket ID: {self.latest_credentials['socketId']}")
                    logger.info(f"School ID: {self.latest_credentials['schoolId']}")
                    logger.info(f"User ID: {self.latest_credentials['userId']}")
                    logger.info(f"Token: {self.latest_credentials['token'][:20]}...")
                    logger.info(f"Referer: {self.latest_credentials['referer']}")

                logger.debug(f"提取到数据: {extracted_info}")

        except Exception as e:
            logger.error(f"处理响应时出错: {e}")

    def _process_heartbeat_request(self, session, headers):
        """处理心跳包请求，提取视频信息"""
        try:
            if session.RequestMethod.upper() == 'POST':
                request_body = session.GetRequestBodyAsString()
                if request_body:
                    try:
                        heartbeat_data = json.loads(request_body)

                        # 提取视频信息
                        section_id = heartbeat_data.get('section_id')
                        if section_id:
                            video_info = {
                                'section_id': section_id,
                                'clazz_id': heartbeat_data.get('clazz_id'),
                                'course_id': heartbeat_data.get('course_id'),
                                'course_name': heartbeat_data.get('course_name'),
                                'section_name': heartbeat_data.get('section_name'),
                                'total_time': heartbeat_data.get('total_time'),
                                'close_time': heartbeat_data.get('close_time'),
                                'viewing_time': heartbeat_data.get('viewing_time'),
                                'study_status': heartbeat_data.get('study_status'),
                                'timestamp': time.time()
                            }

                            # 存储到本地
                            self.video_info[section_id] = video_info

                            # 更新到全局管理器
                            if video_info_manager:
                                video_info_manager.update_video_info(section_id, video_info)

                            logger.info(f"📺 检测到视频心跳包 - {heartbeat_data.get('section_name')}")
                            if heartbeat_data.get('total_time'):
                                logger.info(f"   总时长: {heartbeat_data.get('total_time')}秒")
                            if heartbeat_data.get('close_time') is not None:
                                logger.info(f"   当前进度: {heartbeat_data.get('close_time')}秒")

                            # 记录完整的心跳包数据用于调试
                            logger.debug(f"完整心跳包数据: {heartbeat_data}")

                    except json.JSONDecodeError as e:
                        logger.debug(f"心跳包JSON解析失败: {e}")
                        logger.debug(f"原始数据: {request_body}")
        except Exception as e:
            logger.error(f"处理心跳包时出错: {e}")

    def extract_target_fields(self, headers, session):
        """提取目标字段：socketId, schoolId, userId, token, referer"""
        result = {
            'socketId': None,
            'schoolId': None,
            'userId': None,
            'token': None,
            'referer': None
        }

        # 从请求头中提取
        for key, value in headers.items():
            key_lower = key.lower()
            if 'socketid' in key_lower:
                result['socketId'] = value
            elif 'schoolid' in key_lower:
                result['schoolId'] = value
            elif 'userid' in key_lower:
                result['userId'] = value
            elif 'token' in key_lower or 'authorization' in key_lower:
                result['token'] = value
            elif 'referer' in key_lower:
                result['referer'] = value

        # 从URL参数中提取
        try:
            parsed_url = urlparse(session.fullUrl)
            params = parse_qs(parsed_url.query)

            for param_name, param_values in params.items():
                param_lower = param_name.lower()
                if param_values:
                    value = param_values[0]
                    if 'socketid' in param_lower:
                        result['socketId'] = value
                    elif 'schoolid' in param_lower:
                        result['schoolId'] = value
                    elif 'userid' in param_lower:
                        result['userId'] = value
                    elif 'token' in param_lower:
                        result['token'] = value
        except:
            pass

        # 从请求体中提取（如果是POST请求）
        try:
            if session.RequestMethod.upper() == 'POST':
                request_body = session.GetRequestBodyAsString()
                if request_body:
                    # 尝试解析JSON
                    try:
                        json_data = json.loads(request_body)
                        for key, value in json_data.items():
                            key_lower = key.lower()
                            if 'socketid' in key_lower:
                                result['socketId'] = str(value)
                            elif 'schoolid' in key_lower:
                                result['schoolId'] = str(value)
                            elif 'userid' in key_lower:
                                result['userId'] = str(value)
                            elif 'token' in key_lower:
                                result['token'] = str(value)
                    except:
                        # 如果不是JSON，尝试表单数据
                        form_params = parse_qs(request_body)
                        for param_name, param_values in form_params.items():
                            param_lower = param_name.lower()
                            if param_values:
                                value = param_values[0]
                                if 'socketid' in param_lower:
                                    result['socketId'] = value
                                elif 'schoolid' in param_lower:
                                    result['schoolId'] = value
                                elif 'userid' in param_lower:
                                    result['userId'] = value
                                elif 'token' in param_lower:
                                    result['token'] = value
        except:
            pass

        return result

    def start_monitoring(self, timeout=None):
        """开始监控"""
        if not self.fiddler_loaded:
            logger.error("FiddlerCore未正确加载，无法启动监控")
            return False

        if not self.setup_fiddler():
            return False

        self.is_running = True
        self.credentials_found = False

        logger.info(f"🔍 开始监控 {self.target_domain} 的流量...")
        logger.info("📱 请在位来足迹微信小程序中进行操作以获取凭据")
        logger.info("⏹️  按 Ctrl+C 停止监控")

        start_time = time.time()
        timeout = timeout or config.fiddler_config.get('monitor_timeout', 60)

        try:
            while self.is_running:
                # 检查超时
                if timeout and (time.time() - start_time) > timeout:
                    logger.warning(f"监控超时 ({timeout}秒)")
                    break

                # 检查是否获取到完整凭据
                if self.credentials_found:
                    logger.info("✅ 凭据获取完成，停止监控")
                    break

                time.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("用户中断监控")

        self.stop_monitoring()
        return self.credentials_found

    def stop_monitoring(self):
        """停止监控"""
        if self.is_running:
            logger.info("正在停止监控...")
            self.is_running = False

            try:
                if FiddlerApplication:
                    FiddlerApplication.Shutdown()
            except:
                pass

            logger.info("监控已停止")

            # 保存提取的数据
            self.save_extracted_data()

    def save_extracted_data(self):
        """保存提取的数据到文件"""
        if self.extracted_data:
            filename = f"traffic_data_{int(time.time())}.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
                logger.info(f"流量数据已保存到: {filename}")
            except Exception as e:
                logger.error(f"保存流量数据失败: {e}")

        # 保存视频信息
        if self.video_info:
            video_filename = f"video_info_{int(time.time())}.json"
            try:
                with open(video_filename, 'w', encoding='utf-8') as f:
                    json.dump(self.video_info, f, ensure_ascii=False, indent=2)
                logger.info(f"视频信息已保存到: {video_filename}")
            except Exception as e:
                logger.error(f"保存视频信息失败: {e}")

    def get_credentials(self):
        """获取提取的凭据"""
        return self.latest_credentials.copy()

    def get_video_info(self, section_id=None):
        """获取视频信息"""
        if section_id:
            return self.video_info.get(str(section_id))
        return self.video_info.copy()

    def has_complete_credentials(self):
        """检查是否有完整的凭据"""
        required_fields = ['socketId', 'schoolId', 'userId', 'token', 'referer']
        return all(self.latest_credentials.get(field) for field in required_fields)

    def is_available(self):
        """检查FiddlerCore是否可用"""
        return self.fiddler_loaded

    def get_dll_status(self):
        """获取DLL状态信息"""
        return {
            'loaded': self.fiddler_loaded,
            'dll_path': self.dll_path,
            'exists': os.path.exists(self.dll_path) if self.dll_path else False
        }