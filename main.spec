# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

# 收集数据文件
datas = [
    (os.path.join(project_root, 'config.json'), '.'),
]

# 检查是否存在FiddlerCore4.dll并添加到数据文件
fiddler_dll_path = os.path.join(project_root, 'FiddlerCore4.dll')
if os.path.exists(fiddler_dll_path):
    datas.append((fiddler_dll_path, '.'))
    print(f"✅ 找到 FiddlerCore4.dll，将包含在打包中: {fiddler_dll_path}")
else:
    print(f"⚠️  未找到 FiddlerCore4.dll: {fiddler_dll_path}")
    print("   请将 FiddlerCore4.dll 放置在项目根目录中")

# 收集隐藏导入
hiddenimports = [
    'clr',
    'System',
    'System.Collections.Generic',
    'Fiddler',
    'requests',
    'colorama',
    'json',
    'time',
    'threading',
    'urllib.parse',
    'signal',
    'logging',
    'random',
    'os',
    'sys',
]

# 尝试收集pythonnet相关模块
try:
    import pythonnet
    hiddenimports.extend([
        'pythonnet',
        'clr',
    ])
    print("✅ 检测到 pythonnet，将包含相关模块")
except ImportError:
    print("⚠️  未检测到 pythonnet，自动抓包功能可能不可用")

# 排除的模块（可选）
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
]

# 分析主程序
a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WeLaiZuJi_Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
    version_file='version_info.txt',  # 版本信息文件
)

# 如果需要创建目录分发版本，取消注释以下代码
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='WeChatCourseBot'
# )