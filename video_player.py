import time
from logger_config import logger
from config import config
from utils import format_time


class VideoPlayer:
    def __init__(self, api, course_data, section_data):
        self.api = api
        self.course_data = course_data
        self.section_data = section_data
        self.video_config = config.video_config

        # 视频信息
        self.clazz_id = section_data.get('clazz_id')
        self.course_id = section_data.get('course_id')
        self.section_id = section_data.get('section_id')
        self.course_name = course_data.get('course_name', '未知课程')
        self.section_name = section_data.get('section_name', '未知小节')

        # 使用足够大的时长确保完成
        self.completion_time = self.video_config.get('completion_time', 3600)  # 1小时
        self.viewing_time = self.video_config.get('viewing_time', 3600000)  # 1小时毫秒

    def start_play(self):
        """开始播放视频"""
        try:
            # 验证必要字段
            if not self._validate_section_data():
                return False

            logger.info(f"🎯 开始完成小节: {self.section_name}")

            # 启动视频播放接口
            play_data = self.api.start_video_play(
                self.clazz_id,
                self.course_id,
                self.section_id
            )

            if not play_data:
                logger.error("视频播放接口调用失败")
                return False

            logger.info("✅ 视频播放接口调用成功")

            # 直接发送完成请求
            return self._complete_immediately()

        except Exception as e:
            logger.error(f"播放视频时出错: {e}")
            return False

    def _validate_section_data(self):
        """验证小节数据的完整性"""
        if not self.clazz_id:
            logger.error("缺少 clazz_id")
            return False
        if not self.course_id:
            logger.error("缺少 course_id")
            return False
        if not self.section_id:
            logger.error("缺少 section_id")
            return False
        return True

    def _complete_immediately(self):
        """立即完成视频学习"""
        logger.info("⚡ 发送完成请求...")
        logger.info(f"   设置时长: {format_time(self.completion_time)}")
        logger.info(f"   观看时长: {format_time(self.viewing_time / 1000)}")

        try:
            success = self.api.send_heartbeat(
                clazz_id=self.clazz_id,
                course_id=self.course_id,
                section_id=self.section_id,
                course_name=self.course_name,
                section_name=self.section_name,
                close_time=self.completion_time,  # 足够大的完成时间
                total_time=self.completion_time,  # 总时长
                viewing_time=self.viewing_time,  # 观看时长(毫秒)
                study_status="completed"  # 完成状态
            )

            if success:
                logger.info("🎉 小节完成成功!")
                logger.info(f"📊 提交数据: 进度 {format_time(self.completion_time)}/{format_time(self.completion_time)}")
                return True
            else:
                logger.error("❌ 完成请求发送失败")

                # 如果失败，尝试用learning状态再发一次
                logger.info("🔄 尝试发送学习状态请求...")
                success = self.api.send_heartbeat(
                    clazz_id=self.clazz_id,
                    course_id=self.course_id,
                    section_id=self.section_id,
                    course_name=self.course_name,
                    section_name=self.section_name,
                    close_time=self.completion_time * 0.95,  # 95%进度
                    total_time=self.completion_time,
                    viewing_time=self.viewing_time,
                    study_status="learning"
                )

                if success:
                    logger.info("✅ 学习状态请求成功")
                    return True

                return False

        except Exception as e:
            logger.error(f"发送完成请求时出错: {e}")
            return False

    def stop(self):
        """停止播放"""
        logger.info("视频播放已停止")