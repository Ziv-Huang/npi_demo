關於利用AVCP產生情緒(Negative(1,2),Neutral(3),Positive(4))後，
即時預測NPI分數，主要程式碼如附檔.ipynb所示，包含：

1.	資料處理：data_processor
2.	建立情緒特徵：feature_generator
3.	模型預測：model_forecast
4.	NPI預測分數：test_final_forecast

另外，臉部標記的sample資料，如.csv所示，主要需要包含：

1.	ID(Name)
2.	時間(Date)
3.	多個時機點預測情緒(0~13)：1,2(Negative), 3(Neutral), 4(Positive), NA(未偵測到)

最後，.pkl檔為先前訓練模型之儲存檔， 
主要是之後會即時產生每個人的NPI分數
