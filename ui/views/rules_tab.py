from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QSplitter, QTextEdit,
    QCheckBox, QHeaderView, QAbstractItemView, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox, QComboBox, QMessageBox, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
import yaml
import os
import re

class RuleEditDialog(QDialog):
    """规则编辑对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑规则")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI组件"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # 规则名
        self.name_edit = QLineEdit()
        form_layout.addRow("规则名:", self.name_edit)
        
        # 正则表达式
        self.regex_edit = QLineEdit()
        form_layout.addRow("正则表达式:", self.regex_edit)
        
        # 规则类型
        type_group = QGroupBox("规则类型")
        type_layout = QHBoxLayout()
        self.findlink_radio = QRadioButton("FindLink")
        self.findlink_radio.setChecked(True)
        self.excludelink_radio = QRadioButton("ExcludeLink")
        type_layout.addWidget(self.findlink_radio)
        type_layout.addWidget(self.excludelink_radio)
        type_group.setLayout(type_layout)
        form_layout.addRow(type_group)
        
        # 大小写敏感
        self.case_sensitive_checkbox = QCheckBox("大小写敏感")
        self.case_sensitive_checkbox.setChecked(True)
        form_layout.addRow("", self.case_sensitive_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def set_rule_data(self, rule_data):
        """设置对话框中的规则数据"""
        self.name_edit.setText(rule_data.get('name', ''))
        self.regex_edit.setText(rule_data.get('f_regex', ''))
        self.case_sensitive_checkbox.setChecked(rule_data.get('sensitive', True))
        # 设置规则类型，默认为findLink
        rule_type = rule_data.get('type', 'findLink')
        index = self.type_combo.findData(rule_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

    def get_rule_data(self):
        """获取对话框中的规则数据"""
        rule_type = 'findLink' if self.findlink_radio.isChecked() else 'excludeLink'
        return {
            'name': self.name_edit.text(),
            'f_regex': self.regex_edit.text(),
            'sensitive': self.case_sensitive_checkbox.isChecked(),
            'type': rule_type  # 获取当前选择的规则类型
        }


class RulesTab(QWidget):
    """规则标签页，显示rules.yml中的正则表达式规则"""

    # 定义信号
    status_changed_signal = Signal(str)  # 状态变化信号，用于更新主窗口状态栏

    def __init__(self):
        super().__init__()
        self.rules_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rules.yml')
        self.rules_data = None
        self.patterns = {}  # 存储编译后的正则表达式模式
        self.init_ui()
        self.load_rules()

    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建顶部标题区域
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("正则表达式规则:")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setMinimumWidth(100)
        self.refresh_button.clicked.connect(self.load_rules)

        self.add_rule_button = QPushButton("添加规则")
        self.add_rule_button.setMinimumWidth(100)
        self.add_rule_button.clicked.connect(self.add_rule)

        top_layout.addWidget(title_label)
        top_layout.addStretch(1)
        top_layout.addWidget(self.add_rule_button)
        top_layout.addWidget(self.refresh_button)

        # 添加顶部区域到主布局
        main_layout.addWidget(top_widget)

        # 创建分割器
        self.splitter = QSplitter(Qt.Vertical)

        # 创建FindLink规则表格
        findlink_group = QGroupBox("FindLink规则")
        findlink_layout = QVBoxLayout()

        self.findlink_table = QTableWidget()
        self.findlink_table.setColumnCount(5)  # 规则名、正则表达式、大小写敏感、启用、操作
        self.findlink_table.setHorizontalHeaderLabels(["规则名", "正则表达式", "大小写敏感", "启用", "操作"])
        
        # 设置表格属性
        self.findlink_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.findlink_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.findlink_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.findlink_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.findlink_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.findlink_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.findlink_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.findlink_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        findlink_layout.addWidget(self.findlink_table)
        findlink_group.setLayout(findlink_layout)

        # 创建excludeLink规则表格
        excludelink_group = QGroupBox("excludeLink规则")
        excludelink_layout = QVBoxLayout()

        self.excludelink_table = QTableWidget()
        self.excludelink_table.setColumnCount(5)  # 规则名、正则表达式、大小写敏感、启用、操作
        self.excludelink_table.setHorizontalHeaderLabels(["规则名", "正则表达式", "大小写敏感", "启用", "操作"])
        
        # 设置表格属性
        self.excludelink_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.excludelink_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.excludelink_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.excludelink_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.excludelink_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.excludelink_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.excludelink_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.excludelink_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        excludelink_layout.addWidget(self.excludelink_table)
        excludelink_group.setLayout(excludelink_layout)

        # 将两个表格区域添加到分割器
        self.splitter.addWidget(findlink_group)
        self.splitter.addWidget(excludelink_group)

        # 设置分割器的初始大小
        self.splitter.setSizes([300, 300])

        # 将分割器添加到主布局
        main_layout.addWidget(self.splitter, 1)

    def load_rules(self):
        """加载rules.yml文件中的规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as file:
                self.rules_data = yaml.safe_load(file)
            
            # 清空现有模式
            self.patterns = {}
            
            # 确保数据结构正确
            if not self.rules_data:
                self.rules_data = {'rules': []}
            if 'rules' not in self.rules_data:
                self.rules_data['rules'] = []
            
            # 检查是否有FindLink和excludeLink分组
            has_findlink = any(g.get('group') == 'FindLink' for g in self.rules_data['rules'])
            has_excludelink = any(g.get('group') == 'excludeLink' for g in self.rules_data['rules'])
            
            # 如果没有分组，创建默认分组
            if not has_findlink and not has_excludelink:
                self.rules_data['rules'] = [
                    {'group': 'FindLink', 'rule': []},
                    {'group': 'excludeLink', 'rule': []}
                ]
            
            # 加载并编译正则表达式
            for group in self.rules_data['rules']:
                if 'rule' in group:
                    for rule in group['rule']:
                        try:
                            pattern = re.compile(rule['f_regex'])
                            self.patterns[rule['name']] = pattern
                        except re.error as e:
                            self.status_changed_signal.emit(f"正则表达式编译错误 ({rule['name']}): {str(e)}")
            
            self.update_rules_tables()
            self.status_changed_signal.emit("规则加载成功")
        except Exception as e:
            self.status_changed_signal.emit(f"加载规则失败: {str(e)}")
            self.update_rules_tables()

    def update_rules_tables(self):
        """更新规则表格"""
        self.findlink_table.setRowCount(0)
        self.excludelink_table.setRowCount(0)
        
        if not self.rules_data or 'rules' not in self.rules_data:
            return
            
        for group in self.rules_data['rules']:
            if 'rule' not in group:
                continue
                
            for rule in group['rule']:
                rule_name = rule['name']
                regex = rule['f_regex']
                sensitive = "是" if rule.get('sensitive', True) else "否"
                
                # 根据规则分组决定添加到哪个表格
                if group.get('group') == 'excludeLink':
                    table = self.excludelink_table
                    row = self.excludelink_table.rowCount()
                else:
                    # 默认放到findLink表格
                    table = self.findlink_table
                    row = self.findlink_table.rowCount()
                
                # 添加新行
                table.insertRow(row)
                
                # 规则名
                rule_item = QTableWidgetItem(rule_name)
                rule_item.setData(Qt.UserRole, {'type': 'rule', 'data': rule})
                table.setItem(row, 0, rule_item)
                
                # 正则表达式
                regex_item = QTableWidgetItem(regex)
                regex_item.setToolTip(regex)
                table.setItem(row, 1, regex_item)
                
                # 大小写敏感
                sensitive_item = QTableWidgetItem(sensitive)
                table.setItem(row, 2, sensitive_item)
                
                # 启用复选框
                enabled_widget = QWidget()
                enabled_layout = QHBoxLayout(enabled_widget)
                enabled_layout.setContentsMargins(5, 0, 5, 0)
                enabled_layout.setAlignment(Qt.AlignCenter)
                
                enabled_checkbox = QCheckBox()
                enabled_checkbox.setChecked(rule.get('enabled', True))
                enabled_checkbox.stateChanged.connect(lambda state, r=row, t=table: self.toggle_rule_enabled(r, state, t))
                
                enabled_layout.addWidget(enabled_checkbox)
                table.setCellWidget(row, 3, enabled_widget)
                
                # 操作按钮
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 0, 5, 0)
                actions_layout.setSpacing(2)
                
                edit_button = QPushButton("编辑")
                edit_button.setMaximumWidth(60)
                edit_button.clicked.connect(lambda _, r=row, t=table: self.edit_rule(r, t))
                
                delete_button = QPushButton("删除")
                delete_button.setMaximumWidth(60)
                delete_button.clicked.connect(lambda _, r=row, t=table: self.delete_rule(r, t))
                
                actions_layout.addWidget(edit_button)
                actions_layout.addWidget(delete_button)
                
                table.setCellWidget(row, 4, actions_widget)


    def toggle_rule_enabled(self, row, state, table):
        """切换规则启用状态"""
        if row < 0 or row >= table.rowCount():
            return
            
        rule_item = table.item(row, 0)  # 修改为获取第0列的规则名
        if not rule_item:
            return
            
        item_data = rule_item.data(Qt.UserRole)
        if not item_data:
            return
            
        data = item_data.get('data')
        if not data:
            return
            
        # 更新规则启用状态
        data['enabled'] = state == Qt.Checked
            
        # 标记规则已修改，需要保存
        self.rules_modified = True
        
    def add_rule(self):
        """添加新规则"""
        dialog = RuleEditDialog(self)
            
        if dialog.exec() == QDialog.Accepted:
            # 获取对话框中的完整规则数据
            new_rule = dialog.get_rule_data()
            new_rule['enabled'] = True  # 确保新规则默认启用
            
            # 初始化数据结构
            if not self.rules_data:
                self.rules_data = {'rules': [
                    {'group': 'FindLink', 'rule': []},
                    {'group': 'excludeLink', 'rule': []}
                ]}
            elif 'rules' not in self.rules_data:
                self.rules_data['rules'] = [
                    {'group': 'FindLink', 'rule': []},
                    {'group': 'excludeLink', 'rule': []}
                ]
            elif not self.rules_data['rules']:
                self.rules_data['rules'] = [
                    {'group': 'FindLink', 'rule': []},
                    {'group': 'excludeLink', 'rule': []}
                ]
            
            # 根据规则类型添加到对应分组
            target_group = 'FindLink' if new_rule['type'] == 'findLink' else 'excludeLink'
            for group in self.rules_data['rules']:
                if group.get('group') == target_group:
                    if 'rule' not in group:
                        group['rule'] = []
                    group['rule'].append(new_rule)
                    break
            
            # 编译正则表达式
            try:
                self.patterns[new_rule['name']] = re.compile(
                    new_rule['f_regex'], 
                    0 if new_rule['sensitive'] else re.IGNORECASE
                )
            except re.error as e:
                self.status_changed_signal.emit(f"正则表达式编译错误 ({new_rule['name']}): {str(e)}")
            
            # 更新表格
            self.update_rules_tables()
            
            # 标记规则已修改并立即保存
            self.rules_modified = True
            self.save_rules()
            
    def edit_rule(self, row, table):
        """编辑规则"""
        if row < 0 or row >= table.rowCount():
            return
            
        rule_item = table.item(row, 0)
        if not rule_item:
            return
            
        item_data = rule_item.data(Qt.UserRole)
        if not item_data:
            return
            
        data = item_data.get('data')
        if not data:
            return
            
        dialog = RuleEditDialog(self)
        
        # 设置当前规则数据
        dialog.name_edit.setText(data.get('name', ''))
        dialog.regex_edit.setText(data.get('f_regex', ''))
        dialog.case_sensitive_checkbox.setChecked(data.get('sensitive', True))
        
        # 设置规则类型
        rule_type = data.get('type', 'findLink')
        if rule_type == 'findLink':
            dialog.findlink_radio.setChecked(True)
        else:
            dialog.excludelink_radio.setChecked(True)
        
        if dialog.exec() == QDialog.Accepted:
            # 获取对话框中的完整规则数据
            updated_rule = dialog.get_rule_data()
            updated_rule['enabled'] = data.get('enabled', True)  # 保持原有启用状态
            
            old_name = data.get('name')
            old_type = data.get('type', 'findLink')
            new_type = updated_rule['type']
            
            # 从原分组中删除规则
            for group in self.rules_data['rules']:
                if group.get('group') == ('FindLink' if old_type == 'findLink' else 'excludeLink'):
                    if 'rule' in group:
                        for i, rule in enumerate(group['rule']):
                            if rule.get('name') == old_name:
                                del group['rule'][i]
                                break
            
            # 添加到新分组
            target_group = 'FindLink' if new_type == 'findLink' else 'excludeLink'
            for group in self.rules_data['rules']:
                if group.get('group') == target_group:
                    if 'rule' not in group:
                        group['rule'] = []
                    group['rule'].append(updated_rule)
                    break
            
            # 更新编译后的正则表达式
            try:
                # 删除旧的模式
                if old_name in self.patterns:
                    del self.patterns[old_name]
                
                # 添加新的模式
                self.patterns[updated_rule['name']] = re.compile(
                    updated_rule['f_regex'], 
                    0 if updated_rule['sensitive'] else re.IGNORECASE
                )
            except re.error as e:
                self.status_changed_signal.emit(f"正则表达式编译错误 ({updated_rule['name']}): {str(e)}")
            
            # 更新表格
            self.update_rules_tables()
            
            # 标记规则已修改并立即保存
            self.rules_modified = True
            self.save_rules()
            
    def delete_rule(self, row, table, save=True, confirm=True):
        """删除规则"""
        if row < 0 or row >= table.rowCount():
            return
            
        rule_item = table.item(row, 0)
        if not rule_item:
            return
            
        item_data = rule_item.data(Qt.UserRole)
        if not item_data:
            return
            
        data = item_data.get('data')
        if not data:
            return
            
        rule_name = data.get('name')
        
        # 确认删除
        if confirm:
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除规则 '{rule_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # 从规则数据中删除规则
        for group in self.rules_data['rules']:
            if 'rule' in group:
                for i, rule in enumerate(group['rule']):
                    if rule.get('name') == rule_name:
                        del group['rule'][i]
                        break
        
        # 删除编译后的正则表达式
        if rule_name in self.patterns:
            del self.patterns[rule_name]
        
        # 更新表格
        self.update_rules_tables()
        
        # 标记规则已修改，需要保存
        self.rules_modified = True
        
        # 如果需要，保存规则
        if save and self.rules_modified:
            self.save_rules()

    def save_rules(self):
        """保存规则到rules.yml文件"""
        try:
            # 确保数据结构正确
            if not self.rules_data:
                self.rules_data = {'rules': []}
            if 'rules' not in self.rules_data:
                self.rules_data['rules'] = []
            
            # 确保有FindLink和excludeLink分组
            findlink_group = next((g for g in self.rules_data['rules'] if g.get('group') == 'FindLink'), None)
            excludelink_group = next((g for g in self.rules_data['rules'] if g.get('group') == 'excludeLink'), None)
            
            if not findlink_group:
                findlink_group = {'group': 'FindLink', 'rule': []}
                self.rules_data['rules'].append(findlink_group)
            if not excludelink_group:
                excludelink_group = {'group': 'excludeLink', 'rule': []}
                self.rules_data['rules'].append(excludelink_group)
            
            # 保存到文件
            with open(self.rules_file, 'w', encoding='utf-8') as file:
                yaml.dump(self.rules_data, file, allow_unicode=True)
            
            self.rules_modified = False
            self.status_changed_signal.emit("规则保存成功")
        except Exception as e:
            self.status_changed_signal.emit(f"规则保存失败: {str(e)}")
