# Copyright (C) 2025 ka5fxt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys
import os
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont

class TrainThread(QThread):
    update_log = pyqtSignal(str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=self.cwd,
                shell=True if os.name == 'nt' else False
            )
            for line in iter(self.process.stdout.readline, ''):
                self.update_log.emit(line.strip())
            self.process.wait()
            if self.process.returncode != 0:
                self.error_occurred.emit(f"训练异常结束，错误码：{self.process.returncode}")
            else:
                self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"启动训练失败：{str(e)}")

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
        self.setGeometry(200, 200, 1000, 800)
        self.setup_fonts()
        self.create_widgets()
        self.create_layout()
        self.load_settings()

    def setup_fonts(self):
        self.font = QFont()
        self.font.setPointSize(10)

    def create_widgets(self):
        # 路径配置部分
        self.yolov5_root_input = self.create_path_input("YOLOv5根目录", is_file=False)
        self.venv_python_input = self.create_path_input("Python环境路径", is_file=True)
        self.data_yaml_input = self.create_path_input("数据集配置文件", is_file=True, 
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

    def create_path_input(self, label, is_file=False, filter=None):
        container = QWidget()
        layout = QHBoxLayout(container)
        line_edit = QLineEdit()
        line_edit.setFont(self.font)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(
            lambda: self.select_path(line_edit, is_file, filter=filter)
        )
        
        layout.addWidget(line_edit)
        layout.addWidget(browse_btn)
        return (QGroupBox(label), container)

    def create_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左侧配置面板
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)

        # 添加路径配置
        for widget in [self.yolov5_root_input, 
                      self.venv_python_input,
                      self.data_yaml_input]:
            config_layout.addWidget(widget[0])
            config_layout.addWidget(widget[1])

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
        paths_to_check = [
            (self.yolov5_root_input[1].findChild(QLineEdit), 
                ("YOLOv5根目录", lambda p: (p/"train.py").exists())),
            (self.venv_python_input[1].findChild(QLineEdit), 
                ("Python环境路径", lambda p: p.exists() and "python" in p.name.lower())),
            (self.data_yaml_input[1].findChild(QLineEdit), 
                ("数据集配置文件", lambda p: p.exists() and p.suffix in ['.yaml', '.yml']))
        ]

        for (input_widget, (name, validator)) in paths_to_check:
            path = Path(input_widget.text())
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
        yolov5_root = Path(self.yolov5_root_input[1].findChild(QLineEdit).text())
        venv_python = Path(self.venv_python_input[1].findChild(QLineEdit).text())
        data_yaml = Path(self.data_yaml_input[1].findChild(QLineEdit).text())

        command = [
            str(venv_python.resolve()),
            str((yolov5_root / "train.py").resolve()),
            '--img', '640',
            '--batch', str(self.batch_size.value()),
            '--epochs', str(self.epochs.value()),
            '--data', str(data_yaml.resolve()),  # 直接使用选择的YAML文件
            '--cfg', str((yolov5_root / "models" / f"{self.model_select.currentText()}.yaml").resolve()),
            '--weights', str((yolov5_root / f"{self.model_select.currentText()}.pt").resolve())
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
            self.train_thread.process.terminate()
            self.train_thread.wait()
            self.log_output.append("训练已中止")
            self.training_finished()

    def training_finished(self):
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

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

    def save_settings(self):
        settings = QSettings("YOLOv5Trainer", "Config")
        settings.setValue("yolov5_root", self.yolov5_root_input[1].findChild(QLineEdit).text())
        settings.setValue("venv_python", self.venv_python_input[1].findChild(QLineEdit).text())
        settings.setValue("data_yaml", self.data_yaml_input[1].findChild(QLineEdit).text())

    def load_settings(self):
        settings = QSettings("YOLOv5Trainer", "Config")
        self.yolov5_root_input[1].findChild(QLineEdit).setText(settings.value("yolov5_root", ""))
        self.venv_python_input[1].findChild(QLineEdit).setText(settings.value("venv_python", ""))
        self.data_yaml_input[1].findChild(QLineEdit).setText(settings.value("data_yaml", ""))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YOLOTrainer()
    window.show()
    sys.exit(app.exec_())