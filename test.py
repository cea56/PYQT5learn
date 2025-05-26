from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import *

def btn_click():
    print("you click the button")
    QMessageBox.information(dlg,'Notice','It is cold!',QMessageBox.Yes)

if __name__ == '__main__':
    app=QApplication([])
    CMyDlg,CDlg = uic.loadUiType("mydlg.ui")
    dlg=CDlg()
    myDlg=CMyDlg()
    print(type(myDlg))
    print(type(dlg))
    myDlg.setupUi(dlg)
    myDlg.pushButton.clicked.connect(btn_click)
    dlg.show()
    app.exec_()

