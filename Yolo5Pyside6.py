import sys
import os
import subprocess
import ctypes
import signal  # 补充导入signal模块以处理SIGINT
from pathlib import Path
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import QThread, Signal, QSettings, QTimer
from PySide6.QtGui import QFont

# Windows API定义
if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32

class TrainThread(QThread):
    update_log = Signal(str)
    finished = Signal()
    error_occurred = Signal(str)
    _running = True

    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.process = None
        self.pid = None

    def run(self):
        try:
            self._running = True
            # 创建独立的进程组（仅限Windows）
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=self.cwd,
                shell=True if os.name == 'nt' else False,
                creationflags=creationflags
            )
            self.pid = self.process.pid
            
            for line in iter(self.process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            self._running = True
            while self._running:
                line = self.process.stdout.readline()
                if not line:  # 管道关闭时退出循环
                    break
                self.update_log.emit(line.strip())
            self.process.wait()
            if self.process.returncode != 0:
                self.error_occurred.emit(f"训练异常结束，错误码：{self.process.returncode}")
            else:
                self.finished.emit()
        except Exception as e:
            if "I/O operation on closed file" in str(e):
                self.error_occurred.emit("训练已安全终止")
            else:
                self.error_occurred.emit(f"运行时错误: {str(e)}")
        finally:
            self._running = False

    def send_ctrl_c(self):
        """发送终止信号时同时停止读取循环"""
        self._running = False  # 停止读取循环
        start_time = time.time()
        if self.process and self.process.poll() is None:
            if os.name == 'nt':
                # Windows发送CTRL_C_EVENT
                kernel32.GenerateConsoleCtrlEvent(0, self.pid)
            else:
                # Linux/Mac发送SIGINT
                os.killpg(os.getpgid(self.pid), signal.SIGINT)
            self.wait(1000)  # 等待1秒
        #超时检测
        while self.process.poll() is None and (time.time() - start_time) < 3:
            time.sleep(0.1)
        if self.process.poll() is None:
            self.process.kill()
        

class YOLOTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_paths()
        self.initUI()
        self.train_thread = None

    def setup_paths(self):
        self.settings = {
            'yolov5_root': "",
            'venv_python': "",
            'data_yaml': ""
        }

    def initUI(self):
        self.setWindowTitle('YOLOv5 训练助手')
        self.setGeometry(200, 200, 1000, 600)
        self.setup_fonts()
        self.create_widgets()
        self.create_layout()
        self.load_settings()

    def setup_fonts(self):
        self.font = QFont()
        self.font.setPointSize(10)

    def create_widgets(self):
        # 路径配置部分
        self.yolov5_root_group = self.create_path_group("YOLOv5根目录", is_file=False)
        self.venv_python_group = self.create_path_group("Python环境路径", is_file=True)
        self.data_yaml_group = self.create_path_group("数据集配置文件", is_file=True, 
                                                     filter="YAML文件 (*.yaml *.yml)")
        # 训练参数部分
        self.model_select = QComboBox()
        self.model_select.addItems(['yolov5s', 'yolov5m', 'yolov5l', 'yolov5x'])
        self.model_select.setCurrentIndex(0)

        self.epochs = QSpinBox()
        self.epochs.setRange(1, 1000)
        self.epochs.setValue(100)

        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 64)
        self.batch_size.setValue(2)

        # 按钮部分
        self.train_btn = QPushButton("开始训练")
        self.train_btn.clicked.connect(self.start_training)
        self.stop_btn = QPushButton("停止训练")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)

        # 日志部分
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

    def create_path_group(self, title, is_file=False, filter=None):
        """创建包含路径输入框和浏览按钮的完整组"""
        group = QGroupBox(title)
        layout = QHBoxLayout(group)
        
        self.line_edit = QLineEdit()
        self.line_edit.setFont(self.font)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(
            lambda: self.select_path(self.line_edit, is_file, filter=filter))
        
        layout.addWidget(self.line_edit)
        layout.addWidget(self.browse_btn)
        return group

    def create_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左侧配置面板
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)

        # 添加路径配置组（直接添加组对象）
        config_layout.addWidget(self.yolov5_root_group)
        config_layout.addWidget(self.venv_python_group)
        config_layout.addWidget(self.data_yaml_group)


        # 添加训练参数
        params_group = QGroupBox("训练参数")
        params_layout = QFormLayout()
        params_layout.addRow("模型选择:", self.model_select)
        params_layout.addRow("训练轮次:", self.epochs)
        params_layout.addRow("批大小:", self.batch_size)
        params_group.setLayout(params_layout)
        config_layout.addWidget(params_group)

        # 添加按钮
        btn_group = QWidget()
        btn_layout = QHBoxLayout(btn_group)
        btn_layout.addWidget(self.train_btn)
        btn_layout.addWidget(self.stop_btn)
        config_layout.addWidget(btn_group)

        # 右侧日志面板
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)

        main_layout.addWidget(config_panel, 1)
        main_layout.addWidget(log_group, 2)

    def select_path(self, target_input, is_file, filter=None):
        current_path = target_input.text()
        initial_dir = str(Path.home())
        if current_path:
            initial_dir = str(Path(current_path).parent)

        if is_file:
            path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择文件", 
                initial_dir, 
                filter=filter or "All Files (*)"
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self, "选择目录", initial_dir
            )

        if path:
            target_input.setText(Path(path).as_posix())

    def validate_paths(self):
        errors = []
        # 修改后的路径检查方式
        path_checks = [
            (self.yolov5_root_group, 
             "YOLOv5根目录", 
             lambda p: (p/"train.py").exists()),
            (self.venv_python_group, 
             "Python环境路径", 
             lambda p: p.exists() and "python" in p.name.lower()),
            (self.data_yaml_group, 
             "数据集配置文件", 
             lambda p: p.exists() and p.suffix in ['.yaml', '.yml'])
        ]

        for group, name, validator in path_checks:
            path = Path(self.get_path_from_group(group))
            if not path.exists():
                errors.append(f"{name}不存在")
            elif not validator(path):
                errors.append(f"{name}无效")

        return errors

    def start_training(self):
        if errors := self.validate_paths():
            QMessageBox.critical(self, "配置错误", "\n".join(errors))
            return

        self.save_settings()
        yolov5_root = Path(self.get_path_from_group(self.yolov5_root_group))
        venv_python = Path(self.get_path_from_group(self.venv_python_group))
        data_yaml = Path(self.get_path_from_group(self.data_yaml_group))
        
        # 构造命令时需要验证模型文件路径
        model_file = yolov5_root / "models" / f"{self.model_select.currentText()}.yaml"
        if not model_file.exists():
            QMessageBox.critical(self, "错误", f"模型配置文件 {model_file} 不存在")
            return

        # 构造权重文件路径时需要验证
        weights_file = yolov5_root / f"{self.model_select.currentText()}.pt"
        if not weights_file.exists():
            QMessageBox.critical(self, "错误", f"预训练权重 {weights_file} 不存在")
            return
        command = [
            str(venv_python.resolve()),
            str((yolov5_root / "train.py").resolve()),
            '--img', '640',
            '--batch', str(self.batch_size.value()),
            '--epochs', str(self.epochs.value()),
            '--data', str(data_yaml.resolve()),  # 直接使用选择的YAML文件
            '--cfg', str(model_file.resolve()),
            '--weights', str(weights_file.resolve())
        ]

        self.log_output.clear()
        self.train_thread = TrainThread(command, cwd=yolov5_root)
        self.train_thread.update_log.connect(self.log_output.append)
        self.train_thread.finished.connect(self.training_finished)
        self.train_thread.error_occurred.connect(self.show_error)
        self.train_thread.start()

        self.train_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_training(self):
        if self.train_thread and self.train_thread.isRunning():
            self.stop_btn.setEnabled(False)
            self.log_output.append("正在发送停止信号...")
            
            # 使用异步操作避免阻塞
            QTimer.singleShot(0, self._safe_stop_training)

    def _safe_stop_training(self):
        """安全的停止训练流程"""
        try:
            # 发送Ctrl+C信号
            self.train_thread.send_ctrl_c()
            
            # 检查是否真正退出
            if self.train_thread.isRunning():
                self.log_output.append("进程未正常退出，尝试强制终止...")
                self.train_thread.process.kill()
                self.train_thread.wait(1000)
                
            self.training_finished()
        except Exception as e:
            self.log_output.append(f"停止失败: {str(e)}")
        finally:
            self.stop_btn.setEnabled(True)

    def training_finished(self):
        """清理资源"""
        if self.train_thread:
            try:
                if self.train_thread.process:
                    self.train_thread.process.stdout.close()
                    self.train_thread.process.stderr.close()
                    self.train_thread.process = None
            except:
                pass
            self.train_thread.quit()
            self.train_thread.wait()
            
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_output.append("训练已停止")

    def show_error(self, message):
        QMessageBox.critical(self, "训练错误", message)
        self.training_finished()

    def closeEvent(self, event):
        self.save_settings()
        if self.train_thread and self.train_thread.isRunning():
            reply = QMessageBox.question(
                self, '训练正在进行',
                "训练仍在运行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_training()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def get_path_from_group(self, group):
        """从路径组中获取输入框内容"""
        return group.findChild(QLineEdit).text()

    def save_settings(self):
        settings = QSettings("YOLOv5Trainer", "Config")
        settings.setValue("yolov5_root", self.get_path_from_group(self.yolov5_root_group))
        settings.setValue("venv_python", self.get_path_from_group(self.venv_python_group))
        settings.setValue("data_yaml", self.get_path_from_group(self.data_yaml_group))

    def load_settings(self):
        settings = QSettings("YOLOv5Trainer", "Config")
        self.yolov5_root_group.findChild(QLineEdit).setText(settings.value("yolov5_root", ""))
        self.venv_python_group.findChild(QLineEdit).setText(settings.value("venv_python", ""))
        self.data_yaml_group.findChild(QLineEdit).setText(settings.value("data_yaml", ""))
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YOLOTrainer()
    window.show()
    sys.exit(app.exec())