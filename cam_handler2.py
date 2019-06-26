# necessary Imports
import threading
from threading import Lock
from functools import partial
import serial
import time
from pypylon import pylon
import cv2
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import json
import glob
import numpy as np
from serial_handler import rcv_sr, snd_sr, open_sr

default_state = 0
config_file = "resources/config/config.json"
config_backup_file = "resources/config/config_backup.json"

''' Right Commands '''
lft_ok_bfr = "?02Z"
mdl_ok_bfr = "?03Z"
rht_ok_bfr = "?04Z"
lft_fail_bfr = "?05Z"
mdl_fail_bfr = "?06Z"
rht_fail_bfr = "?07Z"

lft_ok_aft = "?09Z"
mdl_ok_aft = "?10Z"
rht_ok_aft = "?11Z"
lft_fail_aft = "?12Z"
mdl_fail_aft = "?13Z"
rht_fail_aft = "?14Z"

''' Read Commands '''
left_befor = "b'?01Z'"
left_after = "b'?08Z'"
middle_befor = "b'?15Z'"
middle_after = "b'?16Z'"
right_befor = "b'?17Z'"
right_after = "b'?18Z'"


class CameraControl0(threading.Thread):

    def __init__(self, cam, *args):
        threading.Thread.__init__(self, *args)
        self.job_done = threading.Event()
        self.qt_object = QObject()
        self.camera_flag = False
        self.Live = False
        self.Image = not self.Live
        self.i = 0
        self.Test = False
        self.config_js_data = None
        self.cam_js = cam

        # read json file
        self.default = "Faulty"
        with open(config_file, "r") as file:
            self.config_js_data = json.load(file)

        # Loading json file
        self.serial_number = self.config_js_data[self.cam_js]["serial_number"]
        for index in range(len(self.config_js_data[self.cam_js]["settings"])):
            name = self.config_js_data[self.cam_js]["settings"][index]["name"]
            val = self.config_js_data[self.cam_js]["settings"][index]["val"]
            setattr(self, name, val)

        # creating pylon converter
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.factory = pylon.TlFactory.GetInstance()

        self.camera = None
        self.pfs_file_path = "resources/pfs"
        self.scan_device()

        # Serial Trigger Flags
        self.lft_camera_trigger_bfr = False
        self.lft_camera_trigger_aft = False
        self.cntr_camera_trigger_aft = False
        self.cntr_camera_trigger_bfr = False
        self.rht_camera_trigger_bfr = False
        self.rht_camera_trigger_aft = False

        # Count
        self.lhs_cnt = 0
        self.mdl_cnt = 0
        self.rhs_cnt = 0

        self.data = ""
        self.camera_index = self.config_js_data[self.cam_js]["camera_index"]

    def tool_trigger(self, btn_txt):
        print(self.serial_number, btn_txt)
        self.Live = False
        self.Image = False

        if btn_txt == "Live":
            self.Live = True
        elif btn_txt == "Image":
            self.Image = True

    def reset_device(self):

        self.camera.StopGrabbing()
        pfs_file = self.pfs_file_path + "/" + [x for x in os.listdir(self.pfs_file_path) if self.serial_number in x][0]
        print("loading parameter {}".format(pfs_file))
        self.camera.Open()
        pylon.FeaturePersistence.Load(pfs_file, self.camera.GetNodeMap(), True)
        self.camera.Close()

    def scan_device(self):
        device = [dev for dev in self.factory.EnumerateDevices() if dev.GetSerialNumber() == self.serial_number]
        if any(device):
            self.camera = pylon.InstantCamera(self.factory.GetInstance().CreateDevice(device[0]))
            self.camera_flag = True
            print("device {}  available".format(self.serial_number))
            self.reset_device()

        else:
            print("device {} not available".format(self.serial_number))
            self.camera_flag = False

    def camera_stop(self):
        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state", False)
        self.camera_flag = False

    def lhs_object_detection(self, frame):

        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        g_img = rgb_img[:, :, 1]
        ret, thresh = cv2.threshold(g_img, 130, 255, cv2.THRESH_OTSU)
        x, y, w, h = cv2.boundingRect(thresh)
        oimg_crop = frame[y:y + h, x:x + w]
        res = self.lhs_redpart_detection(frame, oimg_crop, x, y)

        return res

    def lhs_redpart_detection(self, frame, oimg_crop, x, y):

        x1, y1, w1, h1 = 450, 680, 160, 390
        sec1_crop = frame[y1:y1 + h1, x1:x1 + w1]
        YCrCb = cv2.cvtColor(sec1_crop, cv2.COLOR_BGR2YCrCb)

        r_img = YCrCb[:, :, 1]

        ret, sec1_bwcrop = cv2.threshold(r_img, 120, 250, cv2.THRESH_BINARY)

        cnts, hierarchy = cv2.findContours(sec1_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0

        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            # print(area)
            Tarea = Tarea + area
        print("LFT RED area", Tarea)
        if Tarea > self.lhs_red:  # 50000
            r = 1
            print("LFT Part1 Is Present")
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 8)

        else:
            print("LFT Part1 Is Missing")
            r = 0
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 8)

        final, res1 = self.lhs_sec2_detection(oimg_crop, x, y, r)
        final, res2 = self.lhs_section3_detection(x, y, final, r)
        final, res3 = self.lhs_rod_detection(x, y, final, r)

        if r == 0 or res1 == 0 or res2 == 0 or res3 == 0:
            return final, 0

        else:
            return final, 1

    def lhs_sec2_detection(self, oimg_crop, x, y, r):
        if r == 0:
            x2, y2, w2, h2 = x + 110, y + 700, 260, 300
        else:
            x2, y2, w2, h2 = x + 110, y + 700, 260, 300

        sec2_crop = oimg_crop[y2:y2 + h2, x2:x2 + w2]
        gray_img = cv2.cvtColor(sec2_crop, cv2.COLOR_BGR2GRAY)
        ret, sec2_bwcrop = cv2.threshold(gray_img, 63, 250, cv2.THRESH_BINARY_INV)
        cnts, hierarchy = cv2.findContours(sec2_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            # print(area)
            Tarea = Tarea + area
        print("LFT PART 2 total area", Tarea)

        if Tarea > self.lhs_sec2:  # 65000
            print("LFT PART 2 Is Present")
            cv2.rectangle(oimg_crop, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 4)
            return oimg_crop, 1

        else:
            print("LFT PART 2 Is Missing")
            cv2.rectangle(oimg_crop, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 4)
            return oimg_crop, 0

    def lhs_rod_detection(self, x, y, oimg_crop, r):
        # print("r = ", r)
        if r == 1:
            x3, y3, w3, h3 = x + 100, y + 250, 100, 550
        else:
            x3, y3, w3, h3 = x + 100, y + 250, 100, 550

        rod_crop = oimg_crop[y3:y3 + h3, x3:x3 + w3]
        YCrCb = cv2.cvtColor(rod_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        ret, rod_bwcrop = cv2.threshold(b_img, 90, 250, cv2.THRESH_BINARY)
        cnts, hierarchy = cv2.findContours(rod_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            # print(area)
            Tarea = Tarea + area

        print("LFT ROD AREA", Tarea)

        if Tarea > self.lhs_rod:  # 3000

            print("LFT Rod Is Present")
            cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 4)
            return oimg_crop, 1

        else:

            print("LFT Rod Is Missing")
            cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 0, 255), 4)

            return oimg_crop, 0

    def lhs_section3_detection(self, x, y, oimg_crop, r):
        if r == 1:
            x33, y33, w33, h33 = x + 220, y + 100, 320, 480
        else:
            x33, y33, w33, h33 = x + 220, y + 100, 320, 480
        sec3_crop = oimg_crop[y33:y33 + h33, x33:x33 + w33]
        YCrCb = cv2.cvtColor(sec3_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        ret, sec3_bwcrop = cv2.threshold(b_img, 30, 240, cv2.THRESH_BINARY_INV)

        cnts, hierarchy = cv2.findContours(sec3_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            Tarea = Tarea + area
        print("LFT Part3 area is ", Tarea)

        if Tarea > 35000:
            print("LFT Part3 Is Present")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 255, 0), 4)

            return oimg_crop, 1

        else:
            print("LFT Part3 Is Missing")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 0, 255), 4)

            return oimg_crop, 0

    def cntr_object_detection(self, frame):

        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)

        g_img = rgb_img[:, :, 1]

        ret, thresh = cv2.threshold(g_img, 130, 255, cv2.THRESH_OTSU)

        x, y, w, h = cv2.boundingRect(thresh)
        oimg_crop = frame[y:y + h, x:x + w]

        res = self.cntr_rod_detection(frame, oimg_crop, x, y)

        return res

    def cntr_rod_detection(self, frame, oimg_crop, x, y):

        x1, y1, w1, h1 = 365, 660, 170, 200
        sec1_crop = frame[y1:y1 + h1, x1:x1 + w1]
        YCrCb = cv2.cvtColor(sec1_crop, cv2.COLOR_BGR2YCrCb)

        r_img = YCrCb[:, :, 1]
        canny = cv2.Canny(r_img, 63, 120)
        det_cnt = cv2.countNonZero(canny)
        print("cntr rod det_cnt = ", det_cnt)
        if det_cnt > self.mdl_rod:  # 200
            r = 1
            print("Rod Is Present")
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 8)
            res = 1
        else:
            print("Rod Is Missing")
            r = 0
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 8)
            res = 0

        final, res3 = self.cntr_rev_det(frame)
        final, res1 = self.cntr_sec2_detection(final, x, y, r)
        final, res2 = self.cntr_section3_detection(x, y, final, r)

        if res == 0 or res1 == 0 or res2 == 0 or res3 == 0:
            return final, 0

        else:
            return final, 1

    def cntr_rev_det(self, frame):

        x1, y1, w1, h1 = 430, 770, 180, 250

        sec5_crop = frame[y1 - 20:y1 + h1 - 220, x1 - 120:x1 + w1 - 250]
        canny2 = cv2.Canny(sec5_crop, 83, 120)

        detected_cnt = cv2.countNonZero(canny2)
        print("detected_cnt = ", detected_cnt)
        if detected_cnt < self.mdl_rev:  # 150
            print("CNTR Placed part is ok")
            cv2.rectangle(frame, (x1 - 120, y1 - 20), (x1 + w1 - 250, y1 + h1 - 220), (0, 255, 0), 4)
            return frame, 1

        else:
            print("CNTR Placed part is Reverse")
            cv2.rectangle(frame, (x1 - 120, y1 - 20), (x1 + w1 - 250, y1 + h1 - 220), (0, 0, 255), 4)
            return frame, 0

    def cntr_sec2_detection(self, frame, x, y, r):
        if r == 0:
            x2, y2, w2, h2 = x + 150, y + 665, 190, 300
        else:
            x2, y2, w2, h2 = x + 150, y + 665, 190, 300

        sec2_crop = frame[y2:y2 + h2, x2:x2 + w2]

        gray_img = cv2.cvtColor(sec2_crop, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray_img, 63, 120)
        cnt_det = cv2.countNonZero(canny)

        print("CNTR sec2 detected count = ", cnt_det)

        if cnt_det > self.mdl_sec2:  # 6000
            print("PART 2 Is Present")

            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 4)
            return frame, 1

        else:
            print("CNTR PART 2 Is Missing")

            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 4)
            return frame, 0

    def cntr_section3_detection(self, x, y, oimg_crop, r):

        if r == 1:
            x33, y33, w33, h33 = x + 150, y + 210, 320, 460
        else:
            x33, y33, w33, h33 = x + 150, y + 210, 320, 460
        sec3_crop = oimg_crop[y33:y33 + h33, x33:x33 + w33]
        YCrCb = cv2.cvtColor(sec3_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        ret, sec3_bwcrop = cv2.threshold(b_img, 30, 240, cv2.THRESH_BINARY_INV)

        cnts, hierarchy = cv2.findContours(sec3_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])

            Tarea = Tarea + area
        print(Tarea)
        if Tarea > self.mdl_sec3:  # 5000
            print("CNTR Part3 Is Present")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 255, 0), 4)
            return oimg_crop, 1

        else:
            print("CNTR Part3 Is Missing")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 0, 255), 4)
            return oimg_crop, 0

    def rhs_object_detection(self, frame):
        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        g_img = rgb_img[:, :, 1]
        ret, thresh = cv2.threshold(g_img, 130, 255, cv2.THRESH_OTSU)
        x, y, w, h = cv2.boundingRect(thresh)
        oimg_crop = frame[y:y + h, x:x + w]
        final, res = self.rhs_redpart_detection(frame, oimg_crop, x, y)

        return final, res

    def rhs_redpart_detection(self, frame, oimg_crop, x, y):
        x1, y1, w1, h1 = 200, 620, 160, 450
        sec1_crop = frame[y1:y1 + h1, x1:x1 + w1]
        YCrCb = cv2.cvtColor(sec1_crop, cv2.COLOR_BGR2YCrCb)

        r_img = YCrCb[:, :, 1]
        ret, sec1_bwcrop = cv2.threshold(r_img, 120, 250, cv2.THRESH_BINARY)

        cnts, hierarchy = cv2.findContours(sec1_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            # print(area)
            Tarea = Tarea + area
        print("RHS Part1 area", Tarea)

        if Tarea > self.rhs_red:  # 25000
            r = 1
            print("RHS Part1 Is Present")
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 8)
            res = 1
        else:
            print("RHS Part1 Is Missing")
            r = 0
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 8)
            res = 0

        final, res3 = self.rhs_rod_detection(x, y, oimg_crop, r)
        final, res1 = self.rhs_sec2_detection(final, x, y, r)
        final, res2 = self.rhs_section3_detection(x, y, final, r)

        if res == 0 or res1 == 0 or res2 == 0 or res3 == 0:
            return final, 0
        else:
            return final, 1

    def rhs_rod_detection(self, x, y, oimg_crop, r):

        if r == 1:
            x3, y3, w3, h3 = x + 620, y + 250, 80, 600
        else:
            x3, y3, w3, h3 = x + 620, y + 250, 80, 600

        rod_crop = oimg_crop[y3:y3 + h3, x3:x3 + w3]
        YCrCb = cv2.cvtColor(rod_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        gray_img = cv2.cvtColor(rod_crop, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray_img, 83, 120)
        det_cnt = cv2.countNonZero(canny)
        print("rhs ROD det_cnt = ", det_cnt)

        if det_cnt > self.rhs_rod:  # 2000

            print("RHS Rod Is Present")
            cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 4)
            return oimg_crop, 1

        else:

            print("RHS Rod Is Missing")
            cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 0, 255), 4)

            return oimg_crop, 0

    def rhs_sec2_detection(self, frame, x, y, r):

        if r == 0:
            x2, y2, w2, h2 = x + 400, y + 720, 260, 290
        else:
            x2, y2, w2, h2 = x + 400, y + 720, 260, 290

        sec2_crop = frame[y2:y2 + h2, x2:x2 + w2]
        gray_img = cv2.cvtColor(sec2_crop, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray_img, 63, 120)
        det_cnt = cv2.countNonZero(canny)
        print("rhs sec2 det_cnt = ", det_cnt)

        if det_cnt > 2200:
            print("RHS PART 2 Is Present")
            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 4)
            return frame, 1

        else:
            print("RHS PART 2 Is Missing")
            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 4)
            return frame, 0

    def rhs_section3_detection(self, x, y, oimg_crop, r):
        if r == 1:
            x33, y33, w33, h33 = x + 300, y + 120, 320, 460
        else:
            x33, y33, w33, h33 = x + 300, y + 120, 320, 460

        sec3_crop = oimg_crop[y33:y33 + h33, x33:x33 + w33]
        YCrCb = cv2.cvtColor(sec3_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        ret, sec3_bwcrop = cv2.threshold(b_img, 30, 240, cv2.THRESH_BINARY_INV)
        cnts, hierarchy = cv2.findContours(sec3_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0

        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            Tarea = Tarea + area
        print("RHS Tarea", Tarea)
        if Tarea > 15000:
            print("RHS Part3 Is Present")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 255, 0), 4)
            return oimg_crop, 1

        else:
            print("RHS Part3 Is Missing")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 0, 255), 4)
            return oimg_crop, 0

    def left_camera_result(self, imgOrg):
        # if self.imgSet is None:
        imgSet = [imgOrg, imgOrg, imgOrg, imgOrg]
        msg = ""
        res = default_state

        final, res = self.lhs_object_detection(imgOrg)

        if not self.Test:
            # return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
            return final, res
        else:
            imgSet[0] = imgOrg
            msg = msg + " \nstatus-{}".format(res)
            return msg, imgSet

    def left_camera_result_aft(self, imgOrg):
        print("left_camera_result_aft Called")
        final = imgOrg

        return final, 1

    def center_camera_result_aft(self, imgOrg):
        print("center_result_aft Called")
        final = imgOrg

        return final, 1

    def right_camera_result_aft(self, imgOrg):
        print("right_camera_result_aft Called")
        final = imgOrg

        return final, 1

    def center_camera_result(self, imgOrg):
        # if self.imgSet is None:
        imgSet = [imgOrg, imgOrg, imgOrg, imgOrg]
        msg = ""
        res = default_state
        final, res = self.cntr_object_detection(imgOrg)

        if not self.Test:
            # return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
            return final, res
        else:
            imgSet[0] = imgOrg
            msg = msg + " \nstatus-{}".format(res)
            return msg, imgSet

    def right_camera_result(self, imgOrg):
        # if self.imgSet is None:
        imgSet = [imgOrg, imgOrg, imgOrg, imgOrg]
        msg = ""
        res = default_state

        final, res = self.rhs_object_detection(imgOrg)

        if not self.Test:
            # return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
            return final, res
        else:
            imgSet[0] = imgOrg
            msg = msg + " \nstatus-{}".format(res)
            return msg, imgSet

    def cam0_operation(self, img):
        try:

            working_image = img

            if self.lft_camera_trigger_bfr and self.Image:
                self.lft_camera_trigger_bfr = False

                # cv2.imwrite(
                #     "/home/shubham/PycharmProjects/Panse Auto_2/Panse Auto/Main Design/Images/cam0_{0}.jpg".format(self.i),
                #     working_image)
                # self.i += 1

                final, res = self.left_camera_result(working_image)
                self.lhs_cnt += 1
                if res == 0:
                    data = "FAULTY"
                    snd_sr(lft_fail_bfr)

                else:
                    data = "OK"
                    snd_sr(lft_ok_bfr)

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)
                # data for Display
                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "count", str(self.lhs_cnt))

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)
            if self.lft_camera_trigger_aft and self.Image:
                self.lft_camera_trigger_aft = False

                final, res = self.left_camera_result_aft(working_image)

                if res == 0:
                    data = "FAULTY"
                    snd_sr(lft_fail_aft)

                else:
                    data = "OK"
                    snd_sr(lft_ok_aft)

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)
                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)


        except Exception as e:
            print("cam0-->")
            print(e)

            working_image = cv2.resize(img, (0, 0), None, resize_threshold, resize_threshold)
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                         "frame", working_image)

    def cam1_operation(self, img):
        try:

            working_image = img

            if self.cntr_camera_trigger_bfr and self.Image:
                self.cntr_camera_trigger_bfr = False
                # cv2.imwrite(
                #     "/home/shubham/PycharmProjects/Panse Auto_2/Panse Auto/Main Design/Images/cam1_{0}.jpg".format(
                #         self.i),
                #     working_image)
                # self.i += 1

                final, res = self.center_camera_result(working_image)
                self.mdl_cnt += 1

                if res == 0:
                    data = "FAULTY"
                    snd_sr(mdl_fail_bfr)

                else:
                    data = "OK"
                    snd_sr(mdl_ok_bfr)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "count", str(self.mdl_cnt))

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)
            if self.cntr_camera_trigger_aft and self.Image:
                self.cntr_camera_trigger_aft = False

                final, res = self.center_camera_result_aft(working_image)

                if res == 0:
                    data = "FAULTY"
                    snd_sr(mdl_fail_aft)

                else:
                    data = "OK"
                    snd_sr(mdl_ok_aft)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)

        except Exception as e:
            print("cam_MIDDLE -->")
            print(e)
            resize_threshold = float("%.2f" % (self.resize / 100))
            working_image = cv2.resize(img, (0, 0), None, resize_threshold, resize_threshold)

            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                         "frame", working_image)

    def cam2_operation(self, img):
        try:

            working_image = img

            if self.rht_camera_trigger_bfr and self.Image:
                self.rht_camera_trigger_bfr = False
                # cv2.imwrite(
                #     "/home/shubham/PycharmProjects/Panse Auto_2/Panse Auto/Main Design/Images/cam2_{0}.jpg".format(
                #         self.i),
                #     working_image)
                # self.i += 1

                final, res = self.right_camera_result(working_image)
                self.rhs_cnt += 1

                if res == 0:
                    data = "FAULTY"
                    snd_sr(rht_fail_bfr)

                else:
                    data = "OK"
                    snd_sr(rht_ok_bfr)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "count", str(self.rhs_cnt))

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)
                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)
            if self.rht_camera_trigger_aft and self.Image:
                self.rht_camera_trigger_aft = False

                final, res = self.right_camera_result_aft(working_image)

                if res == 0:
                    data = "FAULTY"
                    snd_sr(rht_fail_aft)

                else:
                    data = "OK"
                    snd_sr(rht_ok_aft)

                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)),
                             self.serial_number,
                             "data", data)

                resize_threshold = float("%.2f" % (self.resize / 100))
                working_image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)
                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                             "frame", working_image)

        except Exception as e:
            print("cam_ RIGHT-->")
            print(e)

            resize_threshold = float("%.2f" % (self.resize / 100))
            working_image = cv2.resize(img, (0, 0), None, resize_threshold, resize_threshold)
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                         "frame", working_image)

    def get_frame_image(self):
        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            time.sleep(1)
            print(self.serial_number, " > grabing", self.camera.IsGrabbing())
            while self.camera.IsGrabbing() and self.Image:
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult)
                    frame = image.GetArray()

                    if self.serial_number == self.config_js_data["cam0"]["serial_number"]:
                        self.cam0_operation(frame)

                    if self.serial_number == self.config_js_data["cam1"]["serial_number"]:
                        self.cam1_operation(frame)

                    if self.serial_number == self.config_js_data["cam2"]["serial_number"]:
                        self.cam2_operation(frame)

                grabResult.Release()

            self.camera.StopGrabbing()
        except Exception as e:
            print("Error at {}\n".format(self.serial_number), e)
            self.camera_flag = False
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state",
                         False)

    def get_sframe(self):

        frame = cv2.imread(
            "/home/pankaj/Pankaj Projects/Panse-12-06-19/Final Code/Main Design/Images/cam0_{0}.jpg".format(0))
        frame1 = cv2.imread("/home/pankaj/Pankaj Projects/Panse-12-06-19/Final Code/Main Design/Images/cam1_0.jpg")
        frame2 = cv2.imread("/home/pankaj/Pankaj Projects/Panse-12-06-19/Final Code/Main Design/Images/cam2_0.jpg")

        try:

            if self.serial_number == self.config_js_data["cam0"]["serial_number"]:
                self.cam0_operation(frame)

            if self.serial_number == self.config_js_data["cam1"]["serial_number"]:
                self.cam1_operation(frame1)

            if self.serial_number == self.config_js_data["cam2"]["serial_number"]:
                self.cam2_operation(frame2)


        except Exception as e:
            print("Error at {}\n".format(self.serial_number), e)
            self.camera_flag = False

    def get_frame_live(self):
        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            time.sleep(1)
            print(self.serial_number, " > grabing", self.camera.IsGrabbing())
            while self.camera.IsGrabbing() and self.Live:
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult)
                    frame = image.GetArray()

                    if self.serial_number == self.config_js_data["cam0"]["serial_number"]:
                        self.cam0_operation(frame)

                    if self.serial_number == self.config_js_data["cam1"]["serial_number"]:
                        self.cam1_operation(frame)

                    if self.serial_number == self.config_js_data["cam2"]["serial_number"]:
                        self.cam2_operation(frame)

                grabResult.Release()

            self.camera.StopGrabbing()
        except Exception as e:
            print("timeout error\n", e)
            self.camera_flag = False
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state",
                         False)

    def end_job(self):
        self.job_done.set()

    def run(self):

        while not self.job_done.is_set():

            if self.Image:
                # self.get_sframe()
                if self.camera_flag:
                    self.get_frame_image()

                else:
                    self.scan_device()
                    time.sleep(5)


class cameraHandler(QMainWindow):

    def __init__(self, parent):

        super(cameraHandler, self).__init__(parent)

        # Thread 1
        cam = "cam0"
        self.cam0_serialNumber = self.parent().config_js_data[cam]["serial_number"]
        self.parent().btnCam_0.setText("CAM_{}".format(self.cam0_serialNumber))
        self.cam0 = CameraControl0(cam)
        QObject.connect(self.cam0.qt_object, SIGNAL('cam_{}'.format(self.cam0_serialNumber)), self.camera_handler)
        self.cam0.start()

        # Thread 2
        cam = "cam1"
        self.cam1_serialNumber = self.parent().config_js_data[cam]["serial_number"]
        self.parent().btnCam_1.setText("CAM_{}".format(self.cam1_serialNumber))
        self.cam1 = CameraControl0(cam)
        QObject.connect(self.cam1.qt_object, SIGNAL('cam_{}'.format(self.cam1_serialNumber)), self.camera_handler)
        self.cam1.start()

        # Thread 3
        cam = "cam2"
        self.cam2_serialNumber = self.parent().config_js_data[cam]["serial_number"]
        # self.parent().gbCam_2.setTitle("Camera - {}".format(self.cam2_serialNumber))
        self.parent().btnCam_2.setText("CAM_{}".format(self.cam2_serialNumber))
        self.cam2 = CameraControl0(cam)
        QObject.connect(self.cam2.qt_object, SIGNAL('cam_{}'.format(self.cam2_serialNumber)), self.camera_handler)
        self.cam2.start()

        self.active_cam = "cam0"
        self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_0)

        self.obj_string = 0
        self.tname = 1
        self.response = None


        self.trigger_timeout = self.parent().hs_trigger_timeout.value()
        self.timer_prefix = "timer_"

        self.total_timers = 15
        self.timers_control("set")

        for timer_index in range(1, self.total_timers + 1, 1):
            timer_name = self.timer_prefix + str(timer_index)
            setattr(self, timer_name, QTimer())
            timer = getattr(self, timer_name)
            timer.timeout.connect(partial(self.timeout_func, timer_index))
            # timer.setInterval(self.trigger_1_timeout)

        self.timer_object = QTimer()
        self.timer_object.timeout.connect(self.read_object)
        self.timer_object.setInterval(1)
        self.timer_object.start()

        self.trigger_timeout = self.parent().config_js_data["trigger_timeout"]["val"]

    def read_object(self):
        if self.tname == 14:
            self.tname = 1
        else:
            self.tname += 1
        self.obj_string = rcv_sr()

        if len(self.obj_string) > 0:
            timer_name = self.timer_prefix + str(self.tname)
            timer = getattr(self, timer_name)
            self.response = str(self.obj_string)
            print("Response is : ", self.response)
            print("timer active for : {0}".format(self.obj_string))
            timer.start(self.trigger_timeout)

    def timers_control(self, sig):
        if sig == "set":
            for timer_index in range(1, self.total_timers + 1, 1):
                timer_name = self.timer_prefix + str(timer_index)
                setattr(self, timer_name, QTimer())
                timer = getattr(self, timer_name)
                timer.timeout.connect(partial(self.timeout_func, timer_index))
        else:
            for timer_index in range(1, self.total_timers + 1, 1):
                timer_name = self.timer_prefix + str(timer_index)
                timer = getattr(self, timer_name)
                timer.stop()

    def timeout_func(self, timer_index):
        print("timer:{} deactive".format(timer_index))
        timer_name = self.timer_prefix + str(timer_index)

        r = [self.response[i:i + 4] for i in range(2, len(self.response), 4)]

        for j in r:

            if "b'" + str(j) + "'" == left_befor:
                print("matched_response left_befor: ", str(j))
                self.cam0.lft_camera_trigger_bfr = True

            elif "b'" + str(j) + "'" == left_after:
                self.cam0.lft_camera_trigger_aft = True
                print("matched_response left_after: ", str(j))

            elif "b'" + str(j) + "'" == middle_befor:
                self.cam1.cntr_camera_trigger_bfr = True
                print("matched_response middle_befor: ", str(j))

            elif "b'" + str(j) + "'" == middle_after:
                self.cam1.cntr_camera_trigger_aft = True
                print("matched_response middle_after: ", str(j))

            elif "b'" + str(j) + "'" == right_befor:
                self.cam2.rht_camera_trigger_bfr = True
                print("matched_response right_befor: ", str(j))

            elif "b'" + str(j) + "'" == right_after:
                self.cam2.rht_camera_trigger_aft = True
                print("matched_response right_after: ", str(j))

        # if self.response == left_befor:
        #     print("matched_response left_befor: ", self.response)
        #     self.cam0.lft_camera_trigger_bfr = True
        #
        # elif self.response == left_after:
        #     self.cam0.lft_camera_trigger_aft = True
        #     print("matched_response left_after: ", self.response)
        #
        # elif self.response == middle_befor:
        #     self.cam1.cntr_camera_trigger_bfr = True
        #     print("matched_response middle_befor: ", self.response)
        #
        # elif self.response == middle_after:
        #     self.cam1.cntr_camera_trigger_aft = True
        #     print("matched_response middle_after: ", self.response)
        #
        # elif self.response == right_befor:
        #     self.cam2.rht_camera_trigger_bfr = True
        #     print("matched_response: ", self.response)
        #
        # elif self.response == right_after:
        #     self.cam2.rht_camera_trigger_aft = True
        #     print("matched_response right_after: ", self.response)

        timer = getattr(self, timer_name)
        timer.stop()

    def btnToolHandler(self, btn, state):
        btn_text = btn.text()
        if "CAM" in btn_text:
            btn_name = btn_text.split('_')[1]
            if btn_name == self.cam0_serialNumber:
                self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_0)
                self.active_cam = "cam0"
            elif btn_name == self.cam1_serialNumber:
                self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_1)
                self.active_cam = "cam1"
            elif btn_name == self.cam2_serialNumber:
                self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_2)
                self.active_cam = "cam2"

        else:
            cam = getattr(self, self.active_cam)
            if btn_text == "Reset":
                self.parent().val_rhs.clear()
                # self.cam0.rhs_cnt = 0
                self.parent().val_mdl.clear()
                # self.cam1.mdl_cnt = 0
                self.parent().val_lhs.clear()
                # self.cam2.lhs_cnt = 0

                print("Count Set To Zero")

            elif btn_text == "Test":
                self.cam0.Test = False
                self.cam1.Test = False
                self.cam2.Test = False
                if btn.isChecked():
                    print("test on")
                    cam.Test = True
                    self.parent().swView.setCurrentWidget(self.parent().test_view)
                    self.parent().gpCameraTools.setEnabled(False)
                    self.cam0.Live = True
                    self.cam1.Live = True
                    self.cam2.Live = True
                else:
                    print("test off")
                    cam.Test = False
                    self.cam0.Live = False
                    self.cam1.Live = False
                    self.cam2.Live = False
                    self.parent().swView.setCurrentWidget(self.parent().live_view)
                    self.parent().gpCameraTools.setEnabled(True)

            else:
                cam.tool_trigger(btn_text)

    def slider_handler_click(self, slider, value):
        if "Cam" in slider.objectName():
            cam = slider.objectName()[2:6]
            if cam == "Cam0":
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam0 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_text = lb.text().split('-')[0] + "-" + str(value)
                lb.setText(lb_text)
            elif cam == "Cam1":
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam1 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_text = lb.text().split('-')[0] + "-" + str(value)
                lb.setText(lb_text)
            elif cam == "Cam2":
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam2 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_text = lb.text().split('-')[0] + "-" + str(value)
                lb.setText(lb_text)
        else:
            hs = slider.objectName()
            if hs == "hs_trigger_timeout":
                value = slider.value()
                self.parent().lb_trigger_timeout.setText("trigger_timeout-" + str(value))

    def slider_handler_release(self, slider):

        if "Cam" in slider.objectName():
            cam = slider.objectName()[2:6]
            if cam == "Cam0":
                value = slider.value()
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam0 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_par = lb.text().split('-')[0]
                lb_text = lb_par + "-" + str(value)
                lb.setText(lb_text)
                print("cam0", lb_text)
                self.parent().update_camera_setting("cam0", int(cam_id), "val", value)
                setattr(self.cam0, lb_par, value)

            elif cam == "Cam1":
                value = slider.value()
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam1 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_par = lb.text().split('-')[0]
                lb_text = lb_par + "-" + str(value)
                lb.setText(lb_text)
                print("cam1", lb_text)
                self.parent().update_camera_setting("cam1", int(cam_id), "val", value)
                setattr(self.cam1, lb_par, value)
            elif cam == "Cam2":
                value = slider.value()
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam2 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_par = lb.text().split('-')[0]
                lb_text = lb_par + "-" + str(value)
                lb.setText(lb_text)
                print("cam2", lb_text)
                self.parent().update_camera_setting("cam2", int(cam_id), "val", value)
                setattr(self.cam2, lb_par, value)
        else:
            hs = slider.objectName()
            if hs == "hs_trigger_timeout":
                value = slider.value()
                self.parent().lb_trigger_timeout.setText("trigger_timeout-" + str(value))
                self.parent().config_update("trigger_timeout", "val", value)
                self.trigger_timeout = value

    def inspect(self):
        print("Inspecting...")
        self.cam0.lft_camera_trigger_bfr = True
        self.cam1.cntr_camera_trigger_bfr = True
        self.cam2.rht_camera_trigger_bfr = True

    def camera_handler(self, camera_num=None, sig=None, val=None):
        if camera_num == self.cam0_serialNumber:
            if sig == "state":
                if not val:
                    self.parent().lbCam_0.setText("cam_{}\nDisconnected".format(camera_num))
            elif sig == "frame":
                self.showlogo_bycv(self.parent().lbCam_0, val)
            elif sig == "working_image":
                self.showlogo_bycv(self.parent().lbCam_0, val)

            elif sig == "data":
                if val == "FAULTY":
                    self.parent().lbWarn1.setStyleSheet('color: red')
                    self.parent().lbWarn1.setText(val)

                else:
                    self.parent().lbWarn1.setStyleSheet('color: green')
                    self.parent().lbWarn1.setText(val)

            elif sig == "count":
                self.parent().val_rhs.setStyleSheet('color: purple')
                self.parent().val_rhs.setText(val)

            elif sig == "test":
                if type(val) is list:
                    self.parent().lb_test_0.setText(val[0])
                    self.showlogo_bycv(self.parent().lb_test_1, val[1])
                    self.showlogo_bycv(self.parent().lb_test_2, val[2])
                    self.showlogo_bycv(self.parent().lb_test_3, val[3])
                else:
                    self.showlogo_bycv(self.parent().lbCam_0, val)

        if camera_num == self.cam1_serialNumber:
            if sig == "state":
                if not val:
                    self.parent().lbCam_1.setText("cam_{}\nDisconnected".format(camera_num))

            elif sig == "frame":
                self.showlogo_bycv(self.parent().lbCam_1, val)

            elif sig == "working_image":
                self.showlogo_bycv(self.parent().lbCam_1, val)

            elif sig == "data":
                if val == "FAULTY":
                    self.parent().lbWarn2.setStyleSheet('color: red')
                    self.parent().lbWarn2.setText(val)

                else:
                    self.parent().lbWarn2.setStyleSheet('color: green')
                    self.parent().lbWarn2.setText(val)

            elif sig == "count":
                self.parent().val_mdl.setStyleSheet('color: purple')
                self.parent().val_mdl.setText(val)

            elif sig == "test":
                if type(val) is list:
                    self.parent().lb_test_0.setText(val[0])
                    self.showlogo_bycv(self.parent().lb_test_1, val[1])
                    self.showlogo_bycv(self.parent().lb_test_2, val[2])
                    self.showlogo_bycv(self.parent().lb_test_3, val[3])
                else:
                    self.showlogo_bycv(self.parent().lbCam_0, val)

        if camera_num == self.cam2_serialNumber:
            if sig == "state":
                if not val:
                    self.parent().lbCam_2.setText("cam_{}\nDisconnected".format(camera_num))

            elif sig == "frame":
                self.showlogo_bycv(self.parent().lbCam_2, val)

            elif sig == "working_image":
                self.showlogo_bycv(self.parent().lbCam_2, val)

            elif sig == "data":
                if val == "FAULTY":
                    self.parent().lbWarn3.setStyleSheet('color: red')
                    self.parent().lbWarn3.setText(val)

                else:
                    self.parent().lbWarn3.setStyleSheet('color: green')
                    self.parent().lbWarn3.setText(val)

            elif sig == "count":
                self.parent().val_lhs.setStyleSheet('color: purple')
                self.parent().val_lhs.setText(val)

            elif sig == "test":
                if type(val) is list:
                    self.parent().lb_test_0.setText(val[0])
                    self.showlogo_bycv(self.parent().lb_test_1, val[1])
                    self.showlogo_bycv(self.parent().lb_test_2, val[2])
                    self.showlogo_bycv(self.parent().lb_test_3, val[3])
                else:
                    self.showlogo_bycv(self.parent().lbCam_0, val)

    def showlogo_bycv(self, obj, frame, path=None):
        if path:
            img = cv2.imread(frame)
            frame = img

        re_img = QImage(frame, frame.shape[1], frame.shape[0],
                        frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        pix_img = QPixmap.fromImage(re_img)
        obj.setPixmap(pix_img)
