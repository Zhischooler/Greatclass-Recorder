# Greatclass 录播录制工具

屏幕录制 · 白板 · 批注 · 文字输入 · 图片导入 · 导出 MP4  
基于 **PySide6 + ffmpeg**

[English](https://github.com/Zhischooler/Greatclass-Recorder/blob/main/README.md)

---

## 目录结构

```
Greatclass_Recorder/
├── bin/                       # ffmpeg 可执行文件（自行放置）
├── recorder/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                # 主窗口 / 工具栏
│   ├── whiteboard.py          # 白板 / 批注 / 文字 / 图片
│   ├── recorder_engine.py     # ffmpeg 屏幕录制
│   └── packer.py              # 查找 ffmpeg / 导出视频
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`：

```
PySide6>=6.5.0
```

---

## 准备 ffmpeg（必需）

程序按以下顺序查找 ffmpeg：

1. `bin/ffmpeg.exe`（Windows）
2. `bin/ffmpeg`（Linux / macOS）
3. 系统 `PATH` 中的 `ffmpeg`

### Linux（静态构建）

```bash
wget -c https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
mkdir -p bin
mv ffmpeg-*-amd64-static/ffmpeg bin/
chmod +x bin/ffmpeg
```

### macOS

```bash
brew install ffmpeg
mkdir -p bin
cp "$(which ffmpeg)" bin/ffmpeg
```

### Windows（PowerShell）

```powershell
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"
Expand-Archive ffmpeg.zip -DestinationPath .
New-Item -ItemType Directory -Force -Path .\bin | Out-Null
Copy-Item .\ffmpeg-*\bin\ffmpeg.exe .\bin\
Remove-Item -Recurse .\ffmpeg-*
```

验证：

```bash
./bin/ffmpeg -version
# Windows:
.\bin\ffmpeg.exe -version
```

---

## 启动

```bash
python -m recorder
```

---

## 使用流程

1. 工具栏选择工具：**画笔 / 直线 / 矩形 / 箭头 / 文字 / 橡皮擦 / 选择**
2. 「颜色」调画笔颜色，「粗细」SpinBox 调笔宽
3. 「导入图片」支持 `PNG / JPG / JPEG / BMP / GIF / WEBP`  
   导入后切到「选择」模式，可拖动移动、右下角拖动缩放
4. 「文字」工具：在画布空白处点击 → 出现输入框 → 回车确认
5. 点击「开始录制」→ ffmpeg 启动屏幕捕获（含麦克风），  
   白板上的所有绘制、批注、文字、图片都会录进视频
6. 点击「停止录制」→ 视频保存到系统临时目录
7. 点击「导出视频」→ 选择路径 → 输出 MP4

---

## 录制实现细节

| 平台 | 视频源 | 音频源 |
|------|--------|--------|
| Windows | `gdigrab` + `-draw_mouse 1 -i desktop` | `dshow` 自动探测麦克风 |
| Linux   | `x11grab` + `-draw_mouse 1 -i $DISPLAY` | `pulse` 默认设备 |
| macOS   | `avfoundation -capture_cursor 1 -i 1:0` | 同 avfoundation 音轨 |

停止录制时向 ffmpeg 的 stdin 写入 `q`，让 ffmpeg 正常收尾并写入 moov；  
1.5 秒未退出则强制结束进程。

---

## 命令行手动排查

Windows 下查看音频设备名（录制无声时用）：

```powershell
.\bin\ffmpeg.exe -list_devices true -f dshow -i dummy
```

然后手动修改 `recorder_engine.py` 中的 `-i audio=xxx`。

Linux 下查看屏幕 / 音频源：

```bash
./bin/ffmpeg -f x11grab -i $DISPLAY -t 3 test.mp4
./bin/ffmpeg -f pulse -i default -t 3 test.wav
```

macOS 查看可用设备：

```bash
./bin/ffmpeg -f avfoundation -list_devices true -i ""
```

---

## 常见问题

**Q: 录出来只有声音没有画面？**  
A: 检查 ffmpeg 是否支持 `gdigrab`（Windows）或 `x11grab`（Linux）：  
`ffmpeg -devices` 确认列表里存在对应设备。

**Q: 录制无声？**  
A: Windows 下 `dshow` 未找到麦克风时会自动静音录制，用上文命令查看设备名后手动指定。  
macOS 首次运行需在系统设置中授予终端 / 应用麦克风权限。

**Q: 视频体积过大？**  
A: `recorder_engine.py` 中 `-crf` 默认 23，调大到 28 可显著减小体积；  
或降低 `-framerate` 到 15。

**Q: 导出和录制有什么区别？**  
A: 录制 = 抓屏 + 实时 H.264 编码，输出到临时文件；  
导出 = 把临时文件重新走一遍 ffmpeg 编码并保存到你选择的路径。两者共用同一个 ffmpeg。

**Q: 导出未压缩？**  
A: `packer.py` 已实现重编码；若 ffmpeg 缺失会退化为直接复制。

---

## 数据与隐私

- 录制视频仅保存在本机临时目录，程序不主动上传任何内容
- 未生成课程 JSON，仅输出 MP4
- 导入的图片只存在于内存中的白板状态，不写入磁盘

---

## 许可证

GPLv2
