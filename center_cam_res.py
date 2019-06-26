import cv2
import numpy as np


class CenterRes:
    # def __init__(self, frame):
    #     # self.frame = frame

    def cntr_object_detection(self, frame):
        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
        cv2.imshow("frame", rgb_img)
        g_img = rgb_img[:, :, 1]

        ret, thresh = cv2.threshold(g_img, 130, 255, cv2.THRESH_OTSU)
        cv2.namedWindow("binary img", cv2.WINDOW_NORMAL)
        cv2.imshow("binary img", thresh)

        kernel = np.ones((4, 4), np.uint8)
        img_erosion = cv2.erode(thresh, kernel, iterations=2)
        cv2.namedWindow("img_erosion", cv2.WINDOW_NORMAL)
        cv2.imshow("img_erosion", img_erosion)

        points = np.argwhere(img_erosion > 0)
        points = np.fliplr(points)
        # print(points)
        x, y, w, h = cv2.boundingRect(points)
        # print(x,y,w,h)
        oimg_crop = frame[y:y + h, x:x + w]
        cv2.namedWindow("oimg_crop", cv2.WINDOW_NORMAL)
        cv2.imshow('oimg_crop', oimg_crop)

        # print("x",x,"y",y)
        self.cntr_rod_detection(frame, oimg_crop, x, y)

    def cntr_rod_detection(self, frame, oimg_crop, x, y):

        x1, y1, w1, h1 = 365, 660, 170, 200
        sec1_crop = frame[y1:y1 + h1, x1:x1 + w1]
        YCrCb = cv2.cvtColor(sec1_crop, cv2.COLOR_BGR2YCrCb)

        cv2.namedWindow("sec1_crop", cv2.WINDOW_NORMAL)
        cv2.imshow("sec1_crop", sec1_crop)
        r_img = YCrCb[:, :, 1]
        # gray_img=cv2.cvtColor(sec1_crop,cv2.COLOR_BGR2GRAY)
        # ret, sec1_bwcrop = cv2.threshold(r_img, 120, 250, cv2.THRESH_BINARY)
        canny = cv2.Canny(r_img, 63, 120)
        # cv2.imshow("sec1_bwcrop",sec1_bwcrop)
        cv2.imshow("canny", canny)
        det_cnt = cv2.countNonZero(canny)
        print("det_cnt = ", det_cnt)
        if det_cnt > 200:
            r = 1
            print("Rod Is Present")
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 8)

            cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)
            cv2.imshow("Detected part", oimg_crop)
            # cv2.waitKey(0)
        else:
            print("Rod Is Missing")
            r = 0
            cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 4)

            cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)
            cv2.imshow("Detected part", oimg_crop)

        self.cntr_rev_det(frame)
        self.cntr_sec2_detection(frame, oimg_crop, x, y, r)
        self.cntr_section3_detection(x, y, oimg_crop, r)

    def cntr_rev_det(self, frame):

        x1, y1, w1, h1 = 430, 770, 180, 250

        sec5_crop = frame[y1 - 20:y1 + h1 - 220, x1 - 120:x1 + w1 - 250]
        cv2.namedWindow("sec5_crop", cv2.WINDOW_NORMAL)
        cv2.imshow("sec5_crop", sec5_crop)
        canny2 = cv2.Canny(sec5_crop, 83, 120)
        cv2.namedWindow("canny2", cv2.WINDOW_NORMAL)
        cv2.imshow("canny2", canny2)

        detected_cnt = cv2.countNonZero(canny2)
        print("detected_cnt = ", detected_cnt)
        if detected_cnt < 150:
            print("Placed part is ok")
            cv2.rectangle(frame, (x1 - 120, y1 - 20), (x1 + w1 - 250, y1 + h1 - 220), (0, 255, 0), 4)
            cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)
            cv2.imshow("Detected part", frame)
        else:
            print("Placed part is Reverse")
            cv2.rectangle(frame, (x1 - 120, y1 - 20), (x1 + w1 - 250, y1 + h1 - 220), (0, 0, 255), 4)
            cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)
            cv2.imshow("Detected part", frame)

    def cntr_sec2_detection(self, frame, oimg_crop, x, y, r):
        if r == 0:
            x2, y2, w2, h2 = x + 150, y + 665, 190, 300
        else:
            x2, y2, w2, h2 = x + 150, y + 665, 190, 300

        sec2_crop = frame[y2:y2 + h2, x2:x2 + w2]
        cv2.imshow("crop2", sec2_crop)

        gray_img = cv2.cvtColor(sec2_crop, cv2.COLOR_BGR2GRAY)
        # ret, sec2_bwcrop = cv2.threshold(gray_img, 63, 250, cv2.THRESH_BINARY_INV)
        # cv2.imshow("sec2_bwcrop", sec2_bwcrop)
        # # cv2.waitKey(0)
        #
        # cnts, hierarchy = cv2.findContours(sec2_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        canny = cv2.Canny(gray_img, 63, 120)
        cv2.imshow("Cann sec2", canny)
        sec2_cnt = cv2.countNonZero(canny)
        print("sec2_cnt", sec2_cnt)

        if sec2_cnt > 6000:
            print("PART 2 Is Present")

            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 4)
            text = "PART 2"
            cv2.putText(oimg_crop, text, (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)

            cv2.imshow("Detected part", oimg_crop)

        else:
            print("PART 2 Is Missing")

            cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 4)
            text = "PART 2"
            cv2.putText(oimg_crop, text, (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
            cv2.imshow("Detected part", oimg_crop)

    def cntr_section3_detection(self, x, y, oimg_crop, r):
        if r == 1:
            x33, y33, w33, h33 = x + 150, y + 210, 320, 460
        else:
            x33, y33, w33, h33 = x + 150, y + 210, 320, 460
        sec3_crop = oimg_crop[y33:y33 + h33, x33:x33 + w33]
        # cv2.imshow("sec_3", sec3_crop)
        YCrCb = cv2.cvtColor(sec3_crop, cv2.COLOR_BGR2YCrCb)
        b_img = YCrCb[:, :, 0]
        ret, sec3_bwcrop = cv2.threshold(b_img, 30, 240, cv2.THRESH_BINARY_INV)
        # cv2.imshow("r_img", sec3_bwcrop)

        cnts, hierarchy = cv2.findContours(sec3_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        Tarea = 0
        for i in range(len(cnts)):
            cnt = sorted(cnts, key=cv2.contourArea)
            area = cv2.contourArea(cnt[i])
            # print(area)
            Tarea = Tarea + area
        print(Tarea)

        if Tarea > 5000:
            print("Part3 Is Present")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 255, 0), 4)
            # cv2.imshow("Detected part",oimg_crop)
            text = "PART3"
            cv2.putText(oimg_crop, text, (x33, y33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
            cv2.imshow('Detected part', oimg_crop)

        else:
            print("Part3 Is Missing")
            cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 0, 255), 4)
            text = "Part3"
            cv2.putText(oimg_crop, text, (x33, y33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
            # cv2.imshow('result', oimg_crop)
            cv2.imshow("Detected part", oimg_crop)


# for i in range(1, 35):
# frame = cv2.imread("tst1.png")
# cntr_object_detection(frame)
# cv2.waitKey(0)
if __name__ == "__main__":

    for i in range(101, 151):
        frame1 = cv2.imread(
            "/home/pankaj/Pankaj Projects/Panse-12-06-19/Final Code/Main Design/Images/cam1_{0}.jpg".format(i))
        obj = CenterRes()
        obj.cntr_object_detection(frame1)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
