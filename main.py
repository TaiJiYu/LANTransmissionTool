import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from designer import Ui_MainWindow


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        myw = QMainWindow()
        window = Ui_MainWindow()
        myWin = window.setupUi(myw)
        myw.show()
        sign = app.exec()
        window.close()
        sys.exit(sign)
    except Exception as e:
        print("__main__ error:", e)

