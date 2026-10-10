# Greatclass Recorder

Screen recording · Whiteboard · Annotation · Text input · Image import · MP4 export  
Built with **PySide6 + ffmpeg**

[简体中文](docs/README-CN.md)

---

## About

This Project for [GreatClass](https://github.com/pglp006688/GreatClass)'s Record Tools.

[About](https://project.zhixiaoer.dpdns.org/repo/greatclass-recorder.html)

## Directory Structure

```
Greatclass_Recorder/
├── bin/                       # ffmpeg binary (place it yourself)
├── recorder/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                # Main window / toolbar
│   ├── whiteboard.py          # Whiteboard / annotation / text / image
│   ├── recorder_engine.py     # ffmpeg screen recording
│   └── packer.py              # Locate ffmpeg / export video
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`:

```
PySide6>=6.5.0
```

---

## Prepare ffmpeg (Required)

The program looks for ffmpeg in the following order:

1. `bin/ffmpeg.exe` (Windows)
2. `bin/ffmpeg` (Linux / macOS)
3. `ffmpeg` in system `PATH`

### Linux (static build)

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

### Windows (PowerShell)

```powershell
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"
Expand-Archive ffmpeg.zip -DestinationPath .
New-Item -ItemType Directory -Force -Path .\bin | Out-Null
Copy-Item .\ffmpeg-*\bin\ffmpeg.exe .\bin\
Remove-Item -Recurse .\ffmpeg-*
```

Verify:

```bash
./bin/ffmpeg -version
# Windows:
.\bin\ffmpeg.exe -version
```

---

## Run

```bash
python -m recorder
```

---

## Usage

1. Pick a tool from the toolbar: **Pen / Line / Rectangle / Arrow / Text / Eraser / Select**
2. Use **Color** to change pen color; use the **Width** spin box to change pen size
3. **Import Image** supports `PNG / JPG / JPEG / BMP / GIF / WEBP`  
   After importing, switch to **Select** mode to move the image or resize it via the bottom-right handle
4. **Text** tool: click anywhere on the canvas → an input box appears → press Enter to confirm
5. Click **Start Recording** → ffmpeg begins capturing the screen (with microphone);  
   everything drawn on the whiteboard — strokes, annotations, text, images — is recorded into the video
6. Click **Stop Recording** → the video is saved to the system temp directory
7. Click **Export Video** → choose a path → an MP4 is written

---

## Recording Details

| Platform | Video source | Audio source |
|----------|--------------|--------------|
| Windows  | `gdigrab -draw_mouse 1 -i desktop` | `dshow` (auto-detected mic) |
| Linux    | `x11grab -draw_mouse 1 -i $DISPLAY` | `pulse` default device |
| macOS    | `avfoundation -capture_cursor 1 -i 1:0` | same avfoundation audio track |

When you stop recording, the program writes `q` to ffmpeg's stdin so that ffmpeg  
finalizes the file and writes the `moov` atom. If it does not exit within 1.5 s,  
it is terminated forcefully.

---

## Manual Troubleshooting (CLI)

On Windows, list audio devices (useful when recording is silent):

```powershell
.\bin\ffmpeg.exe -list_devices true -f dshow -i dummy
```

Then edit the `-i audio=xxx` argument inside `recorder_engine.py`.

On Linux, list screen / audio sources:

```bash
./bin/ffmpeg -f x11grab -i $DISPLAY -t 3 test.mp4
./bin/ffmpeg -f pulse -i default -t 3 test.wav
```

On macOS, list available devices:

```bash
./bin/ffmpeg -f avfoundation -list_devices true -i ""
```

---

## FAQ

**Q: Only audio is recorded, no video.**  
A: Check whether your ffmpeg supports `gdigrab` (Windows) or `x11grab` (Linux).  
Run `ffmpeg -devices` and confirm the corresponding device is listed.

**Q: Recording has no sound.**  
A: On Windows, `dshow` silently records without audio when no microphone is found —  
use the CLI command above to list devices and specify it manually.  
On macOS, grant microphone permission to the terminal / app on first run.

**Q: The recorded file is too large.**  
A: In `recorder_engine.py`, `-crf` defaults to 23. Raising it to 28 reduces size significantly.  
You can also lower `-framerate` to 15.

**Q: What is the difference between recording and exporting?**  
A: Recording = screen capture + real-time H.264 encoding to a temp file.  
Exporting = re-encoding that temp file with ffmpeg and saving it to a path you choose.  
Both use the same ffmpeg binary.

**Q: Export does not compress?**  
A: `packer.py` performs re-encoding. If ffmpeg is missing, it falls back to a plain file copy.

---

## Data & Privacy

- Recorded videos stay in the local temp directory; nothing is uploaded
- No course JSON is produced — only MP4 output
- Imported images exist only in the in-memory whiteboard state and are never written to disk

---

## License

GPLv2
