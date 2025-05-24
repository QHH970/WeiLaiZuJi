#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import signal
import time
from student import Student
from credential_manager import CredentialManager
from logger_config import logger

def signal_handler(sig, frame):
    """处理中断信号"""
    logger.info("\n收到中断信号，正在退出...")
    sys.exit(0)

def get_credentials_from_monitor():
    """通过流量监控获取凭据"""
    try:
        from traffic_monitor import WeChatTrafficMonitor

        logger.info("🔍 启动流量监控模式")
        logger.info("=" * 60)
        logger.info("操作步骤:")
        logger.info("1. 程序将启动流量监控")
        logger.info("2. 请在位来足迹微信小程序中进行任何操作（如登录、查看课程等）")
        logger.info("3. 程序会自动提取所需的认证信息（包括Referer）")
        logger.info("4. 获取完成后会自动停止监控")
        logger.info("=" * 60)

        monitor = WeChatTrafficMonitor()

        # 检查FiddlerCore是否可用
        if not monitor.is_available():
            logger.error("❌ FiddlerCore不可用，请检查配置")
            logger.error("请确保:")
            logger.error("1. FiddlerCore4.dll 路径正确")
            logger.error("2. 运行在Windows系统上")
            logger.error("3. Python环境支持pythonnet")
            return None

        input("按回车键开始监控...")

        success = monitor.start_monitoring(timeout=120)  # 2分钟超时

        if success and monitor.has_complete_credentials():
            credentials = monitor.get_credentials()
            logger.info("✅ 凭据获取成功!")

            # 保存凭据
            credential_manager = CredentialManager()
            credential_manager.save_credentials(
                credentials['socketId'],
                credentials['schoolId'],
                credentials['userId'],
                credentials['token'],
                credentials.get('referer')
            )

            return (
                credentials['socketId'],
                int(credentials['schoolId']),
                int(credentials['userId']),
                credentials['token'],
                credentials.get('referer')
            )
        else:
            logger.error("❌ 未能获取完整的凭据信息")
            return None

    except ImportError as e:
        logger.error(f"导入流量监控模块失败: {e}")
        logger.error("可能的原因:")
        logger.error("1. 缺少pythonnet依赖: pip install pythonnet")
        logger.error("2. FiddlerCore4.dll路径不正确")
        logger.error("3. 系统不支持FiddlerCore")
        return None
    except Exception as e:
        logger.error(f"流量监控过程中出错: {e}")
        return None

def get_user_credentials_manual():
    """手动输入用户凭据"""
    print("🔐 请手动输入登录信息:")
    print("提示: 这些信息可以从抓包工具中获取")
    print("-" * 50)

    try:
        socket_id = input("Socket ID: ").strip()
        school_id = int(input("School ID: ").strip())
        user_id = int(input("User ID: ").strip())
        token = input("Token: ").strip()
        referer = input("Referer (可选，直接回车使用默认值): ").strip()

        if not all([socket_id, school_id, user_id, token]):
            logger.error("Socket ID, School ID, User ID, Token 都是必填的")
            return None

        if not referer:
            referer = "https://servicewechat.com/wx7cac98d3af471bb0/238/page-frame.html"
            logger.info("使用默认Referer")

        # 保存凭据
        credential_manager = CredentialManager()
        credential_manager.save_credentials(socket_id, school_id, user_id, token, referer)

        return socket_id, school_id, user_id, token, referer

    except ValueError:
        logger.error("School ID 和 User ID 必须是数字")
        return None
    except KeyboardInterrupt:
        logger.info("用户取消登录")
        return None

def load_saved_credentials():
    """加载已保存的凭据"""
    credential_manager = CredentialManager()
    credentials = credential_manager.load_credentials()

    if credentials and credential_manager.is_token_valid(credentials):
        logger.info("发现有效的已保存凭据")
        return (
            credentials['socketId'],
            int(credentials['schoolId']),
            int(credentials['userId']),
            credentials['token'],
            credentials.get('referer')
        )
    elif credentials:
        logger.warning("已保存的凭据可能已过期")
        return None
    else:
        return None

def check_fiddler_availability():
    """检查FiddlerCore是否可用"""
    try:
        from traffic_monitor import WeChatTrafficMonitor
        monitor = WeChatTrafficMonitor()
        return monitor.is_available()
    except:
        return False

def get_credentials():
    """获取用户凭据的主函数"""
    # 首先尝试加载已保存的凭据
    credentials = load_saved_credentials()
    if credentials:
        choice = input("发现已保存的凭据，是否使用？(y/n): ").strip().lower()
        if choice in ['y', 'yes', '']:
            return credentials

    print("\n请选择获取凭据的方式:")

    # 检查FiddlerCore是否可用
    fiddler_available = check_fiddler_availability()

    if fiddler_available:
        print("1. 自动抓包获取 (推荐)")
        print("2. 手动输入")
        print("3. 退出")
        options = ["1", "2", "3"]
    else:
        print("1. 手动输入")
        print("2. 退出")
        print("\n注意: 自动抓包功能不可用，请检查FiddlerCore配置")
        options = ["1", "2"]

    while True:
        try:
            choice = input(f"\n请选择 ({'/'.join(options)}): ").strip()

            if fiddler_available:
                if choice == "1":
                    return get_credentials_from_monitor()
                elif choice == "2":
                    return get_user_credentials_manual()
                elif choice == "3":
                    return None
                else:
                    print(f"无效选择，请输入 {' 或 '.join(options)}")
            else:
                if choice == "1":
                    return get_user_credentials_manual()
                elif choice == "2":
                    return None
                else:
                    print(f"无效选择，请输入 {' 或 '.join(options)}")

        except KeyboardInterrupt:
            logger.info("用户取消操作")
            return None

def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 获取用户凭据
        credentials = get_credentials()
        if not credentials:
            logger.info("未获取到凭据，程序退出")
            return

        socket_id, school_id, user_id, token, referer = credentials

        # 创建学生实例
        student = Student(socket_id, school_id, user_id, token, referer)
        student.login_info()

        # 显示主菜单
        while True:
            print("\n" + "=" * 50)
            print("🎓 位来足迹微信小程序网课自动学习系统")
            print("=" * 50)
            print("1. 查看课程列表")
            print("2. 自动学习所有课程")
            print("3. 选择特定课程学习")
            print("4. 重新获取凭据")
            print("5. 删除已保存的凭据")
            print("0. 退出程序")
            print("-" * 50)

            try:
                choice = input("请选择操作 (输入数字): ").strip()

                if choice == "0":
                    logger.info("👋 再见!")
                    break
                elif choice == "1":
                    student.load_courses()
                elif choice == "2":
                    student.auto_learn_all()
                elif choice == "3":
                    student.show_course_menu()
                elif choice == "4":
                    new_credentials = get_credentials()
                    if new_credentials:
                        socket_id, school_id, user_id, token, referer = new_credentials
                        student = Student(socket_id, school_id, user_id, token, referer)
                        student.login_info()
                elif choice == "5":
                    credential_manager = CredentialManager()
                    credential_manager.delete_credentials()
                else:
                    logger.warning("无效的选择，请重新输入")

            except KeyboardInterrupt:
                logger.info("\n用户中断操作")
                break
            except Exception as e:
                logger.error(f"操作失败: {e}")

    except Exception as e:
        logger.error(f"程序运行出错: {e}")

    finally:
        logger.info("程序退出")

if __name__ == "__main__":
    main()