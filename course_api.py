import requests
import json
from logger_config import logger
from config import config
from utils import safe_request, random_delay


class CourseAPI:
    def __init__(self, socket_id, school_id, user_id, token, referer=None):
        self.socket_id = socket_id
        self.school_id = school_id
        self.user_id = user_id
        self.token = token
        self.referer = referer or config.api_config['headers'].get('Referer',
                                                                   "https://servicewechat.com/wx7cac98d3af471bb0/238/page-frame.html")
        self.base_url = config.api_config['base_url']
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        """设置请求头"""
        headers = config.api_config['headers'].copy()
        headers.update({
            'socketId': self.socket_id,
            'schoolId': str(self.school_id),
            'userId': str(self.user_id),
            'token': self.token,
            'Referer': self.referer  # 使用动态的Referer
        })
        self.session.headers.update(headers)

    def _make_request(self, endpoint, data=None, method='POST'):
        """发起API请求"""
        url = f"{self.base_url}{endpoint}"

        def request_func():
            if method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                response = self.session.get(url, params=data)

            response.raise_for_status()
            return response.json()

        return safe_request(request_func)

    def get_course_list(self, category_id=""):
        """获取课程列表"""
        logger.info("正在获取课程列表...")
        data = {"category_id": category_id}
        response = self._make_request("/v4/course/index_pay", data)
        return response.get('data', {})

    def get_course_info(self, course_id, clazz_id):
        """获取课程详细信息"""
        logger.info(f"正在获取课程信息 - 课程ID: {course_id}")
        data = {"course_id": str(course_id), "clazz_id": str(clazz_id)}
        response = self._make_request("/app/course/course_info", data)
        return response.get('data', {})

    def start_video_play(self, clazz_id, course_id, session_id, hide=1, type_="2"):
        """开始播放视频"""
        logger.info(f"开始播放视频 - 节ID: {session_id}")
        data = {
            "clazz_id": str(clazz_id),
            "course_id": str(course_id),
            "session_id": str(session_id),
            "hide": hide,
            "type": type_
        }
        response = self._make_request("/app/course/video_play", data)
        return response.get('data', {})

    def send_heartbeat(self, clazz_id, course_id, section_id, course_name,
                       section_name, close_time, total_time, viewing_time, study_status):
        """发送学习心跳包"""
        data = {
            "clazz_id": str(clazz_id),
            "course_id": course_id,
            "section_id": section_id,
            "course_name": course_name,
            "section_name": section_name,
            "close_time": close_time,
            "total_time": total_time,
            "viewing_time": viewing_time,
            "study_status": study_status
        }

        try:
            response = self._make_request("/app/course/video_play_back", data)
            success = response.get('code') == 1

            if success:
                logger.debug(f"心跳包发送成功: 进度 {close_time:.1f}/{total_time:.1f}, 状态: {study_status}")
            else:
                logger.warning(f"心跳包发送失败: {response.get('msg', '未知错误')}")

            return success
        except Exception as e:
            logger.error(f"发送心跳包失败: {e}")
            return False

    def get_section_detail(self, clazz_id, course_id, section_id):
        """获取小节详细信息（备用方法）"""
        logger.debug(f"获取小节详细信息 - 小节ID: {section_id}")
        data = {
            "clazz_id": str(clazz_id),
            "course_id": str(course_id),
            "section_id": str(section_id)
        }

        try:
            response = self._make_request("/app/course/section_detail", data)
            return response.get('data', {})
        except Exception as e:
            logger.debug(f"获取小节详细信息失败: {e}")
            return {}

    def batch_complete_sections(self, sections_data):
        """批量完成多个小节（如果API支持）"""
        logger.info(f"尝试批量完成 {len(sections_data)} 个小节...")

        for i, section in enumerate(sections_data, 1):
            try:
                success = self.send_heartbeat(
                    clazz_id=section['clazz_id'],
                    course_id=section['course_id'],
                    section_id=section['section_id'],
                    course_name=section['course_name'],
                    section_name=section['section_name'],
                    close_time=section.get('total_time', 3600),  # 使用总时长作为完成进度
                    total_time=section.get('total_time', 3600),
                    viewing_time=section.get('total_time', 3600) * 1000,  # 毫秒
                    study_status="completed"
                )

                if success:
                    logger.info(f"✅ 小节 {i}/{len(sections_data)} 完成: {section['section_name']}")
                else:
                    logger.warning(f"❌ 小节 {i}/{len(sections_data)} 失败: {section['section_name']}")

                # 短暂延迟避免请求过快
                random_delay(0.5, 1.5)

            except Exception as e:
                logger.error(f"批量完成小节时出错: {e}")
                continue

    def quick_complete_section(self, clazz_id, course_id, section_id, course_name, section_name, target_duration=3600):
        """快速完成单个小节"""
        logger.info(f"🚀 快速完成小节: {section_name}")

        # 分阶段发送心跳包，模拟真实观看
        stages = [0.3, 0.6, 0.9, 1.0]  # 30%, 60%, 90%, 100%

        for i, stage in enumerate(stages):
            current_time = target_duration * stage
            viewing_time = target_duration * stage * 1000  # 毫秒

            status = "completed" if stage >= 1.0 else "learning"

            try:
                success = self.send_heartbeat(
                    clazz_id=clazz_id,
                    course_id=course_id,
                    section_id=section_id,
                    course_name=course_name,
                    section_name=section_name,
                    close_time=current_time,
                    total_time=target_duration,
                    viewing_time=viewing_time,
                    study_status=status
                )

                if success:
                    logger.info(f"📡 阶段 {i + 1}/4 完成 ({stage * 100:.0f}%)")
                else:
                    logger.warning(f"⚠️ 阶段 {i + 1}/4 失败")

                # 短暂延迟
                if i < len(stages) - 1:
                    random_delay(1, 2)

            except Exception as e:
                logger.error(f"快速完成小节时出错: {e}")
                return False

        logger.info(f"✅ 小节完成: {section_name}")
        return True

    def verify_completion(self, course_id, clazz_id):
        """验证课程完成状态"""
        try:
            course_info = self.get_course_info(course_id, clazz_id)

            if course_info:
                chapters = course_info.get('course_chapter_data', [])
                total_sections = 0
                completed_sections = 0

                for chapter in chapters:
                    sections = chapter.get('course_section_data', [])
                    total_sections += len(sections)

                    for section in sections:
                        if section.get('study_status') == 'completed':
                            completed_sections += 1

                completion_rate = (completed_sections / total_sections * 100) if total_sections > 0 else 0

                logger.info(f"📊 课程完成度: {completed_sections}/{total_sections} ({completion_rate:.1f}%)")
                return completion_rate >= 90  # 90%以上认为完成

        except Exception as e:
            logger.error(f"验证完成状态时出错: {e}")

        return False

    def get_user_progress(self):
        """获取用户整体学习进度"""
        try:
            course_data = self.get_course_list()
            teacher_list = course_data.get('teacher_list', [])

            total_courses = len(teacher_list)
            completed_courses = 0

            logger.info("📈 用户学习进度:")

            for course in teacher_list:
                course_name = course.get('course_name', '未知课程')
                percentage = course.get('percentage', 0)

                if percentage >= 90:
                    completed_courses += 1
                    status = "✅"
                else:
                    status = "🔄"

                logger.info(f"  {status} {course_name}: {percentage}%")

            overall_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
            logger.info(f"📊 总体完成度: {completed_courses}/{total_courses} ({overall_rate:.1f}%)")

            return {
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'completion_rate': overall_rate,
                'courses': teacher_list
            }

        except Exception as e:
            logger.error(f"获取学习进度时出错: {e}")
            return None