from Kiwoom.Kiwoom import *
from Trade_Algrithm import python_quant
from DataBase import SQLITE_control
from Finance import finance_data
from collections import namedtuple
import datetime
import numpy as np
from Finance.Thema_list_Crolling_Infostock import *
##04/14
#알고리즘 구조체변수 구조바꾸기 [0],[1],[2].....
#알고리즘 현황 TAB수정

form_class = uic.loadUiType("pytrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.timer = QTimer(self)
        self.timer2 = QTimer(self)

        #self.fs = finance_data.Finance_data()
        #self.pr = finance_data.Price_data()
        #self.quant = python_quant.Quant_Strategy()
        # 키움 로그인
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        self.UI_Initiation()
        self.ongoing = False
        self.stocklist = pd.DataFrame(data=None)
        self.total_algorithm = 0
        self.parameter_tablename = 'system_parameter'
        self.stocklist_tablename = 'stock_list'
        self.DB_Parameter = 'f:\\OneDrive - Moedog, Inc\\STOCK_DB\\Parameter.db'
        self.algo_log = namedtuple('algo_log', 'start end tag stock_list')
        self.algorithm = [None, None, None]
        if self.init_systemparameter():
            self.timer3 = QTimer(self)
            self.timer3.start(5000)
            self.timer3.timeout.connect(self.run_algorithm)
        else:
            pass


    def UI_Initiation(self):
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)
        account_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        account = self.kiwoom.get_login_info("ACCNO")
        account = account.replace(";", "")
        print(account)
        account_list = account
        # account_list = account.split(';')[0:account_num]
        self.comboBox.addItem(account_list)
        self.lineEdit.textChanged.connect(self.code_change)
        self.pushButton.clicked.connect(self.send_order)
        self.pushButton_2.clicked.connect(self.check_balance)
        self.pushButton_3.clicked.connect(self.algorithm_add)  # 알고리즘 추가
        self.pushButton_4.clicked.connect(self.get_trade_list)
        self.pushButton_8.clicked.connect(self.update_PriceData)
        # 투자알고리즘 선택버튼
        self.radioButton_2.clicked.connect(self.quant_algorithm_sel)  # 마법공식
        self.radioButton_3.clicked.connect(self.quant_algorithm_sel)  # 신마법공식
        self.radioButton_4.clicked.connect(self.quant_algorithm_sel)  # 저PER저PBR
        self.radioButton_5.clicked.connect(self.quant_algorithm_sel)  # 고ROE저PER
        self.radioButton_6.clicked.connect(self.quant_algorithm_sel)  # BJ가치투자전략
        # 리밸런싱 선택
        self.radioButton_7.clicked.connect(self.rebalancing_sel)  # 절대모멘텀+동일가중
        self.radioButton_8.clicked.connect(self.rebalancing_sel)  # 스토캐스틱+동일가중
        self.radioButton_9.clicked.connect(self.rebalancing_sel)  # 지수이평선+동일가중
        self.radioButton_10.clicked.connect(self.rebalancing_sel)  # 듀얼모멘텀+동일가중
        self.radioButton_11.clicked.connect(self.rebalancing_sel)  # BJ리밸런싱
        self.radioButton_12.clicked.connect(self.rebalancing_sel)  # 주기리밸런싱

        self.check_rebalance_time()





    def init_systemparameter(self):
        #parameter load
        try:
            parameters = SQLITE_control.DB_LOAD_Table(self.parameter_tablename, self.DB_Parameter)
            stock_list = SQLITE_control. DB_LOAD_Table(self.stocklist_tablename, self.DB_Parameter)
            code_list = SQLITE_control.DB_LOAD_Table(self.fs.TOTAL_JONGMOK_NAME_TABLE, self.fs.DB_TOTAL_JONGMOK_PATH)
            #self.ongoing = parameters.loc['알고리즘_진행중'][0]
            self.stocklist = stock_list
            #self.total_algorithm = parameters.loc['알고리즘_진행갯수'][0]
            # chk validation parameter
            self.kiwoom.reset_opw00018()
            self.account_num = self.kiwoom.get_login_info("ACCNO")
            self.account_num = self.account_num.replace(";", "")
            self.kiwoom.set_input_value("계좌번호", self.account_num)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
            item = []
            while self.kiwoom.remained_data:
                time.sleep(TR_REQ_TIME_INTERVAL)
                self.kiwoom.set_input_value("계좌번호", self.account_num)
                self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
            item_cnt = len(self.kiwoom.opw00018_output['multi'])
            for i in range(item_cnt):
                row = self.kiwoom.opw00018_output['multi'][i]
                item.append(row[0])
            total_list = list(stock_list.loc['algo1']) + list(stock_list.loc['algo2']) + list(stock_list.loc['algo3'])
            total_list = list(map(lambda x: code_list['종목'].loc[x], list(filter(None, total_list))))
            for code in item:
                try:
                    total_list.remove(code)
                except:
                    pass
            if len(total_list) == 0:
                QMessageBox.about(self, "message", "system_parameter 검증완료")
                self.algorithm[0] = self.algo_log(parameters.loc['algo1'][0], parameters.loc['algo1'][1], parameters.loc['algo1'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo1'])))))
                self.algorithm[1] = self.algo_log(parameters.loc['algo2'][0], parameters.loc['algo2'][1], parameters.loc['algo2'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo2'])))))
                self.algorithm[2] = self.algo_log(parameters.loc['algo3'][0], parameters.loc['algo3'][1], parameters.loc['algo3'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo3'])))))
                ret =True
            else:
                QMessageBox.about(self, "message", "system_parameter 검증실패\n알고리즘 종목매수 확인필요")
                self.algorithm[0] = self.algo_log(parameters.loc['algo1'][0], parameters.loc['algo1'][1],
                                                  parameters.loc['algo1'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo1'])))))
                self.algorithm[1] = self.algo_log(parameters.loc['algo2'][0], parameters.loc['algo2'][1],
                                                  parameters.loc['algo2'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo2'])))))
                self.algorithm[2] = self.algo_log(parameters.loc['algo3'][0], parameters.loc['algo3'][1],
                                                  parameters.loc['algo3'][2], list(map(lambda x: code_list['종목'].loc[x], list(filter(None, self.stocklist.loc['algo3'])))))
                ret = True
        except:
            ret = False
        return ret



    def algorithm_add(self):
        quant_sel = self.quant_algorithm_sel()
        rebal_sel = self.rebalancing_sel()
        today = datetime.datetime.today()
        rebal_P = int(str(self.comboBox_4.currentText()).replace('개월', '')) * 30
        end_day = today + datetime.timedelta(days=rebal_P)
        if quant_sel == '마법공식':
            rank = self.quant.get_value_rank_now(value_type='자본수익률', quality_type='이익수익률', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '신마법공식':
            rank = self.quant.get_value_rank_now(value_type='PBR', quality_type='GP/A', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '저PER 저PBR':
            rank = self.quant.get_value_rank_now(value_type='PER', quality_type='PBR', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '고ROE 저PER':
            rank = self.quant.get_value_rank_now(value_type='PER', quality_type='ROE', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == 'BJ가치투자':
            rank = self.quant.get_value_rank_now(value_type='PBR', quality_type='GP/A', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        else:
            rank = None
        algo_number = self.comboBox_3.currentText()
        # ==================================================================================
        # 알고리즘 전역변수 저장 ('알고리즘 추가'버튼 작동 시)
        # ==================================================================================
        if algo_number == '알고리즘1':
            self.algorithm[0] = self.algo_log(today.strftime('%Y-%m-%d'),end_day.strftime('%Y-%m-%d'), quant_sel, list(rank.index))
        elif algo_number == '알고리즘2':
            self.algorithm[1] = self.algo_log(today.strftime('%Y-%m-%d'), end_day.strftime('%Y-%m-%d'), quant_sel, list(rank.index))
        else:
            self.algorithm[2] = self.algo_log(today.strftime('%Y-%m-%d'), end_day.strftime('%Y-%m-%d'), quant_sel, list(rank.index))
        self.timer3 = QTimer(self)
        self.timer3.start(500)
        self.timer3.timeout.connect(self.run_algorithm)
        SQLITE_control.System_Parameter_SAVE(self.algorithm[0], self.algorithm[1], self.algorithm[2])
        QMessageBox.about(self, "message", "알고리즘 저장완료!")


    def update_PriceData(self):
        price_data = finance_data.Price_data.make_total_price_df()

    def quant_algorithm_sel(self):
        if self.radioButton.isChecked() : ret = '마법공식'
        elif self.radioButton_2.isChecked() : ret = '신마법공식'
        elif self.radioButton_3.isChecked() : ret = '저PER 저PBR'
        elif self.radioButton_4.isChecked() : ret = '고ROE 저PER'
        elif self.radioButton_5.isChecked() : ret = 'BJ가치투자'
        else : pass
        return ret

    def rebalancing_sel(self) :
        if self.radioButton_7.isChecked() : ret = '절대모멘텀'
        elif self.radioButton_8.isChecked() : ret = '스토캐스틱'
        elif self.radioButton_9.isChecked() : ret = '지수이평선'
        elif self.radioButton_10.isChecked() : ret = '듀얼모멘텀'
        elif self.radioButton_11.isChecked() : ret = 'BJ리밸런싱'
        elif self.radioButton_12.isChecked() : ret = '주기리밸런싱'
        else : pass
        return ret

    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)
    def run_algorithm(self):
        # ==================================================================================
        # opt00018 TR 요청
        # ==================================================================================
        self.kiwoom.set_input_value("계좌번호", self.account_num)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
        while self.kiwoom.remained_data:
            time.sleep(TR_REQ_TIME_INTERVAL)
            self.kiwoom.set_input_value("계좌번호", self.account_num)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
        item_cnt = len(self.kiwoom.opw00018_output['multi'])
        # 알고리즘 별 손익합계 변수선언
        algo_profit = [0,0,0]
        algo_buy_amount =[0,0,0]
        algo_now_amount = [0,0,0]
        for i in range(item_cnt):
            row = self.kiwoom.opw00018_output['multi'][i]
            for j in range(len(row)):
                item = QTableWidgetItem(row[j])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                if row[j] in self.algorithm[0][3]:
                    self.tableWidget_4.setItem(i, j, item)
                    if j == 2: algo_buy_amount[0] = algo_buy_amount[0] + float(row[j].replace(",",""))
                    if j == 3: algo_now_amount[0] = algo_now_amount[0] + float(row[j].replace(",",""))
                    if j == 4 : algo_profit[0] = algo_profit[0] + float(row[j])
                elif row[j] in self.algorithm[1][3]:
                    self.tableWidget_5.setItem(i, j, item)
                    if j == 2: algo_buy_amount[1] = algo_buy_amount[1] + float(row[j].replace(",",""))
                    if j == 3: algo_now_amount[1] = algo_now_amount[1] + float(row[j].replace(",",""))
                    if j == 4 : algo_profit[1] = algo_profit[1] + float(row[j].replace(",",""))
                else:
                    self.tableWidget_6.setItem(i, j, item)
                    if j == 2: algo_buy_amount[2] = algo_buy_amount[2] + float(row[j].replace(",",""))
                    if j == 3: algo_now_amount[2] = algo_now_amount[2] + float(row[j].replace(",",""))
                    if j == 4 : algo_profit[2] = algo_profit[2] + float(row[j].replace(",",""))
        algo_result = [0,0,0]
        for i in range(0, 3):
            algo_result[i] = pd.DataFrame(data=None, index=['알고리즘', '투자금액', '현재금액', '코스피상관도', '코스닥상관도', '샤프지수'],
                                   columns=['내용'])
        for i in range(0,3):
            algo_result[i].loc['알고리즘'][0] = self.algorithm[i][2]
            algo_result[i].loc['투자금액'][0] = algo_buy_amount[i]
            algo_result[i].loc['현재금액'][0] = algo_now_amount[i]
            algo_result[i].loc['코스피상관도'][0] = np.nan
            algo_result[i].loc['코스닥상관도'][0] = np.nan
            algo_result[i].loc['샤프지수'][0] = np.nan

        self.tableWidget_4.resizeRowsToContents()
        self.tableWidget_5.resizeRowsToContents()
        self.tableWidget_6.resizeRowsToContents()
        # 알고리즘별 손익 데이터 DISPLAY
        temp = QTableWidgetItem(algo_buy_amount[0])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_10.setItem(0, 0, temp)
        temp = QTableWidgetItem(algo_now_amount[0])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_10.setItem(1, 0, temp)
        temp = QTableWidgetItem(algo_profit[0])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_10.setItem(2, 0, temp)
        self.tableWidget_10.resizeRowsToContents()
        temp = QTableWidgetItem(algo_buy_amount[1])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_8.setItem(0, 0, temp)
        temp = QTableWidgetItem(algo_now_amount[1])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_8.setItem(1, 0, temp)
        temp = QTableWidgetItem(algo_profit[1])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_8.setItem(2, 0, temp)
        self.tableWidget_8.resizeRowsToContents()
        temp = QTableWidgetItem(algo_buy_amount[2])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_9.setItem(0, 0, temp)
        temp = QTableWidgetItem(algo_now_amount[2])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_9.setItem(1, 0, temp)
        temp = QTableWidgetItem(algo_profit[2])
        temp.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget_9.setItem(2, 0, temp)
        self.tableWidget_9.resizeRowsToContents()
        # ==================================================================================

    def timeout2(self):
        chk = self.checkBox.isChecked()
        if chk :
            self.check_balance()

    def code_change(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        RQName = "send_order_msg"
        sScreenNo = "0101"
        sAccNo = self.comboBox.currentText()
        hoga = self.comboBox_6.currentText()
        nOrderType = self.comboBox_2.currentText()
        sCode = self.lineEdit.text()
        nQty = self.spinBox.value()
        nPrice = self.spinBox_2.value()
        if nPrice == 0 : self.kiwoom.send_order(RQName, sScreenNo, sAccNo, order_type_lookup[nOrderType], sCode, nQty, nPrice, hoga_lookup[hoga],"")
        else :
            price_data = self.pr.make_jongmok_price_data(sCode, 1)
            nQty = int(int(nPrice*10000) / int(price_data['A'+ sCode][0])) - 1
            self.kiwoom.send_order(RQName, sScreenNo, sAccNo, order_type_lookup[nOrderType], sCode, nQty, price_data, hoga_lookup[hoga],"")

    def get_trade_list(self):
        quant_sel =  self.quant_algorithm_sel()
        rebal_sel = self.rebalancing_sel()

        if quant_sel == '마법공식':
            rank = self.quant.get_value_rank_now(value_type='자본수익률', quality_type='이익수익률', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '신마법공식':
            rank = self.quant.get_value_rank_now(value_type='PBR', quality_type='GP/A', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '저PER 저PBR':
            rank = self.quant.get_value_rank_now(value_type='PER', quality_type='PBR', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == '고ROE 저PER':
            rank = self.quant.get_value_rank_now(value_type='PER', quality_type='ROE', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        elif quant_sel == 'BJ가치투자':
            rank = self.quant.get_value_rank_now(value_type='PBR', quality_type='GP/A', num=30, rim_on=True,
                                                 fs_comp_del_on=True, BJ_Filter=True, apply_rim_L=2)
        else : rank = None

        temp_df = pd.DataFrame(data=rank)
        temp_df = temp_df.reset_index()
        temp_df = temp_df[['code', '종목', '합산순위']]
        for j in range(0,3):
            for i in range(len(temp_df)):
                try:
                    item = QTableWidgetItem(str(temp_df.iloc[i][j]))
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.tableWidget_3.setItem(i, j, item)
                except:
                    item = QTableWidgetItem('-')
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.tableWidget_3.setItem(i, j, item)
        self.tableWidget_3.resizeRowsToContents()

    def check_rebalance_time(self):
        try:
            delta = pd.to_datetime(self.algorithm1[1]) - datetime.datetime.today()
        except:
            delta = 0
        self.lcdNumber.display('-'+str(delta))
        self.lcdNumber.setDigitCount(10)
        self.lcdNumber.setMinimumHeight(72)
        self.lcdNumber.setMinimumWidth(100)


    def check_balance(self):
        self.kiwoom.reset_opw00018()

        self.account_num = self.kiwoom.get_login_info("ACCNO")
        self.account_num = self.account_num.replace(";", "")
        print(self.account_num)
#        self.account_num = account_num.split(';')[0]
        # opt00018 TR 요청
        self.kiwoom.set_input_value("계좌번호", self.account_num)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(TR_REQ_TIME_INTERVAL)
            self.kiwoom.set_input_value("계좌번호", self.account_num)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        self.kiwoom.set_input_value("계좌번호", self.account_num)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        item = QTableWidgetItem(self.kiwoom.deposit_d2)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i-1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)
        self.tableWidget.resizeRowsToContents()

        item_cnt = len(self.kiwoom.opw00018_output['multi'])
        for i in range(item_cnt):
            row = self.kiwoom.opw00018_output['multi'][i]
            for j in range(len(row)):
                item = QTableWidgetItem(row[j])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(i, j, item)
        self.tableWidget_2.resizeRowsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()