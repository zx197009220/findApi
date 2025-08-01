from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot, QDateTime
from PySide6.QtGui import QGuiApplication, QAction
import queue  # 导入queue模块以使用queue.Empty异常

class CrawlerTab(QWidget):
    """爬虫标签页，包含爬虫控制界面、结果显示表格和链接树状预览"""

    # 定义信号
    start_crawler_signal = Signal(dict)  # 开始爬取信号，传递配置字典
    stop_crawler_signal = Signal()  # 停止爬取信号
    status_changed_signal = Signal(str)  # 状态变化信号，用于更新主窗口状态栏

    def __init__(self, crawler_controller):
        super().__init__()
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

        # 连接UI信号到控制器
        self.start_button.clicked.connect(self.start_crawler)
        self.stop_button.clicked.connect(self.stop_crawler)

        # 创建定时器来检查结果队列
        from PySide6.QtCore import QTimer
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_result_queue)
        self.queue_timer.start(100)  # 每100毫秒检查一次队列

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)  # 显式设置布局到窗口
        
        print("UI初始化开始...")  # 调试输出

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
        
        print("UI初始化开始...")  # 调试输出

        # 创建顶部控制区域
        top_control_widget = QWidget()
        top_layout = QHBoxLayout(top_control_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 创建URL输入框
        url_label = QLabel("起始URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入起始URL (例如: https://example.com)")
        self.url_input.setMinimumWidth(400)

        # 创建启动和停止按钮
        self.start_button = QPushButton("开始爬取")
        self.start_button.setMinimumWidth(100)
        self.stop_button = QPushButton("停止爬取")
        self.stop_button.setMinimumWidth(100)
        self.stop_button.setEnabled(False)

        # 将控件添加到顶部布局
        top_layout.addWidget(url_label)
        top_layout.addWidget(self.url_input, 1)
        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.stop_button)

        # 添加顶部控制区域到主布局
        self.main_layout.addWidget(top_control_widget)

        # 创建分割器
        self.splitter = QSplitter(Qt.Vertical)

        # 创建爬取结果表格
        results_widget = QWidget()
        print(f"results_widget 创建成功: {results_widget}")  # 调试输出
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)

        results_label = QLabel("爬取结果:")
        results_layout.addWidget(results_label)
        print(f"results_label 添加成功: {results_label}")  # 调试输出

        self.results_table = QTableWidget()
        print(f"results_table 创建成功: {self.results_table}")  # 调试输出
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
        print(f"preview_group 创建成功: {preview_group}")  # 调试输出
        preview_layout = QVBoxLayout()

        self.link_tree = QTreeWidget()
        print(f"link_tree 创建成功: {self.link_tree}")  # 调试输出
        self.link_tree.setHeaderLabel("链接层级")
        self.link_tree.setColumnCount(1)
        
        # 设置树状视图的上下文菜单策略
        self.link_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.link_tree.customContextMenuRequested.connect(self.create_link_tree_context_menu)

        preview_layout.addWidget(self.link_tree)
        print(f"link_tree 添加到布局: {self.link_tree}")  # 调试输出
        preview_group.setLayout(preview_layout)
        print(f"preview_group 布局设置完成: {preview_group}")  # 调试输出

        # 将树状预览区域添加到分割器
        self.splitter.addWidget(preview_group)

        # 设置分割器的初始大小
        self.splitter.setSizes([600, 400])

        # 将分割器添加到主布局
        print(f"准备添加分割器到主布局: {self.splitter}")  # 调试输出
        self.main_layout.addWidget(self.splitter, 1)
        print(f"分割器已添加到主布局: {self.splitter}")  # 调试输出

        # 连接信号和槽
        self.results_table.itemClicked.connect(self.show_item_details)
        
        # 添加窗口显示后的调试
        print("UI初始化完成，所有控件已添加到布局")  # 调试输出
        print(f"主布局子控件数量: {self.main_layout.count()}")  # 调试输出
        
        # 连接爬虫控制信号
        self.connect_crawler_signals()

    def start_crawler(self):
        """开始爬取"""
        url = self.url_input.text().strip()
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
        config = {
            'start_url': url,
            'max_depth': 3,
            'timeout': 10,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 调用爬虫控制器的启动方法
        self.crawler_controller.start_crawler(config)

    def stop_crawler(self):
        """停止爬取"""
        # 调用爬虫控制器的停止方法
        self.crawler_controller.stop_crawler()

    def update_status(self, status):
        """更新爬虫状态"""
        # 发送状态更新信号给主窗口
        self.status_changed_signal.emit(status)

        # 根据状态更新按钮状态
        if status.startswith("已停止") or status.startswith("完成"):
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        elif status.startswith("正在爬取"):
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def add_log(self, level, message, timestamp):
        """添加日志消息"""
        # 可以考虑在状态栏显示最新的日志消息
        if level == "ERROR":
            self.status_changed_signal.emit(f"错误: {message}")

    def add_link_result(self, url, status_code, type, depth=None, regex_names=None):
        """添加链接结果到表格"""
        # 获取当前时间作为时间戳
        timestamp = QDateTime.currentDateTime().toString("MM-dd hh:mm")

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



    def process_result_queue(self):
        """处理结果队列中的项目"""
        # 处理队列中的所有数据
        while True:
            try:
                # 尝试使用队列的get方法
                result = self.crawler_controller.result_queue.get(block=False)

                # 直接使用模拟数据中的深度
                depth = result.get('depth')

                # 获取URL
                url = result.get('url')

                # 获取状态码
                status_code = result.get('status')

                # 获取类型
                type = result.get('type')

                regex_names = result.get('regex_names')

                # 添加到UI
                self.add_link_result(url, status_code, type, depth, regex_names)

            except queue.Empty:
                # 队列为空，退出循环
                break
            except Exception as e:
                # 处理其他异常情况
                print(f"处理结果队列时出错: {str(e)}")
                break

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

    def copy_selected_url(self, index):
        """双击复制选中行的URL到剪贴板"""
        if index.column() == 4:  # 只在双击URL列时复制
            url_item = self.results_table.item(index.row(), 4)
            if url_item:
                from PySide6.QtGui import QGuiApplication
                clipboard = QGuiApplication.clipboard()
                clipboard.setText(url_item.text())
                self.status_changed_signal.emit(f"已复制URL: {url_item.text()}")
