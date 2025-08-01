from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QGroupBox, QFileDialog, QTextEdit,
    QComboBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Signal, Qt

class ConfigTab(QWidget):
    """配置标签页"""

    # 定义信号
    start_crawler_signal = Signal(dict)  # 启动爬虫信号，传递配置字典
    stop_crawler_signal = Signal()       # 停止爬虫信号

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建基本配置组
        basic_group = QGroupBox("基本配置")
        basic_layout = QFormLayout()

        # 起始URL输入
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入起始URL，例如: https://example.com")
        basic_layout.addRow("起始URL:", self.url_input)

        # URL文件选择
        url_file_layout = QHBoxLayout()
        self.url_file_input = QLineEdit()
        self.url_file_input.setPlaceholderText("选择包含URL列表的文件")
        self.url_file_btn = QPushButton("浏览...")
        self.url_file_btn.clicked.connect(self.select_url_file)
        url_file_layout.addWidget(self.url_file_input)
        url_file_layout.addWidget(self.url_file_btn)
        basic_layout.addRow("URL文件:", url_file_layout)

        # 爬取深度
        self.depth_input = QSpinBox()
        self.depth_input.setRange(1, 10)
        self.depth_input.setValue(3)
        basic_layout.addRow("爬取深度:", self.depth_input)

        # 请求延迟
        self.delay_input = QSpinBox()
        self.delay_input.setRange(0, 10)
        self.delay_input.setValue(1)
        self.delay_input.setSuffix(" 秒")
        basic_layout.addRow("请求延迟:", self.delay_input)

        # 并发数
        self.concurrency_input = QSpinBox()
        self.concurrency_input.setRange(1, 10)
        self.concurrency_input.setValue(3)
        basic_layout.addRow("并发数:", self.concurrency_input)

        # 超时设置
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 60)
        self.timeout_input.setValue(30)
        self.timeout_input.setSuffix(" 秒")
        basic_layout.addRow("请求超时:", self.timeout_input)

        # 设置基本配置组布局
        basic_group.setLayout(basic_layout)

        # 创建高级配置组
        advanced_group = QGroupBox("高级配置")
        advanced_layout = QVBoxLayout()

        # 爬取模式
        mode_layout = QHBoxLayout()
        mode_label = QLabel("爬取模式:")
        self.mode_group = QButtonGroup()
        self.mode_bfs = QRadioButton("广度优先")
        self.mode_dfs = QRadioButton("深度优先")
        self.mode_group.addButton(self.mode_bfs)
        self.mode_group.addButton(self.mode_dfs)
        self.mode_bfs.setChecked(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_bfs)
        mode_layout.addWidget(self.mode_dfs)
        mode_layout.addStretch()
        advanced_layout.addLayout(mode_layout)

        # 请求头设置
        headers_layout = QVBoxLayout()
        headers_label = QLabel("自定义请求头:")
        self.headers_input = QTextEdit()
        self.headers_input.setPlaceholderText("每行一个请求头，格式为 Key: Value\n例如:\nUser-Agent: Mozilla/5.0\nAccept-Language: zh-CN,zh;q=0.9")
        self.headers_input.setMaximumHeight(100)
        headers_layout.addWidget(headers_label)
        headers_layout.addWidget(self.headers_input)
        advanced_layout.addLayout(headers_layout)

        # Cookie设置
        cookies_layout = QVBoxLayout()
        cookies_label = QLabel("Cookie设置:")
        self.cookies_input = QTextEdit()
        self.cookies_input.setPlaceholderText("每行一个Cookie，格式为 Key=Value\n例如:\nsessionid=abc123\ntoken=xyz789")
        self.cookies_input.setMaximumHeight(100)
        cookies_layout.addWidget(cookies_label)
        cookies_layout.addWidget(self.cookies_input)
        advanced_layout.addLayout(cookies_layout)

        # 设置高级配置组布局
        advanced_group.setLayout(advanced_layout)

        # 创建过滤规则组
        filter_group = QGroupBox("过滤规则")
        filter_layout = QVBoxLayout()

        # URL过滤
        url_filter_layout = QVBoxLayout()
        url_filter_label = QLabel("URL过滤规则 (正则表达式):")
        self.url_filter_input = QTextEdit()
        self.url_filter_input.setPlaceholderText("每行一个正则表达式\n包含规则以 + 开头，排除规则以 - 开头\n例如:\n+.*\\.php\\?.*\n-.*\\.(jpg|png|gif)$")
        self.url_filter_input.setMaximumHeight(100)
        url_filter_layout.addWidget(url_filter_label)
        url_filter_layout.addWidget(self.url_filter_input)
        filter_layout.addLayout(url_filter_layout)

        # API过滤
        api_filter_layout = QVBoxLayout()
        api_filter_label = QLabel("API过滤规则 (正则表达式):")
        self.api_filter_input = QTextEdit()
        self.api_filter_input.setPlaceholderText("每行一个正则表达式\n例如:\n/api/.*\n/v1/.*")
        self.api_filter_input.setMaximumHeight(100)
        api_filter_layout.addWidget(api_filter_label)
        api_filter_layout.addWidget(self.api_filter_input)
        filter_layout.addLayout(api_filter_layout)

        # 设置过滤规则组布局
        filter_group.setLayout(filter_layout)

        # 创建操作按钮组
        actions_layout = QHBoxLayout()

        # 保存配置按钮
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)

        # 加载配置按钮
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.clicked.connect(self.load_config)

        # 启动爬虫按钮
        self.start_btn = QPushButton("启动爬虫")
        self.start_btn.clicked.connect(self.start_crawler)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        # 停止爬虫按钮
        self.stop_btn = QPushButton("停止爬虫")
        self.stop_btn.clicked.connect(self.stop_crawler)
        self.stop_btn.setStyleSheet("background-color: #F44336; color: white;")
        self.stop_btn.setEnabled(False)

        # 添加按钮到布局
        actions_layout.addWidget(self.save_config_btn)
        actions_layout.addWidget(self.load_config_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.start_btn)
        actions_layout.addWidget(self.stop_btn)

        # 添加所有组件到主布局
        main_layout.addWidget(basic_group)
        main_layout.addWidget(advanced_group)
        main_layout.addWidget(filter_group)
        main_layout.addLayout(actions_layout)

    def select_url_file(self):
        """选择URL文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择URL文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            self.url_file_input.setText(file_path)

    def save_config(self):
        """保存配置到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            config = self.get_config()
            # 这里应该实现配置保存逻辑
            # 暂时不实现，等待后续开发

    def load_config(self):
        """从文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            # 这里应该实现配置加载逻辑
            # 暂时不实现，等待后续开发
            pass

    def start_crawler(self):
        """启动爬虫"""
        config = self.get_config()
        self.start_crawler_signal.emit(config)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_crawler(self):
        """停止爬虫"""
        self.stop_crawler_signal.emit()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def get_config(self):
        """获取当前配置"""
        # 解析请求头
        headers = {}
        for line in self.headers_input.toPlainText().strip().split('\n'):
            if line and ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        # 解析Cookie
        cookies = {}
        for line in self.cookies_input.toPlainText().strip().split('\n'):
            if line and '=' in line:
                key, value = line.split('=', 1)
                cookies[key.strip()] = value.strip()

        # 解析URL过滤规则
        url_filters = []
        for line in self.url_filter_input.toPlainText().strip().split('\n'):
            if line:
                url_filters.append(line)

        # 解析API过滤规则
        api_filters = []
        for line in self.api_filter_input.toPlainText().strip().split('\n'):
            if line:
                api_filters.append(line)

        # 构建配置字典
        config = {
            'start_url': self.url_input.text(),
            'url_file': self.url_file_input.text(),
            'depth': self.depth_input.value(),
            'delay': self.delay_input.value(),
            'concurrency': self.concurrency_input.value(),
            'timeout': self.timeout_input.value(),
            'mode': 'bfs' if self.mode_bfs.isChecked() else 'dfs',
            'headers': headers,
            'cookies': cookies,
            'url_filters': url_filters,
            'api_filters': api_filters
        }

        return config
