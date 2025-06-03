import sys
import os
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QGridLayout, QScrollArea, QFileDialog, QMessageBox,
    QSizePolicy, QListWidgetItem, QToolBar, QStatusBar, QFormLayout, 
    QLineEdit, QGroupBox, QInputDialog, QFrame, QStyleFactory, QMenu
)
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QAction, QColor, QPalette, QBrush,
    QPainter, QCursor
)
from PySide6.QtCore import Qt, QSize, QDir, QDateTime, QPoint, QRect

class DatabaseManager:
    """数据库管理类，负责图片集和图片的存储"""
    def __init__(self, db_path="album_manager.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_database()
    
    def initialize_database(self):
        """初始化数据库和表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建图片集表
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            create_time TEXT NOT NULL,
            modify_time TEXT NOT NULL,
            notes TEXT DEFAULT ''
        )
        """)
        
        # 创建图片表
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            thumbnail BLOB,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            add_time TEXT NOT NULL,
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
        )
        """)
        
        self.conn.commit()
    
    def create_album(self, name, notes=""):
        """创建新图片集"""
        current_time = datetime.now().isoformat()
        try:
            self.cursor.execute("""
            INSERT INTO albums (name, create_time, modify_time, notes)
            VALUES (?, ?, ?, ?)
            """, (name, current_time, current_time, notes))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def delete_album(self, album_id):
        """删除图片集及其所有图片"""
        self.cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))
        self.cursor.execute("DELETE FROM images WHERE album_id = ?", (album_id,))
        self.conn.commit()
    
    def update_album_notes(self, album_id, notes):
        """更新图片集备注"""
        current_time = datetime.now().isoformat()
        self.cursor.execute("""
        UPDATE albums 
        SET notes = ?, modify_time = ?
        WHERE id = ?
        """, (notes, current_time, album_id))
        self.conn.commit()
    
    def get_all_albums(self):
        """获取所有图片集"""
        self.cursor.execute("SELECT id, name, create_time, modify_time, notes FROM albums")
        return self.cursor.fetchall()
    
    def get_album(self, album_id):
        """获取单个图片集信息"""
        self.cursor.execute("""
        SELECT id, name, create_time, modify_time, notes 
        FROM albums WHERE id = ?
        """, (album_id,))
        return self.cursor.fetchone()
    
    def add_image(self, album_id, file_path, thumbnail_data=None):
        """添加图片到图片集"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        add_time = datetime.now().isoformat()
        
        self.cursor.execute("""
        INSERT INTO images (album_id, file_path, thumbnail, file_name, file_size, add_time)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (album_id, file_path, thumbnail_data, file_name, file_size, add_time))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def delete_image(self, image_id):
        """删除图片"""
        self.cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        self.conn.commit()
    
    def get_images(self, album_id):
        """获取图片集的所有图片"""
        self.cursor.execute("""
        SELECT id, file_path, thumbnail, file_name, file_size, add_time 
        FROM images 
        WHERE album_id = ?
        """, (album_id,))
        return self.cursor.fetchall()
    
    def get_image_count(self, album_id):
        """获取图片集中的图片数量"""
        self.cursor.execute("SELECT COUNT(*) FROM images WHERE album_id = ?", (album_id,))
        return self.cursor.fetchone()[0]
    
    def update_album_modify_time(self, album_id):
        """更新图片集的修改时间"""
        current_time = datetime.now().isoformat()
        self.cursor.execute("""
        UPDATE albums 
        SET modify_time = ?
        WHERE id = ?
        """, (current_time, album_id))
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

class ThemeManager:
    """主题管理器，支持深色和浅色主题切换"""
    @staticmethod
    def apply_dark_theme(app):
        """应用深色主题"""
        palette = QPalette()
        
        # 基础颜色
        palette.setColor(QPalette.Window, QColor("#2c3e50"))
        palette.setColor(QPalette.WindowText, QColor("#ecf0f1"))
        palette.setColor(QPalette.Base, QColor("#34495e"))
        palette.setColor(QPalette.AlternateBase, QColor("#2c3e50"))
        palette.setColor(QPalette.ToolTipBase, QColor("#34495e"))
        palette.setColor(QPalette.ToolTipText, QColor("#ecf0f1"))
        palette.setColor(QPalette.Text, QColor("#ecf0f1"))
        palette.setColor(QPalette.Button, QColor("#34495e"))
        palette.setColor(QPalette.ButtonText, QColor("#ecf0f1"))
        palette.setColor(QPalette.BrightText, QColor("#e74c3c"))
        palette.setColor(QPalette.Link, QColor("#3498db"))
        palette.setColor(QPalette.Highlight, QColor("#3498db"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # 禁用状态颜色
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#bdc3c7"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#bdc3c7"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#bdc3c7"))
        
        app.setPalette(palette)
        
        app.setStyleSheet("""
            /* 主窗口 */
            QMainWindow {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            
            /* 按钮 */
            QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #3d566e;
                color: #7f8c8d;
            }
            
            /* 列表部件 */
            QListWidget {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #7f8c8d;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 3px;
            }
            
            /* 分组框 */
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                margin-top: 20px;
                padding-top: 10px;
                color: #ecf0f1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #ecf0f1;
            }
            
            /* 单行文本框 */
            QLineEdit {
                background-color: #3d566e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
            
            /* 标签 */
            QLabel {
                color: #ecf0f1;
            }
            
            /* 滚动区域 */
            QScrollArea {
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                background-color: #34495e;
            }
            
            /* 状态栏 */
            QStatusBar {
                background-color: #34495e;
                color: #ecf0f1;
                border-top: 1px solid #7f8c8d;
            }
            
            /* 工具栏 */
            QToolBar {
                background-color: #34495e;
                border-bottom: 1px solid #7f8c8d;
                spacing: 10px;
                padding: 5px;
            }
            
            /* 分隔线 */
            QFrame[frameShape="4"] { /* HLine */
                background-color: #7f8c8d;
            }
            
            /* 菜单 */
            QMenu {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            
            /* 工具按钮 */
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)

    @staticmethod
    def apply_light_theme(app):
        """应用浅色主题"""
        palette = QPalette()
        
        # 基础颜色
        palette.setColor(QPalette.Window, QColor("#f8f9fa"))
        palette.setColor(QPalette.WindowText, QColor("#212529"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f8f9fa"))
        palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
        palette.setColor(QPalette.ToolTipText, QColor("#212529"))
        palette.setColor(QPalette.Text, QColor("#212529"))
        palette.setColor(QPalette.Button, QColor("#e9ecef"))
        palette.setColor(QPalette.ButtonText, QColor("#212529"))
        palette.setColor(QPalette.BrightText, QColor("#dc3545"))
        palette.setColor(QPalette.Link, QColor("#0d6efd"))
        palette.setColor(QPalette.Highlight, QColor("#0d6efd"))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # 禁用状态颜色
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#6c757d"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#6c757d"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#6c757d"))
        
        app.setPalette(palette)
        
        app.setStyleSheet("""
            /* 主窗口 */
            QMainWindow {
                background-color: #f8f9fa;
                color: #212529;
            }
            
            /* 按钮 */
            QPushButton {
                background-color: #e9ecef;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0d6efd;
                color: white;
                border-color: #0d6efd;
            }
            QPushButton:pressed {
                background-color: #0b5ed7;
                border-color: #0b5ed7;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
            
            /* 列表部件 */
            QListWidget {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #0d6efd;
                color: white;
                border-radius: 3px;
            }
            
            /* 分组框 */
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #ced4da;
                border-radius: 5px;
                margin-top: 20px;
                padding-top: 10px;
                color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #212529;
            }
            
            /* 单行文本框 */
            QLineEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #86b7fe;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }
            
            /* 标签 */
            QLabel {
                color: #212529;
            }
            
            /* 滚动区域 */
            QScrollArea {
                border: 1px solid #ced4da;
                border-radius: 5px;
                background-color: #ffffff;
            }
            
            /* 状态栏 */
            QStatusBar {
                background-color: #e9ecef;
                color: #212529;
                border-top: 1px solid #ced4da;
            }
            
            /* 工具栏 */
            QToolBar {
                background-color: #e9ecef;
                border-bottom: 1px solid #ced4da;
                spacing: 10px;
                padding: 5px;
            }
            
            /* 分隔线 */
            QFrame[frameShape="4"] { /* HLine */
                background-color: #ced4da;
            }
            
            /* 菜单 */
            QMenu {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
            }
            QMenu::item:selected {
                background-color: #0d6efd;
                color: white;
            }
            
            /* 工具按钮 */
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #0d6efd;
                color: white;
                border-radius: 4px;
            }
        """)

class ImageWidget(QWidget):
    """自定义图片小部件，用于显示缩略图和文件名"""
    def __init__(self, image_id, file_path, file_name, parent=None):
        super().__init__(parent)
        self.image_id = image_id
        self.file_path = file_path
        self.file_name = file_name
        self.is_selected = False
        self.setFixedSize(180, 200)
        
        # 设置样式
        if parent and parent.is_dark_theme:
            self.setStyleSheet("""
                background-color: #3d566e;
                border: 1px solid #7f8c8d;
                border-radius: 8px;
            """)
        else:
            self.setStyleSheet("""
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 8px;
            """)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setFixedSize(170, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # 根据当前主题设置样式
        if parent and parent.is_dark_theme:
            self.image_label.setStyleSheet("""
                background-color: #34495e;
                border: 1px dashed #7f8c8d;
                border-radius: 6px;
            """)
        else:
            self.image_label.setStyleSheet("""
                background-color: #f8f9fa;
                border: 1px dashed #ced4da;
                border-radius: 6px;
            """)
        
        layout.addWidget(self.image_label)
        
        # 图片名称
        self.name_label = QLabel(file_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        
        # 根据当前主题设置样式
        if parent and parent.is_dark_theme:
            self.name_label.setStyleSheet("""
                color: #bdc3c7;
                font-size: 11px;
            """)
        else:
            self.name_label.setStyleSheet("""
                color: #6c757d;
                font-size: 11px;
            """)
        
        layout.addWidget(self.name_label)
        
        # 加载缩略图
        self.load_thumbnail()
    
    def load_thumbnail(self):
        """加载图片缩略图"""
        if os.path.exists(self.file_path):
            pixmap = QPixmap(self.file_path)
            if not pixmap.isNull():
                # 缩放图片以适应标签
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        self.is_selected = not self.is_selected
        self.update_border()
        super().mousePressEvent(event)
    
    def update_border(self):
        """更新边框以显示选中状态"""
        if self.is_selected:
            self.setStyleSheet("""
                background-color: #3d566e;
                border: 2px solid #3498db;
                border-radius: 8px;
            """)
        else:
            if self.parent() and self.parent().is_dark_theme:
                self.setStyleSheet("""
                    background-color: #3d566e;
                    border: 1px solid #7f8c8d;
                    border-radius: 8px;
                """)
            else:
                self.setStyleSheet("""
                    background-color: #ffffff;
                    border: 1px solid #ced4da;
                    border-radius: 8px;
                """)

class AlbumManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片集管理工具")
        self.setGeometry(100, 100, 1200, 800)
        self.current_album_id = None
        self.is_dark_theme = True  # 默认使用深色主题
        
        # 初始化数据库
        self.db = DatabaseManager()
        
        # 创建主部件和布局
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧相册列表区域
        self.album_list_widget = QWidget()
        self.album_list_widget.setFixedWidth(280)
        self.album_layout = QVBoxLayout(self.album_list_widget)
        self.album_layout.setContentsMargins(0, 0, 0, 0)
        self.album_layout.setSpacing(15)
        
        # 相册列表标题和操作按钮
        self.album_header = QWidget()
        self.album_header_layout = QHBoxLayout(self.album_header)
        self.album_label = QLabel("图片集")
        self.album_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.album_header_layout.addWidget(self.album_label)
        
        # 相册操作按钮
        self.add_album_btn = QPushButton()
        self.add_album_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_album_btn.setToolTip("新建图片集")
        self.add_album_btn.setFixedSize(32, 32)
        self.add_album_btn.setObjectName("addAlbumBtn")
        
        self.del_album_btn = QPushButton()
        self.del_album_btn.setIcon(QIcon.fromTheme("list-remove"))
        self.del_album_btn.setToolTip("删除图片集")
        self.del_album_btn.setFixedSize(32, 32)
        self.del_album_btn.setObjectName("delAlbumBtn")
        
        self.album_header_layout.addStretch()
        self.album_header_layout.addWidget(self.add_album_btn)
        self.album_header_layout.addWidget(self.del_album_btn)
        
        self.album_layout.addWidget(self.album_header)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setFixedHeight(1)
        self.album_layout.addWidget(separator)
        
        # 相册列表
        self.album_list = QListWidget()
        self.album_list.setMinimumHeight(400)
        self.album_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.album_list.customContextMenuRequested.connect(self.show_album_context_menu)
        self.album_layout.addWidget(self.album_list)
        
        # 右侧区域 - 分为上下两部分
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setSpacing(20)
        
        # 上部分 - 图片集详细信息
        self.info_panel = QGroupBox("图片集详细信息")
        
        self.info_layout = QFormLayout(self.info_panel)
        self.info_layout.setVerticalSpacing(15)
        self.info_layout.setHorizontalSpacing(20)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建时间
        self.create_time_label = QLabel("")
        self.info_layout.addRow(QLabel("创建时间:"), self.create_time_label)
        
        # 修改时间
        self.modify_time_label = QLabel("")
        self.info_layout.addRow(QLabel("修改时间:"), self.modify_time_label)
        
        # 图片数量
        self.image_count_label = QLabel("0")
        self.info_layout.addRow(QLabel("图片数量:"), self.image_count_label)
        
        # 备注
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("添加图片集备注...")
        self.info_layout.addRow(QLabel("备注:"), self.notes_edit)
        
        # 保存备注按钮
        self.save_notes_btn = QPushButton("保存备注")
        self.save_notes_btn.setFixedWidth(120)
        self.save_notes_btn.setObjectName("saveNotesBtn")
        self.info_layout.addRow("", self.save_notes_btn)
        
        self.right_layout.addWidget(self.info_panel)
        
        # 下部分 - 图片管理区域
        self.image_area = QWidget()
        self.image_layout = QVBoxLayout(self.image_area)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_layout.setSpacing(15)
        
        # 图片区域标题栏
        self.image_header = QWidget()
        self.header_layout = QHBoxLayout(self.image_header)
        self.current_album_label = QLabel("图片管理")
        self.current_album_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.current_album_label)
        
        # 图片操作按钮
        self.img_btn_layout = QHBoxLayout()
        self.img_btn_layout.setSpacing(15)
        
        self.add_image_btn = QPushButton("添加图片")
        self.add_image_btn.setIcon(QIcon.fromTheme("image-x-generic"))
        self.add_image_btn.setFixedHeight(36)
        self.add_image_btn.setObjectName("addImageBtn")
        
        self.del_image_btn = QPushButton("删除选中")
        self.del_image_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.del_image_btn.setFixedHeight(36)
        self.del_image_btn.setObjectName("delImageBtn")
        
        self.export_btn = QPushButton("导出图片集")
        self.export_btn.setIcon(QIcon.fromTheme("document-export"))
        self.export_btn.setFixedHeight(36)
        self.export_btn.setObjectName("exportBtn")
        
        self.img_btn_layout.addStretch()
        self.img_btn_layout.addWidget(self.add_image_btn)
        self.img_btn_layout.addWidget(self.del_image_btn)
        self.img_btn_layout.addWidget(self.export_btn)
        
        self.header_layout.addLayout(self.img_btn_layout)
        self.image_layout.addWidget(self.image_header)
        
        # 图片网格显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.image_layout.addWidget(self.scroll_area)
        
        self.right_layout.addWidget(self.image_area, 1)  # 设置伸缩因子为1，使图片区域占据更多空间
        
        # 添加左右区域到主布局
        self.main_layout.addWidget(self.album_list_widget)
        self.main_layout.addWidget(self.right_container, 1)  # 右侧区域可伸缩
        
        # 创建工具栏
        self.toolbar = self.addToolBar("工具栏")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(28, 28))
        
        self.import_action = QAction(QIcon.fromTheme("document-import"), "导入图片集", self)
        self.export_action = QAction(QIcon.fromTheme("document-export"), "导出图片集", self)
        self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "设置", self)
        self.help_action = QAction(QIcon.fromTheme("help-contents"), "帮助", self)
        self.theme_action = QAction(QIcon.fromTheme("color-management"), "切换主题", self)
        
        self.toolbar.addAction(self.import_action)
        self.toolbar.addAction(self.export_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settings_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.theme_action)
        self.toolbar.addAction(self.help_action)
        
        self.current_album_id = None  # 确保在加载相册前初始化

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 连接信号
        self.add_album_btn.clicked.connect(self.add_album)
        self.del_album_btn.clicked.connect(self.delete_album)
        self.album_list.itemClicked.connect(self.select_album)
        self.add_image_btn.clicked.connect(self.add_image)
        self.del_image_btn.clicked.connect(self.delete_image)
        self.save_notes_btn.clicked.connect(self.save_notes)
        self.theme_action.triggered.connect(self.toggle_theme)
        self.export_btn.clicked.connect(self.export_album)
        
        # 加载图片集
        self.load_albums()
        
        # 应用初始主题
        self.apply_current_theme()
        
        # 当前选中的图片ID列表
        self.selected_images = []
        
        # 当前选中的相册ID
        self.current_album_id = None

    def apply_current_theme(self):
        """应用当前选择的主题"""
        app = QApplication.instance()
        if self.is_dark_theme:
            ThemeManager.apply_dark_theme(app)
            self.status_bar.showMessage("已切换到深色主题", 3000)
        else:
            ThemeManager.apply_light_theme(app)
            self.status_bar.showMessage("已切换到浅色主题", 3000)
        
        # # 更新图片显示以匹配新主题
        # if self.current_album_id:
        #     self.show_album_images(self.current_album_id)
         # 只有当有选中的相册时才显示图片
        if hasattr(self, 'current_album_id') and self.current_album_id:
            self.show_album_images(self.current_album_id)

    def load_albums(self):
        """从数据库加载图片集"""
        self.album_list.clear()
        albums = self.db.get_all_albums()
        
        for album in albums:
            album_id, name, create_time, modify_time, notes = album
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, album_id)  # 存储相册ID
            self.album_list.addItem(item)
        
        # 默认选择第一个相册
        if self.album_list.count() > 0:
            self.album_list.setCurrentRow(0)
            self.select_album(self.album_list.currentItem())

    def show_album_images(self, album_id):
        """显示图片集中的图片"""
        # 清空现有图片
        self.selected_images = []
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 获取图片
        images = self.db.get_images(album_id)
        
        # 添加新图片
        for i, image in enumerate(images):
            image_id, file_path, _, file_name, _, _ = image
            image_widget = ImageWidget(image_id, file_path, file_name, self)
            self.grid_layout.addWidget(image_widget, i // 4, i % 4)

    def add_album(self):
        """添加新相册"""
        new_album, ok = QInputDialog.getText(
            self, "新建图片集", "请输入图片集名称:",
            QLineEdit.Normal, ""
        )
        
        if ok and new_album:
            # 创建新相册
            album_id = self.db.create_album(new_album)
            
            if album_id is None:
                QMessageBox.warning(self, "错误", "图片集名称已存在")
                return
            
            # 添加到列表
            item = QListWidgetItem(new_album)
            item.setData(Qt.UserRole, album_id)
            self.album_list.addItem(item)
            
            # 选择新创建的相册
            self.album_list.setCurrentItem(item)
            self.select_album(item)
            
            self.status_bar.showMessage(f"已创建图片集: {new_album}")

    def delete_album(self):
        """删除选中的相册"""
        if self.album_list.currentRow() < 0:
            QMessageBox.warning(self, "警告", "请先选择一个图片集")
            return
        
        item = self.album_list.currentItem()
        album_id = item.data(Qt.UserRole)
        album_name = item.text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除图片集 '{album_name}' 吗? 此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 从数据库删除
            self.db.delete_album(album_id)
            
            # 从列表删除
            row = self.album_list.currentRow()
            self.album_list.takeItem(row)
            self.status_bar.showMessage(f"已删除图片集: {album_name}")
            
            # 如果没有相册了，清空详情区域
            if self.album_list.count() == 0:
                self.current_album_label.setText("图片管理")
                self.create_time_label.setText("")
                self.modify_time_label.setText("")
                self.image_count_label.setText("0")
                self.notes_edit.setText("")
                # 清空图片区域
                for i in reversed(range(self.grid_layout.count())): 
                    widget = self.grid_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
            else:
                # 选择下一个相册
                if row >= self.album_list.count():
                    row = self.album_list.count() - 1
                if row >= 0:
                    self.album_list.setCurrentRow(row)
                    self.select_album(self.album_list.currentItem())

    def select_album(self, item):
        """选择相册并显示内容"""
        if not item:
            return

        # 获取相册ID
        album_id = item.data(Qt.UserRole)
        self.current_album_id = album_id
        
        # 获取相册信息
        album = self.db.get_album(album_id)
        if album:
            album_id, name, create_time, modify_time, notes = album
            
            # 更新详情面板
            self.create_time_label.setText(create_time)
            self.modify_time_label.setText(modify_time)
            image_count = self.db.get_image_count(album_id)
            self.image_count_label.setText(str(image_count))
            self.notes_edit.setText(notes)
            
            # 更新图片区域标题
            self.current_album_label.setText(f"图片管理 - {name}")
            
            # 显示图片
            self.show_album_images(album_id)
            
            self.status_bar.showMessage(f"已选择图片集: {name}")

    def add_image(self):
        """添加图片到当前相册"""
        if not self.current_album_id:
            QMessageBox.warning(self, "警告", "请先选择一个图片集")
            return
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", 
            QDir.homePath(), 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_paths:
            # 添加图片到数据库
            for file_path in file_paths:
                self.db.add_image(self.current_album_id, file_path)
            
            # 更新图片集修改时间
            self.db.update_album_modify_time(self.current_album_id)
            
            # 更新UI
            image_count = self.db.get_image_count(self.current_album_id)
            self.image_count_label.setText(str(image_count))
            self.status_bar.showMessage(f"已添加 {len(file_paths)} 张图片")
            
            # 刷新图片显示
            self.show_album_images(self.current_album_id)

    def delete_image(self):
        """删除选中的图片"""
        if not self.current_album_id:
            QMessageBox.warning(self, "警告", "请先选择一个图片集")
            return
        
        # 获取所有选中的图片
        selected_images = []
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ImageWidget) and widget.is_selected:
                selected_images.append(widget.image_id)
        
        if not selected_images:
            QMessageBox.warning(self, "警告", "请先选择要删除的图片")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_images)} 张图片吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 从数据库删除
            for image_id in selected_images:
                self.db.delete_image(image_id)
            
            # 更新图片集修改时间
            self.db.update_album_modify_time(self.current_album_id)
            
            # 更新UI
            image_count = self.db.get_image_count(self.current_album_id)
            self.image_count_label.setText(str(image_count))
            self.status_bar.showMessage(f"已删除 {len(selected_images)} 张图片")
            
            # 刷新图片显示
            self.show_album_images(self.current_album_id)

    def save_notes(self):
        """保存备注信息"""
        if not self.current_album_id:
            return
            
        # 更新数据库
        self.db.update_album_notes(self.current_album_id, self.notes_edit.text())
        
        # 更新修改时间
        album = self.db.get_album(self.current_album_id)
        if album:
            _, _, _, modify_time, _ = album
            self.modify_time_label.setText(modify_time)
        
        self.status_bar.showMessage("备注已保存", 3000)

    def toggle_theme(self):
        """切换主题"""
        # 切换主题状态
        self.is_dark_theme = not self.is_dark_theme
        
        # 应用新主题
        self.apply_current_theme()

    def export_album(self):
        """导出图片集"""
        if not self.current_album_id:
            QMessageBox.warning(self, "警告", "请先选择一个图片集")
            return
        
        # 获取相册名称
        album = self.db.get_album(self.current_album_id)
        if not album:
            return
        
        album_name = album[1]
        
        # 选择导出目录
        export_dir = QFileDialog.getExistingDirectory(
            self, 
            "选择导出目录", 
            QDir.homePath()
        )
        
        if not export_dir:
            return
        
        # 创建相册目录
        album_dir = os.path.join(export_dir, album_name)
        os.makedirs(album_dir, exist_ok=True)
        
        # 获取图片
        images = self.db.get_images(self.current_album_id)
        
        # 导出图片
        exported_count = 0
        for image in images:
            image_id, file_path, _, file_name, _, _ = image
            if os.path.exists(file_path):
                try:
                    # 复制文件到导出目录
                    import shutil
                    shutil.copy2(file_path, os.path.join(album_dir, file_name))
                    exported_count += 1
                except Exception as e:
                    print(f"导出图片失败: {e}")
        
        self.status_bar.showMessage(f"已导出 {exported_count}/{len(images)} 张图片到 {album_dir}", 5000)
        QMessageBox.information(
            self, 
            "导出完成", 
            f"已成功导出 {exported_count} 张图片到:\n{album_dir}"
        )

    def show_album_context_menu(self, position):
        """显示相册列表的右键菜单"""
        item = self.album_list.itemAt(position)
        if not item:
            return
        
        album_id = item.data(Qt.UserRole)
        album_name = item.text()
        
        menu = QMenu()
        
        # 重命名操作
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_album(album_id, album_name))
        
        # 导出操作
        export_action = QAction("导出图片集", self)
        export_action.triggered.connect(lambda: self.export_album())
        
        menu.addAction(rename_action)
        menu.addAction(export_action)
        
        # 显示菜单
        menu.exec_(self.album_list.mapToGlobal(position))

    def rename_album(self, album_id, old_name):
        """重命名相册"""
        new_name, ok = QInputDialog.getText(
            self, "重命名图片集", "请输入新名称:",
            QLineEdit.Normal, old_name
        )
        
        if ok and new_name and new_name != old_name:
            # 更新数据库
            current_time = datetime.now().isoformat()
            try:
                self.db.cursor.execute("""
                UPDATE albums 
                SET name = ?, modify_time = ?
                WHERE id = ?
                """, (new_name, current_time, album_id))
                self.db.conn.commit()
                
                # 更新列表
                item = self.album_list.currentItem()
                item.setText(new_name)
                
                # 更新标题
                self.current_album_label.setText(f"图片管理 - {new_name}")
                
                self.status_bar.showMessage(f"已重命名图片集为: {new_name}")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "错误", "图片集名称已存在")

    def closeEvent(self, event):
        """关闭应用时清理资源"""
        self.db.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle(QStyleFactory.create("Fusion"))
    
    window = AlbumManager()
    window.show()
    sys.exit(app.exec())