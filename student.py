from logger_config import logger
from course_api import CourseAPI
from video_player import VideoPlayer
from config import config
from utils import random_delay

class Student:
    def __init__(self, socket_id, school_id, user_id, token, referer=None):
        self.socket_id = socket_id
        self.school_id = school_id
        self.user_id = user_id
        self.token = token
        self.referer = referer
        self.api = CourseAPI(socket_id, school_id, user_id, token, referer)
        self.courses = []
        self.current_course = None

    def login_info(self):
        """显示登录信息"""
        logger.info("=" * 60)
        logger.info("🎓 位来足迹微信小程序网课自动学习系统")
        logger.info("=" * 60)
        logger.info(f"学校ID: {self.school_id}")
        logger.info(f"用户ID: {self.user_id}")
        logger.info(f"会话ID: {self.socket_id}")
        if self.referer:
            logger.info(f"Referer: {self.referer}")
        logger.info("=" * 60)

    def load_courses(self):
        """加载课程列表"""
        try:
            course_data = self.api.get_course_list()

            # 获取必修课程列表
            teacher_list = course_data.get('teacher_list', [])
            if not teacher_list:
                logger.warning("未找到任何课程")
                return False

            self.courses = teacher_list
            logger.info(f"📚 找到 {len(self.courses)} 门课程:")

            for i, course in enumerate(self.courses, 1):
                course_name = course.get('course_name', '未知课程')
                is_compulsory = course.get('is_compulsory', '')
                percentage = course.get('percentage', 0)
                logger.info(f"  {i}. {course_name} [{is_compulsory}] - 进度: {percentage}%")

            return True

        except Exception as e:
            logger.error(f"加载课程列表失败: {e}")
            return False

    def select_course(self, course_index=None):
        """选择要学习的课程"""
        if not self.courses:
            logger.error("没有可用的课程")
            return False

        if course_index is None:
            # 自动选择第一个未完成的课程
            for course in self.courses:
                if course.get('percentage', 0) < 100:
                    self.current_course = course
                    break

            if not self.current_course:
                logger.info("🎉 所有课程都已完成!")
                return False
        else:
            # 手动选择课程
            if 1 <= course_index <= len(self.courses):
                self.current_course = self.courses[course_index - 1]
            else:
                logger.error("课程索引无效")
                return False

        course_name = self.current_course.get('course_name', '未知课程')
        logger.info(f"📖 选择课程: {course_name}")
        return True

    def start_learning(self):
        """开始学习当前课程"""
        if not self.current_course:
            logger.error("未选择课程")
            return False

        try:
            # 获取课程详细信息
            course_info = self.api.get_course_info(
                self.current_course['course_id'],
                self.current_course['clazz_id']
            )

            course_data = course_info.get('course_data', {})
            chapter_data = course_info.get('course_chapter_data', [])

            logger.info(f"📋 课程: {course_data.get('course_name')}")
            logger.info(f"👨‍🏫 教师: {course_data.get('teacher_name')}")
            logger.info(f"📑 共 {len(chapter_data)} 个章节")

            # 学习所有章节
            for chapter in chapter_data:
                if not self._learn_chapter(chapter, course_data):
                    logger.warning(f"章节学习失败: {chapter.get('chapter_name')}")
                    if not self._ask_continue():
                        break

                random_delay(2, 5)  # 章节间隔

            logger.info("✅ 课程学习完成!")
            return True

        except Exception as e:
            logger.error(f"学习课程时出错: {e}")
            return False

    def _learn_chapter(self, chapter, course_data):
        """学习单个章节"""
        chapter_name = chapter.get('chapter_name', '未知章节')
        sections = chapter.get('course_section_data', [])

        logger.info(f"📖 开始学习章节: {chapter_name}")
        logger.info(f"   包含 {len(sections)} 个小节")

        for section in sections:
            if not self._learn_section(section, course_data):
                logger.warning(f"小节学习失败: {section.get('section_name')}")
                return False

            random_delay(1, 3)  # 小节间隔

        logger.info(f"✅ 章节完成: {chapter_name}")
        return True

    def _learn_section(self, section, course_data):
        """学习单个小节"""
        section_name = section.get('section_name', '未知小节')
        study_status = section.get('study_status', 'noview')

        # 跳过已完成的小节
        if study_status == 'completed':
            logger.info(f"⏭️  跳过已完成小节: {section_name}")
            return True

        logger.info(f"🎯 开始学习小节: {section_name}")

        try:
            # 创建视频播放器并立即完成
            player = VideoPlayer(self.api, course_data, section)
            success = player.start_play()

            if success:
                logger.info(f"✅ 小节完成: {section_name}")
            else:
                logger.error(f"❌ 小节学习失败: {section_name}")

            return success

        except Exception as e:
            logger.error(f"学习小节时出错: {e}")
            return False

    def auto_learn_all(self):
        """自动学习所有课程"""
        logger.info("🚀 开始自动学习所有课程...")

        if not self.load_courses():
            return False

        for i, course in enumerate(self.courses):
            course_name = course.get('course_name', '未知课程')
            percentage = course.get('percentage', 0)

            # 跳过已完成的课程
            if percentage >= 100:
                logger.info(f"⏭️  跳过已完成课程: {course_name}")
                continue

            logger.info(f"📚 开始学习课程 {i + 1}/{len(self.courses)}: {course_name}")

            self.current_course = course
            success = self.start_learning()

            if not success:
                logger.error(f"课程学习失败: {course_name}")
                if not self._ask_continue():
                    break

            random_delay(5, 10)  # 课程间隔

        logger.info("🎉 所有课程学习完成!")

    def _ask_continue(self):
        """询问是否继续"""
        if config.course_config.get('auto_continue', True):
            return True

        try:
            choice = input("是否继续？(y/n): ").strip().lower()
            return choice in ['y', 'yes', '']
        except KeyboardInterrupt:
            return False

    def show_course_menu(self):
        """显示课程菜单"""
        if not self.courses:
            if not self.load_courses():
                return

        print("\n📚 课程列表:")
        print("0. 自动学习所有课程")

        for i, course in enumerate(self.courses, 1):
            course_name = course.get('course_name', '未知课程')
            percentage = course.get('percentage', 0)
            status = "✅" if percentage >= 100 else f"{percentage}%"
            print(f"{i}. {course_name} [{status}]")

        try:
            choice = int(input("\n请选择课程 (输入数字): "))

            if choice == 0:
                self.auto_learn_all()
            elif 1 <= choice <= len(self.courses):
                if self.select_course(choice):
                    self.start_learning()
            else:
                logger.error("无效的选择")

        except ValueError:
            logger.error("请输入有效的数字")
        except KeyboardInterrupt:
            logger.info("用户取消操作")