from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QMenu, QMessageBox, QApplication, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, QAction

class ResultsTab(QWidget):
    """结果标签页"""

    # 定义信号
    export_results_signal = Signal(str)  # 导出结果信号，传递文件路径

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建搜索栏
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索结果...")
        self.search_input.textChanged.connect(self.filter_results)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)

        # 创建分割器
        splitter = QSplitter(Qt.Vertical)

        # 创建链接表格
        links_widget = QWidget()
        links_layout = QVBoxLayout(links_widget)
        links_label = QLabel("发现的链接:")
        links_label.setStyleSheet("font-weight: bold;")

        self.links_table = QTableWidget(0, 3)
        self.links_table.setHorizontalHeaderLabels(["URL", "状态码", "标题"])
        self.links_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.links_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.links_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.links_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.links_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.links_table.customContextMenuRequested.connect(self.show_links_context_menu)
        self.links_table.doubleClicked.connect(self.copy_selected_link_url)

        links_layout.addWidget(links_label)
        links_layout.addWidget(self.links_table)

        # 创建API表格
        apis_widget = QWidget()
        apis_layout = QVBoxLayout(apis_widget)
        apis_label = QLabel("发现的API:")
        apis_label.setStyleSheet("font-weight: bold;")

        self.apis_table = QTableWidget(0, 4)
        self.apis_table.setHorizontalHeaderLabels(["URL", "方法", "参数", "描述"])
        self.apis_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.apis_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.apis_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.apis_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.apis_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.apis_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.apis_table.customContextMenuRequested.connect(self.show_apis_context_menu)
        self.apis_table.doubleClicked.connect(self.copy_selected_api_url)

        apis_layout.addWidget(apis_label)
        apis_layout.addWidget(self.apis_table)

        # 添加部件到分割器
        splitter.addWidget(links_widget)
        splitter.addWidget(apis_widget)
        splitter.setSizes([int(self.height() * 0.5), int(self.height() * 0.5)])

        # 创建操作按钮布局
        actions_layout = QHBoxLayout()

        # 清空结果按钮
        self.clear_btn = QPushButton("清空结果")
        self.clear_btn.clicked.connect(self.clear_results)

        # 导出结果按钮
        self.export_btn = QPushButton("导出结果")
        self.export_btn.clicked.connect(self.export_results)

        # 添加按钮到布局
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.export_btn)

        # 添加所有组件到主布局
        main_layout.addLayout(search_layout)
        main_layout.addWidget(splitter)
        main_layout.addLayout(actions_layout)

    @Slot(str, int, str)
    def add_link(self, url, status_code, title):
        """添加链接到表格"""
        row = self.links_table.rowCount()
        self.links_table.insertRow(row)

        url_item = QTableWidgetItem(url)
        url_item.setData(Qt.UserRole, url)  # 存储原始URL用于过滤

        status_item = QTableWidgetItem(str(status_code))
        status_item.setTextAlignment(Qt.AlignCenter)

        title_item = QTableWidgetItem(title)

        self.links_table.setItem(row, 0, url_item)
        self.links_table.setItem(row, 1, status_item)
        self.links_table.setItem(row, 2, title_item)

    @Slot(str, str, str, str)
    def add_api(self, url, method, params, description):
        """添加API到表格"""
        row = self.apis_table.rowCount()
        self.apis_table.insertRow(row)

        url_item = QTableWidgetItem(url)
        url_item.setData(Qt.UserRole, url)  # 存储原始URL用于过滤

        method_item = QTableWidgetItem(method)
        method_item.setTextAlignment(Qt.AlignCenter)

        params_item = QTableWidgetItem(params)

        desc_item = QTableWidgetItem(description)

        self.apis_table.setItem(row, 0, url_item)
        self.apis_table.setItem(row, 1, method_item)
        self.apis_table.setItem(row, 2, params_item)
        self.apis_table.setItem(row, 3, desc_item)

    def filter_results(self):
        """根据搜索关键词过滤结果"""
        keyword = self.search_input.text().lower()

        # 过滤链接表格
        for row in range(self.links_table.rowCount()):
            hide_row = True
            for col in range(self.links_table.columnCount()):
                item = self.links_table.item(row, col)
                if item and keyword in item.text().lower():
                    hide_row = False
                    break
            self.links_table.setRowHidden(row, hide_row)

        # 过滤API表格
        for row in range(self.apis_table.rowCount()):
            hide_row = True
            for col in range(self.apis_table.columnCount()):
                item = self.apis_table.item(row, col)
                if item and keyword in item.text().lower():
                    hide_row = False
                    break
            self.apis_table.setRowHidden(row, hide_row)

    def clear_results(self):
        """清空所有结果"""
        self.links_table.setRowCount(0)
        self.apis_table.setRowCount(0)

    def export_results(self):
        """导出结果到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出结果", "", "CSV文件 (*.csv);;JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            self.export_results_signal.emit(file_path)

    def show_links_context_menu(self, position):
        """显示链接表格的上下文菜单"""
        menu = QMenu()

        copy_url_action = QAction("复制URL", self)
        copy_url_action.triggered.connect(self.copy_selected_link_url)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_selected_link)

        menu.addAction(copy_url_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())

    def show_apis_context_menu(self, position):
        """显示API表格的上下文菜单"""
        menu = QMenu()

        copy_url_action = QAction("复制URL", self)
        copy_url_action.triggered.connect(self.copy_selected_api_url)

        copy_params_action = QAction("复制参数", self)
        copy_params_action.triggered.connect(self.copy_selected_api_params)

        test_api_action = QAction("测试API", self)
        test_api_action.triggered.connect(self.test_selected_api)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_selected_api)

        menu.addAction(copy_url_action)
        menu.addAction(copy_params_action)
        menu.addAction(test_api_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())

    def copy_selected_link_url(self):
        """复制选中的链接URL"""
        selected_rows = self.links_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            url = self.links_table.item(row, 0).text()
            QApplication.clipboard().setText(url)

    def delete_selected_link(self):
        """删除选中的链接"""
        selected_rows = self.links_table.selectionModel().selectedRows()
        if selected_rows:
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                self.links_table.removeRow(index.row())

    def copy_selected_api_url(self):
        """复制选中的API URL"""
        selected_rows = self.apis_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            url = self.apis_table.item(row, 0).text()
            QApplication.clipboard().setText(url)

    def copy_selected_api_params(self):
        """复制选中的API参数"""
        selected_rows = self.apis_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            params = self.apis_table.item(row, 2).text()
            QApplication.clipboard().setText(params)

    def delete_selected_api(self):
        """删除选中的API"""
        selected_rows = self.apis_table.selectionModel().selectedRows()
        if selected_rows:
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                self.apis_table.removeRow(index.row())
