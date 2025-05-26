# Copyright (C) 2025 cea56
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
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal

class TrainThread(QThread):
    update_log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None

    def run(self):
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        for line in iter(self.process.stdout.readline, ''):
            self.update_log.emit(line.strip())
        self.process.wait()
        self.finished.emit()

class YOLOTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.train_thread = None

    def initUI(self):
        self.setWindowTitle('YOLOv5 Training GUI')
        self.setGeometry(100, 100, 800, 600)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # 左侧配置面板
        config_panel = QGroupBox("训练配置")
        config_layout = QFormLayout()
        
        # 数据集选择
        self.dataset_input = QLineEdit()
        self.dataset_btn = QPushButton("选择数据集")
        self.dataset_btn.clicked.connect(self.select_dataset)
        dataset_layout = QHBoxLayout()
        dataset_layout.addWidget(self.dataset_input)
        dataset_layout.addWidget(self.dataset_btn)

        # 模型选择
        self.model_select = QComboBox()
        self.model_select.addItems(['yolov5s', 'yolov5m', 'yolov5l', 'yolov5x'])

        # 训练参数
        self.epochs = QSpinBox()
        self.epochs.setRange(1, 1000)
        self.epochs.setValue(300)
        
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 64)
        self.batch_size.setValue(16)

        # 添加配置项
        config_layout.addRow("数据集路径:", dataset_layout)
        config_layout.addRow("模型选择:", self.model_select)
        config_layout.addRow("训练轮次:", self.epochs)
        config_layout.addRow("批大小:", self.batch_size)
        
        # 训练按钮
        self.train_btn = QPushButton("开始训练")
        self.train_btn.clicked.connect(self.start_training)
        self.stop_btn = QPushButton("停止训练")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)

        config_layout.addRow(self.train_btn)
        config_layout.addRow(self.stop_btn)
        config_panel.setLayout(config_layout)

        # 右侧日志面板
        log_panel = QGroupBox("训练日志")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_output)
        log_panel.setLayout(log_layout)

        layout.addWidget(config_panel, 1)
        layout.addWidget(log_panel, 2)

    def select_dataset(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据集目录")
        if path:
            self.dataset_input.setText(path)

    def start_training(self):
        if not self.dataset_input.text():
            QMessageBox.warning(self, "错误", "请先选择数据集路径")
            return

        # 构建训练命令
        command = [
            'python', 'train.py',
            '--img', '640',
            '--batch', str(self.batch_size.value()),
            '--epochs', str(self.epochs.value()),
            '--data', f'{self.dataset_input.text()}/data.yaml',
            '--cfg', f'models/{self.model_select.currentText()}.yaml',
            '--weights', f'{self.model_select.currentText()}.pt'
        ]

        self.train_thread = TrainThread(command)
        self.train_thread.update_log.connect(self.update_log)
        self.train_thread.finished.connect(self.training_finished)
        self.train_thread.start()

        self.train_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_training(self):
        if self.train_thread and self.train_thread.isRunning():
            self.train_thread.process.terminate()
            self.train_thread.wait()
            self.log_output.append("训练已中止")

    def training_finished(self):
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_output.append("训练完成！")

    def update_log(self, text):
        self.log_output.append(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YOLOTrainer()
    window.show()
    sys.exit(app.exec_())