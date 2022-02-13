# -*- coding: utf-8 -*-
"""
Created on Sat May 15 09:32:03 2021

@author: USER
"""

import asyncio
 
async def add(a, b):
    print('add: {0} + {1}'.format(a, b))
    await asyncio.sleep(1.0)    # 1초 대기. asyncio.sleep도 네이티브 코루틴
    return a + b    # 두 수를 더한 결과 반환
 
async def print_add(a, b):
    result = await add(a, b)    # await로 다른 네이티브 코루틴 실행하고 반환값을 변수에 저장
    print('print_add: {0} + {1} = {2}'.format(a, b, result))
 
loop = asyncio.get_event_loop()             # 이벤트 루프를 얻음
loop.run_until_complete(print_add(1, 2))    # print_add가 끝날 때까지 이벤트 루프를 실행
loop.close() 

#토큰화 및 데이터준비
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from keras.layers import Dropout
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import logging
import pandas as pd
from pykospacing import spacing
from hanspell import spell_checker

# multyprocessing
def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    test = pd.read_excel("d:\\test.xlsx")
    #num_list = ['p1','p2','p3','p4','p5','p6','p7','p8']
    with ProcessPoolExecutor(max_workers=8) as executor:
        data = executor.map(data_spell_spacing_func, test)
    #pool.map(data_spell_spacing_func, num_list, test)    
    logging.info("Main_process : before creating Process")
    #pool.close()
    logging.info("Main_process : running Process")
    #pool.join()
    logging.info("Main_process : Finished Process")
    return data
    
# 1. data 띄워쓰기, 스펠링 체크 (멀티프로세싱 구현필요)
def data_spell_spacing_func(data_Series):
    #print('sub-process {}: starting'.format(name))    
    data_list = list(data_Series['content'])
    spacing_list = []
    spell_list =[]
    new_respacing_data = []
    for num, data in enumerate(data_list):   
        try:
            logging.info("spacing_data {}/{}".format(num,len(data_list)))
            spacing_list.append(spacing(data))
        except:
            #logging.info("spacing_data {}/{}".format(num,len(data_list)))
            pass
        
    for num, content in enumerate(spacing_list):   
        try:
            logging.info("spell_data {}/{}".format(num,len(spacing_list)))
            spelled_sent = spell_checker.check(content)
            spell_list.append(spelled_sent.checked)
        except:
            pass
    
    for num, data in enumerate(spell_list):  
        try:
            logging.info("respacing_data {}/{}".format(num,len(spell_list)))
            new_respacing_data.append(spacing(data))
        except:
            pass
        
    data_Series['content'] = new_respacing_data
    #print('sub-process {}: Finishing'.format(name))
    return data_Series




import pandas as pd
from hanspell import spell_checker
from pykospacing import spacing

def prepare_dataset(data):
    매수 = data[data['매수']==1]
    매도 = data[data['매도']==1]
    매도후매수 = data[data['매도후매수']==1]
    기타 = data[~(data['매수']==1) & ~(data['매도']==1) & ~(data['매도후매수']==1)]
    a = 매수[['Unnamed: 0', 0, '매수']]    
    b = 매도[['Unnamed: 0', 0, '매도']]
    c = 매도후매수[['Unnamed: 0', 0, '매도후매수']]   
    d = 기타[['Unnamed: 0', 0]]
    a['type'] = '매수'
    b['type'] = '매도'
    c['type'] = '매도후매수'
    d['type'] = '기타'
    e = pd.concat([a,b])
    f = pd.concat([c,d])
    result = pd.concat([e,f])
    result = result[['Unnamed: 0', 0, 'type']]
    result.columns = ['No','content','type']
    data_set= result.set_index("No")
    return data_set

    
def prepare_learning_input(train_data, test_data, mode, max_words): # 전처리 함수
    t = Tokenizer(num_words = max_words) # max_words 개수만큼의 단어만 사용한다.
    t.fit_on_texts(train_data)
    X_train = t.texts_to_matrix(train_data, mode=mode) # 샘플 수 × max_words 크기의 행렬 생성
    X_test = t.texts_to_matrix(test_data, mode=mode) # 샘플 수 × max_words 크기의 행렬 생성
    return X_train, X_test, t.index_word, t

def test_result_display(model,test_set):
    test_content = test_set['content'] # 훈련 데이터의 본문 저장
    #test_label = test_set['type'] # 0테스트 데이터의 레이블 
    X_test = t.texts_to_matrix(test_content, mode='binary')
    
    type_list = ['매도후매수', '기타', '매수', '매도']
    test_df = pd.DataFrame(test_set)
    yhat = model.predict(X_test)
    result_type = []
    for result in yhat:
        result = list(result)
        tmp = max(result)
        result_type.append(type_list[result.index(tmp)])
    test_df['판단결과'] = result_type
    return test_df
    

data = pd.read_excel('d:\\1.xlsx')
data2 = pd.read_excel('d:\\2.xlsx')

#train_set = data.iloc[:2000]

#train_set = prepare_dataset(data.iloc[:2000])
train_set = prepare_dataset(data)
test_set = prepare_dataset(data2)
train_content = train_set['content'] # 훈련 데이터의 본문 저장
train_label = train_set['type'] # 훈련 데이터의 레이블 저장
test_content = test_set['content'] # 훈련 데이터의 본문 저장
test_label = test_set['type'] # 0테스트 데이터의 레이블 



max_words = 10000 # 실습에 사용할 단어의 최대 개수
num_classes = 4 #레이;블수


X_train, X_test, index_to_word1, t1  = prepare_learning_input(train_content, test_content, 'binary', 10000)
Y_train, y_test, index_to_word2, t2 = prepare_learning_input(train_label, test_label, 'binary', 4)

model = Sequential()
model.add(Dense(256, input_shape=(max_words,), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(4, activation='softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, Y_train, batch_size=128, epochs=1000, verbose=1, validation_split=0.1)
score = model.evaluate(X_test, y_test, batch_size=128, verbose=0)

predict_data = train_content

predict_X = t1.texts_to_matrix(predict_data, mode='binary')

type_list = ['매도후매수', '기타', '매수', '매도']
test_df = pd.DataFrame(train_set)
yhat = model.predict(predict_X)
result_type = []
for result in yhat:
    result = list(result)
    tmp = max(result)
    result_type.append(type_list[result.index(tmp)])
test_df['판단결과'] = result_type


# 2. 