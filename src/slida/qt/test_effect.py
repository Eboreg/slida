from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsEffect


class TestEffect(QGraphicsEffect):
    def draw(self, painter: QPainter):
        print("TestEffect.draw()")
        pixmap = self.sourcePixmap()
        painter.drawPixmap(0, 0, pixmap)

    def setUmpo(self, value: float):
        print(f"TestEffect.setUmpo({value})")
        self.update()
