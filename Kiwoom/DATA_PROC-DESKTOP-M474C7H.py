import datetime
import time

from PyQt5.QtCore import QThread, pyqtSignal
from config.kiwoomType import RealType
# Thread#2

#=======================================================================================
# 기능: 실시간 종목정보를 파싱하여 오더여부 판단
# 구현요소:  - data/order 큐 저장/로드 기능
#          -
class REAL_REG_PARSING_ORDER(QThread):
    trigger = pyqtSignal()
    dict_updata = pyqtSignal()
    def __init__(self, data_queue, order_queue, logging):
        super().__init__()
        self.logging = logging
        self.data_queue = data_queue  # 데이터를 받는 용
        self.order_queue = order_queue  # 주문 요청용

        self.timestamp = None
        self.limit_delta = datetime.timedelta(seconds=2)
        self.account_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.jango_dict = {}
        self.realType = RealType()
        self.dynamicCall = None
        self.use_money = 0
        self.account_num = None
        #meme_limit 2%
        self.meme_limit = 2

    def run(self):
        while True:
            #self.logging.logger.debug("data acquiring")
            time.sleep(0.1)
            if not self.data_queue.empty():
                data = self.data_queue.get()
                #self.logging.logger.debug("data queue put :%s" % data)
                # 기본적 매수 조건들
                self.process_data(data)


    def order_emit(self, data):
        # 주문 Queue에 주문을 넣음
        self.timestamp = datetime.datetime.now()  # 이전 주문 시간을 기록함
        self.order_queue.put(data)
        self.logging.logger.debug("order_queue put :%s" % data)
        self.trigger.emit()

    def process_data(self, data):
        # 시간 제한을 충족하는가?
        # 실시간 등록된 종목이 account stock 리스트에 없고 가지고 있는 종목도 아닐경우!
        # ===========================================================================================================
        sCode = data
        # 매매 수익률이 -5% 이하 또는 5% 이상일 경우 전량 손절/익절 수행
        # 매도 시 한번에 체결이 되지않으므로 여러번에 걸쳐 매도 주문을 내야할 수있다
        if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
            asd = self.account_stock_dict[sCode]
            meme_rate = (int(self.portfolio_stock_dict[sCode]['현재가']) - int(asd['매입가'].replace(",", ""))) / int(asd['매입가'].replace(",", "")) * 100

            if int(asd['매매가능수량'].replace(",", "")) > 0 and (meme_rate > 5 or meme_rate < -5):
                self.order_emit(["매도",["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode,
                     asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ""]])

        # ===========================================================================================================
        # 실시간 등록된 종목이 계좌에 있는 종목일 경우!
        # ===========================================================================================================
        elif sCode in self.jango_dict.keys():
            jd = self.jango_dict[sCode]
            meme_rate = (self.portfolio_stock_dict[sCode]['현재가'] - jd['매입단가']) / jd['매입단가'] * 100

            if jd['주문가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                self.order_emit(["매도",
                    ["신규매도", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode, jd['주문가능수량'],
                     0, self.realType.SENDTYPE['거래구분']['시장가'], ""]]
                )

        # ===========================================================================================================
        # 실시간 등록된 종목이 계좌에 없고 등락율이 2이상일경우...
        # ===========================================================================================================
        elif self.portfolio_stock_dict[sCode]['등락율'] > 2.0 and sCode not in self.jango_dict and (self.portfolio_stock_dict[sCode]['(최우선)매수호가'] < (self.portfolio_stock_dict[sCode]['meme_price']*(1+self.meme_limit*0.01))):
            self.logging.logger.debug("매수조건 통과 %s " % sCode)

            # result = (self.use_money * self.portfolio_stock_dict[sCode]['비중']) / e
            result = (self.use_money * self.portfolio_stock_dict[sCode]['meme_ratio']) / self.portfolio_stock_dict[sCode][
                'meme_price']
            quantity = int(result)

            # order_success = self.dynamicCall(
            #    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            #    ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode, quantity, e,
            #     self.realType.SENDTYPE['거래구분']['지정가'], ""]
            # )
            self.order_emit(["매수",
                ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode, quantity,
                 self.portfolio_stock_dict[sCode]['meme_price'], self.realType.SENDTYPE['거래구분']['지정가'], ""]])

        not_meme_list = list(self.not_account_stock_dict)
        for order_num in not_meme_list:
            code = self.not_account_stock_dict[order_num]["종목코드"]
            meme_price = self.not_account_stock_dict[order_num]['주문가격']
            not_quantity = self.not_account_stock_dict[order_num]['미체결수량']
            order_gubun = self.not_account_stock_dict[order_num]['주문구분']
            # 매수후 바로 주문취소가 될수 있으므로 2%의 마진까지는 감안하고 주문
            #if order_gubun == "매수" and not_quantity > 0 and (self.portfolio_stock_dict[sCode]['(최우선)매도호가']> (meme_price*(1+self.meme_limit*0.01))):
            if order_gubun == "매수" and not_quantity > 0 and (self.portfolio_stock_dict[code]['(최우선)매도호가'] > (meme_price * (1.05))):
                self.order_emit(["매수", ["매수취소", self.portfolio_stock_dict[code]["주문용스크린번호"], self.account_num, 3, code, 0, 0,
                     self.realType.SENDTYPE['거래구분']['지정가'], order_num]])
            elif not_quantity == 0:
                del self.not_account_stock_dict[order_num]
        '''    
        time_meet = False
        if self.timestamp is None:
            time_meet = True
        else:
            now = datetime.datetime.now()  # 현재시간
            delta = now - self.timestamp  # 현재시간 - 이전 주문 시간
            if delta >= self.limit_delta:
                time_meet = True

        # 알고리즘을 충족하는가?
        algo_meet = True
       
        if data % 2 == 0:
            algo_meet = True
       
        # 알고리즘과 주문 가능 시간 조건을 모두 만족하면
        if time_meet and algo_meet:
            return True
        else:
            return False
        '''