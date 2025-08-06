from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QRunnable, QThreadPool, QRegularExpression, \
    Slot, QDateTime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTableView, QFileDialog, QMessageBox, QProgressDialog
from collections import deque
import re
import time

class ExcludeLogsModel(QAbstractTableModel):
    """用于管理排除日志数据的模型类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries = deque(maxlen=10000)  # 使用双端队列限制最大条目数
        self._cache_valid = False
        self._data_cache = {}
        self._row_count_cache = 0
        self._batch_update = False

    def rowCount(self, parent=QModelIndex()):
        # 使用缓存减少重复计算
        if self._cache_valid:
            return self._row_count_cache
        self._row_count_cache = len(self.log_entries)
        return self._row_count_cache

    def columnCount(self, parent=QModelIndex()):
        return 4  # 固定5列: 时间、规则、链接、来源

    def data(self, index, role=Qt.DisplayRole):
        # 使用更高效的缓存机制
        if not index.isValid():
            return None
            
        # 对于不同的角色使用不同的缓存
        if role == Qt.DisplayRole:
            cache_key = (index.row(), index.column(), 'display')
            if self._cache_valid and cache_key in self._data_cache:
                return self._data_cache[cache_key]

            try:
                entry = self.log_entries[index.row()]
                if index.column() == 0:
                    value = entry['timestamp']
                elif index.column() == 1:
                    value = entry['rule']
                elif index.column() == 2:
                    value = entry['link']
                elif index.column() == 3:
                    value = entry['source']
                else:
                    value = None
                    
                # 更新缓存
                self._data_cache[cache_key] = value
                return value
            except IndexError:
                # 处理索引越界异常，提高稳定性
                return None
        elif role == Qt.TextAlignmentRole:
            # 为不同列设置不同的对齐方式
            if index.column() == 0:  # 时间列居中对齐
                return Qt.AlignCenter
            elif index.column() == 4:  # 父链接序号列右对齐
                return Qt.AlignRight | Qt.AlignVCenter
            else:  # 其他列左对齐
                return Qt.AlignLeft | Qt.AlignVCenter
        elif role == Qt.ToolTipRole:
            # 为长文本添加工具提示
            try:
                entry = self.log_entries[index.row()]
                if index.column() == 2:  # 链接列
                    return entry['link']
                elif index.column() == 1:  # 规则列
                    return entry['rule']
            except IndexError:
                return None
                
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            headers = ["时间", "排除规则", "排除链接", "链接来源"]
            return headers[section]
        return None

    def add_log(self, log_entry):
        """添加单个日志条目"""
        if not self._batch_update:
            self.beginInsertRows(QModelIndex(), len(self.log_entries), len(self.log_entries))

        self.log_entries.append(log_entry)
        self._cache_valid = False  # 使缓存失效

        if not self._batch_update:
            self.endInsertRows()

        # 定期清理旧条目
        if len(self.log_entries) % 5000 == 0:
            self.cleanup_old_entries()

    def cleanup_old_entries(self):
        """清理旧条目以节省内存"""
        if len(self.log_entries) > 5000:  # 降低清理阈值
            self.beginResetModel()
            # 保留最近的5000条记录
            self.log_entries = deque(list(self.log_entries)[-5000:], maxlen=10000)
            self._cache_valid = False  # 使缓存失效
            self.endResetModel()

    def begin_batch_update(self):
        """开始批量更新"""
        self._batch_update = True
        self.beginResetModel()

    def end_batch_update(self):
        """结束批量更新"""
        self._batch_update = False
        self._cache_valid = False  # 使缓存失效
        self.endResetModel()

    def clear(self):
        """清空所有日志条目"""
        self.beginResetModel()
        self.log_entries.clear()
        # 重置缓存
        self._cache_valid = False
        self._data_cache.clear()
        self._row_count_cache = 0
        self.endResetModel()

    def get_all_logs(self):
        """获取所有日志条目"""
        return list(self.log_entries)

class ExcludeLogsTab(QWidget):
    """排除日志标签页"""

    save_logs_signal = Signal(str)
    export_finished = Signal(bool, str, str)

    def __init__(self):
        super().__init__()
        self.log_model = ExcludeLogsModel()
        self.init_ui()

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # 创建顶部控制区域
        top_control_widget = QWidget()
        top_layout = QHBoxLayout(top_control_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 创建搜索控件
        search_label = QLabel("搜索:")
        self.keyword_input = QComboBox()
        self.keyword_input.setEditable(True)
        self.keyword_input.setMinimumWidth(300)
        self.keyword_input.setPlaceholderText("输入关键词搜索")
        
        # 创建搜索列选择下拉框
        self.column_combo = QComboBox()
        self.column_combo.addItems(["全部列", "时间", "排除规则", "排除链接", "链接来源", "父链接序号"])
        
        # 创建搜索按钮
        self.search_button = QPushButton("搜索")
        
        # 创建清空按钮
        self.clear_button = QPushButton("清空")
        
        # 创建导出按钮
        self.export_button = QPushButton("导出")
        
        # 将控件添加到顶部布局
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.keyword_input, 1)
        top_layout.addWidget(self.column_combo)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.clear_button)
        top_layout.addWidget(self.export_button)
        
        # 添加顶部控制区域到主布局
        self.main_layout.addWidget(top_control_widget)
        
        # 创建表格视图
        self.logs_view = QTableView()
        self.logs_view.setAlternatingRowColors(True)
        self.logs_view.setSelectionBehavior(QTableView.SelectRows)
        self.logs_view.setSelectionMode(QTableView.SingleSelection)
        self.logs_view.setSortingEnabled(True)
        self.logs_view.horizontalHeader().setStretchLastSection(True)
        self.logs_view.verticalHeader().setVisible(False)
        
        # 创建代理模型用于过滤和排序
        from PySide6.QtCore import QSortFilterProxyModel
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.log_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        # 设置表格视图的模型
        self.logs_view.setModel(self.proxy_model)
        
        # 设置表格列宽
        self.logs_view.setColumnWidth(0, 150)  # 时间列
        self.logs_view.setColumnWidth(1, 200)  # 排除规则列
        self.logs_view.setColumnWidth(2, 300)  # 排除链接列
        self.logs_view.setColumnWidth(3, 200)  # 链接来源列
        self.logs_view.setColumnWidth(4, 100)  # 父链接序号列
        
        # 添加表格视图到主布局
        self.main_layout.addWidget(self.logs_view, 1)
        
        # 连接信号和槽
        self.search_button.clicked.connect(self.perform_search)
        self.clear_button.clicked.connect(self.clear_logs)
        self.export_button.clicked.connect(self.export_logs)
        self.column_combo.currentIndexChanged.connect(self.change_search_column)
        self.keyword_input.lineEdit().returnPressed.connect(self.perform_search)
        
        # 启动搜索定时器
        self.start_search_timer()

    def start_search_timer(self):
        """启动搜索定时器，用于延迟搜索，避免频繁搜索导致的卡顿"""
        from PySide6.QtCore import QTimer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # 300毫秒延迟
        self.search_timer.timeout.connect(self.perform_search)
        
        # 当文本变化时启动定时器
        self.keyword_input.lineEdit().textChanged.connect(self.search_timer.start)

    def perform_search(self):
        """执行搜索操作"""
        filter_text = self.keyword_input.currentText().strip()

        # 优化：如果搜索文本为空，直接清除过滤器而不是设置空字符串
        if not filter_text:
            self.proxy_model.setFilterFixedString("")
            return

        # 使用QRunnable将搜索操作移至后台线程
        from PySide6.QtCore import QRunnable, QThreadPool, QRegularExpression, Slot

        class SearchRunnable(QRunnable):
            def __init__(self, filter_text, parent):
                super().__init__()
                self.filter_text = filter_text
                self.parent = parent

            @Slot()
            def run(self):
                # 在后台线程中创建正则表达式
                regex = QRegularExpression(self.filter_text, QRegularExpression.CaseInsensitiveOption)

                # 使用信号安全地更新UI
                from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self.parent,
                    "apply_filter",
                    Qt.QueuedConnection,
                    Q_ARG(QRegularExpression, regex),
                    Q_ARG(str, self.filter_text)
                )

        # 创建并启动搜索任务
        search_task = SearchRunnable(filter_text, self)
        QThreadPool.globalInstance().start(search_task)

    @Slot(QRegularExpression, str)
    def apply_filter(self, regex, filter_text):
        """应用过滤器（从后台线程调用）"""
        # 在主线程中应用过滤器
        self.proxy_model.setFilterRegularExpression(regex)

        # 如果有搜索文本且不在下拉列表中，添加到下拉列表
        if self.keyword_input.findText(filter_text) == -1:
            self.keyword_input.addItem(filter_text)
            # 限制历史记录数量，防止内存占用过大
            if self.keyword_input.count() > 20:
                self.keyword_input.removeItem(self.keyword_input.count() - 1)

    def change_search_column(self, index):
        """更改搜索列"""
        self.current_search_column = index
        # 如果已经有搜索关键词，则重新执行搜索
        if self.keyword_input.currentText():
            self.perform_search()

    def add_log(self, log_data):
        """添加单个日志条目"""
        self.log_model.add_log(log_data)
        
        # 如果表格视图已经创建，则滚动到最新的日志
        if hasattr(self, 'logs_view'):
            # 使用QTimer延迟滚动，避免UI卡顿
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """滚动到表格底部"""
        if self.proxy_model.rowCount() > 0:
            last_row = self.proxy_model.rowCount() - 1
            self.logs_view.scrollTo(self.proxy_model.index(last_row, 0))

    def add_logs_batch(self, log_data_list):
        """批量添加日志条目"""
        self.log_model.begin_batch_update()
        for log_data in log_data_list:
            self.log_model.add_log(log_data)
        self.log_model.end_batch_update()

    def clear_logs(self):
        """清空所有日志"""
        self.log_model.clear()

    def save_logs(self):
        """保存日志到文本文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存排除日志", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            # 使用QRunnable在后台线程中执行保存
            from PySide6.QtCore import QRunnable, QThreadPool, Slot

            class SaveRunnable(QRunnable):
                def __init__(self, file_path, log_entries, parent):
                    super().__init__()
                    self.file_path = file_path
                    self.log_entries = log_entries
                    self.parent = parent

                @Slot()
                def run(self):
                    try:
                        with open(self.file_path, 'w', encoding='utf-8') as f:
                            for entry in self.log_entries:
                                f.write(f"{entry['timestamp']}\t{entry['rule']}\t{entry['link']}\t{entry['source']}\t{entry['parent_index']}\n")

                        # 保存成功，发送信号
                        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                        QMetaObject.invokeMethod(
                            self.parent,
                            "on_save_finished",
                            Qt.QueuedConnection,
                            Q_ARG(bool, True),
                            Q_ARG(str, self.file_path),
                            Q_ARG(str, "")
                        )
                    except Exception as e:
                        # 保存失败，发送错误信号
                        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                        QMetaObject.invokeMethod(
                            self.parent,
                            "on_save_finished",
                            Qt.QueuedConnection,
                            Q_ARG(bool, False),
                            Q_ARG(str, self.file_path),
                            Q_ARG(str, str(e))
                        )

            # 显示进度对话框
            progress = QProgressDialog("正在保存日志...", None, 0, 100, self)
            progress.setWindowTitle("保存进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()

            # 连接保存完成信号
            self.save_finished = Signal(bool, str, str)
            self.save_finished.connect(lambda success, path, error_msg: self.on_save_finished(
                success, path, error_msg, progress
            ))

            # 获取日志条目的副本，避免在保存过程中被修改
            log_entries = self.log_model.get_all_logs().copy()

            # 创建并启动保存任务
            save_task = SaveRunnable(file_path, log_entries, self)
            QThreadPool.globalInstance().start(save_task)

    def on_save_finished(self, success, file_path, error_msg, progress_dialog):
        """保存完成后的处理"""
        # 关闭进度对话框
        progress_dialog.close()

        if success:
            # 发出信号通知其他组件
            self.save_logs_signal.emit(file_path)

            # 显示成功消息
            QMessageBox.information(self, "保存成功", f"排除日志已成功保存到:\n{file_path}")
        else:
            # 显示错误消息
            QMessageBox.critical(self, "保存失败", f"保存日志时发生错误:\n{error_msg}")

    def export_logs(self):
        """导出日志到CSV文件"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出排除日志", "", "CSV文件 (*.csv);;Excel文件 (*.xlsx);;所有文件 (*)"
        )
        if not file_path:
            return

        # 显示进度对话框
        progress = QProgressDialog("正在导出日志...", "取消", 0, 100, self)
        progress.setWindowTitle("导出进度")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)  # 立即显示
        progress.setValue(0)
        progress.show()

        # 连接导出完成信号
        self.export_finished.connect(lambda success, path, error_msg: self.on_export_finished(
            success, path, error_msg, progress
        ))

        # 获取日志条目的副本，避免在导出过程中被修改
        log_entries = self.log_model.get_all_logs().copy()

        # 使用QRunnable在后台线程中执行导出
        from PySide6.QtCore import QRunnable, QThreadPool, Slot

        class ExportRunnable(QRunnable):
            def __init__(self, file_path, log_entries, parent):
                super().__init__()
                self.file_path = file_path
                self.log_entries = log_entries
                self.parent = parent

            @Slot()
            def run(self):
                try:
                    # 根据文件类型选择导出方法
                    if self.file_path.lower().endswith('.xlsx'):
                        self.export_to_excel()
                    else:
                        self.export_to_csv()

                    # 导出成功，发送信号
                    from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(
                        self.parent,
                        "export_finished",
                        Qt.QueuedConnection,
                        Q_ARG(bool, True),
                        Q_ARG(str, self.file_path),
                        Q_ARG(str, "")
                    )
                except Exception as e:
                    # 导出失败，发送错误信号
                    from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(
                        self.parent,
                        "export_finished",
                        Qt.QueuedConnection,
                        Q_ARG(bool, False),
                        Q_ARG(str, self.file_path),
                        Q_ARG(str, str(e))
                    )

            def export_to_csv(self):
                """在后台线程中导出到CSV文件"""
                import csv

                with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
                    # 创建CSV写入器
                    writer = csv.writer(f)

                    # 写入标题行
                    writer.writerow(["时间", "排除规则", "排除链接", "链接来源"])

                    # 批量写入日志条目，每次处理1000条
                    batch_size = 1000
                    total_entries = len(self.log_entries)

                    for i in range(0, total_entries, batch_size):
                        batch = self.log_entries[i:i+batch_size]
                        for entry in batch:
                            writer.writerow([
                                entry['timestamp'],
                                entry['rule'],
                                entry['link'],
                                entry['source']
                            ])

                        # 更新进度
                        progress = min(100, int((i + batch_size) / total_entries * 100))
                        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                        QMetaObject.invokeMethod(
                            self.parent.progress_dialog,
                            "setValue",
                            Qt.QueuedConnection,
                            Q_ARG(int, progress)
                        )

            def export_to_excel(self):
                """在后台线程中导出到Excel文件"""
                try:
                    import pandas as pd

                    # 获取所有日志条目
                    total_entries = len(self.log_entries)

                    # 性能优化：使用批处理方式创建DataFrame
                    batch_size = 1000
                    writer = pd.ExcelWriter(self.file_path, engine='openpyxl')

                    # 如果数据量小，直接导出
                    if total_entries <= batch_size:
                        data = []
                        for entry in self.log_entries:
                            data.append({
                                "时间": entry['timestamp'],
                                "排除规则": entry['rule'],
                                "排除链接": entry['link'],
                                "链接来源": entry['source'],
                                "父链接序号": entry['parent_index']
                            })

                        df = pd.DataFrame(data)
                        df.to_excel(writer, index=False, sheet_name='排除日志')

                        # 更新进度
                        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                        QMetaObject.invokeMethod(
                            self.parent.progress_dialog,
                            "setValue",
                            Qt.QueuedConnection,
                            Q_ARG(int, 100)
                        )
                    else:
                        # 数据量大，分批处理
                        for i in range(0, total_entries, batch_size):
                            batch = self.log_entries[i:i+batch_size]
                            data = []
                            for entry in batch:
                                data.append({
                                    "时间": entry['timestamp'],
                                    "排除规则": entry['rule'],
                                    "排除链接": entry['link'],
                                    "链接来源": entry['source'],
                                    "父链接序号": entry['parent_index']
                                })

                            # 创建DataFrame并写入Excel
                            sheet_name = f'批次{i//batch_size+1}'
                            df = pd.DataFrame(data)
                            df.to_excel(writer, index=False, sheet_name=sheet_name)

                            # 更新进度
                            progress = min(100, int((i + batch_size) / total_entries * 100))
                            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                            QMetaObject.invokeMethod(
                                self.parent.progress_dialog,
                                "setValue",
                                Qt.QueuedConnection,
                                Q_ARG(int, progress)
                            )

                    # 保存Excel文件
                    writer.close()
                except ImportError:
                    # 如果没有安装pandas，则使用CSV格式
                    csv_path = self.file_path.rsplit('.', 1)[0] + '.csv'
                    self.file_path = csv_path
                    self.export_to_csv()

        # 保存进度对话框的引用，以便在后台线程中更新
        self.progress_dialog = progress

        # 创建并启动导出任务
        export_task = ExportRunnable(file_path, log_entries, self)
        QThreadPool.globalInstance().start(export_task)

    def on_export_finished(self, success, file_path, error_msg, progress_dialog):
        """导出完成后的处理"""
        # 关闭进度对话框
        progress_dialog.close()

        if success:
            # 发出信号通知其他组件
            self.save_logs_signal.emit(file_path)

            # 显示成功消息
            QMessageBox.information(self, "导出成功", f"排除日志已成功导出到:\n{file_path}")
        else:
            # 显示错误消息
            QMessageBox.critical(self, "导出失败", f"导出日志时发生错误:\n{error_msg}")
