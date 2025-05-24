# 位来足迹微信小程序网课自动学习系统

一个基于Python的微信小程序网课自动学习工具，支持自动抓包获取凭据、快速完成课程学习等功能。

## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关平台的使用条款。使用本工具产生的任何后果由使用者自行承担。如有侵权请联系或发送issue立马删库。

## ✨ 功能特点

- 🔍 **自动抓包获取凭据** - 无需手动抓包，自动获取认证信息
- 🎯 自动获取课程列表和章节信息
- ⚡ **快速完成模式** - 直接发送完成状态，无需等待播放
- 💾 自动保存和加载凭据
- 🎨 彩色日志输出
- 🛡️ 错误重试机制
- 🔄 支持断点续学
- 📊 实时显示学习进度

## 🚀 快速开始

### 方式一：使用打包好的exe程序（推荐）

1. **下载程序**

	- 下载 Releases中的`reWeiLaiZuJi.zip`
	- 将zip解压到任意文件夹中

2. **运行程序**

   - 直接双击运行文件夹中`reWeiLaiZuJi.exe`

3. **开始使用**

	- 程序启动后会自动创建配置文件
	- 选择"自动抓包获取"方式
	- 按提示操作即可开始学习

### 方式二：Python源码运行

### 环境要求

- Python 3.7+
- Windows 系统 (FiddlerCore需要)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 下载FiddlerCore

1. 下载 `FiddlerCore4.dll` 文件
2. 将DLL文件放置在程序根目录，或配置到 `config.json` 中的 `fiddler.dll_path`

### 运行程序

```bash
python main.py
```

## 📱 使用方法

### 方式一：自动抓包获取凭据（推荐）

1. 启动程序，选择"自动抓包获取"
2. 程序会启动流量监控
3. 在微信小程序中进行任何操作（登录、查看课程等）
4. 程序自动提取认证信息（包括动态Referer）
5. 开始自动学习

### 方式二：手动输入凭据

1. 使用抓包工具获取以下信息：
   - Socket ID
   - School ID  
   - User ID
   - Token
   - Referer（可选）
2. 启动程序，选择"手动输入"
3. 按提示输入信息
4. 开始自动学习

## 📁 项目结构

```
WeiLaiZuJi/
├── main.py                 # 主程序入口
├── config.py              # 配置管理
├── course_api.py          # API接口封装
├── student.py             # 学生类
├── video_player.py        # 视频播放器（快速完成模式）
├── utils.py               # 工具函数
├── logger_config.py       # 日志配置
├── traffic_monitor.py     # 流量监控器
├── credential_manager.py  # 凭据管理器
├── requirements.txt       # 依赖包列表
├── config.json           # 配置文件
├── credentials.json      # 凭据文件（自动生成）
├── FiddlerCore4.dll      # FiddlerCore库文件
└── README.md             # 项目说明
```

## ⚙️ 配置说明

### 基本配置

```json
{
    "video": {
        "completion_time": 3600,     // 设置完成时长(秒)
        "viewing_time": 3600000      // 设置观看时长(毫秒)
    },
    "course": {
        "auto_next": true,           // 自动进入下一节
        "completion_threshold": 0.9   // 完成阈值(90%)
    }
}
```

### 抓包配置

```json
{
    "fiddler": {
        "dll_path": "",                       // FiddlerCore DLL路径（空则自动查找）
        "proxy_port": 8888,                   // 代理端口
        "target_domain": "job3.posedu.com.cn", // 目标域名
        "monitor_timeout": 60                 // 监控超时时间(秒)
    }
}
```

### API配置

```json
{
    "api": {
        "base_url": "https://job3.posedu.com.cn/api",
        "headers": {
            "Host": "job3.posedu.com.cn",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0...",
            "Referer": "https://servicewechat.com/wx7cac98d3af471bb0/238/page-frame.html"
        }
    }
}
```

## 🔧 工作原理

### 快速完成模式

1. **启动播放接口** - 调用 `video_play` API启动视频
2. **直接发送完成状态** - 发送包含足够时长的 `video_play_back` 请求
3. **标记完成** - 服务器接收到请求后直接更新学习状态

## 🔧 故障排除

### 常见问题

1. **FiddlerCore加载失败**
   - 检查DLL文件是否存在于程序目录
   - 确保使用Windows系统
   - 安装 `pip install pythonnet`

2. **抓包失败**
   - 确保微信小程序正在运行
   - 检查系统代理设置
   - 尝试重启程序

3. **认证失败**
   - 重新获取凭据
   - 检查token是否过期

4. **课程完成失败**
   - 检查网络连接
   - 确认API接口正常
   - 查看详细错误日志

5. **电脑不能上网**
   - 检查网络连接
   - 清除或恢复系统代理设置

### 调试模式

设置环境变量启用调试模式：
```bash
set PYTHONPATH=%PYTHONPATH%;.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python main.py
```

## 📝 注意事项

- 首次运行可能需要安装证书，请同意
- 程序会自动设置系统代理，使用完毕后会自动恢复
- 每个小节只需几秒钟即可完成
- 凭据会自动保存，下次使用无需重新获取
- 支持中断后继续学习

## 🔒 安全说明

- 凭据信息保存在本地 `credentials.json` 文件中
- 不会上传任何个人信息
- 仅监控目标域名的流量
- 不会拦截或修改任何请求
- 自动处理证书信任

## 📊 使用统计

- ⚡ 平均每个小节完成时间：2-5秒
- 📚 支持批量处理多门课程
- 🎯 完成率：100%
- 💾 凭据有效期：24小时

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**