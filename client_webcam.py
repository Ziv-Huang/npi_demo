#!/usr/bin/python
import cv2
from PIL import Image
import base64
from io import StringIO
from io import BytesIO
import re
import numpy as np
from websocket import create_connection
import json
import threading
import time
import datetime
import math
import os
import emotionAccumulation
import symbol

def IoU(box1, box2):
    """
    :param box1: = [xmin1, ymin1, xmax1, ymax1]
    :param box2: = [xmin2, ymin2, xmax2, ymax2]
    :return: 
    """
    xmin1, ymin1, xmax1, ymax1 = box1
    xmin2, ymin2, xmax2, ymax2 = box2
    # 计算每个矩形的面积
    s1 = (xmax1 - xmin1) * (ymax1 - ymin1)  # C的面积
    s2 = (xmax2 - xmin2) * (ymax2 - ymin2)  # G的面积
 
    # 计算相交矩形
    xmin = max(xmin1, xmin2)
    ymin = max(ymin1, ymin2)
    xmax = min(xmax1, xmax2)
    ymax = min(ymax1, ymax2)
 
    w = max(0, xmax - xmin)
    h = max(0, ymax - ymin)
    area = w * h  # C∩G的面积
    iou = area / (s1 + s2 - area)
    return iou

class person():
    def __init__(self,id):
        self.id = id
        self.bbox = None
        self.date = None
        self.emotionArray = [0,0,0,0,0]
        self.frameNumber = 0


class Client():
    def __init__(self):
        self.frame=None
        self.ret=None
        self.ws=None
        # self.ws_door=None
        self.results=[]
        self.respond=None
        self.quit=False
        self.emotionType = {"Negative":2,"Neutral":3,"Positive":4}
    def grab_cap(self,cap,lock):
        while(self.quit is False): #cap.isOpened()
            lock.acquire()
            if cap.isOpened():
                cap.grab()
                lock.release()
            else :
                lock.release()
                break

            time.sleep(0.001)

    def socket_receive(self):
        while(self.quit is False):
            receive = self.ws.recv()
            # print(receive)
            if receive:
                try:
                    self.respond = receive

                    json.loads(receive)
                    self.results = json.loads(receive)['Response']['Face_List']
                    # print(self.results)
                except:
                    pass
                # print(receive)
                # self.results = json.loads(receive)['FaceList']

    def cv_to_base64(self,frame):
        PIL_image = Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        # output_buffer = StringIO()
        output_buffer = BytesIO()
        PIL_image.save(output_buffer,format='JPEG')
        binary_data = output_buffer.getvalue()
        base64_data = base64.b64encode(binary_data).decode('utf-8')
        # base64_data = base64.encodestring(binary_data)

        ### send to server
        return "data:image/jpeg;base64,"+base64_data
    def ws_connection(self):
        # self.ws = create_connection("ws://localhost:3001/websocket")
        self.ws = create_connection("ws://10.36.172.171:3001/websocket")
        
        # self.ws = create_connection("ws://10.36.172.235:3001/websocket")

        # self.ws = create_connection("ws://192.168.1.100:3001/websocket")
        # self.ws_door = create_connection("ws://192.168.1.100:3003/websocket")
    

    def run(self):
        # url = 'rtsp://admin:admin@192.168.1.2:554/Streaming/Channels/'
        # cap = cv2.VideoCapture(url)
                    

        cap = cv2.VideoCapture(0)
        WIDTH = 1280
        HEIGHT = 720
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)


        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 10.0, (WIDTH,  HEIGHT))
        outOrigin = cv2.VideoWriter('outputOrigin.avi', fourcc, 10.0, (WIDTH,  HEIGHT))
        videoRecord = False

        contextScale = 150

        self.ws_connection()
        
        lock = threading.Lock()
        t1 = threading.Thread(target=self.grab_cap,args = (cap,lock,))
        t1.start()
        self.ret, self.frame = cap.retrieve()

        t_ws_recv = threading.Thread(target=self.socket_receive,args = ())
        t_ws_recv.start()

        intervalFrame = 5
        accumulationCount = 0
        trackingID = 0
        IoUTH = 0.5
        personList = list()
        trackingList = list()
        resultDict = dict()

        while True:
            lock.acquire()
            self.ret, self.frame = cap.retrieve()
            lock.release()

            localtime = time.localtime(time.time())

            accumulationFlag = False
            if int(time.time()*10)%2==0:
                accumulationFlag = True


            # self.frame = cv2.imread("SJ_04.jpg")
            
            if self.ret:
                # self.frame = cv2.resize(self.frame, (640, 480)) 
                height, width, channels = self.frame.shape
                if videoRecord:
                    outOrigin.write(self.frame)
                # print(self.frame.shape)
                img_base64 = self.cv_to_base64(self.frame)
                # dict_info = {"purpose":"analytic","width":width,"height":height,"frame":img_base64}
                dict_info = {
                                "Field": "Smart_Retail_POS",
                                "Task": "Model_Inference",
                                "Pack_ID": "12345678A",
                                "Action": {
                                    "Action_Name": "Face_Feature",
                                    "Algorithm_List":["FaceID","Age","Gender","Emotion"],
                                    "Input":{
                                        "Format":"Streaming",
                                        "Data":img_base64
                                    }
                                }
                            }

                
                self.ws.send(json.dumps(dict_info))
                
                if accumulationCount==intervalFrame:
                    resultDict = dict()
                    nameList = list()
                    dateList = list()
                    emotionLists = [[],[],[],[],[]]
                    
                    for p in personList:
                        nameList.append(p.id)
                        dateList.append(p.date)
                        
                        for i in range(intervalFrame):
                            emotionLists[i].append(p.emotionArray[i])

                    # print("nameList {}".format(nameList))
                    # print("dateList {}".format(dateList))
                    # print("emotionList {}".format(emotionLists))
                    # print(emotionLists)
                    if len(nameList) is not 0:
                        # print(emotionLists)
                        # emotionLists = [[3],[3],[3],[2],[2]]
                        result = emotionAccumulation.emotionAccumulation(nameList,dateList,emotionLists,intervalFrame)
                        # print("result {}".format(result["forecast"].values))
                        # print(result)
                        # print(list(result["Name"]))

                        for r in range(len(result["Name"])):
                            resultDict[result["Name"].values[r]] = result["forecast"].values[r]

                    accumulationCount = 0 
                    personList = list()

                faceNumber = 0
                for face in self.results:
                    
                    # print(face)
                    color = (0,0,255)
                    if face['Gender'] == 'Male':
                        color = (255,0,0)
                    left = face['BBX'][0] if face['BBX'][0]>0 and face['BBX'][0]<width else 0
                    top = face['BBX'][1] if face['BBX'][1]>0 and face['BBX'][1]<height else 0
                    right = face['BBX'][2] if face['BBX'][2]>0 and face['BBX'][2]<width else width
                    bottom = face['BBX'][3] if face['BBX'][3]>0 and face['BBX'][3]<height else height
                    tmpPerson = person(-1)
                    curBbox = [left,top,right,bottom]
                    if accumulationCount==0:
                        # self.id = id
                        # self.bbox = None
                        # self.date = None
                        # self.emotionArray = [0,0,0,0,0]
                        

                        tmpPerson = person(faceNumber+trackingID)
                        tmpPerson.bbox = [left,top,right,bottom]
                        tmpPerson.date = "{}-{}-{}".format(localtime.tm_year,localtime.tm_mon,localtime.tm_mday)
                        tmpPerson.frameNumber = accumulationCount
                        tmpPerson.emotionArray[accumulationCount] = self.emotionType[face['Emotion']]
                        
                        for t in trackingList:
                            if IoU(curBbox,t.bbox)>IoUTH:
                                tmpPerson.id = t.id

                        # trackingID+=1
                        faceNumber+=1
                        trackingList.append(tmpPerson)
                        if accumulationFlag:
                            personList.append(tmpPerson)
                    
                    else:
                        faceExist = False
                        for p in personList:
                            # print(IoU(curBbox,p.bbox))
                            if IoU(curBbox,p.bbox)>IoUTH: # and accumulationCount==p.frameNumber+1:
                                p.bbox = curBbox
                                trackingList[p.id].bbox = curBbox
                                p.emotionArray[accumulationCount] = self.emotionType[face['Emotion']]

                                tmpPerson = p

                                faceExist = True
                                break

                        if faceExist is False:
                            tmpPerson = person(trackingID+faceNumber)
                            tmpPerson.bbox = [left,top,right,bottom]
                            tmpPerson.date = "{}-{}-{}".format(localtime.tm_year,localtime.tm_mon,localtime.tm_mday)
                            tmpPerson.frameNumber = accumulationCount
                            tmpPerson.emotionArray[accumulationCount] = self.emotionType[face['Emotion']]
                            trackingID+=1
                            trackingList.append(tmpPerson)
                            if accumulationFlag:
                                personList.append(tmpPerson)


                    cv2.rectangle(self.frame,(left,top),(right,bottom),color,1)

                    bboxWidth = abs(right-left)
                    npi = -1
                    # if(face['FaceID_List'] and face['FaceID_List'][0]['Confidence'] > 0.5 and bboxWidth >112):
                    #     # print(face['FaceID_List'][0][])
                    #     cv2.putText(self.frame,str(face['FaceID_List'][0]['ID'])+' '+str(face['Age'])+' '+face['Emotion'],(left,top),1,1,(255,255,255),1)

                    # else:
                        
                        # print("ccccccccc{} {}".format(tmpPerson.id,resultDict))
                    if tmpPerson.id in resultDict:
                        npi = resultDict[tmpPerson.id]
                        # print(npi)
                        if npi>symbol.MAX:
                            npi = symbol.MAX
                    
                    # cv2.putText(self.frame,' ID: '+str(tmpPerson.id)+' NPI: '+str(npi)+' '+str(face['Age'])+' '+face['Emotion'],(left,top),1,1,(255,255,255),2)
                    # print(int((npi/symbol.interval)+0.5))
                    # print(npi)
                    faceWidth = right-left
                    if npi<=2:
                        cv2.putText(self.frame,face['Emotion']+' '+symbol.ZeroLevel,(left,top),2,faceWidth/contextScale,(0,255,0),2)
                        
                    else:
                        level = int((npi/symbol.interval)+0.5)
                        if level>symbol.gap-1:
                            level = symbol.gap-1
                        cv2.putText(self.frame,face['Emotion']+' '+symbol.NPILevel[level],(left,top),2,faceWidth/contextScale,(0,0,255),2)

                # if localtime.tm_sec%2==0:
                if accumulationFlag:
                    accumulationCount+=1

                # print(time.time())
                if videoRecord:
                    out.write(self.frame)
                    cv2.circle(self.frame,(WIDTH-100,50),10,(0,0,255),-1)

                cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
                cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.imshow('frame',self.frame)
                keypress = cv2.waitKey(1)
                if keypress & 0xFF == ord('q'):
                    self.quit=True
                    print('done')
                    break
                elif keypress & 0xFF == ord('r'):
                    videoRecord = not videoRecord


        self.ws.close()
        # self.ws_door.close()
        lock.acquire()
        out.release()
        cap.release()
        lock.release()
        cv2.destroyAllWindows()
        t1.join()
        t_ws_recv.join()
        

if __name__ == "__main__":
    d1 = Client()
    d1.run()
### websocket
### image base64
