import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow

def main():
    """UI测试入口点"""
    app = QApplication(sys.argv)

    # 创建主窗口
    main_window = MainWindow()

    # 显示主窗口
    main_window.show()

    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
