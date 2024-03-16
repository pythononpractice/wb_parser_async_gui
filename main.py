from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from main_win import MainWindow


if __name__ == '__main__':
    app = QApplication([])
    app.setFont(QFont("Arial", 13))
    aw = MainWindow()
    app.exec_()
