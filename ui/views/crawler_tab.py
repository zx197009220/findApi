from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMenu, QCheckBox, QRadioButton, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QDateTime, QEvent, QTimer
from PySide6.QtGui import QGuiApplication, QAction, QTextBlockFormat, QTextCursor, QFontMetrics
from datetime import datetime  # 导入datetime模块
from config import ConfigManager

class CrawlerTab(QWidget):
    """爬虫标签页，包含爬虫控制界面、结果显示表格和链接树状预览"""

    # 定义信号
    start_crawler_signal = Signal(dict)  # 开始爬取信号，传递配置字典
    stop_crawler_signal = Signal()  # 停止爬取信号
    status_changed_signal = Signal(str)  # 状态变化信号，用于更新主窗口状态栏

    def __init__(self, crawler_controller):
        super().__init__()
        self.config = ConfigManager()
        self.crawler_controller = crawler_controller
        # 初始化深度序号计数器
        self.depth_counters = {"1": 0}
        self.current_parent = "1"
        self.init_ui()

    def connect_crawler_signals(self):
        """连接爬虫控制器的信号"""
        # 状态变化信号
        self.crawler_controller.status_changed_signal.connect(self.update_status)
        # 日志信号 (级别, 消息, 时间戳)
        self.crawler_controller.log_signal.connect(self.add_log)
        # 数据接收信号 - 直接处理爬虫数据
        self.crawler_controller.data_received_signal.connect(self.process_crawler_data)

        # 连接UI信号到控制器
        self.start_button.clicked.connect(self.start_crawler)
        self.stop_button.clicked.connect(self.stop_crawler)

        # 不再使用定时器轮询队列，改为通过信号触发
        # 但仍然保留queue_timer相关代码以便在需要时可以恢复
        """
        from PySide6.QtCore import QTimer
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_result_queue)
        self.queue_timer.start(100)  # 每100毫秒检查一次队列
        """

    def create_link_tree_context_menu(self, position):
        """创建链接树的上下文菜单"""
        menu = QMenu()
        
        # 添加复制URL菜单项
        copy_action = QAction("复制URL", self)
        copy_action.triggered.connect(self.copy_tree_item_url)
        menu.addAction(copy_action)
        
        # 显示菜单
        menu.exec_(self.link_tree.viewport().mapToGlobal(position))
        
    def copy_tree_item_url(self):
        """复制选中树节点的URL"""
        selected_items = self.link_tree.selectedItems()
        if selected_items:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(selected_items[0].text(0))
            self.status_changed_signal.emit(f"已复制URL: {selected_items[0].text(0)}")

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)  # 显式设置布局到窗口
        


        # 创建顶部控制区域
        top_control_widget = QWidget()
        top_layout = QHBoxLayout(top_control_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 创建URL输入标签
        url_label = QLabel("URL输入:")

        self._expand_timer = QTimer()
        self._expand_timer.setSingleShot(True)
        self._expand_timer.timeout.connect(self._do_expand)
        
        # 创建URL输入框
        self.url_input = QTextEdit()  # 使用QTextEdit支持多行输入
        self.url_input.setAcceptRichText(False)  # 禁止富文本输入
        self.url_input.setLineWrapMode(QTextEdit.NoWrap)  # 不自动换行
        self.url_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.url_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.url_input.cursorPositionChanged.connect(
            lambda: self.url_input.ensureCursorVisible()
        )
        self.url_input.setPlaceholderText("请输入URL，每行一个 (例如:https://example.com\nhttps://example.org)")
        self.url_input.setMinimumWidth(400)
        self.url_input.setMaximumHeight(35)  # 默认显示单行高度


        # 设置样式表以增加行间距
        self.url_input.setStyleSheet("""
            QTextEdit {
                font-size: 10pt;
                padding: 4px;
            }
        """)
        
        # 安装事件过滤器以处理鼠标悬停事件
        self.url_input.installEventFilter(self)

        # 单选按钮已替换为开关，不需要连接信号

        # 创建代理启用复选框
        self.proxy_checkbox = QCheckBox("启用代理")
        self.proxy_checkbox.setChecked(False)  # 默认启用代理

        # 创建启动和停止按钮
        self.start_button = QPushButton("开始爬取")
        self.start_button.setMinimumWidth(100)
        self.stop_button = QPushButton("停止爬取")
        self.stop_button.setMinimumWidth(100)
        self.stop_button.setEnabled(False)

        # 将控件添加到顶部布局
        top_layout.addWidget(url_label)
        top_layout.addWidget(self.url_input, 1)
        top_layout.addWidget(self.proxy_checkbox)
        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.stop_button)

        # 添加顶部控制区域到主布局
        self.main_layout.addWidget(top_control_widget)

        # 创建分割器
        self.splitter = QSplitter(Qt.Vertical)

        # 创建爬取结果表格
        results_widget = QWidget()

        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)

        results_label = QLabel("爬取结果:")
        results_layout.addWidget(results_label)


        self.results_table = QTableWidget()

        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["时间", "深度序号", "响应状态", "链接来源","规则","URL"])
        self.results_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # URL列自动拉伸
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)

        results_layout.addWidget(self.results_table)

        # 连接双击信号（必须在表格创建后）
        self.results_table.doubleClicked.connect(self.copy_selected_url)

        # 将爬取结果区域添加到分割器
        self.splitter.addWidget(results_widget)

        # 创建树状预览区域
        preview_group = QGroupBox("链接树状预览")

        preview_layout = QVBoxLayout()

        self.link_tree = QTreeWidget()

        self.link_tree.setHeaderLabel("链接层级")
        self.link_tree.setColumnCount(1)
        
        # 设置树状视图的上下文菜单策略
        self.link_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.link_tree.customContextMenuRequested.connect(self.create_link_tree_context_menu)

        preview_layout.addWidget(self.link_tree)
        preview_group.setLayout(preview_layout)

        # 将树状预览区域添加到分割器
        self.splitter.addWidget(preview_group)

        # 设置分割器的初始大小
        self.splitter.setSizes([600, 400])

        # 将分割器添加到主布局
        self.main_layout.addWidget(self.splitter, 1)

        # 连接信号和槽
        self.results_table.itemClicked.connect(self.show_item_details)
        
        # 连接爬虫控制信号
        self.connect_crawler_signals()



    def start_crawler(self):
        """开始爬取"""
        url_text = self.url_input.toPlainText().strip()
        if not url_text:
            self.update_status("请输入有效的URL")
            return
        
        # 批量模式：将文本分割成URL列表
        url = [line.strip() for line in url_text.split('\n') if line.strip()]
        if not url:
            self.update_status("请输入有效的URL")
            return

        # 禁用启动按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 更新状态
        self.update_status(f"正在爬取: {url}")

        # 清空结果显示区域
        self.clear_results()

        # 获取配置选项
        self.config.set('CRAWLER', 'ProxySwitch', self.proxy_checkbox.isChecked())

        # 调用爬虫控制器的启动方法
        self.crawler_controller.start_crawler(url)

    def stop_crawler(self):
        """停止爬取"""
        try:
            # 调用爬虫控制器的停止方法
            self.crawler_controller.stop_crawler()
        except Exception as e:
            # 记录错误并更新状态
            self.update_status(f"停止爬虫时出错: {str(e)}")
            # 确保按钮状态正确
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)


    def update_status(self, status):
        """更新爬虫状态"""
        # 发送状态更新信号给主窗口
        self.status_changed_signal.emit(status)

        # 根据状态更新按钮状态
        if status.startswith("已停止") or status.startswith("完成") or status == "爬虫已停止":
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        elif status.startswith("正在爬取") or status == "爬虫已启动":
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)


    def add_log(self, level, message, timestamp):
        """添加日志消息"""
        # 可以考虑在状态栏显示最新的日志消息
        if level == "ERROR":
            self.status_changed_signal.emit(f"错误: {message}")

    def add_link_result(self, timestamp,url, status_code, type, depth=None, regex_names=None):
        """添加链接结果到表格"""

        # 创建表格行
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)

        # 设置表格项
        self.results_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(str(depth)))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(str(status_code)))
        self.results_table.setItem(row_position, 3, QTableWidgetItem(type))
        self.results_table.setItem(row_position, 4, QTableWidgetItem(" 、".join(regex_names)))
        self.results_table.setItem(row_position, 5, QTableWidgetItem(url))

        # 存储额外数据（用于详细信息显示）
        self.results_table.item(row_position, 5).setData(Qt.UserRole, {
            "url": url,
            "status_code": status_code,
            "depth": depth,
            "type": type,
            "time": timestamp,
            "title": "title",
            "content": "",  # 内容预览可以在点击时获取
            "is_api": False,
            "regex_names": regex_names
        })

    def show_item_details(self, item):
        """处理选中项事件，构建树状预览"""
        # 获取选中行
        row = item.row()

        # 存储树状展示数据depth
        parent_depth = []

        # 存储当前父节点
        parent_items = []

        # 获取深度项（第2列）
        depth_item = self.results_table.item(row, 1)
        depth = depth_item.text()

        parent_depth.append(depth)

        # 获取URL项（第5列）
        url_item = self.results_table.item(row, 5)

        # 获取存储的数据
        data = url_item.data(Qt.UserRole)
        if not data:
            return

        # 清空当前树状结构
        self.link_tree.clear()

        # 如果有深度信息，直接使用depth_to_row查找父节点
        while "." in depth:
            depth = depth[:depth.rindex(".")]
            parent_depth.append(depth)

        while parent_depth:
            depth = parent_depth.pop()  # 从列表末尾取出一个层级
            url = self.results_table.item(self.crawler_controller.depth_to_row[depth], 5).text()
            current_item = QTreeWidgetItem([url])

            if not parent_items:
                self.link_tree.addTopLevelItem(current_item)
            else:
                parent_items[-1].addChild(current_item)

            parent_items.append(current_item)

        # 展开所有节点
        self.link_tree.expandAll()




    def stop_queue_timer(self):
        """停止队列处理定时器"""
        try:
            if hasattr(self, 'queue_timer'):
                self.queue_timer.stop()
                self.queue_timer.deleteLater()
                del self.queue_timer
        except Exception as e:
            print(f"停止队列定时器时出错: {str(e)}")

    def generate_depth_number(self):
        """生成深度序号，形如1.2.1"""
        # 获取当前父节点的计数器值并增加
        self.depth_counters[self.current_parent] += 1
        current_count = self.depth_counters[self.current_parent]

        # 生成当前深度序号
        depth = f"{self.current_parent}.{current_count}" if self.current_parent != "1" else f"1.{current_count}"

        # 为新的深度序号初始化计数器（用于子节点）
        self.depth_counters[depth] = 0

        return depth

    def clear_results(self):
        """清空结果"""
        # 清空表格
        self.results_table.setRowCount(0)

        # 清空树状预览
        self.link_tree.clear()

        # 重置深度序号计数器
        self.depth_counters = {"1": 0}
        self.current_parent = "1"

    def process_crawler_data(self, data):
        """直接处理从爬虫接收到的数据"""
        try:
            # 获取数据字段
            timestamp = data.get('timestamp', '')
            url = data.get('url', '')
            status_code = data.get('status', 'N/A')
            depth = data.get('depth', '1')
            type = data.get('type', 'unknown')
            regex_names = data.get('regex_names', [])
            
            # 添加到UI
            self.add_link_result(timestamp,url, status_code, type, depth, regex_names)
            
        except Exception as e:
            self.add_log("ERROR", f"处理爬虫数据时出错: {e}", datetime.now().isoformat())

    def copy_selected_url(self, index):
        """双击复制选中行的URL到剪贴板"""
        if index.column() == 5:  # 只在双击URL列时复制
            url_item = self.results_table.item(index.row(), 5)  # 修正URL列索引为5
            if url_item:
                from PySide6.QtGui import QGuiApplication
                clipboard = QGuiApplication.clipboard()
                clipboard.setText(url_item.text())
                self.status_changed_signal.emit(f"已复制URL: {url_item.text()}")

    def eventFilter(self, obj, event):
        """事件过滤器，处理URL输入框的鼠标悬停事件"""
        if obj == self.url_input:
            if event.type() == QEvent.Type.Enter:
                # 鼠标进入输入框，增加高度以显示多行
                self._expand_timer.start(300)
                return True
            elif event.type() == QEvent.Type.Leave:
                # 鼠标离开输入框，恢复单行高度
                self._expand_timer.stop()
                self._do_collapse()
                return True
        
        # 对于其他事件，让父类处理
        return super().eventFilter(obj, event)

    def _do_expand(self):
        """展开：恢复正常行距"""
        fmt = QTextBlockFormat()
        fmt.setLineHeight(25.0, 2)  # 100 % 行距
        fmt.setTopMargin(0)
        fmt.setBottomMargin(0)

        cur = QTextCursor(self.url_input.document())
        cur.select(QTextCursor.Document)
        cur.mergeBlockFormat(fmt)

        self.url_input.setFixedHeight(100)

    def _do_collapse(self):
        """折叠：行距/段间距清零 + 文档顶端清零 + 高度固定 35px"""
        # 1. 段前/段后/行距清零
        fmt = QTextBlockFormat()
        fmt.setLineHeight(25.0, 2)  # 25 px 行距
        fmt.setTopMargin(0)
        fmt.setBottomMargin(0)

        cur = QTextCursor(self.url_input.document())
        cur.select(QTextCursor.Document)
        cur.mergeBlockFormat(fmt)

        # 2. 文档顶端 margin 清零
        doc = self.url_input.document()
        root_frame_fmt = doc.rootFrame().frameFormat()
        root_frame_fmt.setTopMargin(0)
        root_frame_fmt.setBottomMargin(0)
        doc.rootFrame().setFrameFormat(root_frame_fmt)

        # 3. 滚动到最顶端
        self.url_input.verticalScrollBar().setValue(0)

        # 4. 固定高度
        self.url_input.setFixedHeight(35)
        self.url_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)