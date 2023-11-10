import pandas as pd
import numpy as np
import math
from multiprocessing import Pool
import datetime
import pickle



def feature_generator(face_data):
    face_data_feature = (face_data[['Name','Date']]).copy()
    face_data_feature['weekdiff'] = face_data.iloc[:,2:].fillna(3).diff(axis =1).fillna(0).abs().sum(axis=1)
    face_data_feature['weekmean'] = face_data.iloc[:,2:].mean(axis=1,skipna=True)
    face_data_feature['weekstd'] = face_data.iloc[:,2:].std(axis=1,skipna=True)+0.01
    face_data_feature['weekmaxmin'] = face_data.iloc[:,2:].max(axis=1,skipna=True)-face_data.iloc[:,2:].min(axis=1,skipna=True)
    face_data_feature['weeknegative'] = face_data.iloc[:,2:].isin([1,2]).sum(axis=1)
    face_data_feature['weekneutral'] = face_data.iloc[:,2:].isin([3]).sum(axis=1)
    face_data_feature['weekpositive'] = face_data.iloc[:,2:].isin([4]).sum(axis=1)
    face_data_feature['posminusneg'] = face_data_feature.weekpositive-face_data_feature.weeknegative
    return face_data_feature

def data_processor(face_data, range_index):
    face_data = face_data.drop(['ElderID'], axis=1)
    face_data_week = face_data.copy()
    max_index = np.int(face_data_week.columns.str.encode('utf-8')[-1])+1
    for index in range(max_index):
        face_data_week[str(index)] = np.where(face_data_week[str(index)].apply(lambda x : math.isnan(x)),1,0)
    # determine first or second week
    face_data['first_week'] = np.where((face_data_week.iloc[:,2:(range_index+2)]).sum(axis=1)<=np.floor(range_index/2),1,0)
    # one week
    face_data_first = face_data.loc[(face_data.first_week==1),:].iloc[:,0:(range_index+2)]
    face_data_first = face_data_first.reset_index(drop=True).rename(columns={'ElderName':'Name','SurgeryDate':'Date'})
    # print(face_data_first)
    # generate feature
    face_data_feature = feature_generator(face_data_first)
    face_data_feature = face_data_feature.sort_values(['Name','Date'], ascending=[1,1])
    # dtype some column
    face_data_feature.Date = [str(x) for x in face_data_feature.Date]
    # face_data_feature.Name = face_data_feature.Name.str.encode('utf-8')
    return face_data_feature

def model_forecastor(path, test_data):
    # Load ML model
    lm_model_name = path+'lm_model.pkl'
    rf_model_name = path+'rf_model.pkl'
    with open(lm_model_name, 'rb') as file:  
        lm_model = pickle.load(file,encoding='iso-8859-1')
    with open(rf_model_name, 'rb') as file:  
        rf_model = pickle.load(file,encoding='iso-8859-1')
    # Generate test data
    test_data_final = test_data.drop(['Name','Date'],axis=1)
    # LM Forecast
    test_lm_forecast = lm_model.predict(test_data_final)
    test_lm_forecast = np.floor(np.where(test_lm_forecast<0,0,test_lm_forecast))
    # RF Forecast
    test_rf_forecast = rf_model.predict(test_data_final)
    test_rf_forecast = np.floor(np.where(test_rf_forecast<0,0,test_rf_forecast))
    test_emb_forecast = test_rf_forecast
    test_data_forecast = test_data.copy()[['Name','Date']]
    test_data_forecast['forecast'] = test_emb_forecast
    return test_data_forecast

def emotionAccumulation(nameList,dateList,emotionList,number):
    # NPI forecast main process
    #-- Load data frame
    # face_data = pd.read_csv('/home/ziv/Documents/workspace/Forecast_for_NPI_score_with_AVCP/Face_label_result.csv', encoding='utf-8')
    face_data = pd.DataFrame({'ElderName':nameList,'ElderID':nameList,'SurgeryDate':dateList
                            ,'0':emotionList[0],'1':emotionList[1],'2':emotionList[2],'3':emotionList[3],'4':emotionList[4]})
    # print(face_data)
    #-- Preprocess data frame
    face_data_feature = data_processor(face_data,number)
    #-- Forecast data frame
    test_final_forecast = model_forecastor('',face_data_feature)
    # test_final_forecast
    # print(test_final_forecast)
    return test_final_forecast

if __name__ == '__main__':

    # nameList = [1,2,3,4,5]
    # dateList = ['2019-01-02','2019-01-03','2019-10-12','2019-10-12','2019-10-12']
    # emotionList = [[1,3,0,2,3],[None,4,3,2,3],[None,3,2,3,3],[3,None,0,3,3],[3,None,3,None,3]]

    nameList = [1,2]
    dateList = ['2019-01-02','2019-01-02']
    emotionList = [[1,2], [1,2], [1,3], [1,3], [1,0]]
    

    result = emotionAccumulation(nameList,dateList,emotionList,5)
    print(result)

    #just need ElderName , SurgeryDate and five emotion data
    #確認資料能夠在寫成csv格式
    #AVCP出來的結果每存五筆資料就丟到emotionAccumulation