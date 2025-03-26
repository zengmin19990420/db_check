# SQLite数据库管理工具

这是一个基于PyQt5的SQLite数据库管理工具，提供了友好的图形界面来查看和操作SQLite数据库文件。

## 功能特点

- 连接并浏览SQLite数据库文件
- 查看数据库中的所有表格
- 执行自定义SQL查询
- 浏览表格数据
- 导出表格数据为CSV或Excel格式

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

运行主程序：

```bash
python db_manager.py
```

也可以直接指定数据库文件路径：

```bash
python db_manager.py path/to/your/database.db
```

## 使用说明

1. 点击"浏览..."按钮选择SQLite数据库文件
2. 点击"连接"按钮连接到数据库
3. 从下拉菜单中选择要查看的表格
4. 使用"SQL查询"标签页执行自定义SQL查询
5. 右键点击表格数据可以导出为CSV或Excel格式