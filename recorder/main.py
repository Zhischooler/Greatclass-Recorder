import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog, QColorDialog,
    QMessageBox, QLabel, QSpinBox,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from .whiteboard import WhiteboardWidget
from .recorder_engine import RecorderEngine
from .packer import find_ffmpeg, export_video


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Greatclass 录播录制工具")
        self.resize(1280, 800)

        self.whiteboard = WhiteboardWidget()
        self.setCentralWidget(self.whiteboard)

        self.engine = RecorderEngine(self)
        self.engine.finished.connect(self._on_record_finished)
        self.engine.failed.connect(self._on_record_failed)

        self.ffmpeg = find_ffmpeg()
        self.engine.set_ffmpeg(self.ffmpeg)
        self.last_video = None

        self._build_toolbar()
        self._build_statusbar()

        if not self.ffmpeg:
            self.status_label.setText("未检测到 ffmpeg，请将可执行文件放入 bin/ 目录")

    def _build_toolbar(self):
        bar = QToolBar("工具栏")
        bar.setMovable(False)
        self.addToolBar(bar)

        tools = [
            ("画笔", "pen"),
            ("直线", "line"),
            ("矩形", "rect"),
            ("箭头", "arrow"),
            ("文字", "text"),
            ("橡皮擦", "eraser"),
            ("选择", "select"),
        ]
        for name, mode in tools:
            act = QAction(name, self)
            act.triggered.connect(
                lambda checked=False, m=mode: self.whiteboard.set_mode(m)
            )
            bar.addAction(act)

        bar.addSeparator()

        color_act = QAction("颜色", self)
        color_act.triggered.connect(self._choose_color)
        bar.addAction(color_act)

        bar.addWidget(QLabel("  粗细 "))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 50)
        self.width_spin.setValue(3)
        self.width_spin.valueChanged.connect(self.whiteboard.set_pen_width)
        bar.addWidget(self.width_spin)

        bar.addSeparator()

        import_act = QAction("导入图片", self)
        import_act.triggered.connect(self._import_image)
        bar.addAction(import_act)

        clear_act = QAction("清空", self)
        clear_act.triggered.connect(self.whiteboard.clear)
        bar.addAction(clear_act)

        bar.addSeparator()

        self.record_act = QAction("开始录制", self)
        self.record_act.triggered.connect(self._toggle_record)
        bar.addAction(self.record_act)

        export_act = QAction("导出视频", self)
        export_act.triggered.connect(self._export)
        bar.addAction(export_act)

    def _build_statusbar(self):
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

    def _choose_color(self):
        color = QColorDialog.getColor(self.whiteboard.pen_color(), self)
        if color.isValid():
            self.whiteboard.set_pen_color(color)

    def _import_image(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        for p in paths:
            self.whiteboard.add_image(p)

    def _toggle_record(self):
        if self.engine.recording:
            self.engine.stop()
            self.record_act.setText("开始录制")
            self.status_label.setText("正在停止录制...")
        else:
            if self.engine.start():
                self.record_act.setText("停止录制")
                self.status_label.setText(f"录制中: {self.engine.output_path}")

    def _on_record_finished(self, path):
        self.last_video = path
        self.record_act.setText("开始录制")
        self.status_label.setText(f"录制完成: {path}")

    def _on_record_failed(self, msg):
        self.record_act.setText("开始录制")
        self.status_label.setText(f"录制失败: {msg}")
        QMessageBox.critical(self, "录制失败", msg)

    def _export(self):
        if not self.last_video or not os.path.exists(self.last_video):
            QMessageBox.warning(self, "提示", "请先录制视频")
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "导出视频", "录制.mp4", "MP4 视频 (*.mp4)",
        )
        if not output:
            return
        if not output.lower().endswith(".mp4"):
            output += ".mp4"

        try:
            self.status_label.setText("正在导出视频...")
            QApplication.processEvents()
            export_video(self.last_video, output, self.ffmpeg)
            self.status_label.setText(f"视频已导出: {output}")
            QMessageBox.information(self, "成功", f"视频已导出到:\n{output}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
            self.status_label.setText("导出失败")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()