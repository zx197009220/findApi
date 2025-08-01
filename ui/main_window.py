from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from ui.views import CrawlerTab, ConfigSettingsTab
from ui.views.rules_tab import RulesTab

# 调试时使用模拟爬虫控制器
# from core.mock_crawler_controller import MockCrawlerController as CrawlerController
# 正式使用时切换回真实爬虫控制器
from core.crawler_controller import CrawlerController

class MainWindow(QMainWindow):
    """应用程序主窗口，包含标签页切换机制，爬虫标签页和配置设置标签页"""

    def __init__(self):
        super().__init__()
        # 创建爬虫控制器
        self.crawler_controller = CrawlerController()
        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化UI组件"""
        # 设置窗口属性
        self.setWindowTitle("FindAPI - API接口爬虫工具")
        self.setGeometry(100, 100, 1200, 700)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建标签页控件
        self.tab_widget = QTabWidget()

        # 创建爬虫标签页
        self.crawler_tab = CrawlerTab(self.crawler_controller)
        self.crawler_tab.status_changed_signal.connect(self.update_status_bar)
        self.tab_widget.addTab(self.crawler_tab, "爬虫")

        # 创建配置设置标签页
        self.config_settings_tab = ConfigSettingsTab()
        self.tab_widget.addTab(self.config_settings_tab, "配置设置")

        # 创建规则标签页
        self.rules_tab = RulesTab()
        self.rules_tab.status_changed_signal.connect(self.update_status_bar)
        self.tab_widget.addTab(self.rules_tab, "规则")

        # 将标签页控件添加到主布局
        main_layout.addWidget(self.tab_widget)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QTableWidget {
                border: 1px solid #cccccc;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            
            QTableWidget::item:selected {
                background-color: #4a86e8;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
            
            QStatusBar {
                background-color: #f0f0f0;
                color: #333333;
            }
            
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #3a76d8;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)

    def update_status_bar(self, status):
        """更新状态栏"""
        self.status_bar.showMessage(status)
