import queue
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor
from config import NUM_BARS, VIZ_FPS, BAR_DECAY, BAR_GAIN


class AudioVisualizer(QWidget):
    """Subtle animated audio bars. Monochrome white, thin, elegant."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_bars = NUM_BARS
        self.bar_values = [0.0] * self.num_bars
        self.audio_queue: queue.Queue | None = None

        self._timer = QTimer()
        self._timer.setInterval(1000 // VIZ_FPS)
        self._timer.timeout.connect(self._update_bars)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_audio_queue(self, q: queue.Queue):
        self.audio_queue = q

    def start(self):
        self.bar_values = [0.0] * self.num_bars
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.bar_values = [0.0] * self.num_bars
        self.update()

    def _update_bars(self):
        if not self.audio_queue:
            return

        chunks = []
        while True:
            try:
                chunks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        if chunks:
            latest = chunks[-1]
            chunk = latest[:, 0] if latest.ndim > 1 else latest
            chunk = chunk.astype(np.float32) / 32768.0
            segments = np.array_split(chunk, self.num_bars)
            for i, seg in enumerate(segments):
                if len(seg) > 0:
                    rms = float(np.sqrt(np.mean(seg ** 2)))
                    target = min(rms * BAR_GAIN, 1.0)
                    if target > self.bar_values[i]:
                        self.bar_values[i] = target
                    else:
                        self.bar_values[i] = max(target, self.bar_values[i] * BAR_DECAY)
        else:
            for i in range(self.num_bars):
                self.bar_values[i] *= BAR_DECAY
                if self.bar_values[i] < 0.01:
                    self.bar_values[i] = 0.0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            painter.end()
            return

        gap = 2
        bar_w = max(2, (w - gap * (self.num_bars - 1)) // self.num_bars)
        total_w = self.num_bars * bar_w + (self.num_bars - 1) * gap
        x_off = (w - total_w) // 2
        min_h = 3

        for i, val in enumerate(self.bar_values):
            bar_h = max(min_h, int(val * h * 0.85))
            x = x_off + i * (bar_w + gap)
            y = (h - bar_h) // 2

            # Subtle white, opacity scales with amplitude
            alpha = int(60 + val * 160)
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 1.5, 1.5)

        painter.end()
