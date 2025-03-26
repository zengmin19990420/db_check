import sys
import os
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
                             QPushButton, QWidget, QLineEdit, QLabel, QComboBox, QMessageBox,
                             QFileDialog, QTabWidget, QSplitter, QTextEdit, QHeaderView, QMenu)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QCursor

class PandasModel(QAbstractTableModel):
    """用于在QTableView中显示pandas DataFrame的模型"""
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None

class SQLQueryTab(QWidget):
    """SQL查询执行标签页"""
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # SQL查询输入区域
        self.query_edit = QTextEdit()
        self.query_edit.setPlaceholderText("输入SQL查询语句...")
        layout.addWidget(self.query_edit)
        
        # 执行按钮
        btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("执行查询")
        self.execute_btn.clicked.connect(self.execute_query)
        btn_layout.addWidget(self.execute_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 结果显示区域
        self.result_table = QTableView()
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)
        
        self.setLayout(layout)
    
    def execute_query(self):
        query = self.query_edit.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入SQL查询语句")
            return
        
        try:
            # 执行查询
            df = pd.read_sql_query(query, self.db_connection)
            model = PandasModel(df)
            self.result_table.setModel(model)
            QMessageBox.information(self, "成功", f"查询成功，返回 {len(df)} 条记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询执行失败: {str(e)}")

class TableViewTab(QWidget):
    """表格查看标签页"""
    def __init__(self, db_connection, table_name):
        super().__init__()
        self.db_connection = db_connection
        self.table_name = table_name
        self.initUI()
        self.load_data()

    def initUI(self):
        layout = QVBoxLayout()
        
        # 表格信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"表名: {self.table_name}"))
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_data)
        info_layout.addWidget(self.refresh_btn)
        
        # 添加数据库操作按钮
        self.db_ops_btn = QPushButton("数据库操作")
        self.db_ops_btn.clicked.connect(self.show_db_operations_menu)
        info_layout.addWidget(self.db_ops_btn)
        
        # 添加数据操作按钮
        self.data_ops_btn = QPushButton("数据操作")
        self.data_ops_btn.clicked.connect(self.show_data_operations_menu)
        info_layout.addWidget(self.data_ops_btn)
        
        # 添加导入导出按钮
        self.import_export_btn = QPushButton("导入/导出")
        self.import_export_btn.clicked.connect(self.show_import_export_menu)
        info_layout.addWidget(self.import_export_btn)
        
        # 添加表结构查看按钮
        self.structure_btn = QPushButton("表结构")
        self.structure_btn.clicked.connect(self.show_table_structure)
        info_layout.addWidget(self.structure_btn)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 表格视图
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table_view)
        
        self.setLayout(layout)
    
    def load_data(self):
        try:
            query = f"SELECT * FROM {self.table_name}"
            df = pd.read_sql_query(query, self.db_connection)
            model = PandasModel(df)
            self.table_view.setModel(model)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载表格数据失败: {str(e)}")
    
    def show_table_structure(self):
        """显示表结构信息"""
        try:
            # 创建一个新的对话框显示表结构
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"表结构: {self.table_name}")
            dialog.resize(600, 400)
            layout = QVBoxLayout()
            
            # 创建标签页
            tab_widget = QTabWidget()
            
            # 获取表的列信息
            cursor = self.db_connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            # 创建列信息标签页
            columns_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
            columns_df.columns = ['ID', '列名', '数据类型', '非空', '默认值', '主键']
            columns_table = QTableView()
            columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            columns_table.setModel(PandasModel(columns_df))
            tab_widget.addTab(columns_table, "列信息")
            
            # 获取索引信息
            cursor.execute(f"PRAGMA index_list({self.table_name})")
            indexes = cursor.fetchall()
            
            if indexes:
                indexes_df = pd.DataFrame(indexes, columns=['seq', 'name', 'unique', 'origin', 'partial'])
                indexes_df.columns = ['序号', '索引名', '唯一', '来源', '部分索引']
                indexes_table = QTableView()
                indexes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                indexes_table.setModel(PandasModel(indexes_df))
                tab_widget.addTab(indexes_table, "索引信息")
                
                # 获取每个索引的详细信息
                for index in indexes:
                    index_name = index[1]
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    index_info = cursor.fetchall()
                    if index_info:
                        index_info_df = pd.DataFrame(index_info, columns=['seqno', 'cid', 'name'])
                        index_info_df.columns = ['序号', '列ID', '列名']
                        index_info_table = QTableView()
                        index_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                        index_info_table.setModel(PandasModel(index_info_df))
                        tab_widget.addTab(index_info_table, f"索引详情: {index_name}")
            
            # 获取外键信息
            cursor.execute(f"PRAGMA foreign_key_list({self.table_name})")
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                fk_df = pd.DataFrame(foreign_keys, columns=['id', 'seq', 'table', 'from', 'to', 'on_update', 'on_delete', 'match'])
                fk_df.columns = ['ID', '序号', '引用表', '本表列', '引用列', '更新行为', '删除行为', '匹配方式']
                fk_table = QTableView()
                fk_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                fk_table.setModel(PandasModel(fk_df))
                tab_widget.addTab(fk_table, "外键信息")
            
            # 获取表的创建SQL
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{self.table_name}'")
            create_sql = cursor.fetchone()[0]
            
            if create_sql:
                sql_text = QTextEdit()
                sql_text.setReadOnly(True)
                sql_text.setPlainText(create_sql)
                tab_widget.addTab(sql_text, "创建SQL")
            
            layout.addWidget(tab_widget)
            dialog.setLayout(layout)
            dialog.exec_()            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取表结构失败: {str(e)}")
    
    def show_context_menu(self, position):
        menu = QMenu()
        export_action = menu.addAction("导出数据")
        export_action.triggered.connect(self.export_data)
        menu.exec_(QCursor.pos())
    
    def show_db_operations_menu(self):
        """显示数据库操作菜单"""
        menu = QMenu(self)
        create_table_action = menu.addAction("创建表")
        create_table_action.triggered.connect(self.create_table)
        
        delete_table_action = menu.addAction("删除表")
        delete_table_action.triggered.connect(self.delete_table)
        
        alter_table_action = menu.addAction("修改表结构")
        alter_table_action.triggered.connect(self.alter_table)
        
        menu.exec_(QCursor.pos())
    
    def show_data_operations_menu(self):
        """显示数据操作菜单"""
        menu = QMenu(self)
        add_record_action = menu.addAction("添加记录")
        add_record_action.triggered.connect(self.add_record)
        
        edit_record_action = menu.addAction("编辑记录")
        edit_record_action.triggered.connect(self.edit_record)
        
        delete_record_action = menu.addAction("删除记录")
        delete_record_action.triggered.connect(self.delete_record)
        
        menu.exec_(QCursor.pos())
    
    def show_import_export_menu(self):
        """显示导入导出菜单"""
        menu = QMenu(self)
        import_csv_action = menu.addAction("从CSV导入")
        import_csv_action.triggered.connect(self.import_from_csv)
        
        import_excel_action = menu.addAction("从Excel导入")
        import_excel_action.triggered.connect(self.import_from_excel)
        
        export_csv_action = menu.addAction("导出为CSV")
        export_csv_action.triggered.connect(lambda: self.export_data(format="csv"))
        
        export_excel_action = menu.addAction("导出为Excel")
        export_excel_action.triggered.connect(lambda: self.export_data(format="xlsx"))
        
        menu.exec_(QCursor.pos())
    
    def export_data(self, format=None):
        if format:
            # 如果指定了格式，直接使用该格式
            if format == "csv":
                file_filter = "CSV文件 (*.csv)"
                default_suffix = ".csv"
            elif format == "xlsx":
                file_filter = "Excel文件 (*.xlsx)"
                default_suffix = ".xlsx"
        else:
            # 否则让用户选择格式
            file_filter = "CSV文件 (*.csv);;Excel文件 (*.xlsx)"
            default_suffix = ""
        
        file_path, selected_filter = QFileDialog.getSaveFileName(self, "导出数据", "", file_filter)
        if not file_path:
            return
        
        # 确保文件有正确的扩展名
        if format and not file_path.endswith(default_suffix):
            file_path += default_suffix
        
        try:
            query = f"SELECT * FROM {self.table_name}"
            df = pd.read_sql_query(query, self.db_connection)
            
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "成功", f"数据已成功导出到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据失败: {str(e)}")
    
    def create_table(self):
        """创建新表"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("创建新表")
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        table_name_edit = QLineEdit()
        form_layout.addRow("表名:", table_name_edit)
        
        columns_edit = QTextEdit()
        columns_edit.setPlaceholderText("每行输入一列，格式: 列名 数据类型\n例如:\nid INTEGER PRIMARY KEY\nname TEXT\nage INTEGER")
        form_layout.addRow("列定义:", columns_edit)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            table_name = table_name_edit.text().strip()
            columns_text = columns_edit.toPlainText().strip()
            
            if not table_name or not columns_text:
                QMessageBox.warning(self, "警告", "表名和列定义不能为空")
                return
            
            try:
                # 构建CREATE TABLE语句
                create_sql = f"CREATE TABLE {table_name} (\n"
                columns = [line.strip() for line in columns_text.split('\n') if line.strip()]
                create_sql += ",\n".join(columns)
                create_sql += "\n)"
                
                # 执行创建表操作
                cursor = self.db_connection.cursor()
                cursor.execute(create_sql)
                self.db_connection.commit()
                
                # 更新表格下拉框
                parent = self.parent()
                while parent and not isinstance(parent, DatabaseManager):
                    parent = parent.parent()
                
                if parent and isinstance(parent, DatabaseManager):
                    # 更新表格下拉框
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    parent.table_combo.clear()
                    parent.table_combo.addItems([table[0] for table in tables])
                
                QMessageBox.information(self, "成功", f"表 {table_name} 创建成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建表失败: {str(e)}")
    
    def delete_table(self):
        """删除当前表"""
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除表 {self.table_name} 吗？此操作不可撤销！",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(f"DROP TABLE {self.table_name}")
                self.db_connection.commit()
                
                # 更新表格下拉框并关闭当前标签页
                parent = self.parent()
                while parent and not isinstance(parent, DatabaseManager):
                    parent = parent.parent()
                
                if parent and isinstance(parent, DatabaseManager):
                    # 更新表格下拉框
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    parent.table_combo.clear()
                    parent.table_combo.addItems([table[0] for table in tables])
                    
                    # 关闭当前标签页
                    index = parent.tab_widget.indexOf(self)
                    if index >= 0:
                        parent.tab_widget.removeTab(index)
                
                QMessageBox.information(self, "成功", f"表 {self.table_name} 已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除表失败: {str(e)}")
    
    def alter_table(self):
        """修改表结构"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout, QRadioButton, QGroupBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("修改表结构")
        layout = QVBoxLayout()
        
        # 选项组
        option_group = QGroupBox("选择操作")
        option_layout = QVBoxLayout()
        
        add_column_radio = QRadioButton("添加列")
        add_column_radio.setChecked(True)
        option_layout.addWidget(add_column_radio)
        
        rename_table_radio = QRadioButton("重命名表")
        option_layout.addWidget(rename_table_radio)
        
        option_group.setLayout(option_layout)
        layout.addWidget(option_group)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 添加列的输入框
        column_name_edit = QLineEdit()
        form_layout.addRow("列名:", column_name_edit)
        
        column_type_edit = QLineEdit()
        column_type_edit.setPlaceholderText("例如: TEXT, INTEGER, REAL等")
        form_layout.addRow("数据类型:", column_type_edit)
        
        # 重命名表的输入框
        new_table_name_edit = QLineEdit()
        form_layout.addRow("新表名:", new_table_name_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                cursor = self.db_connection.cursor()
                
                if add_column_radio.isChecked():
                    # 添加列
                    column_name = column_name_edit.text().strip()
                    column_type = column_type_edit.text().strip()
                    
                    if not column_name or not column_type:
                        QMessageBox.warning(self, "警告", "列名和数据类型不能为空")
                        return
                    
                    alter_sql = f"ALTER TABLE {self.table_name} ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    self.db_connection.commit()
                    
                    # 刷新表格数据
                    self.load_data()
                    QMessageBox.information(self, "成功", f"已添加列 {column_name}")
                else:
                    # 重命名表
                    new_table_name = new_table_name_edit.text().strip()
                    
                    if not new_table_name:
                        QMessageBox.warning(self, "警告", "新表名不能为空")
                        return
                    
                    alter_sql = f"ALTER TABLE {self.table_name} RENAME TO {new_table_name}"
                    cursor.execute(alter_sql)
                    self.db_connection.commit()
                    
                    # 更新标签页标题
                    parent = self.parent()
                    while parent and not isinstance(parent, DatabaseManager):
                        parent = parent.parent()
                    
                    if parent and isinstance(parent, DatabaseManager):
                        # 更新表格下拉框
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        parent.table_combo.clear()
                        parent.table_combo.addItems([table[0] for table in tables])
                        
                        # 更新标签页标题
                        index = parent.tab_widget.indexOf(self)
                        if index >= 0:
                            parent.tab_widget.setTabText(index, new_table_name)
                    
                    # 更新当前表名
                    self.table_name = new_table_name
                    QMessageBox.information(self, "成功", f"表已重命名为 {new_table_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"修改表结构失败: {str(e)}")
    
    def add_record(self):
        """添加记录到表中"""
        try:
            # 获取表结构
            cursor = self.db_connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            # 创建添加记录对话框
            from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"添加记录到 {self.table_name}")
            layout = QVBoxLayout()
            
            form_layout = QFormLayout()
            field_inputs = {}
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                # 根据列类型创建适当的输入控件
                if col_type.upper() in ('INTEGER', 'REAL', 'NUMERIC'):
                    input_widget = QLineEdit()
                    input_widget.setPlaceholderText(f"输入 {col_type}")
                elif col_type.upper() == 'BOOLEAN':
                    input_widget = QComboBox()
                    input_widget.addItems(['True', 'False'])
                else:  # TEXT, BLOB, etc.
                    input_widget = QLineEdit()
                
                form_layout.addRow(f"{col_name}:", input_widget)
                field_inputs[col_name] = input_widget
            
            layout.addLayout(form_layout)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # 收集输入的值
                values = {}
                for col_name, input_widget in field_inputs.items():
                    if isinstance(input_widget, QComboBox):
                        values[col_name] = input_widget.currentText()
                    else:
                        values[col_name] = input_widget.text()
                
                # 构建INSERT语句
                columns_str = ", ".join(values.keys())
                placeholders = ", ".join(["?" for _ in values])
                insert_sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                
                # 执行插入操作
                cursor.execute(insert_sql, list(values.values()))
                self.db_connection.commit()
                
                # 刷新表格数据
                self.load_data()
                QMessageBox.information(self, "成功", "记录添加成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加记录失败: {str(e)}")
    
    def edit_record(self):
        """编辑选中的记录"""
        # 获取选中的行
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "警告", "请先选择要编辑的记录")
            return
        
        # 获取选中行的第一行
        row = selected_indexes[0].row()
        
        try:
            # 获取表结构
            cursor = self.db_connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            # 获取主键列（如果有）
            primary_key_col = None
            for col in columns:
                if col[5] > 0:  # 第6列表示是否为主键
                    primary_key_col = col[1]
                    break
            
            # 获取当前行的数据
            model = self.table_view.model()
            row_data = {}
            for col_idx, col in enumerate([col[1] for col in columns]):
                value = model.data(model.index(row, col_idx), Qt.DisplayRole)
                row_data[col] = value
            
            # 创建编辑记录对话框
            from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"编辑记录")
            layout = QVBoxLayout()
            
            form_layout = QFormLayout()
            field_inputs = {}
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                # 根据列类型创建适当的输入控件
                if col_type.upper() in ('INTEGER', 'REAL', 'NUMERIC'):
                    input_widget = QLineEdit(row_data.get(col_name, ""))
                elif col_type.upper() == 'BOOLEAN':
                    input_widget = QComboBox()
                    input_widget.addItems(['True', 'False'])
                    input_widget.setCurrentText(row_data.get(col_name, "False"))
                else:  # TEXT, BLOB, etc.
                    input_widget = QLineEdit(row_data.get(col_name, ""))
                
                form_layout.addRow(f"{col_name}:", input_widget)
                field_inputs[col_name] = input_widget
                
                # 如果是主键，禁止编辑
                if col_name == primary_key_col:
                    input_widget.setReadOnly(True)
            
            layout.addLayout(form_layout)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # 收集输入的值
                new_values = {}
                for col_name, input_widget in field_inputs.items():
                    if isinstance(input_widget, QComboBox):
                        new_values[col_name] = input_widget.currentText()
                    else:
                        new_values[col_name] = input_widget.text()
                
                # 构建UPDATE语句
                set_clause = ", ".join([f"{col} = ?" for col in new_values.keys()])
                
                # 构建WHERE子句
                if primary_key_col:
                    where_clause = f"{primary_key_col} = ?"
                    params = list(new_values.values()) + [row_data[primary_key_col]]
                else:
                    # 如果没有主键，使用所有列作为条件
                    where_conditions = []
                    params = []
                    for col in columns:
                        col_name = col[1]
                        where_conditions.append(f"{col_name} = ?")
                        params.append(row_data[col_name])
                    where_clause = " AND ".join(where_conditions)
                    params = list(new_values.values()) + params
                
                update_sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
                
                # 执行更新操作
                cursor.execute(update_sql, params)
                self.db_connection.commit()
                
                # 刷新表格数据
                self.load_data()
                QMessageBox.information(self, "成功", "记录更新成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新记录失败: {str(e)}")
    
    def delete_record(self):
        """删除选中的记录"""
        # 获取选中的行
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "警告", "请先选择要删除的记录")
            return
        
        # 获取选中的所有不同行
        rows = set(index.row() for index in selected_indexes)
        
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除选中的 {len(rows)} 条记录吗？此操作不可撤销！",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 获取表结构
                cursor = self.db_connection.cursor()
                cursor.execute(f"PRAGMA table_info({self.table_name})")
                columns = cursor.fetchall()
                
                # 获取主键列（如果有）
                primary_key_col = None
                for col in columns:
                    if col[5] > 0:  # 第6列表示是否为主键
                        primary_key_col = col[1]
                        break
                
                # 获取当前选中行的数据
                model = self.table_view.model()
                deleted_count = 0
                
                for row in sorted(rows, reverse=True):  # 从后向前删除，避免索引变化
                    if primary_key_col:
                        # 如果有主键，使用主键作为条件
                        pk_col_idx = [col[1] for col in columns].index(primary_key_col)
                        pk_value = model.data(model.index(row, pk_col_idx), Qt.DisplayRole)
                        delete_sql = f"DELETE FROM {self.table_name} WHERE {primary_key_col} = ?"
                        cursor.execute(delete_sql, (pk_value,))
                    else:
                        # 如果没有主键，使用所有列作为条件
                        where_conditions = []
                        params = []
                        for col_idx, col in enumerate([col[1] for col in columns]):
                            value = model.data(model.index(row, col_idx), Qt.DisplayRole)
                            where_conditions.append(f"{col} = ?")
                            params.append(value)
                        
                        where_clause = " AND ".join(where_conditions)
                        delete_sql = f"DELETE FROM {self.table_name} WHERE {where_clause}"
                        cursor.execute(delete_sql, params)
                    
                    deleted_count += 1
                
                self.db_connection.commit()
                
                # 刷新表格数据
                self.load_data()
                QMessageBox.information(self, "成功", f"成功删除 {deleted_count} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除记录失败: {str(e)}")
    
    def import_from_csv(self):
        """从CSV文件导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", "", "CSV文件 (*.csv)")
        if not file_path:
            return
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 获取表结构
            cursor = self.db_connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 检查CSV文件的列是否与表结构匹配
            csv_columns = df.columns.tolist()
            if not all(col in columns for col in csv_columns):
                QMessageBox.warning(self, "警告", "CSV文件的列与表结构不匹配")
                return
            
            # 确认导入
            reply = QMessageBox.question(self, "确认导入", 
                                        f"确定要导入 {len(df)} 条记录吗？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 构建INSERT语句
                columns_str = ", ".join(csv_columns)
                placeholders = ", ".join(["?" for _ in csv_columns])
                insert_sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                
                # 执行批量插入
                for _, row in df.iterrows():
                    values = [row[col] for col in csv_columns]
                    cursor.execute(insert_sql, values)
                
                self.db_connection.commit()
                
                # 刷新表格数据
                self.load_data()
                QMessageBox.information(self, "成功", f"成功导入 {len(df)} 条记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入数据失败: {str(e)}")
    
    def import_from_excel(self):
        """从Excel文件导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)")
        if not file_path:
            return
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 获取表结构
            cursor = self.db_connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 检查Excel文件的列是否与表结构匹配
            excel_columns = df.columns.tolist()
            if not all(col in columns for col in excel_columns):
                QMessageBox.warning(self, "警告", "Excel文件的列与表结构不匹配")
                return
            
            # 确认导入
            reply = QMessageBox.question(self, "确认导入", 
                                        f"确定要导入 {len(df)} 条记录吗？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 构建INSERT语句
                columns_str = ", ".join(excel_columns)
                placeholders = ", ".join(["?" for _ in excel_columns])
                insert_sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                
                # 执行批量插入
                for _, row in df.iterrows():
                    values = [row[col] for col in excel_columns]
                    cursor.execute(insert_sql, values)
                
                self.db_connection.commit()
                
                # 刷新表格数据
                self.load_data()
                QMessageBox.information(self, "成功", f"成功导入 {len(df)} 条记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入数据失败: {str(e)}")

class DatabaseManager(QMainWindow):
    """数据库管理器主窗口"""
    def __init__(self):
        super().__init__()
        self.db_connection = None
        self.db_path = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("SQLite数据库管理器")
        self.setGeometry(100, 100, 1000, 600)
        
        # 主布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 数据库连接区域
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("数据库文件:"))
        
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        conn_layout.addWidget(self.db_path_edit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_database)
        conn_layout.addWidget(self.browse_btn)
        
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.connect_database)
        conn_layout.addWidget(self.connect_btn)
        
        main_layout.addLayout(conn_layout)
        
        # 表格选择区域
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("选择表格:"))
        
        self.table_combo = QComboBox()
        self.table_combo.setEnabled(False)
        self.table_combo.currentIndexChanged.connect(self.open_table)
        table_layout.addWidget(self.table_combo)
        
        main_layout.addLayout(table_layout)
        
        # 标签页区域
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)
        
        self.setCentralWidget(central_widget)
        
        # 添加SQL查询标签页
        self.sql_tab = None
    
    def browse_database(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择SQLite数据库文件", "", "SQLite数据库文件 (*.db *.sqlite *.db3);;所有文件 (*)")
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def connect_database(self):
        db_path = self.db_path_edit.text()
        if not db_path:
            QMessageBox.warning(self, "警告", "请选择数据库文件")
            return
        
        try:
            # 关闭现有连接
            if self.db_connection is not None:
                self.db_connection.close()
            
            # 建立新连接
            self.db_connection = sqlite3.connect(db_path)
            self.db_path = db_path
            
            # 获取表格列表
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # 更新表格下拉框
            self.table_combo.clear()
            self.table_combo.addItems([table[0] for table in tables])
            self.table_combo.setEnabled(True)
            
            # 关闭所有标签页
            self.tab_widget.clear()
            
            # 添加SQL查询标签页
            self.sql_tab = SQLQueryTab(self.db_connection)
            self.tab_widget.addTab(self.sql_tab, "SQL查询")
            
            QMessageBox.information(self, "成功", f"成功连接到数据库: {db_path}\n发现 {len(tables)} 个表格")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接数据库失败: {str(e)}")
    
    def open_table(self, index):
        if index < 0 or self.db_connection is None:
            return
        
        table_name = self.table_combo.currentText()
        
        # 检查是否已经打开了该表格
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == table_name:
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 创建新的表格标签页
        table_tab = TableViewTab(self.db_connection, table_name)
        self.tab_widget.addTab(table_tab, table_name)
        self.tab_widget.setCurrentWidget(table_tab)
    
    def close_tab(self, index):
        # 不关闭SQL查询标签页
        if self.tab_widget.widget(index) == self.sql_tab:
            return
        
        self.tab_widget.removeTab(index)

def main():
    app = QApplication(sys.argv)
    window = DatabaseManager()
    window.show()
    
    # 如果有命令行参数，尝试自动连接到数据库
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.db_path_edit.setText(sys.argv[1])
        window.connect_database()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()