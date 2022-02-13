import re
import sys
import os
import tqdm
import time

ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)
from pathlib import Path
import math
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

#from Kiwoom.config.kiwoomType import *
from config.kiwoomType import *
#from Kiwoom.config.log_class import *
from config.log_class import *
import Finance.finance_data
import FinanceDataReader as fdr
from Finance.make_quarter_finance_from_valuesheet import GET_RIM_DATA
from Finance.make_quarter_finance_from_valuesheet import GET_EXCEL_DATA

import Finance.finance_data
import pandas as pd

import datetime

import Trade_Algrithm.python_quant
import Finance.finance_data
from config.kiwoomType import RealType
from config.log_class import Logging
#from Kiwoom.config.kiwoomType import RealType
#from Kiwoom.config.log_class import Logging
from multiprocessing import Queue
TR_REQ_TIME_INTERVAL = 0.6
#from Kiwoom.DATA_PROC import *
from DATA_PROC import *
#import DATA_PROC
import DataBase.MySQL_control
import Telegram_Bot.telegram_bot
# form_class = uic.loadUiType("pytrader.ui")[0]
from CMD_DEFINE import *
class Kiwoom(QAxWidget):
    def __init__(self, data_queue=None, order_queue=None):
        super().__init__()
        if data_queue == None:
            data_queue = Queue()
        if order_queue == None:
            order_queue = Queue()
        #self.NB = Naver_Band.Naver_Band.Naver_Band()
        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.logging = Logging(self.ROOT_DIR + '\\config\\logging.conf')
        self.logging.logger.debug("Kiwoom() class start.")
        self.DB = DataBase.MySQL_control.DB_control(self.logging)

        self.data_queue = data_queue
        self.order_queue = order_queue
        self.realType = RealType()
        # REAL REG설정

        self.REAL_REG = REAL_REG_PARSING_ORDER(data_queue, order_queue, self.logging)
        # Telegram Thread Func
        self.telegram_data_que = Queue()
        #self.telegram_data_que = telegram_data_que
        self.Tbot = Telegram_Bot.telegram_bot.TeleBot(self.telegram_data_que,self.logging)
        self.Tbot.kw_func_req.connect(self.telegram_req_process)
        self.Tbot.start()
        #self.REAL_REG.dynamicCall = self.dynamicCall
        #self.REAL_REG.realType = self.realTypepo

        ####### 계좌 관련된 변수
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.deposit = 0  # 예수금
        self.use_money = 0  # 실제 투자에 사용할 금액
        self.use_money_percent = 1.0  # 예수금에서 실제 사용할 비율
        self.output_deposit = 0  # 출력가능 금액
        self.total_profit_loss_money = 0  # 총평가손익금액
        self.total_profit_loss_rate = 0.0  # 총수익률(%)

        ######## 종목 정보 가져오기
        self.portfolio_stock_dict = {}
        self.jango_dict = {}
        self.all_stock_dict = {}

        ####### 요청 스크린 번호
        self.screen_my_info = "2000"  # 계좌 관련한 스크린 번호
        self.screen_calculation_stock = "4000"  # 계산용 스크린 번호
        self.screen_real_stock = "5000"  # 종목별 할당할 스크린 번호
        self.screen_meme_stock = "6000"  # 종목별 할당할 주문용스크린 번호
        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린번호

        ####### 종목정보 딕셔너리 초기화
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': [], 'trading_value': []}
        self.opw00018_output = {'single': [], 'multi': []}
        self.tick_ohlcv = {"date": [], "close": [], 'open': [], 'high': [], 'low': []}
        self.prev_screen_overwrite= []

        ####### 알고리즘 결과종목 저장 경로
        #self.AV_Algo_result_path = self.ROOT_DIR + "\\files\\AV_Algo_result.txt "  # 그랜빌 4법칙
        #self.quant_result_path = self.ROOT_DIR + "\\files\\quant_result.txt "  # 그랜빌 4법칙
        self.tick_data = pd.DataFrame(data=None)
        self.Trade_algo = Trade_Algrithm.python_quant.Quant_Strategy()

        self.price = Finance.finance_data.Price_data()
        self.opw00018_output = {'single': [], 'multi': []}
        self.Kiwoom_DB_PATH = 'F:\\OneDrive - Office 365\\STOCK_DB\\Kiwoom.db'
        self.Kiwoom_initial_setting = {'fs_last_update': []}
        self.fs = Finance.finance_data.Finance_data()
        self.DB_Valuetool = 'stocks_value_list'
        self.DB_finance_quarter = 'stocks_finance'
        self.DB_finance_rim = 'stocks_rim'

        ####### screen num set
        self._create_kiwoom_instance()
        ####### kiwoom login
        self._get_condition_slots()
        self._set_signal_slots()
        self._real_event_slots()
        self.comm_connect()
        self.get_login_info()
        # kw order/get info signal
        self.REAL_REG.trigger.connect(self.order_stock)
        # 계좌정보 요청
        self.detail_account_info_event_loop = QEventLoop()  # 예수금 요청용 이벤트루프
        self.calculator_event_loop = QEventLoop()
        self.get_detail_account_info()  # 예수금 요청 시그널 포함
        self.get_detail_account_mystock()  # 계좌평가잔고내역 요청 시그널 포함

        # 포트폴리오 Task Initialize
        self.Stocks_Portfolio_Initialize('강환국_울트라_소형주')
        # 조건식 로드 TEST
        self.condition_dict = {"index": [], "name": []}
        result=self.dynamicCall("GetConditionLoad")
        print(result)
        self.telegram_req_flag=False
        temp = self.DB.DB_LOAD_TABLE_LIST("stocks_rim")
        self.stock_rim = self.DB.DB_LOAD_Table("stocks_rim", temp[-1])
        self.stock_rim = self.stock_rim.reset_index().set_index('종목')
        self.stock_code_name = self.stock_rim[['CODE']].copy()
        del(self.stock_rim)

        QTimer.singleShot(3000, self.not_conclude_account)  # 5초 뒤에 미체결 종목들 가져오기 실행
        QTest.qWait(1000)
        ####### 포트폴리오 로드 file path : ..\..\kiwoom\files\..
        # 실시간 수신 관련 함수
        '''  
        self.korea_market_stocklist = pd.DataFrame(data=None, columns=["code", "name"])
        kosdaq_list = self.get_code_list_by_market('10')
        kospi_list = self.get_code_list_by_market('0')
        total_list = kosdaq_list + kospi_list
        self.korea_market_stocklist['code'] = total_list
        self.korea_market_stocklist = self.korea_market_stocklist.set_index('code')
        for i, code in enumerate(self.korea_market_stocklist.index) :
            self.korea_market_stocklist.loc[code] = self.get_master_code_name(code)
        self.korea_market_stocklist.to_excel("f:\\koreamarketlist.xlsx")
        '''

    #@pyqtSlot(list)
    def telegram_req_process(self, req_list):
        if req_list[0] == kw_condition_sort_CMD:
            self.telegram_req_flag = True
            self.Set_Condition_Receive(req_list[1], 0)

        elif req_list[0] == meme_CMD:         # 매수_삼성전자_53000_2000000
            meme_type = req_list[1].split("_")[0]
            meme_stock = self.stock_code_name.loc[req_list[1].split("_")[1],'CODE'].replace("A", "")
            meme_price = int(req_list[1].split("_")[2])
            df = fdr.DataReader(meme_stock)
            cur_price = str(df['Close'][-1])
            meme_amount = math.floor((int(req_list[1].split("_")[3]) / int(cur_price))-0.5)

            self.get_detail_account_info()
            time.sleep(1)
            stock_ratio = format(float(meme_amount/self.deposit),".1f")
            #if

            self.screen_number_setting()
            self.set_realtime_stock(meme_stock, req_list[1].split("_")[1], meme_price, meme_type, stock_ratio)
            self.telegram_data_que.put([meme_CMD, self.portfolio_stock_dict])
    @staticmethod
    def change_format_money(data):
        strip_data = data.lstrip('-0')
        if strip_data == "" or strip_data == '.00':
            strip_data = 0
        format_data = format(int(strip_data), ',d')
        if data.startswith('-'):
            format_data = '-' + format_data
        return format_data

    @staticmethod
    def change_format_rate(data):
        strip_data = data.lstrip('-0')
        if strip_data == "":
            strip_data = 0

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data
        return strip_data

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 이벤트 관리 함수
    def _get_condition_slots(self):
        self.OnReceiveConditionVer.connect(self._OnReceiveConditionVer)
        self.OnReceiveTrCondition.connect(self._OnReceiveTrCondition)
        #self.OnReceiveRealCondition.connect(self._OnReceiveRealCondition)

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveMsg.connect(self.msg_slot)
        # self.OnReceiveChejanData.connect(self._receive_chejan_data)

    #===================================================================================================================
    # 조건식 관련 Callback 함수
    def _OnReceiveConditionVer(self,Ret, Msg):
        if Ret==1:
            name_list = self.dynamicCall("GetConditionNameList()").split(";")
            name_list = [x for x in name_list if len(x)>0]
            print(name_list)
            for condition in name_list:
                temp_str=condition.split("^")
                self.condition_dict["index"].append(str(temp_str[0]))
                self.condition_dict["name"].append(str(temp_str[1]))

            self.Set_Condition_Receive("고승덕 스토캐스틱",0)

    # 조건식 실시간/1회성 검색 선택 요청함수
    # type 1 => 실시간  0 => 1회성
    def Set_Condition_Receive(self, condition_name, type):
        ScrNo = "0156"
        try:
            ret = self.dynamicCall("SendCondition(QString, QString, int, int)", str(ScrNo), str(condition_name), int(self.condition_dict["index"][self.condition_dict["name"].index(condition_name)]), int(type))
            if ret == 1:
                self.logging.logger.debug("조건검색 조회 요청 성공")
            else:
                self.logging.logger.debug("조건검색 조회 요청 실패")
        except:
            self.logging.logger.debug("조건검색식명을 올바르게 입력해주세요")
    def _OnReceiveTrCondition(self, ScrNo, Code_list, Conditionname, nIndex, Nnext):
        Condition_List=[]
        Condition_List.append(Code_list)
        temp = Condition_List.pop()
        self.logging.logger.debug("{}".format(temp))
        if self.telegram_req_flag :
            eval_stock = self.Get_DB_From_Latest_Table("stocks_가치평가")
            for col in eval_stock.columns:
                try:
                    eval_stock[col] = eval_stock[col].astype('float')
                except:
                    continue
            temp_list = temp.split(";")
            stock_code = ['A'+x for x in temp_list if len(x)==6]
            #new_df = eval_stock.loc[stock_code]
            sort_df = pd.DataFrame(data=None, columns=eval_stock.columns)

            for i,code in enumerate(tqdm.tqdm(stock_code)):
                try:
                    if i == 0:
                        sort_df = eval_stock.loc[[code]].copy()
                    else :
                        sort_df = pd.concat([sort_df, eval_stock.loc[[code]].copy()],axis=0)
                    temp_price = self.get_current_price(code)
                    sort_df.loc[code,'현재가(원)']=temp_price
                    if float(temp_price) <= float(sort_df.loc[code,'RIM(원)']) : sort_df.loc[code,'RIM'] = 1
                    else : sort_df.loc[code,'RIM'] = 0
                    if float(temp_price) <= float(sort_df.loc[code,'숙향(원)']) : sort_df.loc[code,'숙향'] = 1
                    else : sort_df.loc[code,'숙향'] = 0
                    if float(temp_price) <= float(sort_df.loc[code,'EPS성장율(원)']) : sort_df.loc[code,'EPS성장율'] = 1
                    else : sort_df.loc[code,'EPS성장율'] = 0
                    if float(temp_price) <= float(sort_df.loc[code,'눈덩이(원)']) : sort_df.loc[code,'roe&pbr'] = 1
                    else : sort_df.loc[code,'roe&pbr'] = 0
                    if float(temp_price) <= float(sort_df.loc[code,'야마구치(원)']) : sort_df.loc[code,'야마구치'] = 1
                    else : sort_df.loc[code,'야마구치'] = 0
                    if float(temp_price) <= float(sort_df.loc[code,'무성장가치(원)']) : sort_df.loc[code,'무성장가치'] = 1
                    else : sort_df.loc[code,'무성장가치'] = 0
                except:
                    #print(code)
                    continue
            sort_df['합산']=sort_df['RIM'].astype('int')+sort_df['숙향'].astype('int')+sort_df['EPS성장율'].astype('int')+sort_df['roe&pbr'].astype('int')+sort_df['야마구치'].astype('int')+sort_df['무성장가치'].astype('int')

            sort_df['순위'] = sort_df['합산'].rank(method='first',ascending=False)
            sort_df = sort_df.sort_values(by='순위', ascending=True)
            display_list = ['순위','합산','종목','시가총액(억)','RIM(원)','현재가(원)','PER','PBR','ROE']
            sort_df = sort_df[display_list]
            sort_df['RIM(원)'] = sort_df['RIM(원)'].apply(lambda x: "{:.1f}".format(float(x)) if x != '-' else x)
            sort_df['PER']= sort_df['PER'].apply(lambda x: "{:.1f}".format(float(x)) if x != '-' else x)
            sort_df['PBR'] = sort_df['PBR'].apply(lambda x: "{:.1f}".format(float(x)) if x != '-' else x)
            sort_df['ROE'] = sort_df['ROE'].apply(lambda x: "{:.1f}".format(float(x))if x != '-' else x)
            #sort_df=sort_df.set_index("순위")
            self.telegram_data_que.put([kw_condition_sort_CMD,sort_df.iloc[:20]])
            self.telegram_req_flag = False
        else:
            pass



    def Get_DB_From_Latest_Table(self, skima, multi=False):
        table_list = self.DB.DB_LOAD_TABLE_LIST(skima)
        table = self.DB.DB_LOAD_Table(skima,table_list[-1], multi)
        return table
    #===================================================================================================================
    #@pyqtSlot(name="OrderStock")
    def order_stock(self):
        input  = self.order_queue.get()
        sell_buy = input[0]
        data = input[1]
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", data)
        if order_success == 0:
            self.logging.logger.debug("%s 전달 성공",data[0])
        else:
            self.logging.logger.debug("주문 전달 실패")
        '''
        if sell_buy == "매도":
            sell_order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", data)
        elif sell_buy == "매수":
            buy_order_success = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", data)

        if sell_order_success == 0:
            self.logging.logger.debug("매도주문 전달 성공")
            del self.account_stock_dict[data[4]]     #data[1][4] = scode
        elif buy_order_success == 0:
            self.logging.logger.debug("매수주문 전달 성공")
        else:
            self.logging.logger.debug("주문 전달 실패")
        '''

    def _real_event_slots(self):
        self.OnReceiveRealData.connect(self._receive_real_data)
        self.OnReceiveChejanData.connect(self._chejan_slot)  # 종목 주문체결 관련한 이벤트

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    # 로그인 slot 함수
    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected_due to errcode is_" + err_code)
        #       QMessageBox.about(self, "m",'구분:' + str(self.get_chejan_data(300)) + '\r\n종목코드:' + str(self.get_chejan_data(9203)))
        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)", code, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        self.logging.logger.debug("스크린: %s, 요청이름: %s, tr코드: %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

    def file_delete(self):
        if os.path.isfile(self.AV_Algo_result_path):
            os.remove(self.AV_Algo_result_path)

    def  _chejan_slot(self, sGubun, nItemCnt, sFidList):
        if int(sGubun) == 0:  # 주문체결
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()

            origin_order_number = self.dynamicCall("GetChejanData(int)",
                                                   self.realType.REALTYPE['주문체결']['원주문번호'])  # 출력 : defaluse : "000000"
            order_number = self.dynamicCall("GetChejanData(int)",
                                            self.realType.REALTYPE['주문체결']['주문번호'])  # 출럭: 0115061 마지막 주문번호

            order_status = self.dynamicCall("GetChejanData(int)",
                                            self.realType.REALTYPE['주문체결']['주문상태'])  # 출력: 접수, 확인, 체결
            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])  # 출력 : 3
            order_quan = int(order_quan)

            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])  # 출력: 21000
            order_price = int(order_price)

            not_chegual_quan = self.dynamicCall("GetChejanData(int)",
                                                self.realType.REALTYPE['주문체결']['미체결수량'])  # 출력: 15, default: 0
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])  # 출력: -매도, +매수
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            chegual_time_str = self.dynamicCall("GetChejanData(int)",
                                                self.realType.REALTYPE['주문체결']['주문/체결시간'])  # 출력: '151028'

            chegual_price = self.dynamicCall("GetChejanData(int)",
                                             self.realType.REALTYPE['주문체결']['체결가'])  # 출력: 2110  default : ''
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall("GetChejanData(int)",
                                                self.realType.REALTYPE['주문체결']['체결량'])  # 출력: 5  default : ''
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가'])  # 출력: -6000
            current_price = abs(int(current_price))

            first_sell_price = self.dynamicCall("GetChejanData(int)",
                                                self.realType.REALTYPE['주문체결']['(최우선)매도호가'])  # 출력: -6010
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)",
                                               self.realType.REALTYPE['주문체결']['(최우선)매수호가'])  # 출력: -6000
            first_buy_price = abs(int(first_buy_price))

            ######## 새로 들어온 주문이면 주문번호 할당
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number: {}})

            self.not_account_stock_dict[order_number].update({"종목코드": sCode})
            self.not_account_stock_dict[order_number].update({"주문번호": order_number})
            self.not_account_stock_dict[order_number].update({"종목명": stock_name})
            self.not_account_stock_dict[order_number].update({"주문상태": order_status})
            self.not_account_stock_dict[order_number].update({"주문수량": order_quan})
            self.not_account_stock_dict[order_number].update({"주문가격": order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량": not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"원주문번호": origin_order_number})
            self.not_account_stock_dict[order_number].update({"주문구분": order_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간": chegual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가": chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량": chegual_quantity})
            self.not_account_stock_dict[order_number].update({"현재가": current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가": first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매수호가": first_buy_price})

            self.get_detail_account_mystock()
        elif int(sGubun) == 1:  # 잔고

            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)",
                                               self.realType.REALTYPE['잔고']['총매입가'])  # 계좌에 있는 종목의 총매입가
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode: {}})

            self.jango_dict[sCode].update({"현재가": current_price})
            self.jango_dict[sCode].update({"종목코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": like_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가": total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})

            if stock_quan == 0:
                del self.jango_dict[sCode]

    def Stocks_Portfolio_Initialize(self, port_sel):
        portfolio_list = self.DB.DB_LOAD_TABLE_LIST("stocks_portfolio")
        # 1. portfolio data load
        # 포트폴리오 설정이 안되어있을 경우
        if len(portfolio_list) == 0:
            self.logging.logger.debug('There are not STOCKS PORTFOLIO')
            self.quant_algo_fnc(port_sel, 0.4)
        # 포트폴리오 설정이 되어있을경우 df 로드
        else:
            if len(portfolio_list) >= 2:
                self.logging.logger.debug('Please Check Your STOCKS PORTFOLIO!')
            else:
                for port in portfolio_list:
                    if port == port_sel:
                        self.port_df = self.DB.DB_LOAD_Table("stocks_Portfolio", port)
                        self.port_df = self.port_df.set_index("code")
                # 키움 잔고데이터 비교

    def read_code(self):
        #portfolio_list = self.DB.DB_LOAD_Table('system_parameter', 'meme_portfolio', multi_index=False)
        #portfolio_list = portfolio_list.set_index('code')
        for jongmok in self.port_df.index:
            stock_code = jongmok
            account_code = stock_code.replace("A","")
            stock_name = self.port_df.loc[stock_code][0]
            stock_price = self.port_df.loc[stock_code][1]
            stock_price = abs(stock_price)
            stock_sell_buy = self.port_df.loc[stock_code][2]
            meme_ratio = float(self.port_df.loc[stock_code][3])
            stock_ratio = float(self.port_df.loc[stock_code][4])
            # 포트폴리오 종목이 account 잔고에 있을때....
            if account_code in self.account_stock_dict.keys():
                a = float(self.account_stock_dict[account_code]["매입금액"].replace(",", ""))
                b = float(self.opw00018_output['single'][3].replace(",", ""))
                scode_ratio =  a / b
                if (stock_ratio * 0.8) < scode_ratio:
                    # account dict 중 비중매입 완료한 경우 계속 감시 필요...조건 만족시 매도 필요
                    #
                    self.portfolio_stock_dict.update({account_code: {"name": stock_name, "meme_price": int(stock_price),
                                                                   "meme": '유지',
                                                                   "meme_ratio": 0,
                                                                   "target_ratio": stock_ratio}})
                    # 매수비중 목표치 이상인 종목은 리스트에서 제외시켜 줌
                    #sql = "DELETE FROM {}.{} WHERE {}={};".format('system_parameter', 'meme_portfolio', 'code', stock_code)
                    #self.DB.DB_DEL_ROW_FROM_TABLE(sql)
                else:
                    need_ratio = stock_ratio - scode_ratio
                    cur_price = self.get_current_price(account_code)
                    if stock_price > (cur_price * 1.03):
                        stock_price = cur_price
                    else:
                        # elif stock_price <= (cur_price*1.03):
                        pass
                    self.portfolio_stock_dict.update({account_code: {"name": stock_name, "meme_price": int(stock_price),
                                                                   "meme": stock_sell_buy,
                                                                   "meme_ratio": need_ratio,
                                                                   "target_ratio": stock_ratio}})
            # 포트폴리오 종목이 account 잔고에 없을때....
            else:
                cur_price = self.get_current_price(account_code)
                if stock_price > (cur_price * 1.03):
                    stock_price = cur_price
                else:
                    pass
                self.portfolio_stock_dict.update(
                    {account_code: {"name": stock_name, "meme_price": int(stock_price), "meme": stock_sell_buy, "meme_ratio": stock_ratio, "target_ratio": stock_ratio}})
        # 포트폴리오 리스트에 없는 종목인 경우?
        for stock in self.account_stock_dict.keys():
            if stock in self.portfolio_stock_dict.keys():
                pass
            elif stock in self.account_stock_dict.keys():
                self.portfolio_stock_dict.update({stock: {"name": stock_name, "meme_price": int(stock_price),
                                                          "meme": '매도',
                                                          "meme_ratio": 0,
                                                          "target_ratio": stock_ratio}})
            else:
                self.portfolio_stock_dict.update({stock : {"name": stock_name, "meme_price": int(stock_price),
                                                                 "meme": '유지',
                                                                 "meme_ratio": 0,
                                                                 "target_ratio": stock_ratio}})
        temp_data = pd.DataFrame(data=self.portfolio_stock_dict)
        temp_data = temp_data.T.reset_index()
        temp_data.rename(columns={'index':'code'}, inplace=True)
        self.DB.DB_SAVE('system_parameter', 'meme_portfolio', temp_data)
        self.logging.logger.debug('SUCCESS UPDATE meme_portfolio')

        self.screen_number_setting()
        QTest.qWait(3000)

        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE['장시작시간']['장운영구분'], "0")
        real_reg_list = set(list(self.portfolio_stock_dict.keys())+list(self.account_stock_dict.keys()))
        #real_reg_list = set(real_reg_list)
        #for code in self.portfolio_stock_dict.keys():
        for code in real_reg_list:
            if code in self.portfolio_stock_dict.keys():
                screen_num = self.portfolio_stock_dict[code]['스크린번호']
            else:
                screen_num = '5002'
            fids = self.realType.REALTYPE['주식체결']['체결시간']
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

        self.REAL_REG.start()

    def set_realtime_stock(self, code, name, meme_price, meme_type, stock_ratio):
        screen_num = "5002"
        self.portfolio_stock_dict.update({code: {}})
        self.portfolio_stock_dict.update(
            {code: {"name": name, "meme_price": int(meme_price), "meme": meme_type,
                          "meme_ratio": stock_ratio, "target_ratio": stock_ratio}})
        self.portfolio_stock_dict[code].update({"스크린번호": screen_num})
        #self.screen_number_setting()
        fids = self.realType.REALTYPE['주식체결']['체결시간']
        QTest.qWait(3000)
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")


    def read_code_fromFile(self):
        if os.path.exists("files/condition_stock.txt"): # 해당 경로에 파일이 있는지 체크한다.
            f = open("files/condition_stock.txt", "r", encoding="utf8") # "r"을 인자로 던져주면 파일 내용을 읽어 오겠다는 뜻이다.
            #try:
            lines = f.readlines() #파일에 있는 내용들이 모두 읽어와 진다.
            for line in lines: #줄바꿈된 내용들이 한줄 씩 읽어와진다.
                if line != "":
                    ls = line.split("\t")
                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = int(ls[2].split("\n")[0])
                    stock_price = abs(stock_price)
                    stock_sell_buy = ls[3]
                    stock_ratio = float(1 / lines.__len__())
                    # 만일 계좌에 있는 종목이라면 포트폴리오 등록X
                    if stock_code in self.account_stock_dict.keys():
                        scode_ratio = float(self.account_stock_dict[stock_code]["매입금액"].replace(",","")) / float(self.opw00018_output['single'][3].replace(",",""))
                        if (stock_ratio * 0.8) < scode_ratio:
                            pass
                        else:
                            stock_ratio = stock_ratio - scode_ratio
                            cur_price = self.get_current_price(stock_code)
                            if stock_price > (cur_price*1.03):
                                stock_price = cur_price
                            else:
                            #elif stock_price <= (cur_price*1.03):
                                pass
                            self.portfolio_stock_dict.update({stock_code: {"종목명": stock_name, "매수희망가": stock_price,
                                                                           "비중": stock_ratio,
                                                                           "매수_매도": stock_sell_buy}})
                    else:
                        cur_price = self.get_current_price(stock_code)
                        if stock_price > (cur_price * 1.03):stock_price = cur_price
                        else:pass
                        self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "매수희망가":stock_price, "비중":stock_ratio, "매수_매도":stock_sell_buy}})
            f.close()
            #except:
            #    pass
    def get_current_price(self, code):
        df = fdr.DataReader(code.replace("A",""))
        ret = df.iloc[-1]['Close']
        return ret

    def screen_number_setting(self):
        screen_overwrite = []
        # 계좌평가잔고내역에 있는 종목들
        '''
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        # 미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']
            if code not in screen_overwrite:
                screen_overwrite.append(code)
        '''
        # 포트폴리로에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린번호 할당
        cnt = 0
        for code in screen_overwrite:
            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)
            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)
            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)
            if (code in self.portfolio_stock_dict.keys()) and (code not in self.prev_screen_overwrite):
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})
            elif (code not in self.portfolio_stock_dict.keys()) and (code not in self.prev_screen_overwrite):
                self.portfolio_stock_dict.update(
                    {code: {"스크린번호": str(self.screen_real_stock), "주문용스크린번호": str(self.screen_meme_stock)}})
            cnt += 1
        self.prev_screen_overwrite = screen_overwrite.copy()

    def _receive_real_data(self, sCode, sRealType, sRealData):
        code = 'A' + sCode
        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분']  # (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)

            if value == '0':
                self.logging.logger.debug("장 시작 전")

            elif value == '3':
                self.logging.logger.debug("장 시작")

            elif value == "2":
                self.logging.logger.debug("장 종료, 동시호가로 넘어감")

            elif value == "4":
                self.logging.logger.debug("3시30분 장 종료")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[code]['스크린번호'], code)

                QTest.qWait(5000)

                #self.file_delete()
                #self.Granbill_calculator_fnc(type='Naver', market='10')
                #self.Granbill_calculator_fnc(type='Naver', market='0')

                sys.exit()

        elif sRealType == "주식체결":

            a = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['체결시간'])  # 출력 HHMMSS
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['현재가'])  # 출력 : +(-)2520
            b = abs(int(b))
            c = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['전일대비'])  # 출력 : +(-)2520
            c = abs(int(c))
            d = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['등락율'])  # 출력 : +(-)12.98
            d = float(d)
            e = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['(최우선)매도호가'])  # 출력 : +(-)2520
            e = abs(int(e))
            f = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['(최우선)매수호가'])  # 출력 : +(-)2515
            f = abs(int(f))
            g = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['거래량'])  # 출력 : +240124  매수일때, -2034 매도일 때
            g = abs(int(g))
            h = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['누적거래량'])  # 출력 : 240124
            h = abs(int(h))
            i = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['고가'])  # 출력 : +(-)2530
            i = abs(int(i))
            j = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['시가'])  # 출력 : +(-)2530
            j = abs(int(j))
            k = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['저가'])  # 출력 : +(-)2530
            k = abs(int(k))
            # 포트폴리오에는 없지만 realreg에 등록된 경우
            # 장중 추가 어떤 알고리즘에 의해 매수종목으로 등록된 경우?
            if sCode not in self.portfolio_stock_dict:
                if sCode in self.account_stock_dict.keys():  # 포트폴리오 매수리스트는 없고 이미 비율대로 매수된 종목일
                    pass
                else:
                    self.set_realtime_stock(sCode)

            self.portfolio_stock_dict[sCode].update({"체결시간": a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비": c})
            self.portfolio_stock_dict[sCode].update({"등락율": d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": f})
            self.portfolio_stock_dict[sCode].update({"거래량": g})
            self.portfolio_stock_dict[sCode].update({"누적거래량": h})
            self.portfolio_stock_dict[sCode].update({"고가": i})
            self.portfolio_stock_dict[sCode].update({"시가": j})
            self.portfolio_stock_dict[sCode].update({"저가": k})
            self.REAL_REG.account_stock_dict = self.account_stock_dict
            self.REAL_REG.portfolio_stock_dict = self.portfolio_stock_dict
            self.REAL_REG.jango_dict = self.jango_dict
            self.REAL_REG.not_account_stock_dict = self.not_account_stock_dict
            self.REAL_REG.use_money = self.use_money
            self.data_queue.put(sCode)



    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "예수금상세현황요청":
            self._opw00001(rqname, trcode)
            self.stop_screen_cancel(self.screen_my_info)

        elif rqname == "계좌평가잔고내역요청":
            self._opw00018(rqname, trcode, next)

        elif rqname == "실시간미체결요청":
            self._opt10075(screen_no, rqname, trcode, record_name, next)

        elif rqname == "주식일봉차트조회":
            self._opt10081(screen_no, rqname, trcode, record_name, next)

        elif rqname == "주식분봉차트조회":
            self._opt10080(screen_no, rqname, trcode, record_name, next)

    #        try:
    #            self.tr_event_loop.exit()
    #        except AttributeError:
    #            pass
    # ============================================================================================
    # 키움에서 해당스크린번호를 계속 인식하고 있음.. 불필요한 요청상태로 남아있기 때문에 삭제..
    def stop_screen_cancel(self, sScrNo=None):
        self.dynamicCall("DisconnectRealData(Qstring)", sScrNo)

    # ============================================================================================

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        QMessageBox.about(self, "m",
                          '구분:' + str(self.get_chejan_data(gubun)) + '/r/n 종목코드:' + str(self.get_chejan_data(9203)))

        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))

    def get_detail_account_info(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", sPrevNext,
                         self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def get_detail_account_mystock(self, sPrevNext="0"):

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext,
                         self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def get_login_info(self):
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")  # 계좌번호 반환
        account_num = account_list.split(';')[0]
        #time.sleep(10)
        self.account_num = account_num
        self.REAL_REG.account_num = account_num
        self.logging.logger.debug("계좌번호 : %s" % account_num)

    # 미체결 종목 현황
    def not_conclude_account(self, sPrevNext="0"):
        print("미체결 종목정보")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext,
                         self.screen_my_info)
        self.detail_account_info_event_loop.exec_()
        #미체결정보 모두 확인 후 코드를 읽자
        self.read_code()

    def merge_dict(self):
        self.all_stock_dict.update({"계좌평가잔고내역": self.account_stock_dict})
        self.all_stock_dict.update({'미체결종목': self.not_account_stock_dict})
        self.all_stock_dict.update({'포트폴리오종목': self.portfolio_stock_dict})

    def tick_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(3600)  # 3.6초마다 딜레이를 준다.

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "15")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        # if date != None:
        #    self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식분봉차트조회", "opt10080", sPrevNext,
                         self.screen_calculation_stock)  # Tr서버로 전송 -Transaction

        self.calculator_event_loop.exec_()

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(3600)  # 3.6초마다 딜레이를 준다.

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext,
                         self.screen_calculation_stock)  # Tr서버로 전송 -Transaction

        self.calculator_event_loop.exec_()

    def _opw00001(self, rqname, trcode):
        self.deposit_d2 = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.deposit_d2 = self.change_format_money(self.deposit_d2)
        deposit = self._comm_get_data(trcode, "", rqname, 0, "예수금")
        self.deposit = int(deposit)

        use_money = float(self.deposit) * self.use_money_percent
        self.use_money = int(use_money)
        #self.use_money = self.use_money / 4

        output_deposit = self._comm_get_data(trcode, "", rqname, 0, "출금가능금액")
        self.output_deposit = int(output_deposit)

        self.logging.logger.debug("예수금 : %s" % self.output_deposit)

        self.stop_screen_cancel(self.screen_my_info)

        self.detail_account_info_event_loop.exit()

    def _opt10080(self, screen_no, rqname, trcode, record_name, next):
        code = self._comm_get_data(trcode, "", rqname, 0, "종목코드")
        code = code.strip()
        # 종목조회 시 한번에 600개 조회가능함... 600개 넘어가면 NEXT=2로 요청
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            start_price = self._comm_get_data(trcode, "", rqname, i, "시가")
            high_price = self._comm_get_data(trcode, "", rqname, i, "고가")
            low_price = self._comm_get_data(trcode, "", rqname, i, "저가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            # value = self._comm_get_data(trcode, "", rqname, i, "거래량")
            # trading_value = self._comm_get_data(trcode, "", rqname, i, "거래대금")

            self.tick_ohlcv['date'].append(date)
            self.tick_ohlcv['open'].append(int(start_price))
            self.tick_ohlcv['high'].append(int(high_price))
            self.tick_ohlcv['low'].append(int(low_price))
            self.tick_ohlcv['close'].append(abs(int(current_price)))
            # self.ohlcv['volume'].append(int(value))
            # self.ohlcv['trading_value'].append(int(trading_value))

        if next == 2:
            self.tick_kiwoom_db(code=code, sPrevNext=next)

        else:
            self.logging.logger.debug("총 일수 %s" % len(self.tick_ohlcv['date']))
        temp_df = pd.DataFrame(data=self.tick_ohlcv)
        temp_df = temp_df.set_index("date").fillna(method='ffill')
        # 이평선 돌파 알고리즘
        if self.AV_algo_on and not temp_df["close"].dropna().empty:
            pass_success = self.Trade_algo.Average_Break_Strategy(temp_df, code, 120, self.logging, "tick",
                                                                  real_trade=True)
            if pass_success == True:
                self.logging.logger.debug("조건부 통과됨")
                code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
                f = open("files/condition_stock.txt", "a", encoding="utf8")
                f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.tick_ohlcv['close'][0])))
                f.close()
            else:
                self.logging.logger.debug("조건부 통과 못함")

        # temp_df = pd.DataFrame(data = self.tick_ohlcv)
        # temp_df = temp_df.set_index("date").fillna(method='ffill')
        new_code = "A" + code
        temp_df.columns = [[new_code] * len(temp_df.columns), temp_df.columns]
        if self.tick_acq_num == 0:
            self.tick_data = temp_df
        else:
            self.tick_data = pd.concat([self.tick_data, temp_df], axis=1)
        # print(self.tick_data)
        self.reset_tick_ohlcv()
        self.calculator_event_loop.exit()

    def _opt10081(self, screen_no, rqname, trcode, record_name, next):
        code = self._comm_get_data(trcode, "", rqname, 0, "종목코드")
        code = code.strip()
        # 종목조회 시 한번에 600개 조회가능함... 600개 넘어가면 NEXT=2로 요청
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            start_price = self._comm_get_data(trcode, "", rqname, i, "시가")
            high_price = self._comm_get_data(trcode, "", rqname, i, "고가")
            low_price = self._comm_get_data(trcode, "", rqname, i, "저가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            value = self._comm_get_data(trcode, "", rqname, i, "거래량")
            trading_value = self._comm_get_data(trcode, "", rqname, i, "거래대금")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(start_price))
            self.ohlcv['high'].append(int(high_price))
            self.ohlcv['low'].append(int(low_price))
            self.ohlcv['close'].append(int(current_price))
            self.ohlcv['volume'].append(int(value))
            self.ohlcv['trading_value'].append(int(trading_value))

        if next == 2:
            self.day_kiwoom_db(code=code, sPrevNext=next)

        else:
            self.logging.logger.debug("총 일수 %s" % len(self.ohlcv['date']))
        # 이평선 돌파 알고리즘
        if self.AV_algo_on:
            pass_success = self.Trade_algo.Average_Break_Strategy(self.ohlcv, code, 120, self.logging, "day",
                                                                  real_trade=True)

        if pass_success == True:
            self.logging.logger.debug("조건부 통과됨")
            code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
            f = open("files/condition_stock.txt", "a", encoding="utf8")
            f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.ohlcv['close'][0])))
            f.close()
        else:
            self.logging.logger.debug("조건부 통과 못함")

        self.reset_ohlcv()
        self.calculator_event_loop.exit()

    def _opt10075(self, screen_no, rqname, trcode, record_name, next):
        print("")
        rows = self._get_repeat_cnt(rqname, trcode)
        for i in range(rows):
            code = self._comm_get_data(trcode, "", rqname, i, "종목코드").strip()
            code_nm = self._comm_get_data(trcode, rqname, i, "종목명").strip()
            order_no = self._comm_get_data(trcode, rqname, i, "주문번호").strip()
            order_state = self._comm_get_data(trcode, rqname, i, "주문상태").strip()
            order_quantity = self._comm_get_data(trcode, rqname, i, "주문수량").strip()
            order_price = self._comm_get_data(trcode, rqname, i, "주문가격").strip()
            order_gubun = self._comm_get_data(trcode, rqname, i, "주문구분").strip().lstrip('+').lstrip('-')
            order_not_quantity = self._comm_get_data(trcode, rqname, i, "미체결수량").strip()
            order_ok_quantity = self._comm_get_data(trcode, rqname, i, "체결량").strip()
            if order_no in self.not_account_stock_dict:
                pass
            else:
                self.not_account_stock_dict[order_no] = {}
            self.not_account_stock_dict[order_no].update({'종목코드': code})
            self.not_account_stock_dict[order_no].update({'종목명': code_nm})
            self.not_account_stock_dict[order_no].update({'주문상태': order_state})
            self.not_account_stock_dict[order_no].update({'주문수량': order_quantity})
            self.not_account_stock_dict[order_no].update({'주문가격': order_price})
            self.not_account_stock_dict[order_no].update({'주문구분': order_gubun})
            self.not_account_stock_dict[order_no].update({'미체결수량': order_not_quantity})
            self.not_account_stock_dict[order_no].update({'체결량': order_ok_quantity})

            print("미체결수량: %s" % (order_not_quantity))
        self.detail_account_info_event_loop.exit()

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString,QString)", "Getservergubun", "")
        return ret

    # 계좌평가잔고내역요청
    def _opw00018(self, rqname, trcode, next):

        total_purchase_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, 0, "총매입금액"))
        total_eval_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, 0, "총평가금액"))
        total_eval_profit_loss_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액"))
        total_earning_rate = self.change_format_rate(self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)"))
        estimated_deposit = self.change_format_money(self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산"))

        self.opw00018_output['single'].append(total_purchase_price)
        self.opw00018_output['single'].append(total_eval_price)
        self.opw00018_output['single'].append(total_eval_profit_loss_price)
        self.opw00018_output['single'].append(estimated_deposit)

        if self.get_server_gubun() == 1:
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)
        print(self.opw00018_output['single'])
        self.logging.logger.debug(
            "계좌평가잔고내역요청 싱글데이터 : %s - %s - %s" % (
            total_purchase_price, total_eval_profit_loss_price, total_earning_rate))

        cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(cnt):
            code = self._comm_get_data(trcode, "", rqname, i, "종목번호")  # 출력 : A039423 // 알파벳 A는 장내주식, J는 ELW종목, Q는 ETN종목
            code = code.strip()[1:]
            code_nm = self._comm_get_data(trcode, "", rqname, i, "종목명")
            stock_quantity = self.change_format_money(self._comm_get_data(trcode, "", rqname, i, "보유수량"))
            buy_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, i, "매입가"))
            current_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, i, "현재가"))
            eval_profit_loss_price = self.change_format_money(self._comm_get_data(trcode, "", rqname, i, "평가손익"))
            earning_rate = self.change_format_rate(self._comm_get_data(trcode, "", rqname, i, "수익률(%)"))
            total_chegual_price = self.change_format_rate(self._comm_get_data(trcode, "", rqname, i, "매입금액"))
            possible_quantity = self._comm_get_data(trcode, "", rqname, i, "매매가능수량")

            if code in self.account_stock_dict:  # dictionary 에 해당 종목이 있나 확인
                pass
            else:
                self.account_stock_dict[code] = {}

            self.account_stock_dict[code].update({"종목명": code_nm})
            self.account_stock_dict[code].update({"보유수량": stock_quantity})
            self.account_stock_dict[code].update({"매입가": buy_price})
            self.account_stock_dict[code].update({"수익률(%)": earning_rate})
            self.account_stock_dict[code].update({"현재가": current_price})
            self.account_stock_dict[code].update({"매입금액": total_chegual_price})
            self.account_stock_dict[code].update({'매매가능수량': possible_quantity})

        self.logging.logger.debug("sPreNext : %s" % next)
        print("계좌에 가지고 있는 종목은 %s " % cnt)
        if self.remained_data:
            self.get_detail_account_mystock(sPrevNext="2")
        else:
            self.detail_account_info_event_loop.exit()

    def reset_opw00018(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def reset_ohlcv(self):
        self.ohlcv['date'] = []
        self.ohlcv['open'] = []
        self.ohlcv['high'] = []
        self.ohlcv['low'] = []
        self.ohlcv['close'] = []
        self.ohlcv['volume'] = []
        # self.ohlcv['trading_value'].clear()

    def reset_tick_ohlcv(self):
        self.tick_ohlcv['date'] = []
        self.tick_ohlcv['open'] = []
        self.tick_ohlcv['high'] = []
        self.tick_ohlcv['low'] = []
        self.tick_ohlcv['close'] = []

    def system_para_save(self):
        # 당일 매수가 불가했던 종목들의 경우 로그를 남겨두고 매매를 계속 할것인지 판단하자.,,..,
        #not_account_stock = self.not_account_stock_dict.keys()
        #self.fs.SQL.DB_SAVE(temp, self.Kiwoom_DB_PATH, "not_account_stock")
        temp = pd.DataFrame(self.Kiwoom_initial_setting, index=list(range(len(self.Kiwoom_initial_setting.keys()))))
        self.DB.DB_SAVE('system_parameter', "fs_last_update", temp)

    ################################################# 데이타수집 ############################################################
    def tick_data_acq(self, market='10'):
        code_list = self.get_code_list_by_market(market)
        self.logging.logger.debug("코스닥 갯수 %s " % len(code_list))
        self.AV_algo_on = True
        for idx, code in enumerate(code_list):
            self.tick_acq_num = idx
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)  # 스크린 연결 끊기
            self.logging.logger.debug(
                "%s / %s :  KOSDAQ Stock Code : %s is updating... " % (idx + 1, len(code_list), code))
            self.tick_kiwoom_db(code=code)
        self.tick_data = self.tick_data[-900:].dropna(axis=1)
        if market == "10":
            path = self.ROOT_DIR + "\\files\\kodaq_AV_algo_df.xlsx"
        else:
            path = self.ROOT_DIR + "\\files\\kospi_AV_algo_df.xlsx"
        self.tick_data.to_excel(path)
        self.AV_algo_on = False

    ################################################# 매수전략 #############################################################
    # 그랜빌 4법칙 전략 수정 필요
    # 거의 안걸림.....
    # day_tick : 일봉 or 분봉
    # acq_type : 네이버금융 or 키움증권API
    # market : 0(kospi), 10(kosdaq)
    def Granbill_calculator_fnc(self, day_tick='day', acq_type='Naver', market='10'):
        code_list = self.get_code_list_by_market(market)
        self.AV_algo_on = True  # 알고리즘 ON
        if market == '10':
            self.logging.logger.debug("코스닥 갯수 %s " % len(code_list))
        else:
            self.logging.logger.debug("코스피 갯수 %s " % len(code_list))
        for idx, code in enumerate(code_list):
            self.tick_acq_num = idx  # tick데이타에서만 사용...데이터프레임 합치기 위해...
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)  # 스크린 연결 끊기
            # 로그
            if market == '10':
                self.logging.logger.debug(
                    "%s / %s :  KOSDAQ Stock Code : %s is updating... " % (idx + 1, len(code_list), code))
            else:
                self.logging.logger.debug(
                    "%s / %s :  KOSPI Stock Code : %s is updating... " % (idx + 1, len(code_list), code))
            # 키움 데이터 수집 '틱' , '데이' 분류
            if type == 'KW' and day_tick == 'day':
                self.day_kiwoom_db(code=code)
            elif day_tick == 'tick':
                self.tick_kiwoom_db(code=code)
            else:
                # 그랜빌 4법칙
                pass_success, price_data_latest = self.Trade_algo.Average_Break_Strategy(code, 120, self.logging)
                if pass_success == True:
                    self.logging.logger.debug("조건부 통과됨")
                    code_nm = self.dynamicCall("GetMasterCodeName(QString)", code)
                    f = open(self.AV_Algo_result_path, "a", encoding="utf8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(price_data_latest['close'][0])))
                    # test = str(price_data_latest['close'][0])
                    f.close()
                else:
                    self.logging.logger.debug("조건부 통과 못함")
        # 데이터 저장 in case of "tick"
        if day_tick == 'tick':
            self.tick_data = self.tick_data[-900:].dropna(axis=1)
            if market == "10":
                path = self.ROOT_DIR + "\\files\\kodaq_AV_algo_df.xlsx"
            else:
                path = self.ROOT_DIR + "\\files\\kospi_AV_algo_df.xlsx"
            self.tick_data.to_excel(path)
        self.AV_algo_on = False

        return True
    def decision_strategy_date(self, start):
        start = str(start)
        start_year = start.split('-')[0]
        start_month = start.split('-')[1]
        if (int(start_month) > 3) & (int(start_month) < 6):
            strategy_date = str(int(start_year) - 1) + '/' + '12'
        elif (int(start_month) > 5) & (int(start_month) < 9):
            strategy_date = str(start_year) + '/' + '03'
        elif (int(start_month) > 8) & (int(start_month) < 12):
            strategy_date = str(start_year) + '/' + '06'
        else:
            if int(start_month) == 12:
                strategy_date = str(start_year) + '/' + '09'
            else:
                strategy_date = str(int(start_year) - 1) + '/' + '09'
        return strategy_date

    def get_latest_file(self, path, type_file='value tool'):
        make_time_max = 0
        prev_ctime = 0
        for num, file in enumerate(os.listdir(path)):
            if type_file in file:
                if ".xlsb" in file:
                    ctime = int(re.findall('\d+', file)[0])
                    if num == 0:
                        latest_file = file
                        prev_ctime = ctime
                    elif ctime > prev_ctime:
                        latest_file = file
                        prev_ctime = ctime
                    else:
                        continue
        return os.path.join(path, latest_file)

    def quant_algo_fnc(self, quant_strategy, currency_ratio):
        '''
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.fs.Excel_Value_now_Path)).strftime("%Y-%m-%d")
        self.Kiwoom_initial_setting.update({'fs_last_update': mtime})
        last_time = self.DB.DB_LOAD_Table('system_parameter', 'fs_last_update', multi_index=False)
        last_time = self.fs.SQL.DB_LOAD_Table("fs_last_update", )
        try:
            if last_time.index.empty:
                list_update= True
            else :
                last_time = last_time.index[0]
                if mtime == last_time:
                    list_update = False
                else:
                    list_update= True
        except:
            list_update= True

        if list_update : finance_data = self.fs.get_Finance_now_excel()
        else : finance_data = self.DB.DB_LOAD_Table('finance', self.fs.EXCEL_NOW_FS_TABLE)
        '''
        table_list = self.DB.DB_LOAD_TABLE_LIST(self.DB_Valuetool)
        #1. 분기재무재표 data저장 최신본 확인
        quarter_finance_list = self.DB.DB_LOAD_TABLE_LIST(self.DB_finance_quarter)
        date=datetime.datetime.today()
        cur_date="{}-{}".format(date.year, date.month)
        check_finance_date=self.decision_strategy_date(cur_date)
        current_path=os.getcwd()
        current_path=Path(current_path)
        # 2. Rim data 최신본 확인
        rim_list = self.DB.DB_LOAD_TABLE_LIST(self.DB_finance_rim)
        v_path = 'ValueTool\Valuetool'
        path = os.path.join(current_path.parent.parent.parent, v_path)
        excel_path = self.get_latest_file(path, '가치평가 tool')
        try:
            check_rim_date=re.findall('\d+',str(excel_path).split("\\")[-1])[0]
        except:
            check_rim_date = re.findall('\d+', str(excel_path).split("\\")[-1])

        check_finance_date = self.decision_strategy_date(cur_date)

        current_path = Path(os.getcwd())
        v_path = 'ValueTool\Valuetool'
        total_path = os.path.join(current_path.parent.parent.parent, v_path)
        excel_path = self.get_latest_file(total_path, '가치평가 tool')
        self.logging.logger.debug("가치평가 file_path : %s", excel_path)
        #Rim_df = pd.read_excel(excel_path, sheet_name="RIM")

        if (check_finance_date in quarter_finance_list) and (check_rim_date in rim_list):
            self.logging.logger.debug("%s 최신 Finance DATA OK....", check_finance_date)
            self.logging.logger.debug("%s 최신 rim DATA OK....", check_rim_date)

            finance_data = self.DB.DB_LOAD_Table(self.DB_Valuetool, table_list[-1])
            trailing_index_quarter = check_finance_date
            rim_index=check_rim_date
            #finance_quarter_data = self.DB.DB_LOAD_Table(self.DB_finance_quarter, check_finance_date)
            #finance_rim_data = self.DB.DB_LOAD_Table(self.DB_finance_rim, check_rim_date)

            # 3. Price Data GET

                # ==============================================================================================================
            # 전략 선택
            # ==============================================================================================================
            if quant_strategy == 'PER_ROE':
                rank = self.Trade_algo.get_value_rank_now(finance_data, value_type='PER', quality_type='ROE', num=30,
                                                          rim_on=True, fs_comp_del_on=True,
                                                          BJ_Filter=True, apply_rim_L=2)
                f = open("files/condition_stock.txt", "a", encoding="utf8")
                for code in rank.index:
                    f.write("%s\t%s\t%s\t%s\n" % (code, rank.loc[code]["종목"], rank.loc[code]["현재가"], "매수"))
                f.close()

                # rank.to_excel(self.quant_result_path + "\\PER_ROE.xlsx")

            elif quant_strategy == '마법공식2':
                rank = self.Trade_algo.get_value_rank_now(finance_data, value_type='PBR', quality_type='GP/A', num=30,
                                                          rim_on=True, fs_comp_del_on=True,
                                                          BJ_Filter=True, apply_rim_L=2)
                f = open("Kiwoom/files/condition_stock.txt", "a", encoding="utf8")
                for code in rank.index:
                    f.write("%s\t%s\t%s\t%s\n" % (code, rank.loc[code]["종목"], rank.loc[code]["현재가"], "매수"))
                f.close()
                # rank.to_excel(self.quant_result_path + "\\마법공식2.xlsx")

            elif quant_strategy == '마법공식':
                rank = self.Trade_algo.get_value_rank_now(finance_data, value_type='자본수익률', quality_type='이익수익률', num=30,
                                                          rim_on=True, fs_comp_del_on=True,
                                                          BJ_Filter=True, apply_rim_L=2)
                f = open("files/condition_stock.txt", "a", encoding="utf8")
                for code in rank.index:
                    f.write("%s\t%s\t%s\t%s\n" % (code, rank.loc[code]["종목"], rank.loc[code]["현재가"], "매수"))
                f.close()
            elif quant_strategy == '강환국_울트라_소형주':
                comp_size = quant_strategy.split("_")[2]
                invest_in_df = self.Trade_algo.make_invest_from_quarter(trailing_index_quarter)
                #invest_in_df.to_excel('f:\\invest_in_df.xlsx')
                # print(len(invest_in_df),strategy_date, start)
                invest_df = self.Trade_algo.select_code_by_price_excel(invest_in_df, comp_size, rim_on=True, fs_comp_del_on=True, BJ_Filter=False, apply_rim_L=2)
                #invest_df.to_excel('f:\\invest_df.xlsx')
                value_factor = []
                value_factor.append(['PER', "오름차순", 0.2, None])
                value_factor.append(['PBR', "오름차순", 0.2, None])
                value_factor.append(['PFCR', "오름차순", 0.0, None])
                value_factor.append(['GP_A', "내림차순", 0.0, None])
                value_factor.append(['영업이익-차입금_증가비율', "내림차순", None, None])
                value_factor.append(['자산성장률_QOQ', "내림차순", None, None])
                value_factor.append(['영업이익성장률_QOQ', "내림차순", None, None])
                value_factor.append(['지배지분순이익성장률_QOQ', "내림차순", None, None])
                rank = self.Trade_algo.ultra_value_strategy_by_kang(invest_df, value_factor, stock_num=20)
                stock_list=self.DB.DB_LOAD_Table("stocks_lists", "stocks_lists_all")
                stock_list=stock_list.set_index('Symbol')
                rank['종목']=[stock_list.loc[x,'Name'] for x in rank.index]
                f = open("files/condition_stock.txt", "a", encoding="utf8")
                for code in rank.index:
                    f.write("%s\t%s\t%s\t%s\n" % (code, rank.loc[code,"종목"], rank.loc[code,"현재가"], "매수"))
                f.close()
                #rank.to_excel(self.quant_result_path + "\\마법공식.xlsx")
            # rank list DB에 저장
            temp = rank[['종목','현재가']]

            #price_list = [fdr.DataReader(x).iloc[-1]['Close'] for x in temp.index]
            #temp['현재가'] = price_list
            temp['meme'] = '매수'
            temp['meme_ratio'] = (1-currency_ratio)*float(1/len(rank))
            temp['target_ratio'] = (1-currency_ratio)*float(1/len(rank))
            temp['current_ratio'] = 0

            temp = temp.reset_index()
            temp.rename(columns={'index': 'code','종목': 'name','현재가': 'meme_price'}, inplace=True)
            #temp.columns =['code','name','meme_price','meme','meme_ratio','target_ratio']

            self.DB.DB_SAVE('stocks_portfolio',quant_strategy, temp)
            #mtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.fs.Excel_Value_now_Path)).strftime("%Y-%m-%d")
            #self.Kiwoom_initial_setting.update({'fs_last_update': mtime})
            #self.system_para_save()
        elif (check_finance_date not in quarter_finance_list) and (check_rim_date in rim_list):
            self.logging.logger.debug("%s 최신 Finance DATA 업데이트 필요!..", check_finance_date)
            self.logging.logger.debug("%s 최신 rim DATA OK....", check_rim_date)
            value = GET_EXCEL_DATA(self.get_latest_file(path, 'value tool'))
            value.Get_Stocks_Finance_Quarter()
            self.logging.logger.debug("%s 최신 Finance DATA 업데이트 완료!..", str(self.get_latest_file(path, 'value tool')))
            self.quant_algo_fnc(quant_strategy, currency_ratio)
            rank = []

        elif (check_finance_date in quarter_finance_list) and (check_rim_date not in rim_list):
            self.logging.logger.debug("%s 최신 Finance DATA OK..", check_finance_date)
            self.logging.logger.debug("%s 최신 rim DATA 업데이트 필요!..", check_rim_date)
            GET_RIM_DATA(path)
            self.quant_algo_fnc(quant_strategy, currency_ratio)
            rank = []
        else:
            self.logging.logger.debug("%s 최신 Finance DATA 업데이트 필요!..", check_finance_date)
            self.logging.logger.debug("%s 최신 rim DATA 업데이트 필요!..", check_rim_date)
            value=GET_EXCEL_DATA(self.get_latest_file(path, 'value tool'))
            value.Get_Stocks_Finance_Quarter()
            self.logging.logger.debug("%s 최신 Finance DATA 업데이트 완료!..", str(self.get_latest_file(path, 'value tool')))
            GET_RIM_DATA(path)
            self.logging.logger.debug("%s 최신 rim DATA 업데이트 완료!..", str(excel_path))
            self.quant_algo_fnc(quant_strategy, currency_ratio)
            rank=[]
        return rank

    def HTH_quant_algo_fnc(self):
        meme_list = self.NB.HTH_Algo_fnc()
        for stock in meme_list :
            code = self.korea_market_stocklist[self.korea_market_stocklist['name'] == stock[0]].index[0]
            self.portfolio_stock_dict.update({code:{"종목명":stock[0], "매수희망가":int(stock[1]), "비중":float(stock[2])}})
        self.screen_number_setting()
        #print(self.portfolio_stock_dict)




from multiprocessing import Process

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data_queue = Queue()
    order_queue = Queue()
    kiwoom = Kiwoom(data_queue, order_queue)
    #time.sleep(10)
    #data_queue2 = Queue()
    #order_queue2 = Queue()
    #kiwoom2 = Kiwoom(data_queue2, order_queue2)
    #kiwoom.quant_algo_fnc('마법공식2')
    app.exec_()
