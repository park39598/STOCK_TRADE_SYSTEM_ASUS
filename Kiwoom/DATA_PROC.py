import datetime
import time
import os, sys
#import FinanceDataReader as fdr
ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
#from Kiwoom.config.kiwoomType import RealType
from config.kiwoomType import RealType
from PyQt5.QtTest import QTest
import collections
import pandas as pd

# Thread#2

#=======================================================================================
# 기능: 실시간 종목정보를 파싱하여 오더여부 판단
# 구현요소:  - data/order 큐 저장/로드 기능
#          -
class REAL_REG_PARSING_ORDER(QThread):
    #mutex = QMutex()
    meme_trigger = pyqtSignal(list)
    dict_updata = pyqtSignal()
    def __init__(self, port, data_queue, buy_upper_limit, buy_cancel_limit, sell_upper_limit, sell_lower_limit, stock_quatity, logging):
        super().__init__()
        self.logging = logging
        self.data_queue = data_queue  # 데이터를 받는 용
        self.port_name= port
        #self.order_queue = order_queue  # 주문 요청용

        self.timestamp = None
        self.limit_delta = datetime.timedelta(seconds=2)
        self.account_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.jango_dict = {}
        self.not_account_stock_dict = {}
        self.realType = RealType()
        self.dynamicCall = None
        self.use_money = 0
        self.account_num = None
        self.max_stocks_quatity = stock_quatity
        self.mutex = QMutex()
        #meme_limit 2%
        #주문시 어느정도 상방 몇%까지는 그냥 매수하겠다...
        self.Buy_Upper_limit = buy_upper_limit
        self.Buy_Cancel_limit = buy_cancel_limit
        self.Sell_Upper_Limit = sell_upper_limit
        self.Sell_Lower_Limit = sell_lower_limit
        #중복주문 방지 지연시간
        self.meme_delay=0.5
        # 포트별 ORDER LIST 관리
        # 최종 KW시스템으로의 ORDER CMD가 아닌 포트TASK에서 ORDER TASK로 주문명령에 대한 LOG임
        self.order_list = collections.defaultdict(dict)
        # 노이즈 주문 중복방지 delay 2초
        self.noiseorder_delay = 2

    def run(self):
        while True:
            self.mutex.lock()
            time.sleep(0.1)
            if not self.data_queue.empty():
                data = self.data_queue.get()
                self.account_stock_dict = data[1]
                self.portfolio_stock_dict = data[2]
                self.jango_dict = data[3]
                self.not_account_stock_dict = data[4]
                self.use_money = data[5]
                self.account_num = data[6]
                self.finance = data[7]
                self.thema_screen = data[8]

                print("data queue put :%s" % data[0])
                # 노이즈 주문 제거
                # 짧은간격내 여러번 주문의 경우 노이즈로 판단 Screen
                ret = self.NoiseOrder_Screen(data[0])
                # 기본적 매수 조건들
                if ret : self.process_data(data[0])
                else : pass
            # portfolio 20개 관리
            self.mutex.unlock()

    def NoiseOrder_Screen(self, code):
        now = datetime.datetime.today()
        if code in self.order_list.keys():
            order_time=pd.to_datetime(self.order_list[code][0])
            diff = now - order_time
            # 2초이후 들어온 주문이라면 노이즈가 아닌 ORDER
            if diff.seconds > self.noiseorder_delay:
                ret = True
            # 2초 이내면 노이즈 ORDER이다....
            else:
                ret = False

    def order_emit(self, data):
        # 주문 Queue에 주문을 넣음
        self.timestamp = datetime.datetime.now()  # 이전 주문 시간을 기록함
        #self.order_queue.put(data)
        self.logging.logger.debug("order_queue put :%s" % data)
        self.meme_trigger.emit(data)
        now = datetime.datetime.today().strftime('%H:%M:%S')
        self.order_list.update({data[1][4]:[now, data[0], data[1][5], data[1][6]]})

    # 매수 / 매도 process 따로 두어 구분하자...
    # 불필요한 자원소모 제거
    def Buy_Process(self, data):
        sCode=data
        if self.portfolio_stock_dict[sCode]['(최우선)매수호가'] < (self.portfolio_stock_dict[sCode]['meme_price'] * (1 + (self.Buy_Upper_limit * 0.01))):
            self.logging.logger.debug("매수조건 통과 %s " % sCode)
            result = (self.use_money * self.portfolio_stock_dict[sCode]['meme_ratio'])/ self.portfolio_stock_dict[sCode][
                'meme_price']
            quantity = int(result)
            self.order_emit(["매수",
                             ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode, quantity,
                              self.portfolio_stock_dict[sCode]['meme_price'], self.realType.SENDTYPE['거래구분']['지정가'], ""]])
        # 미체결 주문의 경우
        not_meme_list = list(self.not_account_stock_dict.keys())
        for sCode in not_meme_list:
            order_num = self.not_account_stock_dict[sCode]["주문번호"]
            meme_price = self.not_account_stock_dict[sCode]['주문가격']
            not_quantity = self.not_account_stock_dict[sCode]['미체결수량']
            order_gubun = self.not_account_stock_dict[sCode]['주문구분']
            # 매수후 바로 주문취소가 될수 있으므로 2%의 마진까지는 감안하고 주문
            # 매도호가가 내가 타겟 프라이스보다 x% 높아져있는 상태라면 그냥 주문 취소한다....
            # if order_gubun == "매수" and not_quantity > 0 and (self.portfolio_stock_dict[sCode]['(최우선)매도호가']> (meme_price*(1+self.meme_limit*0.01))):
            if order_gubun == "매수" and not_quantity > 0 and (
                    self.not_account_stock_dict[sCode]['(최우선)매도호가'] > (meme_price * (1 + (self.Buy_Cancel_limit * 0.01)))):
                self.order_emit(
                    ["매수", ["매수취소", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 3, sCode, 0, 0,
                            self.realType.SENDTYPE['거래구분']['지정가'], order_num]])
            elif not_quantity == 0:
                del self.not_account_stock_dict[sCode]

    def Sell_Process(self, data):
        sCode = data
        # 매매 수익률이 -5% 이하 또는 5% 이상일 경우 전량 손절/익절 수행
        # 매도 시 한번에 체결이 되지않으므로 여러번에 걸쳐 매도 주문을 내야할 수있다
        # 매수/매도 주문에 관한 것은 모두  포트폴리오 딕셔너리로 넣자...
        if sCode in self.account_stock_dict.copy().keys():
            # 매도 분류 종목 중 포트폴리오 리스트 속한것  -> 매입가 대비 +-5% 손절 익절 실시
            if sCode in self.portfolio_stock_dict.keys():
                asd = self.account_stock_dict[sCode]
                if self.portfolio_stock_dict[sCode]['target_ratio'] == 0:
                    self.order_emit(
                        ["매도", ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode,
                                asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ""]])

    def WatchDog_Process(self, data):
        sCode = data
        # 매매 수익률이 -5% 이하 또는 5% 이상일 경우 전량 손절/익절 수행
        # 매도 시 한번에 체결이 되지않으므로 여러번에 걸쳐 매도 주문을 내야할 수있다
        # 매수/매도 주문에 관한 것은 모두  포트폴리오 딕셔너리로 넣자...
        if (sCode in self.account_stock_dict.keys()) and (sCode not in self.jango_dict.keys()):
            # 매도 분류 종목 중 포트폴리오 리스트 속한것  -> 매입가 대비 +-5% 손절 익절 실시
            if sCode in self.portfolio_stock_dict.keys():
                asd = self.account_stock_dict[sCode]
                if self.portfolio_stock_dict[sCode]['meme_price'] == 0:
                    meme_rate = 100
                else:
                    meme_rate = (int(self.portfolio_stock_dict[sCode]['현재가']) - int(asd['매입가'].replace(",", ""))) / int(
                        asd['매입가'].replace(",", "")) * 100

                if int(asd['매매가능수량'].replace(",", "")) > 0 and (meme_rate > self.Sell_Upper_Limit or meme_rate < self.Sell_Lower_Limit):
                    self.order_emit(
                        ["매도", ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode,
                                asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ""]])


            # 매도 분류 종목 중 포트폴리오 리스트 속하지 않은것  -> 전량 시장가 매도
            else:
                asd = self.account_stock_dict[sCode]
                self.order_emit(
                    ["매도", ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode,
                            asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ""]])
        # ===========================================================================================================
        # 실시간 등록된 종목이 계좌에 있는 종목일 경우!
        # ===========================================================================================================
        '''
        elif sCode in self.jango_dict.keys():
            jd = self.jango_dict[sCode]
            meme_rate = (self.portfolio_stock_dict[sCode]['현재가'] - jd['매입단가']) / jd['매입단가'] * 100
            if (jd['주문가능수량'] > 0) and (meme_rate > 7 or meme_rate < -3):
                self.order_emit(["매도",
                                 ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode,
                                  jd['주문가능수량'],+
                                  0, self.realType.SENDTYPE['거래구분']['시장가'], ""]]
                                )
        '''

    def process_data(self, data):
        # 시간 제한을 충족하는가?
        # 실시간 등록된 종목이 account stock 리스트에 없고 가지고 있는 종목도 아닐경우!
        # ===========================================================================================================
        sCode = data
        meme = self.portfolio_stock_dict[sCode]['meme']
        if meme == '매수':
            if (self.port_name == "단테떡상이1") or (self.port_name == "단테떡상이2"):
                for thema in  self.thema_screen['0주전'].keys():
                    if sCode in self.thema_screen['0주전'][thema]:
                        self.Buy_Process(data)
                        break
            else:
                self.Buy_Process(data)
        elif meme == '매도':
            self.Sell_Process(data)
        elif meme == '유지':
            self.WatchDog_Process(data)
        elif meme == '주문완료':
            if sCode in list(self.not_account_stock_dict.keys()) :
                if self.not_account_stock_dict[sCode]["미체결수량"] != 0 :
                    pass
                else:
                    self.portfolio_stock_dict[sCode]['meme']='유지'
                #meme 되었는지 확인 필요 not_account_dict확인 or account_dict확인
        else:
            self.portfolio_stock_dict[sCode]['meme']='삭제'

        # 중복주문 방지용.... 여러번 주문되는 경우 방지...
        #QTest.qWait(300)





        # ===========================================================================================================
        # 실시간 등록된 종목이 계좌에 없고 등락율이 2이상일경우...
        # ===========================================================================================================

