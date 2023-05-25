import sys
import numpy as np
import cv2
import pyautogui
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QDesktopWidget, QPushButton
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.uic.properties import QtGui


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        # Get the screen size
        self.regions = []
        screen = QDesktopWidget().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        self.window_width, self.window_height = screen_width, screen_height
        self.setMinimumSize(self.window_width, self.window_height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.5)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.pix = QPixmap(self.rect().size())
        self.pix.fill(Qt.white)

        self.begin, self.destination = QPoint(), QPoint()
        # Create a minimize button
        self.minimize_button = QPushButton("Minimize")
        layout.addWidget(self.minimize_button)
        self.minimize_button.setStyleSheet("font-size: 180px; color: purple;")
        self.minimize_button.clicked.connect(self.showMinimized)
        # Create a Close button
        self.close_button = QPushButton("Close")
        layout.addWidget(self.close_button)
        self.close_button.setStyleSheet("font-size: 180px; color: brick;")

        # Connect the Close button's clicked signal to the window's close slot
        self.close_button.clicked.connect(self.close)
        # Create a Record button
        self.record_button = QPushButton("Record")
        layout.addWidget(self.record_button)
        self.record_button.setStyleSheet("font-size: 180px; color: red;")

        # Connect the Record button's clicked signal to the toggle_recording slot
        self.record_button.clicked.connect(self.toggle_recording)

        self.is_recording = False
        self.video_writers = []

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.pix)

        for rect in self.regions:
            painter.setPen(QPen(QColor("bleu"), 8))
            painter.drawRect(QRect(*rect))

        if not self.begin.isNull() and not self.destination.isNull():
            rect = QRect(self.begin, self.destination)
            painter.drawRect(rect.normalized())

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.begin = event.pos()
            self.destination = self.begin
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.destination = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() & Qt.LeftButton:
            rect = QRect(self.begin, self.destination).normalized()
            self.regions.append((rect.left(), rect.top(), rect.width(), rect.height()))

        painter = QPainter(self.pix)
        painter.drawRect(rect.normalized())

        self.begin, self.destination = QPoint(), QPoint()
        self.update()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
            self.window().showMinimized()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_button.setText("Stop Recording")

            # Create a video writer for each region
            self.video_writers = []
            for region in self.regions:
                video_writer = cv2.VideoWriter(f"recorded_video_{region}.mp4",
                                               cv2.VideoWriter_fourcc(*"mp4v"),
                                               10,
                                               (region[2], region[3]))
                self.video_writers.append(video_writer)

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.setText("Record")

            # Release video writers
            for video_writer in self.video_writers:
                video_writer.release()

            self.video_writers = []

    def record_frame(self):
        if self.is_recording:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            for region, video_writer in zip(self.regions, self.video_writers):
                cropped_frame = frame[region[1]:region[1] + region[3], region[0]:region[0] + region[2]]
                video_writer.write(cropped_frame)

    def closeEvent(self, event):
        self.stop_recording()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('''QWidget {font-size: 30px;}''')

    myApp = MyApp()
    myApp.show()

    timer = QTimer()
    timer.timeout.connect(myApp.record_frame)
    timer.start(100)

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Closing Window...')
