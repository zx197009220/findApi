from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QGroupBox, QFileDialog, QTextEdit,
    QComboBox, QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Signal, Qt, QTimer
from config import ConfigManager


class ConfigSettingsTab(QWidget):
    """配置设置标签页，用于编辑config.ini文件"""

    # 定义信号
    config_saved_signal = Signal()  # 配置保存信号



    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        
        # 初始化保存定时器
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(1000)  # 1秒延迟
        self.save_timer.timeout.connect(self._delayed_save_template)
        self.init_ui()
        # 初始化时加载message文件内容
        self.reset_template()


    def create_default_config(self):
        """创建默认配置"""
        self.config.create_default_config()
        # 重新读取配置到UI
        self.reset_config()

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
        self.max_depth_input.setValue(self.config.crawler_max_depth)
        crawler_layout.addRow("最大爬取深度:", self.max_depth_input)

        # 最大失败重试次数
        self.max_retries_input = QSpinBox()
        self.max_retries_input.setRange(0, 10)
        self.max_retries_input.setValue(self.config.crawler_max_retries)
        crawler_layout.addRow("最大失败重试次数:", self.max_retries_input)

        # 代理地址
        self.proxies_input = QLineEdit()
        self.proxies_input.setText(self.config.crawler_proxies)
        self.proxies_input.setPlaceholderText("输入代理地址，例如: http://127.0.0.1:8080")
        crawler_layout.addRow("代理地址:", self.proxies_input)

        # fuzz参数字典开关
        self.param_switch_input = QCheckBox()
        self.param_switch_input.setChecked(self.config.crawler_param_switch)
        crawler_layout.addRow("启用fuzz参数字典:", self.param_switch_input)

        # 扫描范围
        self.subdomain_input = QLineEdit()
        self.subdomain_input.setText(self.config.crawler_sub_domain)
        self.subdomain_input.setPlaceholderText("输入扫描范围，例如: *.example.com")
        crawler_layout.addRow("扫描范围:", self.subdomain_input)

        # 设置爬虫配置组布局
        crawler_group.setLayout(crawler_layout)

        # 创建报文模板配置组
        templates_group = QGroupBox("报文模板配置")
        templates_layout = QVBoxLayout()
        
        # 模板编辑区
        self.template_edit = QTextEdit()
        self.template_edit.setPlaceholderText("输入HTTP请求模板")
        self.template_edit.setText(self.config.get('TEMPLATES', 'DefaultTemplate', ''))
        self.template_edit.setMinimumHeight(200)
        self.template_edit.setLineWrapMode(QTextEdit.NoWrap)
        
        # 添加组件到模板布局
        templates_layout.addWidget(QLabel("HTTP请求模板:"))
        templates_layout.addWidget(self.template_edit)
        
        # 设置报文模板配置组布局
        templates_group.setLayout(templates_layout)

        # 创建提取器配置组
        extractor_group = QGroupBox("提取器配置")
        extractor_layout = QFormLayout()

        # 排除大文件后缀
        self.exclude_extensions_input = QLineEdit()
        self.exclude_extensions_input.setText(self.config.extractor_Suffix)
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
        main_layout.addWidget(extractor_group)
        main_layout.addWidget(templates_group)
        main_layout.addLayout(actions_layout)
        main_layout.addStretch()

        # 连接模板编辑区的文本变化信号到定时器
        self.template_edit.textChanged.connect(self._trigger_save)

    def save_config(self):
        """保存配置"""
        # 更新配置对象
        self.config.set('CRAWLER', 'MaxDepth', str(self.max_depth_input.value()))
        self.config.set('CRAWLER', 'MaxRetries', str(self.max_retries_input.value()))
        self.config.set('CRAWLER', 'Proxies', self.proxies_input.text())
        self.config.set('CRAWLER', 'ParamSwitch', str(self.param_switch_input.isChecked()))
        self.config.set('CRAWLER', 'SubDomain', self.subdomain_input.text())
        self.config.set('EXTRACTOR', 'Suffix', self.exclude_extensions_input.text())

        # 发送配置保存信号
        self.config_saved_signal.emit()

    def reset_config(self):
        """重置为默认配置"""
        self.create_default_config()

        # 更新UI
        self.max_depth_input.setValue(int(self.config.crawler_max_depth))
        self.max_retries_input.setValue(int(self.config.crawler_max_retries))
        self.proxies_input.setText(self.config.crawler_proxies)
        self.param_switch_input.setChecked(self.config.crawler_param_switch)
        self.subdomain_input.setText(self.config.crawler_sub_domain)
        self.exclude_extensions_input.setText(self.config.extractor_Suffix)
        try:
            with open('message', 'r', encoding='utf-8') as f:
                self.template_edit.setText(f.read())
        except FileNotFoundError:
            self.template_edit.setText("")



    def reset_template(self):
        """从message文件读取模板内容"""
        try:
            with open('message', 'r', encoding='utf-8') as f:
                self.template_edit.setText(f.read())
        except FileNotFoundError:
            self.template_edit.setText("")
        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"读取模板失败: {str(e)}")

    def _trigger_save(self):
        """触发延迟保存"""
        self.save_timer.start()
        
    def _delayed_save_template(self):
        """延迟保存模板到文件"""
        try:
            with open('message', 'w', encoding='utf-8') as f:
                f.write(self.template_edit.toPlainText())
        except Exception as e:
            print(f"自动保存模板失败: {e}")
