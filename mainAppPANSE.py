try:
    import psutil
except:
    pass
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

import cv2
import os
import sys
from mainDesign import Ui_MainWindow
import json

config_file = "resources/config/config.json"
config_backup_file = "resources/config/config_backup.json"

# from cam_handler import cameraHandler
from cam_handler2 import cameraHandler
from functools import partial
from serial_handler import open_sr, close_sr, snd_sr


class ExampleApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.move(0, 0)
        self.config_js_data = None
        self.isDirectlyClose = False

        with open(config_file, "r") as file:
            self.config_js_data = json.load(file)

        with open(config_backup_file, "r") as file:
            self.config_js_backup = json.load(file)

        self.setWindowTitle("Onceptual Design Pvt. Ltd.")
        self.camHandler = cameraHandler(self)

        self.btn_inspect.clicked.connect(self.camHandler.inspect)

        self.btn_login.clicked.connect(lambda state, arg=self.btn_login: self.btnApplicationHandler(arg, state))
        self.btnTest.clicked.connect(lambda state, arg=self.btnTest: self.camHandler.btnToolHandler(arg, state))

        self.swView.setCurrentWidget(self.live_view)

        self.hs_trigger_timeout.valueChanged[int].connect(
            partial(self.camHandler.slider_handler_click, self.hs_trigger_timeout))
        self.hs_trigger_timeout.sliderReleased.connect(
            partial(self.camHandler.slider_handler_release, self.hs_trigger_timeout))

        self.hs_trigger_timeout.setRange(
            self.config_js_data["trigger_timeout"]["min"],
            self.config_js_data["trigger_timeout"]["max"])
        self.hs_trigger_timeout.setValue(self.config_js_data["trigger_timeout"]["val"])
        self.lb_trigger_timeout.setText(
            "trigger_timeout-" + str(self.config_js_data["trigger_timeout"]["val"]))
        #
        # for btn in self.gpSourceTools_0.children():
        #     btn.clicked.connect(lambda state, arg=btn: self.camHandler.btnToolHandler(arg, state))
        # for btn in self.gpSourceTools_1.children():
        #     btn.clicked.connect(lambda state, arg=btn: self.camHandler.btnToolHandler(arg, state))
        # for btn in self.gpSourceTools_2.children():
        #     btn.clicked.connect(lambda state, arg=btn: self.camHandler.btnToolHandler(arg, state))
        # for btn in self.gpCameraTools.children():
        #     btn.clicked.connect(lambda state, arg=btn: self.camHandler.btnToolHandler(arg, state))

        self.btnBackup.clicked.connect(self.get_Backup)
        self.btnReload.clicked.connect(self.get_Reload)
        self.btnReset.clicked.connect(lambda state, arg=self.btnReset: self.camHandler.btnToolHandler(arg, state))

        # open serial PORT for communication
        open_sr()

        # camera_0
        self.camera0 = "cam0"

        camera = self.camera0
        self.fmCamSample_0.hide()

        self.fm_prefix_cam0 = "fmCam0_"
        self.hs_prefix_cam0 = "hsCam0_"
        self.lb_prefix_cam0 = "lbCam0_"

        for index in range(0, len(self.config_js_data[camera]["settings"]), 1):
            fm_name = self.fm_prefix_cam0 + str(index)
            hs_name = self.hs_prefix_cam0 + str(index)
            lb_name = self.lb_prefix_cam0 + str(index)

            setattr(self, fm_name, QtGui.QFrame(self.sawcsCam_0))
            fm = getattr(self, fm_name)

            fm.setMinimumSize(QtCore.QSize(220, 100))
            fm.setMaximumSize(QtCore.QSize(220, 100))
            fm.setFrameShape(QtGui.QFrame.StyledPanel)
            fm.setFrameShadow(QtGui.QFrame.Raised)
            fm.setObjectName(_fromUtf8(fm_name))

            setattr(self, hs_name, QtGui.QSlider(fm))
            hs = getattr(self, hs_name)

            hs.setGeometry(QtCore.QRect(20, 20, 181, 29))
            hs.setOrientation(QtCore.Qt.Horizontal)
            hs.setObjectName(_fromUtf8(hs_name))

            setattr(self, lb_name, QtGui.QLabel(fm))
            lb = getattr(self, lb_name)

            lb.setGeometry(QtCore.QRect(30, 60, 171, 31))
            lb.setAlignment(QtCore.Qt.AlignCenter)
            lb.setObjectName(_fromUtf8(lb_name))

            self.gridLayout_8.addWidget(fm, index, 0, 1, 1)

            hs.valueChanged[int].connect(partial(self.camHandler.slider_handler_click, hs))
            hs.sliderReleased.connect(partial(self.camHandler.slider_handler_release, hs))
            hs.setRange(self.config_js_data[camera]["settings"][index]["min"],
                        self.config_js_data[camera]["settings"][index]["max"])
            hs.setValue(self.config_js_data[camera]["settings"][index]["val"])

            lb_text = self.config_js_data[camera]["settings"][index]["name"] + "-" + str(hs.value())
            lb.setText(lb_text)

        # camera_1
        self.camera1 = "cam1"
        camera = self.camera1
        self.fmCamSample_1.hide()
        self.fm_prefix_cam1 = "fmCam1_"
        self.hs_prefix_cam1 = "hsCam1_"
        self.lb_prefix_cam1 = "lbCam1_"

        for index in range(0, len(self.config_js_data[camera]["settings"]), 1):
            fm_name1 = self.fm_prefix_cam1 + str(index)
            hs_name1 = self.hs_prefix_cam1 + str(index)
            lb_name1 = self.lb_prefix_cam1 + str(index)

            setattr(self, fm_name1, QtGui.QFrame(self.sawcsCam_1))
            fm1 = getattr(self, fm_name1)

            fm1.setMinimumSize(QtCore.QSize(220, 100))
            fm1.setMaximumSize(QtCore.QSize(220, 100))
            fm1.setFrameShape(QtGui.QFrame.StyledPanel)
            fm1.setFrameShadow(QtGui.QFrame.Raised)
            fm1.setObjectName(_fromUtf8(fm_name1))

            setattr(self, hs_name1, QtGui.QSlider(fm1))
            hs1 = getattr(self, hs_name1)

            hs1.setGeometry(QtCore.QRect(20, 20, 181, 29))
            hs1.setOrientation(QtCore.Qt.Horizontal)
            hs1.setObjectName(_fromUtf8(hs_name1))

            setattr(self, lb_name1, QtGui.QLabel(fm1))
            lb1 = getattr(self, lb_name1)

            lb1.setGeometry(QtCore.QRect(30, 60, 171, 31))
            lb1.setAlignment(QtCore.Qt.AlignCenter)
            lb1.setObjectName(_fromUtf8(lb_name1))

            self.gl_setting_cam_1.addWidget(fm1, index, 0, 1, 1)

            hs1.valueChanged[int].connect(partial(self.camHandler.slider_handler_click, hs1))
            hs1.sliderReleased.connect(partial(self.camHandler.slider_handler_release, hs1))
            hs1.setRange(self.config_js_data[camera]["settings"][index]["min"],
                         self.config_js_data[camera]["settings"][index]["max"])
            hs1.setValue(self.config_js_data[camera]["settings"][index]["val"])

            lb_text = self.config_js_data[camera]["settings"][index]["name"] + "-" + str(hs1.value())
            lb1.setText(lb_text)
        # camera_2
        self.camera2 = "cam2"
        camera = self.camera2
        self.fmCamSample_2.hide()
        self.fm_prefix_cam2 = "fmCam2_"
        self.hs_prefix_cam2 = "hsCam2_"
        self.lb_prefix_cam2 = "lbCam2_"

        for index in range(0, len(self.config_js_data[camera]["settings"]), 1):
            fm_name2 = self.fm_prefix_cam2 + str(index)
            hs_name2 = self.hs_prefix_cam2 + str(index)
            lb_name2 = self.lb_prefix_cam2 + str(index)

            setattr(self, fm_name2, QtGui.QFrame(self.sawcsCam_2))
            fm2 = getattr(self, fm_name2)

            fm2.setMinimumSize(QtCore.QSize(220, 100))
            fm2.setMaximumSize(QtCore.QSize(220, 100))
            fm2.setFrameShape(QtGui.QFrame.StyledPanel)
            fm2.setFrameShadow(QtGui.QFrame.Raised)
            fm2.setObjectName(_fromUtf8(fm_name2))

            setattr(self, hs_name2, QtGui.QSlider(fm2))
            hs2 = getattr(self, hs_name2)

            hs2.setGeometry(QtCore.QRect(20, 20, 181, 29))
            hs2.setOrientation(QtCore.Qt.Horizontal)
            hs2.setObjectName(_fromUtf8(hs_name2))

            setattr(self, lb_name2, QtGui.QLabel(fm2))
            lb2 = getattr(self, lb_name2)

            lb2.setGeometry(QtCore.QRect(30, 60, 171, 31))
            lb2.setAlignment(QtCore.Qt.AlignCenter)
            lb2.setObjectName(_fromUtf8(lb_name2))

            self.gridLayout_10.addWidget(fm2, index, 0, 1, 1)

            hs2.valueChanged[int].connect(partial(self.camHandler.slider_handler_click, hs2))
            hs2.sliderReleased.connect(partial(self.camHandler.slider_handler_release, hs2))
            hs2.setRange(self.config_js_data[camera]["settings"][index]["min"],
                         self.config_js_data[camera]["settings"][index]["max"])
            hs2.setValue(self.config_js_data[camera]["settings"][index]["val"])

            lb_text = self.config_js_data[camera]["settings"][index]["name"] + "-" + str(hs2.value())
            lb2.setText(lb_text)

        self.login = True
        self.btn_login.setChecked(self.login)
        self.tabWidget.setCurrentIndex(0)

        # Login Unable

        if not self.login:
            self.tabWidget.setTabEnabled(1, False)

    def config_update(self, obj, key=None, val=None):
        print("updated > ", obj, val)
        if key is None:
            self.config_js_data[obj] = val
        else:
            self.config_js_data[obj][key] = val
        with open(config_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)

    def update_camera_setting(self, cam, index, par, val):
        self.config_js_data[cam]["settings"][index][par] = val

        with open(config_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)

    def get_Backup(self):
        with open(config_backup_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)
            print("backup updated")

    def get_Reload(self):
        with open(config_file, "w") as file:
            json.dump(self.config_js_backup, file, indent=4)
            print("backup reloaded")

    def showlogo_bycv(self, obj, img, path=None):
        if path:
            img = cv2.imread(img)
        frame = cv2.resize(img, (obj.size().width(), obj.size().height()))
        resizedImage = QImage(frame, frame.shape[1], frame.shape[0],
                              frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        obj.setPixmap(QPixmap.fromImage(resizedImage))

    def btnApplicationHandler(self, btn, state):
        btn_text = btn.text()
        if btn_text == "Test":
            print("test")
        else:
            if state:
                if btn_text == "Start":
                    btn.setText("Stop")
                    print("Start")

                elif btn_text == "login":
                    text, ok = QInputDialog.getText(self, 'admin login', 'Enter password:', QLineEdit.Password)

                    if ok:
                        if text == "shree":
                            QMessageBox.information(None, "Message", "login successfully")
                            btn.setChecked(True)
                            self.login = True
                            self.tabWidget.setTabEnabled(1, True)

                        else:
                            QMessageBox.warning(None, "Message", "login failed")
                            btn.setChecked(False)
                            self.login = False
                            self.tabWidget.setTabEnabled(1, False)
                            self.tabWidget.setCurrentIndex(0)
                            # self.sa_result_0.hide()
                            # self.sa_result_1.hide()
                            # self.sa_result_2.hide()
                            # self.lb_reportCard_1.hide()
            else:
                if btn_text == "Stop":
                    btn.setText("Start")
                    print("stop")
                elif btn_text == "login":
                    btn.setChecked(False)
                    self.login = False
                    self.tabWidget.setTabEnabled(1, False)
                    self.tabWidget.setCurrentIndex(0)

    def closeApp(self):
        def kill_proc(pid, including_parent=True):
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            if including_parent:
                parent.kill()

        me = os.getpid()
        kill_proc(me)

    def closeEvent(self, evnt):
        try:
            close_sr()
            self.closeApp()

        except:
            print("error")


def main():
    app = QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
