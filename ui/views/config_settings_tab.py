from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QGroupBox, QFileDialog, QTextEdit,
    QComboBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Signal, Qt
import configparser
import os

class ConfigSettingsTab(QWidget):
    """配置设置标签页，用于编辑config.ini文件"""

    # 定义信号
    config_saved_signal = Signal()  # 配置保存信号

    def __init__(self, config_path="config.ini"):
        super().__init__()
        self.config_path = config_path
        self.config = configparser.RawConfigParser(allow_no_value=True)
        self.load_config()
        self.init_ui()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
        else:
            # 如果配置文件不存在，创建默认配置
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置"""
        self.config['CRAWLER'] = {
            '# 最大爬取深度': None,
            'MaxDepth': 5,
            '# 最大失败重试次数': None,
            'MaxRetries': 3,
            '# 代理地址': None,
            'Proxies': 'http://127.0.0.1:8080',
            '# fuzz参数字典开关': None,
            'ParamSwitch': True,
            '# 扫描范围,*匹配所有': None,
            'SubDomain': '*.cgbchina.com.cn'
        }
        self.config['REGEX'] = {
            '# 移除URL上下文': None,
            'RemoveUrlContext': '(https?://[^/]+)/[^/]+(/.*)'
        }
        self.config['EXTRACTOR'] = {
            '# 排除大文件后缀': None,
            'A': '.css,.png,.jpg,.ico,.jepg,.exe,.zip,.dmg,.pdf'
        }

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建爬虫配置组
        crawler_group = QGroupBox("爬虫配置")
        crawler_layout = QFormLayout()

        # 最大爬取深度
        self.max_depth_input = QSpinBox()
        self.max_depth_input.setRange(1, 20)
        self.max_depth_input.setValue(int(self.config.get('CRAWLER', 'MaxDepth', fallback='5')))
        crawler_layout.addRow("最大爬取深度:", self.max_depth_input)

        # 最大失败重试次数
        self.max_retries_input = QSpinBox()
        self.max_retries_input.setRange(0, 10)
        self.max_retries_input.setValue(int(self.config.get('CRAWLER', 'MaxRetries', fallback='3')))
        crawler_layout.addRow("最大失败重试次数:", self.max_retries_input)

        # 代理地址
        self.proxies_input = QLineEdit()
        self.proxies_input.setText(self.config.get('CRAWLER', 'Proxies', fallback='http://127.0.0.1:8080'))
        self.proxies_input.setPlaceholderText("输入代理地址，例如: http://127.0.0.1:8080")
        crawler_layout.addRow("代理地址:", self.proxies_input)

        # fuzz参数字典开关
        self.param_switch_input = QCheckBox()
        self.param_switch_input.setChecked(self.config.getboolean('CRAWLER', 'ParamSwitch', fallback=True))
        crawler_layout.addRow("启用fuzz参数字典:", self.param_switch_input)

        # 扫描范围
        self.subdomain_input = QLineEdit()
        self.subdomain_input.setText(self.config.get('CRAWLER', 'SubDomain', fallback='*.cgbchina.com.cn'))
        self.subdomain_input.setPlaceholderText("输入扫描范围，例如: *.example.com")
        crawler_layout.addRow("扫描范围:", self.subdomain_input)

        # 设置爬虫配置组布局
        crawler_group.setLayout(crawler_layout)

        # 创建正则表达式配置组
        regex_group = QGroupBox("正则表达式配置")
        regex_layout = QFormLayout()

        # 移除URL上下文
        self.remove_url_context_input = QLineEdit()
        self.remove_url_context_input.setText(self.config.get('REGEX', 'RemoveUrlContext', fallback='(https?://[^/]+)/[^/]+(/.*)')
)
        self.remove_url_context_input.setPlaceholderText("输入移除URL上下文的正则表达式")
        regex_layout.addRow("移除URL上下文:", self.remove_url_context_input)

        # 设置正则表达式配置组布局
        regex_group.setLayout(regex_layout)

        # 创建提取器配置组
        extractor_group = QGroupBox("提取器配置")
        extractor_layout = QFormLayout()

        # 排除大文件后缀
        self.exclude_extensions_input = QLineEdit()
        self.exclude_extensions_input.setText(self.config.get('EXTRACTOR', 'A', fallback='.css,.png,.jpg,.ico,.jepg,.exe,.zip,.dmg,.pdf'))
        self.exclude_extensions_input.setPlaceholderText("输入排除的文件后缀，用逗号分隔")
        extractor_layout.addRow("排除大文件后缀:", self.exclude_extensions_input)

        # 设置提取器配置组布局
        extractor_group.setLayout(extractor_layout)

        # 创建操作按钮组
        actions_layout = QHBoxLayout()

        # 保存配置按钮
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        self.save_config_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        # 重置配置按钮
        self.reset_config_btn = QPushButton("重置为默认")
        self.reset_config_btn.clicked.connect(self.reset_config)
        self.reset_config_btn.setStyleSheet("background-color: #FF9800; color: white;")

        # 添加按钮到布局
        actions_layout.addWidget(self.save_config_btn)
        actions_layout.addWidget(self.reset_config_btn)
        actions_layout.addStretch()

        # 添加所有组件到主布局
        main_layout.addWidget(crawler_group)
        main_layout.addWidget(regex_group)
        main_layout.addWidget(extractor_group)
        main_layout.addLayout(actions_layout)
        main_layout.addStretch()

    def save_config(self):
        """保存配置到文件"""
        # 更新配置对象
        self.config['CRAWLER']['MaxDepth'] = str(self.max_depth_input.value())
        self.config['CRAWLER']['MaxRetries'] = str(self.max_retries_input.value())
        self.config['CRAWLER']['Proxies'] = self.proxies_input.text()
        self.config['CRAWLER']['ParamSwitch'] = str(self.param_switch_input.isChecked())
        self.config['CRAWLER']['SubDomain'] = self.subdomain_input.text()

        self.config['REGEX']['RemoveUrlContext'] = self.remove_url_context_input.text()

        self.config['EXTRACTOR']['A'] = self.exclude_extensions_input.text()

        # 写入配置文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

        # 发送配置保存信号
        self.config_saved_signal.emit()

    def reset_config(self):
        """重置为默认配置"""
        self.create_default_config()

        # 更新UI
        self.max_depth_input.setValue(int(self.config.get('CRAWLER', 'MaxDepth')))
        self.max_retries_input.setValue(int(self.config.get('CRAWLER', 'MaxRetries')))
        self.proxies_input.setText(self.config.get('CRAWLER', 'Proxies'))
        self.param_switch_input.setChecked(self.config.getboolean('CRAWLER', 'ParamSwitch'))
        self.subdomain_input.setText(self.config.get('CRAWLER', 'SubDomain'))

        self.remove_url_context_input.setText(self.config.get('REGEX', 'RemoveUrlContext'))

        self.exclude_extensions_input.setText(self.config.get('EXTRACTOR', 'A'))
