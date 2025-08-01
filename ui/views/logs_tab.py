from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog,
    QComboBox, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

class LogsTab(QWidget):
    """日志标签页"""

    # 定义信号
    clear_logs_signal = Signal()  # 清空日志信号
    save_logs_signal = Signal(str)  # 保存日志信号，传递文件路径

    # 日志级别颜色
    LOG_COLORS = {
        "DEBUG": QColor(128, 128, 128),  # 灰色
        "INFO": QColor(0, 0, 0),         # 黑色
        "WARNING": QColor(255, 165, 0),  # 橙色
        "ERROR": QColor(255, 0, 0),      # 红色
        "CRITICAL": QColor(139, 0, 0)    # 深红色
    }

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建过滤器布局
        filter_layout = QHBoxLayout()

        # 日志级别过滤
        level_label = QLabel("日志级别:")
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)

        # 关键词过滤
        keyword_label = QLabel("关键词:")
        self.keyword_input = QComboBox()
        self.keyword_input.setEditable(True)
        self.keyword_input.setInsertPolicy(QComboBox.InsertAtTop)
        self.keyword_input.editTextChanged.connect(self.filter_logs)

        # 自动滚动选项
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)

        # 添加组件到过滤器布局
        filter_layout.addWidget(level_label)
        filter_layout.addWidget(self.level_combo)
        filter_layout.addWidget(keyword_label)
        filter_layout.addWidget(self.keyword_input)
        filter_layout.addStretch()
        filter_layout.addWidget(self.auto_scroll_check)

        # 创建日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, Monaco, "Courier New", monospace;
                font-size: 10pt;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
            }
        """)

        # 创建操作按钮布局
        actions_layout = QHBoxLayout()

        # 清空日志按钮
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.clicked.connect(self.clear_logs)

        # 保存日志按钮
        self.save_btn = QPushButton("保存日志")
        self.save_btn.clicked.connect(self.save_logs)

        # 添加按钮到布局
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.save_btn)

        # 添加所有组件到主布局
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.log_text)
        main_layout.addLayout(actions_layout)

        # 存储原始日志
        self.log_entries = []

    @Slot(str, str, str)
    def add_log(self, level, message, timestamp):
        """添加日志条目"""
        # 存储日志条目
        log_entry = {
            "level": level,
            "message": message,
            "timestamp": timestamp
        }
        self.log_entries.append(log_entry)

        # 如果当前没有过滤或者符合过滤条件，则显示日志
        if self.should_display_log(log_entry):
            self.display_log(log_entry)

        # 添加关键词到下拉框（如果是新的）
        words = message.split()
        for word in words:
            if len(word) > 4 and self.keyword_input.findText(word) == -1:
                self.keyword_input.addItem(word)

    def should_display_log(self, log_entry):
        """检查日志是否应该显示（基于过滤条件）"""
        # 检查日志级别
        level_filter = self.level_combo.currentText()
        if level_filter != "全部" and log_entry["level"] != level_filter:
            return False

        # 检查关键词
        keyword = self.keyword_input.currentText().strip()
        if keyword and keyword not in log_entry["message"]:
            return False

        return True

    def display_log(self, log_entry):
        """显示单条日志"""
        # 创建格式
        format = QTextCharFormat()

        # 设置颜色
        if log_entry["level"] in self.LOG_COLORS:
            format.setForeground(self.LOG_COLORS[log_entry["level"]])

        # 如果是错误或严重级别，设置为粗体
        if log_entry["level"] in ["ERROR", "CRITICAL"]:
            format.setFontWeight(700)  # 粗体

        # 构建日志文本
        log_text = f"[{log_entry['timestamp']}] [{log_entry['level']}] {log_entry['message']}"

        # 获取当前光标
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 插入文本
        cursor.insertText(log_text + "\n", format)

        # 如果启用了自动滚动，滚动到底部
        if self.auto_scroll_check.isChecked():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()

    def filter_logs(self):
        """根据过滤条件重新显示日志"""
        # 清空日志显示
        self.log_text.clear()

        # 重新显示符合条件的日志
        for log_entry in self.log_entries:
            if self.should_display_log(log_entry):
                self.display_log(log_entry)

    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_entries.clear()
        self.clear_logs_signal.emit()

    def save_logs(self):
        """保存日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "", "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            self.save_logs_signal.emit(file_path)
