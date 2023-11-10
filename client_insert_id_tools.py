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

class Client():
    def __init__(self):
        self.frame=None
        self.ret=None
        self.ws=None
        self.ws_door=None
        self.results=[]
        self.respond=None
        self.quit=False
        self.packid=None
        self.s_packid=None
        self.img_buff = {}
        self.count_flag = 0
        self.count_image=1
        self.face_flag = False
        self.ws_lock = threading.Lock()
    def grab_cap(self,cap,lock):
        while(self.quit is False): #cap.isOpened()
            lock.acquire()
            if cap.isOpened():
                # print('grab 0')
                cap.grab()
                # print('grab 1')
                lock.release()
            else :
                lock.release()
                break

            time.sleep(0.001)

    def socket_receive(self,lock):
        now = time.time()
        total_time=0
        count=0
        iter_t=0
        while(self.quit is False):
            receive = self.ws.recv()
            
            print(receive)

            try:
                self.packid = json.loads(receive)['Response']['Pack_ID']
            except:
                pass

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
        # self.ws = create_connection("ws://10.36.172.214:3001/websocket")
        
        # self.ws = create_connection("ws://10.42.0.225:3001/websocket")
        # self.ws = create_connection("ws://10.36.126.121:3001/websocket")
        self.ws = create_connection("ws://10.36.126.121:3001/websocket")

        # self.ws = create_connection("ws://127.0.0.1:3001/websocket")
        #self.ws = create_connection("ws://192.168.1.100:3001/websocket")
        #self.ws_door = create_connection("ws://192.168.1.100:3003/websocket")

    def test_id(self,id):
        
        dict_info = {
                        "API": "Smart_Retail_POS",
                        "Task": "Model_Update",
                        "Pack_ID": str(id),
                        "Action": {
                            "Action_Name": "Reload_All",
                            "Algorithm":"FaceID"
                        },
                        "Pack_ID":"12345678a"
                    }
        self.ws.send(json.dumps(dict_info))
    
    def delete_id(self,id):
        
        dict_info = {
                        "API": "Smart_Retail_POS",
                        "Task": "Model_Update",
                        "Pack_ID": "str(packid)",
                        "Action": {
                            "Action_Name": "Delete_By_ID",
                            "Algorithm":"FaceID",
                            "Input":{
                                "ID":str(id),
                            }
                        },
                        "Pack_ID":str(id)
                   }

        # dict_info = {
        #                 "Field": "Smart_Retail_POS",
        #                 "Task": "Model_Update",
        #                 "Pack_ID": str(id),
        #                 "Action": {
        #                     "Action_Name": "Delete_All",
        #                     "Algorithm":"FaceID"
        #                 }
        #             }

        self.ws.send(json.dumps(dict_info))

    def insert_id(self,id,img):
        dict_info = {
                        "Field": "Smart_Retail_POS",
                        "Task": "Model_Update",
                        "Pack_ID": str(id),
                        "Action": {
                            "Action_Name": "Insert_ID",
                            "Algorithm":"FaceID",
                            "Input":{
                                "ID":str(id),
                                "Format":"Streaming",
                                "Data" : img
                                # "Data":[img]
                            }
                        }
                    }
        
        self.ws.send(json.dumps(dict_info))
        
            
    
    def run(self):
        self.ws_connection()
        self.ws.recv()
        lock_info = threading.Lock()
        
        # imgs_dir = 'AVCP_ipcam_image/'
        # if not os.path.isdir(imgs_dir):
        #     os.mkdir(imgs_dir)
        # self.s_packid = 0
        # self.frame = cv2.imread("1.png")
        # img_base64 = self.cv_to_base64(self.frame)

        path = "/home/ziv/Documents/workspace/Forecast_for_NPI_score_with_AVCP/aaa"

        for img_dir in os.listdir(path):
            img_path = os.path.join(path,img_dir)
            frameList = list()
            for i in os.listdir(img_path):
                frame = cv2.imread(os.path.join(img_path,i))
                imgBase64 = self.cv_to_base64(frame)
                frameList.append(imgBase64)
            
            self.insert_id(img_dir,frameList)
            print(img_dir," : ",self.ws.recv())
        
        
        


        # time.sleep(1000)
               
        self.ws.close()
        # lock.acquire()
        # cap.release()
        # lock.release()
        # cv2.destroyAllWindows()
        # t1.join()
        # t_ws_recv.join()
        

if __name__ == "__main__":
    d1 = Client()
    d1.run()
### websocket
### image base64
