import math

from PySide6.QtWidgets import QWidget, QLineEdit
from PySide6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QBrush, QFont, QFontMetrics,
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize


class WhiteboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(True)
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._background_color = QColor(255, 255, 255)
        self._strokes = []
        self._current_points = []
        self._texts = []
        self._images = []
        self._pen = QPen(QColor(0, 0, 0), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self._mode = "pen"
        self._start = None
        self._end = None
        self._selected_image_index = -1
        self._drag_offset = QPoint()
        self._resize_handle = -1
        self._text_editor = None

    def pen_color(self):
        return self._pen.color()

    def set_pen_color(self, color):
        self._pen.setColor(color)

    def set_pen_width(self, width):
        self._pen.setWidth(int(width))

    def set_mode(self, mode):
        self._commit_text()
        self._mode = mode
        self._selected_image_index = -1
        self._start = None
        self._end = None
        self.update()

    def clear(self):
        self._commit_text()
        self._strokes.clear()
        self._texts.clear()
        self._images.clear()
        self._current_points = []
        self._start = None
        self._end = None
        self._selected_image_index = -1
        self.update()

    def add_image(self, file_path, pos=None):
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        if pixmap.width() > 800:
            pixmap = pixmap.scaledToWidth(800, Qt.SmoothTransformation)
        if pos is None:
            pos = QPoint(60, 60)
        self._images.append({"pixmap": pixmap, "pos": pos, "size": pixmap.size()})
        self.update()
        return True

    def _draw_polyline(self, painter, points):
        if len(points) < 2:
            return
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

    def _draw_arrow_head(self, painter, start, end):
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        length = 14
        a1 = angle + math.pi / 6
        a2 = angle - math.pi / 6
        p1 = QPoint(int(end.x() - length * math.cos(a1)), int(end.y() - length * math.sin(a1)))
        p2 = QPoint(int(end.x() - length * math.cos(a2)), int(end.y() - length * math.sin(a2)))
        painter.drawLine(end, p1)
        painter.drawLine(end, p2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        for img in self._images:
            painter.drawPixmap(img["pos"], img["pixmap"].scaled(img["size"]))

        painter.setPen(self._pen)
        for stroke in self._strokes:
            kind = stroke[0]
            if kind == "pen":
                self._draw_polyline(painter, stroke[1])
            elif kind == "line":
                painter.drawLine(stroke[1], stroke[2])
            elif kind == "rect":
                painter.drawRect(stroke[1])
            elif kind == "arrow":
                painter.drawLine(stroke[1], stroke[2])
                self._draw_arrow_head(painter, stroke[1], stroke[2])

        for item in self._texts:
            painter.setFont(QFont("Sans", item["size"]))
            painter.setPen(item["color"])
            painter.drawText(item["pos"], item["text"])

        if self._mode == "pen" and self._current_points:
            painter.setPen(self._pen)
            self._draw_polyline(painter, self._current_points)

        if self._start is not None and self._end is not None:
            preview = QPen(QColor(0, 120, 215), self._pen.width(), Qt.DashLine)
            painter.setPen(preview)
            if self._mode == "line":
                painter.drawLine(self._start, self._end)
            elif self._mode == "rect":
                painter.drawRect(QRect(self._start, self._end).normalized())
            elif self._mode == "arrow":
                painter.drawLine(self._start, self._end)
                self._draw_arrow_head(painter, self._start, self._end)

        if 0 <= self._selected_image_index < len(self._images):
            img = self._images[self._selected_image_index]
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.drawRect(QRect(img["pos"], img["size"]))
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            handle_size = 8
            painter.drawRect(QRect(
                img["pos"] + QPoint(img["size"].width() - handle_size,
                                    img["size"].height() - handle_size),
                QSize(handle_size, handle_size)))
            painter.setBrush(Qt.NoBrush)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()

        if self._mode == "text":
            self._start_text_edit(pos)
            return

        if self._mode == "select":
            self._selected_image_index = -1
            for i in range(len(self._images) - 1, -1, -1):
                img = self._images[i]
                rect = QRect(img["pos"], img["size"])
                if rect.contains(pos):
                    self._selected_image_index = i
                    self._drag_offset = pos - img["pos"]
                    handle = QRect(
                        img["pos"] + QPoint(img["size"].width() - 8,
                                            img["size"].height() - 8),
                        QSize(8, 8))
                    self._resize_handle = 1 if handle.contains(pos) else 0
                    break
            self.update()
            return

        if self._mode == "pen":
            self._current_points = [pos]
            self.update()
        elif self._mode == "eraser":
            self._erase_at(pos)
            self.update()
        else:
            self._start = pos
            self._end = pos
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self._mode == "select" and self._selected_image_index >= 0:
            img = self._images[self._selected_image_index]
            if self._resize_handle == 1:
                new_w = max(20, pos.x() - img["pos"].x())
                new_h = max(20, pos.y() - img["pos"].y())
                img["size"] = QSize(new_w, new_h)
            elif self._resize_handle == 0:
                img["pos"] = pos - self._drag_offset
            self.update()
        elif self._mode == "pen" and self._current_points and (event.buttons() & Qt.LeftButton):
            self._current_points.append(pos)
            self.update()
        elif self._mode == "eraser" and (event.buttons() & Qt.LeftButton):
            self._erase_at(pos)
            self.update()
        elif self._start is not None and (event.buttons() & Qt.LeftButton):
            self._end = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()
        if self._mode == "pen" and self._current_points:
            if len(self._current_points) >= 2:
                self._strokes.append(("pen", list(self._current_points)))
            self._current_points = []
            self.update()
        elif self._mode in ("line", "rect", "arrow") and self._start is not None:
            self._end = pos
            if self._start != self._end:
                if self._mode == "line":
                    self._strokes.append(("line", self._start, self._end))
                elif self._mode == "rect":
                    self._strokes.append(("rect", QRect(self._start, self._end).normalized()))
                elif self._mode == "arrow":
                    self._strokes.append(("arrow", self._start, self._end))
            self._start = None
            self._end = None
            self.update()
        elif self._mode == "select":
            self._resize_handle = -1

    def _erase_at(self, pos):
        radius = 20
        new_strokes = []
        for stroke in self._strokes:
            kind = stroke[0]
            if kind == "pen":
                keep = any((p - pos).manhattanLength() > radius for p in stroke[1])
                if keep:
                    new_strokes.append(stroke)
            elif kind in ("line", "arrow"):
                if not QRect(stroke[1], stroke[2]).normalized().adjusted(
                        -radius, -radius, radius, radius).contains(pos):
                    new_strokes.append(stroke)
            elif kind == "rect":
                if not stroke[1].adjusted(-radius, -radius, radius, radius).contains(pos):
                    new_strokes.append(stroke)
        self._strokes = new_strokes
        self._texts = [t for t in self._texts
                       if (t["pos"] - pos).manhattanLength() > radius]

    def _start_text_edit(self, pos):
        if self._text_editor is not None:
            self._commit_text()
        editor = QLineEdit(self)
        pt = max(12, self._pen.width() * 4)
        editor.setFont(QFont("Sans", pt))
        editor.setStyleSheet(
            "QLineEdit {"
            "  background: rgba(255, 255, 255, 210);"
            "  border: 1px dashed #0078d7;"
            f" color: {self._pen.color().name()};"
            "  padding: 2px;"
            "}"
        )
        editor.move(pos)
        editor.setMinimumWidth(180)
        editor.adjustSize()
        editor.returnPressed.connect(self._commit_text)
        editor.editingFinished.connect(self._commit_text)
        editor.show()
        editor.setFocus()
        self._text_editor = editor

    def _commit_text(self):
        editor = self._text_editor
        if editor is None:
            return
        self._text_editor = None
        text = editor.text().strip()
        if text:
            pt = max(12, self._pen.width() * 4)
            font = QFont("Sans", pt)
            fm = QFontMetrics(font)
            self._texts.append({
                "text": text,
                "pos": QPoint(editor.x() + 4, editor.y() + fm.ascent() + 4),
                "color": QColor(self._pen.color()),
                "size": pt,
            })
        editor.deleteLater()
        self.update()