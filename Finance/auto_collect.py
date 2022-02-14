import sys
import PyQt5.QtWidgets
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import pandas as pd
import FinanceDataReader as fdr
import pymysql
from sqlalchemy import create_engine

import DataBase.MySQL_control

pymysql.install_as_MySQLdb()
#import MySQLdb
#import OpenDartReader
import tqdm
import datetime
import warnings
import DataBase.MySQL_control

warnings.simplefilter(action='ignore', category=FutureWarning)
import multiprocessing


##auto-trader ver : 2020.1.1
##@클래스 및 함수 검색#####################################################################################
## Ctrl + f 후 클래스 검색

## @ + widget          : 위젯모음 클래스
## @ + functions       : 메인창에서 사용할 기능모음 클래스
## @ + trader          : (메인창)오토트레이더 클래스
## @ + kiwoom          : 키움 openAPI (별도클래스로 구성하지 않은 이유 : api수신 결과를 ui에 직접띄우기가 용이함)
## @ + collector_base  : DB체크 후 존재하지 않을 경우 DB를 생성하고 종목리스트를 수집하는 클래스, 스레드 방식으로 운영함
## @ + collector_price : 주가 정보를 수집하는 클래스, 스레드방식으로 운영
## @ + monitor         : 정보체크, 현황체크 등 모니터링(미완, 별도클래스로 구성하지 않은 이유 : ui에 직접띄우기가 용이함 )
## @ + backtester      : 알고리즘 백테스팅(미완,별도클래스로 구성하지 않은 이유 : ui에 직접띄우기가 용이함 )


##@widget 시작#############################################################################################
class Widget(PyQt5.QtWidgets.QWidget):
    def __init__(self, parent):
        super(Widget, self).__init__(parent)
        self.db = DataBase.MySQL_control.DB_control()
        self.initUI()

    def initUI(self):
        ##!Trader_UI 시작#################################################################################

        ##### 계좌번호 선택 라벨
        self.account_label = PyQt5.QtWidgets.QLabel("계좌")
        self.account_label.setMaximumWidth(40)
        self.account_label.setMinimumWidth(40)
        ##### 계좌번호 선택 콤보
        self.account_combo = PyQt5.QtWidgets.QComboBox(self)
        self.account_combo.setMaximumWidth(160)
        self.account_combo.setMinimumWidth(160)

        ##### 주문방식 선택 라벨
        self.order_label = PyQt5.QtWidgets.QLabel("주문")
        self.order_label.setMaximumWidth(40)
        self.order_label.setMinimumWidth(40)
        ##### 계좌번호 선택 콤보
        self.order_combo = PyQt5.QtWidgets.QComboBox(self)
        self.order_combo.setMaximumWidth(160)
        self.order_combo.setMinimumWidth(160)
        self.order_combo.addItem("신규매수")
        self.order_combo.addItem("신규매도")
        self.order_combo.addItem("매수취소")
        self.order_combo.addItem("매도취소")

        ##### 종목선택 라벨1
        self.name_labe_1 = PyQt5.QtWidgets.QLabel("종목")
        self.name_labe_1.setMaximumWidth(40)
        self.name_labe_1.setMinimumWidth(40)
        ##### 종목선택 에디트1
        self.name_edit_1 = PyQt5.QtWidgets.QLineEdit(self)
        self.name_edit_1.setMaximumWidth(160)
        self.name_edit_1.setMinimumWidth(160)

        ##### 종목선택 라벨2
        self.name_labe_2 = PyQt5.QtWidgets.QLabel("")
        self.name_labe_2.setMaximumWidth(40)
        self.name_labe_2.setMinimumWidth(40)
        ##### 종목선택 에디트2
        self.name_edit_2 = PyQt5.QtWidgets.QLineEdit(self)
        self.name_edit_2.setEnabled(False)
        self.name_edit_2.setMaximumWidth(160)
        self.name_edit_2.setMinimumWidth(160)

        ##### 종류 선택 라벨
        self.type_label = PyQt5.QtWidgets.QLabel("종류")
        self.type_label.setMaximumWidth(40)
        self.type_label.setMinimumWidth(40)
        ##### 종류 선택 콤보
        self.type_spin = PyQt5.QtWidgets.QComboBox(self)
        self.type_spin.setMaximumWidth(160)
        self.type_spin.setMinimumWidth(160)
        self.type_spin.addItem("시장가")
        self.type_spin.addItem("지정가")

        ##### 수량 선택 라벨
        self.num_label = PyQt5.QtWidgets.QLabel("수량")
        self.num_label.setMaximumWidth(40)
        self.num_label.setMinimumWidth(40)
        ##### 수량 선택 스핀
        self.num_spin = PyQt5.QtWidgets.QSpinBox(self)
        self.num_spin.setMaximumWidth(160)
        self.num_spin.setMinimumWidth(160)

        ##### 가격 선택 라벨
        self.price_label = PyQt5.QtWidgets.QLabel("가격")
        self.price_label.setMaximumWidth(40)
        self.price_label.setMinimumWidth(40)
        ##### 가격 선택 스핀
        self.price_spin = PyQt5.QtWidgets.QSpinBox(self)
        self.price_spin.setMaximumWidth(160)
        self.price_spin.setMinimumWidth(160)

        ##### 현금매수 클릭 푸쉬
        self.active_buy = PyQt5.QtWidgets.QPushButton("현금매수", self)
        self.active_buy.setMaximumWidth(230)
        self.active_buy.setMinimumWidth(230)
        #####################################################################

        ##### 종목코드를 표출할 위젯 생성
        # self.listWidget = QListWidget(self)

        ##### openAPI에서 발생하는 이벤트를 표출할 영역 생성
        self.text_edit = PyQt5.QtWidgets.QTextEdit(self)
        self.text_edit.setEnabled(False)
        self.text_edit.setFixedHeight(100)

        ##### 잔고표출 영역생성
        #####################################################################
        self.tableWidget_balance = PyQt5.QtWidgets.QTableWidget(self)
        balance = ['예수금(d+2)', '출금가능금액', '총매입금', '총평가', '총손익', '총수익률', '추정예탁자산']
        self.tableWidget_balance.setRowCount(1)  # 행의 갯수
        self.tableWidget_balance.setColumnCount(len(balance))  # 컬럼의 갯수
        self.tableWidget_balance.setHorizontalHeaderLabels(balance)  # 컬럼명 설정
        # self.tableWidget_balance.resizeColumnsToContents()                # 컬럼 사이즈를 내용에 맞추어설정
        self.tableWidget_balance.resizeRowsToContents()  # 행의 사이즈를 내용에 맞추어설정
        self.tableWidget_balance.setFixedHeight(100)  # 위젯크기 고정
        self.tableWidget_balance.setColumnWidth(0, 100)  # 0에 위치한것 크기조정(원하는사이즈로 수정가능)
        self.tableWidget_balance.setColumnWidth(1, 100)
        self.tableWidget_balance.setColumnWidth(2, 100)
        self.tableWidget_balance.setColumnWidth(3, 100)
        self.tableWidget_balance.setColumnWidth(4, 100)
        self.tableWidget_balance.setColumnWidth(5, 100)
        self.tableWidget_balance.setColumnWidth(6, 100)

        ##### 보유종목현황 영역생성
        self.tableWidget_item = PyQt5.QtWidgets.QTableWidget(self)
        item = ['종목명', '보유량', '매입가', '현재가', '평가손익', '수익률']
        # self.tableWidget_item.setRowCount(100)
        self.tableWidget_item.setColumnCount(len(item))
        self.tableWidget_item.setHorizontalHeaderLabels(item)
        # self.tableWidget_item.resizeColumnsToContents()
        self.tableWidget_item.resizeRowsToContents()
        self.tableWidget_item.setFixedHeight(300)

        ##### 주문대기현황(선정종목 리스트)
        self.tableWidget_buy_lists = PyQt5.QtWidgets.QTableWidget(self)
        buy_lists = ['주문유형', '종목명', '호가구분', '수량', '가격', '상태']
        self.tableWidget_buy_lists.setColumnCount(len(buy_lists))
        self.tableWidget_buy_lists.setHorizontalHeaderLabels(buy_lists)
        self.tableWidget_buy_lists.resizeRowsToContents()
        # 행갯수는 나중에 주문형태가 구성되면 지정
        #####################################################################

        ##### layout 영역
        #####################################################################

        groupbox1_1 = PyQt5.QtWidgets.QGroupBox('수동주문')
        sub_groupbox1_1 = PyQt5.QtWidgets.QVBoxLayout()
        condition1_1 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_1.addWidget(self.account_label)
        condition1_1.addWidget(self.account_combo)
        condition1_2 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_2.addWidget(self.order_label)
        condition1_2.addWidget(self.order_combo)
        condition1_3 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_3.addWidget(self.name_labe_1)
        condition1_3.addWidget(self.name_edit_1)
        condition1_4 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_4.addWidget(self.name_labe_2)  # QHBoxLayout() or QVBoxLayout()안에 기능을 넣을때는addWidget()
        condition1_4.addWidget(self.name_edit_2)
        condition1_5 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_5.addWidget(self.type_label)
        condition1_5.addWidget(self.type_spin)
        condition1_6 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_6.addWidget(self.num_label)
        condition1_6.addWidget(self.num_spin)
        condition1_7 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_7.addWidget(self.price_label)
        condition1_7.addWidget(self.price_spin)
        condition1_8 = PyQt5.QtWidgets.QHBoxLayout()
        condition1_8.addWidget(self.active_buy)
        sub_groupbox1_1.addLayout(condition1_1)  # QHBoxLayout() or QVBoxLayout() 끼리는 addLayout 사용
        sub_groupbox1_1.addLayout(condition1_2)
        sub_groupbox1_1.addLayout(condition1_3)
        sub_groupbox1_1.addLayout(condition1_4)
        sub_groupbox1_1.addLayout(condition1_5)
        sub_groupbox1_1.addLayout(condition1_6)
        sub_groupbox1_1.addLayout(condition1_7)
        sub_groupbox1_1.addLayout(condition1_8)
        groupbox1_1.setLayout(sub_groupbox1_1)  # QGroupBox()에는 setLayout() 사용
        groupbox1_1.setFixedHeight(350)

        groupbox1_2 = PyQt5.QtWidgets.QGroupBox('처리현황')
        condition1_2 = PyQt5.QtWidgets.QVBoxLayout()
        condition1_2.addWidget(self.text_edit)
        groupbox1_2.setLayout(condition1_2)
        groupbox1_2.setSizePolicy(PyQt5.QtWidgets.QSizePolicy.Fixed, PyQt5.QtWidgets.QSizePolicy.Fixed)

        groupbox1 = PyQt5.QtWidgets.QVBoxLayout()
        groupbox1.addWidget(groupbox1_1)
        groupbox1.addWidget(groupbox1_2)

        groupbox2 = PyQt5.QtWidgets.QGroupBox('잔고 및 보유종목현황')
        condition2 = PyQt5.QtWidgets.QVBoxLayout()
        condition2.addWidget(self.tableWidget_balance)
        condition2.addWidget(self.tableWidget_item)
        groupbox2.setLayout(condition2)

        groupbox3 = PyQt5.QtWidgets.QGroupBox('주문대기현황(선정종목 리스트)')
        condition3 = PyQt5.QtWidgets.QVBoxLayout()
        condition3.addWidget(self.tableWidget_buy_lists)
        groupbox3.setLayout(condition3)

        sub_layout1 = PyQt5.QtWidgets.QVBoxLayout()
        sub_layout1.addLayout(groupbox1)
        sub_layout1.addStretch(1)

        sub_layout2 = PyQt5.QtWidgets.QVBoxLayout()
        sub_layout2.addWidget(groupbox2)
        sub_layout2.addWidget(groupbox3)

        main_layout1 = PyQt5.QtWidgets.QHBoxLayout()
        main_layout1.addLayout(sub_layout1)
        main_layout1.addLayout(sub_layout2)
        main_layout1.setStretchFactor(sub_layout1, 0)
        main_layout1.setStretchFactor(sub_layout2, 1)
        ##!Trader_UI 종료#############################################################################

        ##!Collector_UI 시작##########################################################################

        ##### 처리결과를 표출할 에디터
        self.check_edit = PyQt5.QtWidgets.QTextEdit(self)
        self.check_edit.setEnabled(False)
        self.check_edit.setFixedHeight(250)

        ##### 주가 정보수집 실행 버튼
        self.collection_price = PyQt5.QtWidgets.QPushButton("주가정보수집", self)
        self.collection_price.setFont(QFont('Arial', 8))
        self.collection_price.setMaximumWidth(90)
        self.collection_price.setMinimumWidth(90)

        ##### 주가정보 상태진행 바 생성
        self.collector_price_progress = PyQt5.QtWidgets.QProgressBar(self)
        self.collector_price_progress.setAlignment(Qt.AlignCenter)

        ##### 재무 정보수집 실행 버튼
        self.collection_finance = PyQt5.QtWidgets.QPushButton("재무정보수집", self)
        self.collection_finance.setFont(QFont('Arial', 8))
        self.collection_finance.setMaximumWidth(90)
        self.collection_finance.setMinimumWidth(90)

        ##### 주가정보 상태진행 바 생성
        self.collector_finance_progress = PyQt5.QtWidgets.QProgressBar(self)
        self.collector_finance_progress.setAlignment(Qt.AlignCenter)

        #####################################################
        groupbox10_1 = PyQt5.QtWidgets.QGroupBox('정보수집현황')

        check_result = PyQt5.QtWidgets.QVBoxLayout()
        check_result.addWidget(self.check_edit)

        collect_price = PyQt5.QtWidgets.QHBoxLayout()
        collect_price.addWidget(self.collection_price)
        collect_price.addWidget(self.collector_price_progress)

        collect_finance = PyQt5.QtWidgets.QHBoxLayout()
        collect_finance.addWidget(self.collection_finance)
        collect_finance.addWidget(self.collector_finance_progress)

        sub_layout10_1 = PyQt5.QtWidgets.QVBoxLayout()
        sub_layout10_1.addLayout(check_result)
        sub_layout10_1.addLayout(collect_price)
        sub_layout10_1.addLayout(collect_finance)

        groupbox10_1.setLayout(sub_layout10_1)
        groupbox10_1.setFixedHeight(400)
        groupbox10_1.setFixedWidth(280)

        sub_sub_layout10_1 = PyQt5.QtWidgets.QVBoxLayout()
        sub_sub_layout10_1.addWidget(groupbox10_1)
        sub_sub_layout10_1.addStretch(1)

        groupbox10_2 = PyQt5.QtWidgets.QGroupBox('상세정보 검색')

        main_layout2 = PyQt5.QtWidgets.QHBoxLayout()
        main_layout2.addLayout(sub_sub_layout10_1)
        main_layout2.addWidget(groupbox10_2)
        ##!Collector_UI 종료##########################################################################

        ##!각각의 UI 탭위젯에 셋팅#####################################################################
        ##### 탭위젯
        main_widget1 = PyQt5.QtWidgets.QWidget()
        main_widget2 = PyQt5.QtWidgets.QWidget()
        main_widget3 = PyQt5.QtWidgets.QWidget()
        main_widget4 = PyQt5.QtWidgets.QWidget()

        tabs = PyQt5.QtWidgets.QTabWidget()
        tabs.addTab(main_widget1, 'Trader')
        main_widget1.setLayout(main_layout1)
        tabs.addTab(main_widget2, 'Collector')
        main_widget2.setLayout(main_layout2)
        tabs.addTab(main_widget3, 'Monitor')
        tabs.addTab(main_widget4, 'Backtester')

        vbox = PyQt5.QtWidgets.QVBoxLayout()
        vbox.addWidget(tabs)
        ##!각각의 UI 탭위젯에 셋팅#####################################################################

        self.setLayout(vbox)


##########################################################################


##@mainwindow 시작 ######################################################################################
class Trader(PyQt5.QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Trader, self).__init__(parent)

        self.kiwoom()

        ##### 위젯 창 연결
        self.mywidget = Widget(self)
        self.setCentralWidget(self.mywidget)

        ##### 메인창 이름설정 및 크기설정
        self.setWindowTitle("auto-trader")
        self.setGeometry(300, 300, 1200, 800)
        # self.setStyleSheet("background-color : black")

        ##### 메인창을 중앙에 위치
        qr = self.frameGeometry()
        cp = PyQt5.QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        ##### 상태표시줄 생성
        self.statusbar = PyQt5.QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        ##### 타이머 설정 1 - 상태표시줄 현재시간
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        ##### 타이머 설정 2 - 실시간 조회
        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)

        ##### 종목명 또는 종목코드로 검색
        self.mywidget.name_edit_1.returnPressed.connect(self.total_changed)  # textChanged 텍스트 변경옵션

        ##### 현금주문 실행
        self.mywidget.active_buy.clicked.connect(self.send_order)

        ##### 버튼 클릭시 start_thread_collector_price함수로 이동
        self.mywidget.collection_price.clicked.connect(self.start_thread_collector_price)
        ##### 버튼 클릭시 start_thread_collector_finance함수로 이동
        self.mywidget.collection_finance.clicked.connect(self.start_thread_collector_finance)

        ##### collector실행 시기 정의해놓은 함수 실행
        self.collector_timer()

    def collector_timer(self):
        ##### 프로그램 실행 즉시 start_thread_collector_base함수 실행
        self.start_thread_collector_base()

        ##### collector_price를 실행할 타이머 설정
        ##### 시간이 17시에 실행
        timer3 = QTimer(self)
        timer3.start(1000)
        timer3.timeout.connect(self.timeout3)

        ##### collector_finance를 실행할 날짜 설정
        current_time = datetime.datetime.now()
        current_time = current_time.strftime("%m-%d")
        if current_time == "04-01" or "07-01" or "10-01" or "01-01" or "07-06":
            timer4 = QTimer(self)
            timer4.start(1000)
            timer4.timeout.connect(self.timeout4)

    ##### collector_base스레드 클래스 객체를 생성하고 실행
    def start_thread_collector_base(self):
        self.collector_base = Collector_base(self)  # 스레드 생성
        self.collector_base.start()  # 스레드 실행
        self.collector_base.finished_edit.connect(self.update_db)  # 클래스에서 신호가 발생하면 슬롯으로 전달 finished_edit을 사용하고 있음

    ##### collector_price 스레드 클래스 객체를 생성하고 실행
    def start_thread_collector_price(self):
        self.collector_price = Collector_price(self)
        self.collector_price.start()
        self.collector_price.finished_edit.connect(self.update_db)
        self.collector_price.finished_price.connect(self.update_price_db)

    ##### collector_finance 스레드 클래스 객체를 생성하고 실행
    def start_thread_collector_finance(self):
        self.collector_finance = Collector_finance(self)
        self.collector_finance.start()
        self.collector_finance.finished_edit.connect(self.update_db)
        self.collector_finance.finished_finance.connect(self.update_finance_db)

    ##### 슬롯을 @pyqtSlot(str) 정의 해줌, 슬롯에서 받은 data를 mywidget객체에 띄움
    @pyqtSlot(str)
    def update_db(self, data):
        self.mywidget.check_edit.append(data)

    ##### 슬롯을 @pyqtSlot(int, int) 정의 해줌, 슬롯에서 받은 data를 mywidget객체에 띄움
    @pyqtSlot(int, int)
    def update_price_db(self, steps, step):
        ##### progressbar위젯 초기화, 다른 기능에서 사용했을 경우 초기화가 필요
        self.mywidget.collector_price_progress.reset()
        ##### progressbar위젯에 최대값 셋팅, 최소값도 지정 가능 setMinimum
        self.mywidget.collector_price_progress.setMaximum(steps)
        ##### setFormat을 지정하지 않을 경우 %로 증가 할 것임
        self.mywidget.collector_price_progress.setFormat("%v/%m")
        ##### 진행상태 값이 될것을 셋팅
        self.mywidget.collector_price_progress.setValue(step)

        ##### 슬롯을 @pyqtSlot(int, int) 정의 해줌, 슬롯에서 받은 data를 mywidget객체에 띄움

    @pyqtSlot(int, int)
    def update_finance_db(self, steps, step):
        ##### progressbar위젯 초기화, 다른 기능에서 사용했을 경우 초기화가 필요
        self.mywidget.collector_finance_progress.reset()
        ##### progressbar위젯에 최대값 셋팅, 최소값도 지정 가능 setMinimum
        self.mywidget.collector_finance_progress.setMaximum(steps)
        ##### setFormat을 지정하지 않을 경우 %로 증가 할 것임
        self.mywidget.collector_finance_progress.setFormat("%v/%m")
        ##### 진행상태 값이 될것을 셋팅
        self.mywidget.collector_finance_progress.setValue(step)

        ##### 상태표시줄에 들어갈 현재시간

    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간 : " + text_time

        self.statusbar.showMessage("서버 연결 중 | " + time_msg)

    ##### 잔고 및 보유종목현황 실시간 조회
    def timeout2(self):
        self.kiwoom.OnEventConnect.connect(self.detail_account_info1)  # 예수금 정보 요청
        self.kiwoom.OnEventConnect.connect(self.detail_account_info2)  # 잔고정보 요청
        self.kiwoom.OnReceiveTrData.connect(self.trdata_slot)  # 예수금 및잔고 정보 수신
        self.mywidget.text_edit.append("잔고현황 업데이트")

        ##### collector_price를 실행시간 정의

    def timeout3(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")

        if text_time == "02:11:00":
            self.start_thread_collector_price()

    ##### collector_finance를 실행할 시간 정의
    def timeout4(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")

        if text_time == "02:11:00":
            self.start_thread_collector_finance()

    ##### 클로즈 이벤트
    def closeEvent(self, QCloseEvent):
        re = PyQt5.QtWidgets.QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                                                  PyQt5.QtWidgets.QMessageBox.Yes | PyQt5.QtWidgets.QMessageBox.No)

        if re == PyQt5.QtWidgets.QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()

    ##@mainwindow 종료 ######################################################################################

    ##@kiwoom 시작 ###########################################################################################

    def kiwoom(self):
        ##### 로그인 영역
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.dynamicCall("CommConnect()")
        #self.stocks
        ##### 이벤트실행 실행
        self.kiwoom.OnEventConnect.connect(self.event_connect)  # 로그인
        self.kiwoom.OnEventConnect.connect(self.account)  # 계좌정보
        self.kiwoom.OnEventConnect.connect(self.stocks)  # 종목코드
        self.kiwoom.OnEventConnect.connect(self.detail_account_info1)  # 예수금 정보 요청
        self.kiwoom.OnEventConnect.connect(self.detail_account_info2)  # 잔고정보 요청
        self.kiwoom.OnReceiveTrData.connect(self.trdata_slot)  # 예수금 및잔고 정보 수신

    ##### CommConnect()호출 후 반환값이 리턴 되면 UI에 text_edit 표출
    def event_connect(self, err_code):
        if err_code == 0:
            self.mywidget.text_edit.append("로그인 성공")
        else:
            self.mywidget.text_edit.append("로그인 실패")

            ##### 계좌정보 가저오는 함수

    def account(self):
        num = int(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCOUNT_CNT"]))
        account_list = self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"])
        # self.mywidget.text_edit.append("계좌번호: " + account_list.rstrip(';'))
        self.mywidget.account_combo.addItems(account_list.split(';')[0:num])
        # self.account_num = account_list.split(';')[0]

    ##### 예수금 정보 요청 함수
    def detail_account_info1(self, sPrevNext="0"):
        account_num = self.mywidget.account_combo.currentText()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_num)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", sPrevNext,
                                "0362")

    ##### 계좌평가잔고 정보 요청 함수
    def detail_account_info2(self, sPrevNext="0"):
        account_num = self.mywidget.account_combo.currentText()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_num)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext,
                                "0362")

        ### 루프 생성
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    ##### 계좌 정보 수신 함수
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        ##### 예수금 및 출금가능금액
        if sRQName == "예수금상세현황요청":
            ##### 예수금 데이터 반환
            deposit = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")

            ##### 출금가능 데이터 반환
            output_deposit = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                                     "출금가능금액")

            ##### 예수금에 필요없는 숫자 삭제하고 원화 표출양식으로 변환
            deposit = self.change_format(deposit)
            output_deposit = self.change_format(output_deposit)

            ##### 결과값 표출
            deposit = PyQt5.QtWidgets.QTableWidgetItem(deposit)
            deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 0, deposit)

            output_deposit = PyQt5.QtWidgets.QTableWidgetItem(output_deposit)
            output_deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 1, output_deposit)

        ##### 매입금액 등 현황 수신
        elif sRQName == "계좌평가잔고내역요청":
            ##### 잔고현황 반환
            total_purchsase = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                      0, "총매입금액")
            total_eval_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       0, "총평가금액")
            total_eval_profit_loss = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                             sRQName, 0, "총평가손익금액")
            total_earning_rate = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, 0, "총수익률(%)")
            estimated_deposit = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                        0, "추정예탁자산")

            ##### 잔고현황 결과값 숫자형태 변환
            total_purchsase = self.change_format(total_purchsase)
            total_eval_price = self.change_format(total_eval_price)
            total_eval_profit_loss = self.change_format(total_eval_profit_loss)
            total_earning_rate = self.change_format(total_earning_rate)
            estimated_deposit = self.change_format(estimated_deposit)

            ##### 테이블위젯에 결과값 넣기
            total_purchsase = PyQt5.QtWidgets.QTableWidgetItem(total_purchsase)
            total_purchsase.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 2, total_purchsase)

            total_eval_price = PyQt5.QtWidgets.QTableWidgetItem(total_eval_price)
            total_eval_price.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 3, total_eval_price)

            total_eval_profit_loss = PyQt5.QtWidgets.QTableWidgetItem(total_eval_profit_loss)
            total_eval_profit_loss.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 4, total_eval_profit_loss)

            total_earning_rate = PyQt5.QtWidgets.QTableWidgetItem(total_earning_rate)
            total_earning_rate.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 5, total_earning_rate)

            estimated_deposit = PyQt5.QtWidgets.QTableWidgetItem(estimated_deposit)
            estimated_deposit.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.mywidget.tableWidget_balance.setItem(0, 6, estimated_deposit)
            ###############################################################

            ##### 종목현황 반환
            rows = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            item_output = []
            ##### 종목현황 반환된 값에서 원하는 값 추출
            for i in range(rows):
                name = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                               "종목명")
                name = name.strip()

                quantity = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                                   "보유수량")
                purchase_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, i, "매입가")
                current_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                        i, "현재가")
                eval_profit_loss = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName, i, "평가손익")
                eraning_rate = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       i, "수익률(%)")

                ##### 결과값 숫자형태 변환
                quantity = self.change_format(quantity)
                purchase_price = self.change_format(purchase_price)
                current_price = self.change_format(current_price)
                eval_profit_loss = self.change_format(eval_profit_loss)
                eraning_rate = self.change_format2(eraning_rate)

                ##### 리스트에 저장
                item_output.append([name, quantity, purchase_price, current_price, eval_profit_loss, eraning_rate])

            ##### item의 갯수세고 띄워줄 테이블에 로우를 만듬
            item_count = len(item_output)
            self.mywidget.tableWidget_item.setRowCount(item_count)

            ##### 종목을 UI에 띄우기
            for j in range(item_count):
                item_output[j]
                for i, k in enumerate(item_output[j]):
                    item = PyQt5.QtWidgets.QTableWidgetItem(k)
                    if i == 0:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                        self.mywidget.tableWidget_item.setItem(j, i, item)
                    else:
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                        self.mywidget.tableWidget_item.setItem(j, i, item)
            ###############################################################

            ##### 로그현황에 결과 띄우기
            self.mywidget.text_edit.append("잔고현황 실시간조회 실행")

            ##### 슬롯연결 끊기
            self.stop_screen_cancel("0362")

            ##### 루프 종료
            self.detail_account_info_event_loop.exit()

    ##### 슬롯연결 끊기 함수
    def stop_screen_cancel(self, sScrNo=None):
        self.kiwoom.dynamicCall("DisconnectRealData(QString)", sScrNo)  # 스크린 번호 연결 끊기

    ##### 숫자 표출형식 변환 1
    def change_format(self, data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'
        try:
            format_data = format(int(strip_data), ',d')
        except:
            format_data = format(float(strip_data))
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    ##### 수익률 표출형식 변환 2
    def change_format2(self, data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    ##### 종목코드 가저오는 함수
    def stocks(self, input_name):
        ret = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", ["0"])
        kospi_code_list = ret.split(';')
        kospi_code_name_list = []

        for x in kospi_code_list:
            name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", [x])
            kospi_code_name_list.append(x + " : " + name)

    ##### 종목 UI에 종목명 입력시 종목코드 출력실행 함수
    def total_changed(self):
        input_text = self.mywidget.name_edit_1.text()
        if input_text.isdigit() == True:
            code = self.mywidget.name_edit_1.text()
            name = self.get_master_code(code)
            self.mywidget.name_edit_2.setText(name)
        else:
            name = self.mywidget.name_edit_1.text()
            code = self.get_master_name(name)
            self.mywidget.name_edit_2.setText(code)

            ##### 종목 UI에 종목명 입력시 종목코드 출력실행 함수

    def name_changed(self):
        name = self.mywidget.name_edit_1.text()
        code = self.get_master_name(name)
        self.mywidget.name_edit_2.setText(code)

    ##### 종목 UI에 코드 입력시 종목명 출력실행 함수
    def code_changed(self):
        code = self.mywidget.name_edit_1.text()
        name = self.get_master_code(code)
        self.mywidget.name_edit_2.setText(name)

    ##### 하나의 종목명 입력시 종목코드 출력
    def get_master_name(self, input_name):
        ret = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", ["0"])
        kospi_code_list = ret.split(';')

        kospi_code_name_lists = []
        for x in kospi_code_list:
            name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", [x])
            kospi_code_name_lists.append(["{}".format(name), "{}".format(x)])

        kospi_code_name_lists = dict(kospi_code_name_lists)

        try:
            code = kospi_code_name_lists["{}".format(input_name)]
        except KeyError:
            code = ""
        return code

    ##### 종목명 출력
    def get_master_code(self, input_code):
        name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", input_code)
        return name

    ##### 수동주문
    def send_order(self):
        order_type_lookup = {"신규매수": 1, "신규매도": 2, "매수취소": 3, "매도취소": 4}
        hoga_lookup = {"시장가": "03", "지정가": "00"}

        account = self.mywidget.account_combo.currentText()  ### UI에서 현재 선택되어있는 계좌정보를 받아옴
        order_type = self.mywidget.order_combo.currentText()  ### UI에서 현재 선택되어있는 주문형태정보를 받아옴
        code = self.mywidget.name_edit_2.text()  ### UI에서 현재 선택되어있는 주문하고자 하는 종목의 코드를 받아옴
        hoga = self.mywidget.type_spin.currentText()  ### UI에서 현재 선택되어있는 시장가,지정가 선택
        num = self.mywidget.num_spin.value()  ### UI에서 현재 선택되어있는 수량정보를 받아옴
        price = self.mywidget.price_spin.value()  ### UI에서 현재 선택되어있는 지정가일 경우 가격정보를 받아옴

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                ["send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                                 hoga_lookup[hoga], ""])


##@kiwoom 종료############################################################################################


##@collector 클래스로 분할###########################################################################################

## collector는 정보를 수집해서 데이터베이스에 저장하는 기능을 담당
## UI를 운영하면서 정보는 정보대로 수집해야하기 때문에 스레드로 운영, UI에 띄우는 정보는 signal/slot처리

## collector_base      : DB체크, DB생성, 종목리스트 수집
## collector_price     : 주가정보수집
## collector_finance   : 재무제표 수집


## DB명칭 및 기능
## db_log              : 각각의 db업데이트 기록 저장
## stocks_lists        : 전체상장사 목록
## stocks_price        : 주가정보
## stocks_finance      : 재무제표(bs,is)

##@create_DB 시작 #############################################################################################
class Create_DB:

    ##### DB에 접근 하기 위해 cursor를 많이 사용할 예정이기때문에 함수로 생성해둔다.
    ##### DB에 접근 할 cursor생성 함수
    def create_cursor(self):
        ##### pymysql라이브러리로 내 데이터베이스에 접속
        self.conn = pymysql.connect(host='localhost', user='root', password='#wkdhrl1024', charset='utf8')

        ##### cursor객체 생성, cursor를 반복적으로 사용하기 위해 전역변수로 선언한다.
        self.cursor = self.conn.cursor()

    ##### DB접근을 종료 할 cursor삭제 함수
    def delete_cursor(self):
        self.conn.commit()
        self.conn.close()

    ##### to_sql메서드를 활용 하기위한 engine을 생성
    def create_engine(self, db_name):
        self.engine = create_engine("mysql+mysqldb://root:" + "#wkdhrl1024" + "@localhost/{}".format(db_name),
                                    encoding='utf-8')
        self.conn2 = self.engine.connect()

        ##### 생성한 engine 삭제

    def delete_engine(self):
        self.conn2.close()


##@collector_base 시작 #############################################################################################
class Collector_base(QThread, Create_DB):
    ##### 시그널 생성/mainUI에 정보 전달
    finished_edit = pyqtSignal(str)

    def run(self):
        ##### db 리스트 정의
        self.db_lists = ['db_log', 'stocks_lists', 'stocks_price', 'stocks_finance', 'system_parameter']

        ##### auto-trader 실행 즉시 db_check 실행
        self.db_check()

        ##### stocks_lists DB체크
        self.collect_stocks_lists_check()

    ##### DB의 현황을 확인하고 미리 정의한 DB가 없을 경우 생성하는 함수
    def db_check(self):

        ##### cursor생성 함수 실행
        self.create_cursor()

        ##### 미리 정의해둔 디비 명을 for문으로 하나씩 확인
        for db_list in self.db_lists:

            ##### Information_schema을 활용해서 현재 생성되어 있는 DB를 체크 함
            db_check_query = "SELECT 1 FROM Information_schema.SCHEMATA WHERE SCHEMA_NAME = '{}'".format(db_list)
            self.cursor.execute(db_check_query)
            result = self.cursor.fetchall()

            ##### DB가 있을 경우 auto-trader UI에 결과 띄우기
            if len(result):
                data = "DB Check: {} ".format(db_list)
                self.finished_edit.emit(data)
                # self.mywidget.check_edit.append("DB Check: {} ".format(db_list))

            ##### DB가 없을 경우 auto-trader UI에 결과 띄우고 데이터베이스를 생성 한 후 다시 결과 띄우기
            else:

                # self.mywidget.check_edit.append("DB None!!: {} ".format(db_list))
                create_DB_Non_Exist = "CREATE DATABASE {}".format(db_list)
                self.cursor.execute(create_DB_Non_Exist)
                # self.mywidget.check_edit.append("<== DB Create : {} ==>".format(db_list))
                data = "<== DB Create : {} ==>".format(db_list)
                ##### emit으로 data signal변수에 data전달
                self.finished_edit.emit(data)

                ##### DB 생성후 다시 확인
                self.cursor.execute(db_check_query)
                result2 = self.cursor.fetchall()
                if len(result2):
                    # self.mywidget.check_edit.append("DB Check: {} ".format(db_list))
                    data = "DB Check: {} ".format(db_list)
                    ##### emit으로 data signal변수에 data전달
                    self.finished_edit.emit(data)
                else:
                    self.mywidget.check_edit.append("DB 생성오류: {} ".format(db_list))
                    data = "DB 생성오류: {} ".format(db_list)
                    ##### emit으로 data signal변수에 data전달
                    self.finished_edit.emit(data)

                    ##### cursor종료 함수 실행
        self.delete_cursor()

    ##### stocks_lists 체크, 상장사 목록이 기존에 수집한자료와 다른경우 생성
    def Get_Korea_Stocks_info(self):
        url = 'https://kind.krx.co.kr/corpgeneral/corpList.do'  # 1
        kosdaq = pd.read_html(url + "?method=download&marketType=kosdaqMkt",header=None)[0]  # 2
        kosdaq = kosdaq.iloc[1:]
        kospi = pd.read_html(url + "?method=download&marketType=stockMkt",header=None)[0]  # 3
        kospi = kospi.iloc[1:]
        merge=pd.concat([kospi,kosdaq])
        merge.columns=['Name', 'Symbol', '업종', '주요제품', '상장일', '결산월', '대표자명', '홈페이지', '지역']
        merge['Symbol']=merge['Symbol'].apply(lambda x: ('0'*6+str(x))[-6:])
        return merge

    def collect_stocks_lists_check(self):

        ##### cursor생성 함수 실행
        self.create_cursor()

        ##### stocks_lists DB로 이동
        query = "use stocks_lists"
        self.cursor.execute(query)

        ##### stocks_lists DB에 stocks_lists_all 테이블이 존재하는지 확인
        query = "SELECT 1 FROM Information_schema.tables WHERE table_schema = 'stocks_lists' AND table_name = 'stocks_lists_all'"
        self.cursor.execute(query)

        ##### 조회한 결과를 result변수에 저장
        result = self.cursor.fetchone()

        ##### cursor종료 함수 실행(아래에서 engine을 사용해야하기때문에 종료함)
        self.delete_cursor()

        ##### fdr라이브러리로 상장사 전체 목록 수집하고 전역변수에 저장
        #try:

        add_extra1 = {'Symbol': "ks11", "Name": "코스피지수"}
        add_extra2 = {'Symbol': "kq11", "Name": "코스닥지수"}
        self.stocks_lists_all = self.Get_Korea_Stocks_info()

        self.stocks_lists_all['Symbol']=['A'+str(x).zfill(6) for x in self.stocks_lists_all['Symbol']]
        #print(self.stocks_lists_all.head())
        self.stocks_lists_all = self.stocks_lists_all.append(add_extra1, ignore_index= True)
        self.stocks_lists_all = self.stocks_lists_all.append(add_extra2, ignore_index= True)

        #except:
        #    pass
        self.create_engine("system_parameter")
        table_df = pd.read_sql('jongmok_code_name', con=self.engine, index_col=None)
        table_df = table_df.set_index(table_df.columns[0])
        new_index = []
        '''
        for i in table_df.index:
            new_index.append(i.replace("A", ""))
        table_df.index = new_index
        '''
        self.stocks_lists_all['IFRS'] = None
        self.stocks_lists_all = self.stocks_lists_all.set_index('Symbol')
        for a in self.stocks_lists_all.index:
            try:
                self.stocks_lists_all['IFRS'].loc[a] = table_df.loc[a][0]
            except:
                self.stocks_lists_all['IFRS'].loc[a] = '개별'
        self.stocks_lists_all = self.stocks_lists_all.reset_index()
        self.delete_engine()

        ##### stocks_lists_all에 테이블이 없을 경우 즉시 상장사 목록 수집 함수 실행
        if result == None:
            self.collect_stocks_code()

        ##### stocks_lists_all에 테이블이 있는 경우 데이터의 전체 개수를 파악
        else:
            self.create_cursor()
            query = "use stocks_lists"
            self.cursor.execute(query)
            query = "SELECT COUNT(*) FROM stocks_lists_all"
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            ##### 테이블내에 전체 개수와 위에서 fdr라이브러리로 가지고 온 결과의 갯수를 비교
            ##### 같은 경우 결과를 UI에 띄우기
            if self.stocks_lists_all["Symbol"].count() == int(result[0]):
                data = "Table Check : stocks_lists_all"
                self.finished_edit.emit(data)

            ##### 다른경우 즉시 상장사 목록 수집 함수 실행
            else:
                self.collect_stocks_code()

    ##### 상장사 목록 수집
    def collect_stocks_code(self):
        ##### engine생성함수 실행, 사용할 db를 인수로 전달
        self.create_engine("stocks_lists")

        ##### 상장사 목록 저장, 대체방식 if_exists = 'replace'
        self.stocks_lists_all.to_sql(name="stocks_lists_all", con=self.engine, if_exists='replace')

        ##### engine종료함수 실행
        self.delete_engine()

        ##### 결과를 UI에 띄워주기
        data = "Update : stocks_lists_all"
        self.finished_edit.emit(data)


##@collector_base 종료 #############################################################################################


##@collector_price 시작#############################################################################################
class Collector_price(QThread, Create_DB):
    ##### 시그널 생성/mainUI에 정보 전달
    finished_edit = pyqtSignal(str)
    finished_price = pyqtSignal(int, int)

    def run(self):
        ##### 현재날짜 구하기 데이터 수집할때 체크를 위함
        self.price_start = '2000-01-01'
        self.current_time = datetime.datetime.now()
        self.stocks_price()



    ##### 가격정보(주가정보) 수집 함수
    def stocks_price(self):
        ##### 시그널에 데이터 전달
        data = "Update : stocks_price"
        self.finished_edit.emit(data)

        ##### DB접속 커서 생성 함수 실행
        self.create_cursor()

        ##### 종목리스트 수집 DB로 이동
        query = "use stocks_lists"
        self.cursor.execute(query)

        ##### 종목리스트 DB에서 종목코드와 종목명을 가지고옴
        ##### 현재 사용할 것은 종목코드이므로 종목코드만 가지고와도 됨
        query = "SELECT Symbol, Name FROM stocks_lists_all"
        self.cursor.execute(query)
        results = self.cursor.fetchall()

        ##### 현재는 필요 없으나 나중에 사용 할 수도 있기 때문에 dataframe에 저장 해둔다.
        #results_df = pd.DataFrame(results, columns=["Symbol", "Name"])

        ##### 생성한 커서 삭제, 삭제 하는 이유는 수집한 주가정보를 DB에 저장 할때 engine을 사용하기 위함
        self.delete_cursor()

        ##### 종목코드를 하나씩 가지고 온다.
        ##### 수집상태를 파악하기 위해 tpdm을 걸어준다.
        ##### tpdm은 터미널에 현황을 파악 할 수 있게 도와주며, 대략적인 시간도 측정한다.
        ##### 사실 DB에 정보를 수집하는 것은 UI에서 버튼을 만들어서 버튼 클릭시 수집하도록 할 예정이며,
        ##### 장이 마감되면 UI의 실행버튼을 자동으로 클릭 하도록 할 예정이다.
        ##### 따라서 UI에서 현재 진행상태를 PyQt의 progressbar위젯을 활용하는 방안이 더 좋을것 같다.

        ##### progressbar위젯 셋팅, widget클래스에 self.collection_progress = QProgressBar(self) 생성
        ##### 최대값이 될 기준을 상장사 목록 전체 갯수를 steps변수에 저장, 최대값이 됨
        ##### step은 for문이 한번돌때마다 1씩 증가 할 것이고 if step < steps if문이 거짓이 될때까지 count는 증가한다.
        steps = len(results)
        step = 0
        for symbol in tqdm.tqdm(results):
            if step < steps:
                step += 1
                self.finished_price.emit(int(steps), int(step))

            ##### 커서생성
            self.create_cursor()

            ##### 실제 주가 정보를 수집하기 전에 테이블을 체크 한다.
            ##### stocks_priceDB에 종목코드로 된 테이블의 존재여부를 파악한다.
            ##### 참고 테이블 명을 종목코드 그대로 하면 6자리의 숫자코드가 되는데
            ##### 숫자로 테이블 명을 정할 경우 테이블 조회할때 잘 찾지 못하는 경우가 있다.
            ##### 따라서 테이블 명은 a + 종목코드로 한다.
            query = "SELECT 1 FROM Information_schema.tables WHERE table_schema = 'stocks_price' AND table_name = +'a{}'".format(
                symbol[0].lower())
            self.cursor.execute(query)

            ##### 조회 결과는 테이블이 없을경우 None을 반환하고 있을 경우 1을 반환한다.
            if_exists = self.cursor.fetchone()

            ##### 커서를 종료한다.
            self.delete_cursor()

            ##### 종목코드수집 테이블이 없을 경우
            if if_exists == None:
                ##### DataReader로 종목별 주가정보를 가지고 온다.
                try : price_df = fdr.DataReader(symbol[0].replace("A",""), self.price_start)
                except : continue

                ##### 주가정보를 데이터프레임에 넣어준다.
                price_df = pd.DataFrame(price_df)

                ##### 날짜 컬럼이 인덱스이고 이 인덱스를 그대로 사용할 것이기때문에 인덱스를 초기화한다.
                price_df = price_df.reset_index()

                ##### 간혹 주가정보가 없는 경우도 있기때문에 empty메서드로 데이터프레임이 빈데이터프레임인지 확인한다.
                if price_df.empty == True:
                    ##### 빈데이터프레임일 경우 pass
                    pass

                ##### 주가정보를 담은 데이터프레임이 빈것이 아닐 경우 engine으로 db에 저장한다.
                ##### 저장 방식은 테이블이 존재할 경우 append로 정의 하고 인덱스는 무시한다.
                ##### 인덱스를 무시하지 않을 경우 자동으로 0부터 채번되고, 무시 할경우 날짜 컬럼이 인덱스라인에 들어간다.
                else:
                    self.create_engine("stocks_price")
                    if (str(symbol[0].lower()) == "ks11" or str(symbol[0].lower()) =="kq11"):
                        price_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='replace',
                                        index=False)
                    else :
                        price_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='replace', index=False)
                    self.delete_engine()

            ##### 가장 상위의 if에서 테이블이 있는지 없는지 확인해서 없는 경우를 실행 완료 했고
            ##### 이번에는 테이블이 있는 경우를 실행한다.
            else:
                ##### 커서를 생성한다. 앞에서 engine을 사용했을 수도 있기 때문에 다시 커서를 생성해야한다.
                self.create_cursor()

                ##### stocks_price DB로 이동
                query = "use stocks_price"
                self.cursor.execute(query)

                ##### 이번에는 테이블은 있지만 테이블 내에 데이터가 없는 경우도 있을 것을 가정해서 다시한번 체크한다.
                ##### SELECT * FROM {}은 테이블을 모두가지고 오라라는 쿼리
                ##### 그것을 다시 SELECT EXISTS로 데이터의 존재 여부를 확인
                ##### 존재 할 경우 1을 존재 하지 않을 경우 0을 반환한다.
                if (str(symbol[0].lower()) == "ks11" or str(symbol[0].lower()) == "kq11"):
                    query = "SELECT EXISTS (SELECT * FROM {}) as success".format(str(symbol[0].lower()))
                else :
                    query = "SELECT EXISTS (SELECT * FROM {}) as success".format(str(symbol[0].lower()))
                self.cursor.execute(query)
                if_exists = self.cursor.fetchone()
                ##### 우선 테이블 내에 데이터가 존재 할 경우를 실행 한다.
                if if_exists[0] == 1:

                    ##### 테이블 내에 데이터가 존재 할 경우 가장 최근에 수집한 날짜 이후부터 수집해야함
                    ##### 그렇지 않고 그냥 수집 했을 경우 쓸모없는 데이터가 많아짐으로 용량을 많이 차지함.
                    ##### 물론 다 수집해서 테이블의 중복데이터를 삭제 해주는 쿼리를 써도 됨
                    ##### SELECT * FROM {} 는 테이블의 데이터를 어떠한 조건으로 가지고오라는 쿼리
                    ##### ORDER BY Date DESC 는 Date컬럼을 내림차순으로 정렬하고 (ASC는 오름차순, DESC는 내림차순)
                    ##### LIMIT 1 은 최근 데이터 1개를 가지고 오라는 쿼리 (숫자를 2, 3 넣으면 2개, 3개 가지고온다.)
                    if (str(symbol[0].lower()) == "ks11" or str(symbol[0].lower()) == "kq11"):
                        query = "SELECT * FROM {} ORDER BY Date DESC LIMIT 1".format(str(symbol[0].lower()))
                    else :
                        query = "SELECT * FROM {} ORDER BY Date DESC LIMIT 1".format(str(symbol[0].lower()))
                    self.cursor.execute(query)

                    ##### 최근의 날짜의 행을 가지고 와서 date변수에 저장
                    date = self.cursor.fetchone()

                    ##### date[0] 은 행을 가지고 오면 튜플형태로 반환되기 때문에 그중에 날짜데이터만 필요함으로 사용
                    ##### 기존날짜에 하루를 더함, 하루를 더하는 이유는 최근날짜 다음날부터 재수집하기 위함
                    target_date = date[0] + datetime.timedelta(days=1)

                    ##### 날짜 형태 변환, 이것은 크게 중요하지 않다.
                    ##### DataReader에 시작 날짜를 넣을때 사용하고자 함인데, 그냥 datetime형태로 넣어도 됨
                    target_date = target_date.strftime("%Y-%m-%d")

                    ##### 상단에서 오늘날짜를 구해놓은 것을 활용해서 오늘날짜에 하루를 더함
                    ##### 이유는 target_date와 동일
                    current_time = self.current_time + datetime.timedelta(days=1)
                    current_time = current_time.strftime("%Y-%m-%d")

                    ##### 두날짜를 비교해서 동일하면 그냥 넘어감
                    if current_time == target_date:
                        pass

                    ##### 두날짜가 일치 하지 않은경우 DataReader로 주가 수집, 이하 코드 위의
                    ##### 1차if에서 사용한것과 동일
                    else:
                        try : price_df = fdr.DataReader(symbol[0], target_date)
                        except  : continue
                        price_df = pd.DataFrame(price_df)
                        price_df = price_df.reset_index()
                        self.delete_cursor()
                        if price_df.empty == True:
                            pass
                        else:
                            self.create_engine("stocks_price")
                            if (str(symbol[0].lower()) == "ks11" or str(symbol[0].lower()) == "kq11"):
                                price_df.to_sql(name = str(symbol[0].lower()), con=self.engine, if_exists='replace',
                                                index=False)
                            else :
                                price_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='replace',
                                            index=False)

                            self.delete_engine()
                ##### 위에서 테이블 내에 데이터가 존재 할 경우를 실행 완료 했으며,
                ##### 테이블 내에 데이터가 없을 경우를 실행
                ##### 한번더 실행 하는 이유는 간홀 데이터 수집도중에 오류나 에러에 의해서 중단될 경우
                ##### 테이블은 생성되었는데 데이터 저장이 안될수도 있음
                ##### 그래서 혹시 모르니 한번더 실행
                else:
                    try : price_df = fdr.DataReader(symbol[0], '1990-01-01')
                    except : continue
                    price_df = pd.DataFrame(price_df)
                    price_df = price_df.reset_index()
                    if price_df.empty == True:
                        pass
                    else:
                        self.create_engine("stocks_price")
                        if (str(symbol[0].lower()) == "ks11" or str(symbol[0].lower()) == "kq11"):
                            price_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='replace',
                                            index=False)
                        else :
                            price_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='replace',
                                        index=False)
                        self.delete_engine()
        data = "Update : stocks_close_price"
        self.finished_edit.emit(data)
        self.db = DataBase.MySQL_control.DB_control()
        temp = self.db.DB_LOAD_Close_Price_Data('1999-01-01')
        self.db.DB_SAVE_Price_Data(temp)

        data = "Complete : stocks_price"
        self.finished_edit.emit(data)  # 시그널을 발생시켜서 mainclass에 정보 전달


##@collector_price 종료#############################################################################################


##@collector_finance 시작#############################################################################################

class Collector_finance(QThread, Create_DB):
    ##### 시그널 생성/mainUI에 정보 전달
    finished_edit = pyqtSignal(str)
    finished_finance = pyqtSignal(int, int)

    def run(self):

        ##### 현재날짜 구하기 데이터 수집할때 체크를 위함
        self.current_time = datetime.datetime.now()

        self.stocks_finance()

    def stocks_finance(self):
        try:
            api_key = 'c20e3bbef3e51058473e1ac22681725435663867'
            dart = OpenDartReader(api_key)

            ##### 시그널에 데이터 전달
            data = "Update : stocks_finance"
            self.finished_edit.emit(data)

            ##### 커서생성
            self.create_cursor()

            ##### DB접속 커서 생성 함수 실행
            self.create_cursor()

            ##### 종목리스트 수집 DB로 이동
            query = "use stocks_lists"
            self.cursor.execute(query)

            ##### 종목리스트 DB에서 종목코드와 종목명을 가지고옴
            ##### 현재 사용할 것은 종목코드이므로 종목코드만 가지고와도 됨
            query = "SELECT Symbol, Name FROM stocks_lists_all"
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            ##### 생성한 커서 삭제, 삭제 하는 이유는 수집한 주가정보를 DB에 저장 할때 engine을 사용하기 위함
            self.delete_cursor()

            ##### 프로그래스 바에 정보 전달 할 것
            steps = len(results)
            step = 0
            for symbol in tqdm.tqdm(results):
                ##### 프로그래스바에 띄울 내용
                if step < steps:
                    step += 1
                    self.finished_finance.emit(int(steps), int(step))

                ##### 커서생성
                self.create_cursor()

                ##### DB체크
                query = "SELECT 1 FROM Information_schema.tables WHERE table_schema = 'stocks_finance' AND table_name = +'a{}'".format(
                    symbol[0].lower())
                self.cursor.execute(query)

                ##### 조회 결과는 테이블이 없을경우 None을 반환하고 있을 경우 1을 반환한다.
                if_exists = self.cursor.fetchone()

                ##### 커서를 종료한다.
                self.delete_cursor()

                ##### 테이블이 없으면 생성해야하는데 그전에 한번더 확인한다.
                ##### 최근 재무제표가 없으면 테이블생성도 할필요가 없음
                try:
                    finance_db_check = dart.finstate(symbol[0], self.current_time.year - 1, reprt_code="11011")
                    finance_db_check = pd.DataFrame(finance_db_check)
                    if finance_db_check.empty == True:
                        pass
                    else:
                        ##### 테이블이 없을경우 테이블 생성, 컬럼부터 생성
                        if if_exists == None:

                            db_col = ["date", "cfs_crt_asset", "cfs_n_crt_asset", "cfs_total_asset",
                                      "cfs_crt_liability",
                                      "cfs_n_crt_liability", "cfs_total_liability", "cfs_equity",
                                      "cfs_retained_earnings",
                                      "cfs_total_equity", "cfs_sales", "cfs_operating_income", "cfs_before_income_tax",
                                      "cfs_net_income", "ofs_crt_asset", "ofs_n_crt_asset", "ofs_total_asset",
                                      "ofs_crt_liability", "ofs_n_crt_liability", "ofs_total_liability", "ofs_equity",
                                      "ofs_retained_earnings", "ofs_total_equity", "ofs_sales", "ofs_operating_income",
                                      "ofs_before_income_tax", "ofs_net_income"]

                            ##### dataframe을 생성하고 db_col변수를 컬럼으로 지정한다.
                            base_df = pd.DataFrame(data=None, index=None, columns=db_col)

                            ##### 컬럼을 만들어넣은 데이터프레임을 엔진으로 간편하게 삽입
                            ##### 컬럼은 create하면서 설정해주면 되지만, 컬럼성격 설정이 귀찮음
                            ##### 그리고 중요한건 opendart에서 가지고 오는 방식이 문자열, 간혹 이상한문자도 섞여있어서 특정짓기 어려움
                            self.create_engine("stocks_finance")
                            base_df.to_sql(name=str(symbol[0].lower()), con=self.engine, if_exists='fail',
                                           index=False)
                            self.delete_engine()

                            ##### range함수로 조회할 연도를 만듬, +1은 range함수가 마지막숫자는 빼고 만들기때문임
                            for i in range(2016, self.current_time.year + 1):
                                target_years = i

                                ##### 문서코드 분기를 나타냄
                                report_codes = ["11013", "11012", "11014", "11011"]
                                for report_code in report_codes:

                                    try:
                                        finance_df = dart.finstate(symbol[0], target_years, reprt_code=report_code)

                                        finance_df = pd.DataFrame(finance_df)

                                        ##### 데이터를 저장할때 데이터의 압단에 date를 만들어 줘야한다.
                                        ##### 분기이기때문에 target_years를 활용하여 분기별로 변수로 만들수 있다.
                                        if report_code == "11013":
                                            ind = str(target_years) + "_" + "1Q"
                                        if report_code == "11012":
                                            ind = str(target_years) + "_" + "2Q"
                                        if report_code == "11014":
                                            ind = str(target_years) + "_" + "3Q"
                                        if report_code == "11011":
                                            ind = str(target_years) + "_" + "4Q"

                                            ##### 데이터프레임이 비었을 경우 pass
                                        if finance_df.empty == True:
                                            pass

                                        else:
                                            ##### 연결과 개별을 구분하는 fs_div컬럼과 계정컬럼 account_nm을 합처서 새로운 컬럼에 넣는다.
                                            ##### 신규 컬럼의 한글 계정명을 위에서 미리 구성한 계정명과 일치시키기위해 replace한다.
                                            ##### replace하는 작업이 번거롭기 때문에 엑셀을 사용해서 & 수식으로 최대한 편리하게 사용할수있다.
                                            ##### 더 좋은 방법을 알게되면 꼭 기록이 필요하다.

                                            finance_df["account_name"] = finance_df["fs_div"] + "_" + finance_df[
                                                "account_nm"]
                                            finance_df["account_name"] = finance_df["account_name"].replace('CFS_유동자산',
                                                                                                            "cfs_crt_asset").replace(
                                                'CFS_비유동자산', "cfs_n_crt_asset").replace('CFS_자산총계',
                                                                                        "cfs_total_asset").replace(
                                                'CFS_유동부채', "cfs_crt_liability").replace('CFS_비유동부채',
                                                                                         "cfs_n_crt_liability").replace(
                                                'CFS_부채총계', "cfs_total_liability").replace('CFS_자본금', "cfs_equity")
                                            finance_df["account_name"] = finance_df["account_name"].replace('CFS_이익잉여금',
                                                                                                            "cfs_retained_earnings").replace(
                                                'CFS_자본총계', "cfs_total_equity").replace('CFS_매출액', "cfs_sales").replace(
                                                'CFS_영업이익', "cfs_operating_income").replace('CFS_법인세차감전 순이익',
                                                                                            "cfs_before_income_tax").replace(
                                                'CFS_당기순이익', "cfs_net_income").replace('OFS_유동자산',
                                                                                       "ofs_crt_asset").replace(
                                                'OFS_비유동자산', "ofs_n_crt_asset").replace('OFS_자산총계',
                                                                                        "ofs_total_asset").replace(
                                                'OFS_유동부채', "ofs_crt_liability").replace('OFS_비유동부채',
                                                                                         "ofs_n_crt_liability").replace(
                                                'OFS_부채총계', "ofs_total_liability").replace('OFS_자본금',
                                                                                           "ofs_equity").replace(
                                                'OFS_이익잉여금', "ofs_retained_earnings").replace('OFS_자본총계',
                                                                                              "ofs_total_equity").replace(
                                                'OFS_매출액', "ofs_sales").replace('OFS_영업이익',
                                                                                "ofs_operating_income").replace(
                                                'OFS_법인세차감전 순이익', "ofs_before_income_tax").replace('OFS_당기순이익',
                                                                                                   "ofs_net_income")
                                            ##### 사전작업을 마친 계정명을 컬럼으로 넣기 위해 리스트 자료형으로 변형한다.
                                            col = finance_df["account_name"].to_list()

                                            ##### 사전준비가 모두 끝났기 때문에 데이터 수집이 끝난것을 딕셔너리 형태로 묶어준다.
                                            ##### T메서드를 이용해서 열로 구성되어있는 자료를 행으로 변환한다.
                                            ##### columns을 지정한다.
                                            ##### 기존에 DB에 만들어둔 컬럼에는 index를 지정하지 않았기 때문에
                                            ##### 현재의 ind도 reset시켜서 컬럼화 시킨다.
                                            ##### 컬럼화시킨 ind는 자동으로 index라는 컬럼을 가지게 되기때문에 date로 변형한다.

                                            temp_df = pd.DataFrame({ind: finance_df["thstrm_amount"]})
                                            temp_df = temp_df.T
                                            temp_df.columns = col
                                            temp_df = temp_df.reset_index()
                                            temp_df.rename(columns={'index': 'date'}, inplace=True)

                                            ##### db에 저장한다 기존의 컬럼을 구성할때와 같은방식으로 해야한다.
                                            ##### db에 저장을 많이 할 필요가 있다면 함수로 구성하는 방법도 있다.
                                            ##### if_exists옵션을 append로 하지 않고 replace로 할 수 있지만 비효율적이다.
                                            ##### 대신 stocks_finance_sub DB를 체크 할 DB를 생성 해서 stocks_finance_sub에 언제의 정보가
                                            ##### 최근정보인지를 체크 하게 하고 최근정보가 없을 경우 신규로 받을 수 있도록 구성이 필요하다.
                                            ##### 이방법으로 할 경우 DB를 업데이트 하는데 시간적 효율성을 확보 할 수 있다.
                                            self.create_engine("stocks_finance")
                                            temp_df.to_sql(name=str(symbol[0].lower()), con=self.engine,
                                                           if_exists='append', index=False)
                                            self.delete_engine()

                                    except TypeError:
                                        continue

                        else:
                            self.create_cursor()

                            ##### stocks_finance DB로 이동
                            query = "use stocks_finance"
                            self.cursor.execute(query)

                            ##### 이번에는 테이블은 있지만 테이블 내에 데이터가 없는 경우도 있을 것을 가정해서 다시한번 체크한다.
                            ##### SELECT * FROM {}은 테이블을 모두가지고 오라라는 쿼리
                            ##### 그것을 다시 SELECT EXISTS로 데이터의 존재 여부를 확인
                            ##### 존재 할 경우 1을 존재 하지 않을 경우 0을 반환한다.
                            query = "SELECT EXISTS (SELECT * FROM {}) as success".format(str(symbol[0].lower()))
                            self.cursor.execute(query)
                            if_exists = self.cursor.fetchone()

                            ##### 테이블 내에 데이터가 존재 할 경우를 실행 한다.
                            if if_exists[0] == 1:
                                query = "SELECT * FROM {} ORDER BY Date DESC LIMIT 1".format(
                                    str(symbol[0].lower()))
                                self.cursor.execute(query)

                                ##### 최근의 날짜의 행을 가지고 와서 date변수에 저장
                                date = self.cursor.fetchone()
                                date = date[0]
                                date_target_year = int(date[:4])
                                date_target_month = date[5:]

                                ##### 최근데이가 있는경우 그이후부터 수집하기 위해 변수를 경우에따라 생성
                                # report_codes = ["11013""11012","11014","11011"]
                                if date_target_month == "1Q":
                                    date = date_target_year
                                    report_codes = ["11012", "11014", "11011"]
                                if date_target_month == "2Q":
                                    date = date_target_year
                                    report_codes = ["11014", "11011"]
                                if date_target_month == "3Q":
                                    date = date_target_year
                                    report_codes = ["11011"]
                                if date_target_month == "4Q":
                                    date = date_target_year + 1
                                    report_codes = ["11013", "11012", "11014", "11011"]

                                ##### db의 최근데이터를 가지고 와서 이후 연도를 만듬
                                for i in range(date, self.current_time.year + 1):
                                    target_years = i

                                    for report_code in report_codes:

                                        try:
                                            finance_df = dart.finstate(symbol[0], target_years, reprt_code=report_code)

                                            finance_df = pd.DataFrame(finance_df)

                                            ##### 데이터를 저장할때 데이터의 압단에 date를 만들어 줘야한다.
                                            ##### 분기이기때문에 target_years를 활용하여 분기별로 변수로 만들수 있다.
                                            if report_code == "11013":
                                                ind = str(target_years) + "_" + "1Q"
                                            if report_code == "11012":
                                                ind = str(target_years) + "_" + "2Q"
                                            if report_code == "11014":
                                                ind = str(target_years) + "_" + "3Q"
                                            if report_code == "11011":
                                                ind = str(target_years) + "_" + "4Q"

                                            if finance_df.empty == True:
                                                pass
                                            else:
                                                ##### 연결과 개별을 구분하는 fs_div컬럼과 계정컬럼 account_nm을 합처서 새로운 컬럼에 넣는다.
                                                ##### 신규 컬럼의 한글 계정명을 위에서 미리 구성한 계정명과 일치시키기위해 replace한다.
                                                ##### replace하는 작업이 번거롭기 때문에 엑셀을 사용해서 & 수식으로 최대한 편리하게 사용할수있다.
                                                ##### 더 좋은 방법을 알게되면 꼭 기록이 필요하다.

                                                finance_df["account_name"] = finance_df["fs_div"] + "_" + finance_df[
                                                    "account_nm"]
                                                finance_df["account_name"] = finance_df["account_name"].replace(
                                                    'CFS_유동자산', "cfs_crt_asset").replace('CFS_비유동자산',
                                                                                         "cfs_n_crt_asset").replace(
                                                    'CFS_자산총계', "cfs_total_asset").replace('CFS_유동부채',
                                                                                           "cfs_crt_liability").replace(
                                                    'CFS_비유동부채', "cfs_n_crt_liability").replace('CFS_부채총계',
                                                                                                "cfs_total_liability").replace(
                                                    'CFS_자본금', "cfs_equity").replace('CFS_이익잉여금',
                                                                                     "cfs_retained_earnings").replace(
                                                    'CFS_자본총계', "cfs_total_equity").replace('CFS_매출액',
                                                                                            "cfs_sales").replace(
                                                    'CFS_영업이익', "cfs_operating_income").replace('CFS_법인세차감전 순이익',
                                                                                                "cfs_before_income_tax").replace(
                                                    'CFS_당기순이익', "cfs_net_income").replace('OFS_유동자산',
                                                                                           "ofs_crt_asset").replace(
                                                    'OFS_비유동자산', "ofs_n_crt_asset").replace('OFS_자산총계',
                                                                                            "ofs_total_asset").replace(
                                                    'OFS_유동부채', "ofs_crt_liability").replace('OFS_비유동부채',
                                                                                             "ofs_n_crt_liability").replace(
                                                    'OFS_부채총계', "ofs_total_liability").replace('OFS_자본금',
                                                                                               "ofs_equity").replace(
                                                    'OFS_이익잉여금', "ofs_retained_earnings").replace('OFS_자본총계',
                                                                                                  "ofs_total_equity").replace(
                                                    'OFS_매출액', "ofs_sales").replace('OFS_영업이익',
                                                                                    "ofs_operating_income").replace(
                                                    'OFS_법인세차감전 순이익', "ofs_before_income_tax").replace('OFS_당기순이익',
                                                                                                       "ofs_net_income")

                                                ##### 사전작업을 마친 계정명을 컬럼으로 넣기 위해 리스트 자료형으로 변형한다.
                                                col = finance_df["account_name"].to_list()

                                                ##### 사전준비가 모두 끝났기 때문에 데이터 수집이 끝난것을 딕셔너리 형태로 묶어준다.
                                                ##### T메서드를 이용해서 열로 구성되어있는 자료를 행으로 변환한다.
                                                ##### columns을 지정한다.
                                                ##### 기존에 DB에 만들어둔 컬럼에는 index를 지정하지 않았기 때문에
                                                ##### 현재의 ind도 reset시켜서 컬럼화 시킨다.
                                                ##### 컬럼화시킨 ind는 자동으로 index라는 컬럼을 가지게 되기때문에 date로 변형한다.

                                                temp_df = pd.DataFrame({ind: finance_df["thstrm_amount"]})
                                                temp_df = temp_df.T
                                                temp_df.columns = col
                                                temp_df = temp_df.reset_index()
                                                temp_df.rename(columns={'index': 'date'}, inplace=True)

                                                ##### db에 저장한다 기존의 컬럼을 구성할때와 같은방식으로 해야한다.
                                                ##### db에 저장을 많이 할 필요가 있다면 함수로 구성하는 방법도 있다.
                                                ##### if_exists옵션을 append로 하지 않고 replace로 할 수 있지만 비효율적이다.
                                                ##### 대신 stocks_finance_sub DB를 체크 할 DB를 생성 해서 stocks_finance_sub에 언제의 정보가
                                                ##### 최근정보인지를 체크 하게 하고 최근정보가 없을 경우 신규로 받을 수 있도록 구성이 필요하다.
                                                ##### 이방법으로 할 경우 DB를 업데이트 하는데 시간적 효율성을 확보 할 수 있다.
                                                self.create_engine("stocks_finance")
                                                temp_df.to_sql(name=str(symbol[0].lower()), con=self.engine,
                                                               if_exists='append', index=False)
                                                self.delete_engine()

                                        except TypeError:
                                            continue

                            else:
                                report_codes = ["11013", "11012", "11014", "11011"]
                                for i in range(2016, self.current_time.year + 1):
                                    target_years = i

                                    for report_code in report_codes:

                                        try:
                                            finance_df = dart.finstate(symbol[0], target_years, reprt_code=report_code)

                                            finance_df = pd.DataFrame(finance_df)

                                            ##### 데이터를 저장할때 데이터의 압단에 date를 만들어 줘야한다.
                                            ##### 분기이기때문에 target_years를 활용하여 분기별로 변수로 만들수 있다.
                                            if report_code == "11013":
                                                ind = str(target_years) + "_" + "1Q"
                                            if report_code == "11012":
                                                ind = str(target_years) + "_" + "2Q"
                                            if report_code == "11014":
                                                ind = str(target_years) + "_" + "3Q"
                                            if report_code == "11011":
                                                ind = str(target_years) + "_" + "4Q"

                                            if finance_df.empty == True:
                                                pass
                                            else:
                                                ##### 연결과 개별을 구분하는 fs_div컬럼과 계정컬럼 account_nm을 합처서 새로운 컬럼에 넣는다.
                                                ##### 신규 컬럼의 한글 계정명을 위에서 미리 구성한 계정명과 일치시키기위해 replace한다.
                                                ##### replace하는 작업이 번거롭기 때문에 엑셀을 사용해서 & 수식으로 최대한 편리하게 사용할수있다.
                                                ##### 더 좋은 방법을 알게되면 꼭 기록이 필요하다.

                                                finance_df["account_name"] = finance_df["fs_div"] + "_" + finance_df[
                                                    "account_nm"]
                                                finance_df["account_name"] = finance_df["account_name"].replace(
                                                    'CFS_유동자산', "cfs_crt_asset").replace('CFS_비유동자산',
                                                                                         "cfs_n_crt_asset").replace(
                                                    'CFS_자산총계', "cfs_total_asset").replace('CFS_유동부채',
                                                                                           "cfs_crt_liability").replace(
                                                    'CFS_비유동부채', "cfs_n_crt_liability").replace('CFS_부채총계',
                                                                                                "cfs_total_liability").replace(
                                                    'CFS_자본금', "cfs_equity").replace('CFS_이익잉여금',
                                                                                     "cfs_retained_earnings").replace(
                                                    'CFS_자본총계', "cfs_total_equity").replace('CFS_매출액',
                                                                                            "cfs_sales").replace(
                                                    'CFS_영업이익', "cfs_operating_income").replace('CFS_법인세차감전 순이익',
                                                                                                "cfs_before_income_tax").replace(
                                                    'CFS_당기순이익', "cfs_net_income").replace('OFS_유동자산',
                                                                                           "ofs_crt_asset").replace(
                                                    'OFS_비유동자산', "ofs_n_crt_asset").replace('OFS_자산총계',
                                                                                            "ofs_total_asset").replace(
                                                    'OFS_유동부채', "ofs_crt_liability").replace('OFS_비유동부채',
                                                                                             "ofs_n_crt_liability").replace(
                                                    'OFS_부채총계', "ofs_total_liability").replace('OFS_자본금',
                                                                                               "ofs_equity").replace(
                                                    'OFS_이익잉여금', "ofs_retained_earnings").replace('OFS_자본총계',
                                                                                                  "ofs_total_equity").replace(
                                                    'OFS_매출액', "ofs_sales").replace('OFS_영업이익',
                                                                                    "ofs_operating_income").replace(
                                                    'OFS_법인세차감전 순이익', "ofs_before_income_tax").replace('OFS_당기순이익',
                                                                                                       "ofs_net_income")

                                                ##### 사전작업을 마친 계정명을 컬럼으로 넣기 위해 리스트 자료형으로 변형한다.
                                                col = finance_df["account_name"].to_list()

                                                ##### 사전준비가 모두 끝났기 때문에 데이터 수집이 끝난것을 딕셔너리 형태로 묶어준다.
                                                ##### T메서드를 이용해서 열로 구성되어있는 자료를 행으로 변환한다.
                                                ##### columns을 지정한다.
                                                ##### 기존에 DB에 만들어둔 컬럼에는 index를 지정하지 않았기 때문에
                                                ##### 현재의 ind도 reset시켜서 컬럼화 시킨다.
                                                ##### 컬럼화시킨 ind는 자동으로 index라는 컬럼을 가지게 되기때문에 date로 변형한다.

                                                temp_df = pd.DataFrame({ind: finance_df["thstrm_amount"]})
                                                temp_df = temp_df.T
                                                temp_df.columns = col
                                                temp_df = temp_df.reset_index()
                                                temp_df.rename(columns={'index': 'date'}, inplace=True)

                                                ##### db에 저장한다 기존의 컬럼을 구성할때와 같은방식으로 해야한다.
                                                ##### db에 저장을 많이 할 필요가 있다면 함수로 구성하는 방법도 있다.
                                                ##### if_exists옵션을 append로 하지 않고 replace로 할 수 있지만 비효율적이다.
                                                ##### 대신 stocks_finance_sub DB를 체크 할 DB를 생성 해서 stocks_finance_sub에 언제의 정보가
                                                ##### 최근정보인지를 체크 하게 하고 최근정보가 없을 경우 신규로 받을 수 있도록 구성이 필요하다.
                                                ##### 이방법으로 할 경우 DB를 업데이트 하는데 시간적 효율성을 확보 할 수 있다.
                                                self.create_engine("stocks_finance")
                                                temp_df.to_sql(name=str(symbol[0].lower()), con=self.engine,
                                                               if_exists='append', index=False)
                                                self.delete_engine()
                                        except TypeError:
                                            continue
                except TypeError:
                    continue


        except ValueError:
            ##### 시그널에 데이터 전달
            data = "Update Stop(limit) : stocks_finance"
            self.finished_edit.emit(data)

        ##@collector_finance 종료#############################################################################################


if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    trader = Trader()

    trader.show()
    app.exec_()
