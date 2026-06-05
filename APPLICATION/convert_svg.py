import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import QSize

app = QApplication(sys.argv)
renderer = QSvgRenderer('logo.svg')
image = QImage(256, 256, QImage.Format_ARGB32)
image.fill(QColor(0, 0, 0, 0)) # transparent background
painter = QPainter(image)
renderer.render(painter)
painter.end()
image.save('logo.png')
