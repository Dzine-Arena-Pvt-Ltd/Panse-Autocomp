import cv2
import numpy as np

import time

def nothing(x):
    pass


def lhs_object_detection(frame):
    rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    imgGray = 255 - rgb_img
    cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

    cv2.imshow("frame", rgb_img)


    g_img = rgb_img[:, :, 1]

    ret, thresh = cv2.threshold(g_img, 130, 255, cv2.THRESH_OTSU)
    # cv2.namedWindow("binary img", cv2.WINDOW_NORMAL)
    # cv2.imshow("binary img", thresh)

    kernel = np.ones((4, 4), np.uint8)
    img_erosion = cv2.erode(thresh, kernel, iterations=2)
    # cv2.namedWindow("img_erosion", cv2.WINDOW_NORMAL)
    # cv2.imshow("img_erosion", img_erosion)

    points = np.argwhere(img_erosion > 0)
    points = np.fliplr(points)
    # print(points)
    x, y, w, h = cv2.boundingRect(points)
    # print(x,y,w,h)
    oimg_crop = frame[y:y + h, x:x + w]
    # cv2.namedWindow("oimg_crop", cv2.WINDOW_NORMAL)
    # cv2.imshow('oimg_crop', oimg_crop)



    # print("x",x,"y",y)
    lhs_redpart_detection(frame, oimg_crop, x, y)


def lhs_redpart_detection(frame, oimg_crop, x, y):
    gray_img = cv2.cvtColor(oimg_crop, cv2.COLOR_BGR2GRAY)
    x1, y1, w1, h1 = 450, 680, 160, 390
    sec1_crop = frame[y1:y1 + h1, x1:x1 + w1]
    YCrCb = cv2.cvtColor(sec1_crop, cv2.COLOR_BGR2YCrCb)

    # cv2.namedWindow("sec1_crop", cv2.WINDOW_NORMAL)
    # cv2.imshow("sec1_crop", sec1_crop)
    # cv2.waitKey(0)
    r_img = YCrCb[:, :, 1]
    # gray_img=cv2.cvtColor(sec1_crop,cv2.COLOR_BGR2GRAY)
    ret, sec1_bwcrop = cv2.threshold(r_img, 120, 250, cv2.THRESH_BINARY)
    # cv2.imshow("sec1_bwcrop",sec1_bwcrop)
    # cv2.imshow("sec1_crop",sec1_crop)

    cnts, hierarchy = cv2.findContours(sec1_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    Tarea = 0
    for i in range(len(cnts)):
        cnt = sorted(cnts, key=cv2.contourArea)
        area = cv2.contourArea(cnt[i])
        # print(area)
        Tarea = Tarea + area
    print("total area", Tarea)
    if Tarea > 50000:
        r = 1
        # print("Part1 Is Present")
        cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 8)
        text = "PART1"
        # cv2.putText(oimg_crop, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), lineType=cv2.LINE_AA)
        cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)

        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)
    else:
        print("Part1 Is Missing")
        r = 0
        cv2.rectangle(oimg_crop, (x1, y1), (x1 + w1, y1 + h1), (0, 0, 255), 8)
        text = "PART1"
        # cv2.putText(oimg_crop, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), lineType=cv2.LINE_AA)

        cv2.namedWindow("Detected part", cv2.WINDOW_NORMAL)
        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)
    #
    lhs_sec2_detection(frame, oimg_crop, x, y, r)
    lhs_rod_detection(x, y, oimg_crop, r)
    lhs_section3_detection(x, y, oimg_crop, r)

def lhs_sec2_detection(frame, oimg_crop, x, y, r):
    if r == 0:
        x2, y2, w2, h2 = x + 110, y + 700, 260, 300
    else:
        x2, y2, w2, h2 = x + 110, y + 700, 260, 300

    sec2_crop = frame[y2:y2 + h2, x2:x2 + w2]
    # cv2.imshow("crop2", sec2_crop)

    gray_img = cv2.cvtColor(sec2_crop, cv2.COLOR_BGR2GRAY)
    ret, sec2_bwcrop = cv2.threshold(gray_img, 63, 250, cv2.THRESH_BINARY_INV)
    # cv2.imshow("sec2_bwcrop", sec2_bwcrop)
    # cv2.waitKey(0)

    cnts, hierarchy = cv2.findContours(sec2_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    Tarea = 0
    for i in range(len(cnts)):
        cnt = sorted(cnts, key=cv2.contourArea)
        area = cv2.contourArea(cnt[i])
        # print(area)
        Tarea = Tarea + area
    print("PART 2 total area", Tarea)
    # cv2.rectangle(frame,(x2-25,y2+50),(w2+50,h2+50),(0,255,0),4)
    # cv2.imshow("Detected part",oimg_crop)
    if Tarea > 65000:
        print("PART 2 Is Present")

        cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 8)
        text = "PART 2"
        cv2.putText(oimg_crop, text, (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)

        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)
    else:
        print("PART 2 Is Missing")

        cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 8)
        text = "PART 2"
        cv2.putText(oimg_crop, text, (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)

def lhs_rod_detection(x, y, oimg_crop, r):
    print("r = ", r)
    if r == 1:
        x3, y3, w3, h3 = x + 100, y + 250, 100, 550  # x + 280, y - 150, 750, 180
    else:
        x3, y3, w3, h3 = x + 100, y + 250, 100, 550  # x + 280, y - 150, 750, 180

    rod_crop = oimg_crop[y3:y3 + h3, x3:x3 + w3]
    # cv2.imshow("rod_crop", rod_crop)
    YCrCb = cv2.cvtColor(rod_crop, cv2.COLOR_BGR2YCrCb)
    b_img = YCrCb[:, :, 0]
    ret, rod_bwcrop = cv2.threshold(b_img, 90, 250, cv2.THRESH_BINARY)
    # cv2.imshow("r_img", rod_bwcrop)
    cnts, hierarchy = cv2.findContours(rod_bwcrop, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    Tarea = 0
    for i in range(len(cnts)):
        cnt = sorted(cnts, key=cv2.contourArea)
        area = cv2.contourArea(cnt[i])
        # print(area)
        Tarea = Tarea + area

    print("ROD AREA", Tarea)

    if Tarea > 3000:

        print("Rod Is Present")
        cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 8)
        # cv2.imshow("Detected part",oimg_crop)
        # cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 8)
        text = "ROD"
        cv2.putText(oimg_crop, text, (x3, y3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
        # cv2.imshow('result', oimg_crop)
        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)

    else:
        print("Rod Is Missing")
        cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 0, 255), 8)
        # print("Part2 Is Missing")
        # cv2.rectangle(oimg_crop, (x3, y3), (x3 + w3, y3 + h3), (0, 0, 255), 4)
        text = "ROD"
        cv2.putText(oimg_crop, text, (x3, y3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)

        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)

def lhs_section3_detection(x, y, oimg_crop, r):
    if r == 1:
        x33, y33, w33, h33 = x + 220, y + 100, 320, 480
    else:
        x33, y33, w33, h33 = x + 220, y + 100, 320, 480
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
    if Tarea > 35000:
        print("Part3 Is Present")
        cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 255, 0), 8)
        # cv2.imshow("Detected part",oimg_crop)
        text = "PART3"
        cv2.putText(oimg_crop, text, (x33, y33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
        cv2.imshow('Detected part', oimg_crop)
        # cv2.waitKey(0)
    else:
        print("Part3 Is Missing")
        cv2.rectangle(oimg_crop, (x33, y33), (x33 + w33, y33 + h33), (0, 0, 255), 8)
        text = "Part3"
        cv2.putText(oimg_crop, text, (x33, y33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), lineType=cv2.LINE_AA)
        # cv2.imshow('result', oimg_crop)
        cv2.imshow("Detected part", oimg_crop)
        # cv2.waitKey(0)

#
for i in range(131, 150):
    frame = cv2.imread("/home/pankaj/Pankaj Projects/Panse-12-06-19/Final Code/Main Design/Images/cam0_{0}.jpg".format(i))
    lhs_object_detection(frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


