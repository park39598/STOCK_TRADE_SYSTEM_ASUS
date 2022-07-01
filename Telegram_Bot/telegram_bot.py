import os
import time
import telegram
from PyQt5.QtCore import QThread, pyqtSignal
from telegram.ext import Updater
from telegram.ext import CommandHandler
import FinanceDataReader as fdr
import DataBase.MySQL_control
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.family'] = 'Malgun Gothic'
import six
from Kiwoom.CMD_DEFINE import *
from config.log_class import Logging

class TeleBot(QThread):
    kw_func_req = pyqtSignal(list)
    #dict_updata = pyqtSignal()
    def __init__(self, data_queue, logging):
        super().__init__()
        self.logging = logging
        self.kw_get_que = data_queue
        self.DB = DataBase.MySQL_control.DB_control()
        #pbj_stockbot token
        #self.token = '2111552958:AAFcTY2nJIGt1EWeJ2klZ9m-mjVM5dU0b2g'
        # pbj8524_bot token
        self.token = '5364399476:AAGRyVaGvvqghjMqMYCj9gEYweYhLcuMOdY'
        self.bot = telegram.Bot(self.token)
        update = self.bot.getUpdates()
        #self.chat_id = update[0].message.chat_id
        self.chat_id = 931477629
        # updater
        updater = Updater(token=self.token, use_context=True)
        self.dispatcher = updater.dispatcher
        self.Set_Telegram_CommandHandler(price_CMD.replace('/',""), self.price)
        self.Set_Telegram_CommandHandler(rim_CMD.replace('/', ""), self.rim)
        self.Set_Telegram_CommandHandler(help_CMD.replace('/', ""), self.help)
        self.Set_Telegram_CommandHandler(kw_condition_sort_CMD.replace('/', ""), self.Kw_Func_Req)
        self.Set_Telegram_CommandHandler(fdr_Index_CMD.replace('/', ""), self.Fdr_Index)
        self.Set_Telegram_CommandHandler(meme_CMD.replace('/', ""), self.Kw_Func_Req)

        # polling
        updater.start_polling()

    def Set_Telegram_CommandHandler(self, CMD, Func):
        start_handler = CommandHandler(CMD, Func)
        self.dispatcher.add_handler(start_handler)

    def Fdr_Index(self,update, context):
        user_text = update.message.text
        temp_str = user_text.split(" ")

        if len(temp_str[1].split("_")) != 2:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Fdr Index 커맨드에 맞게 다시 입력해주세요!")
            context.bot.send_message(chat_id=update.effective_chat.id, text="/b 지수명_시작날짜")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="{}데이터를 확인중입니다^^.....".format(str(temp_str[1].split("_")[0])))
            index_name=str(temp_str[1].split("_")[0])
            start_day=str(temp_str[1].split("_")[1])
            try:
                df = fdr.DataReader(index_name, start_day)
                plt.plot(df['Close'])
                plt.savefig("USD_KRW.png")
                time.sleep(2)
                plt.cla()
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="데이타 로딩완료~!")
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("USD_KRW.png", 'rb'))
                time.sleep(1)
                os.remove("USD_KRW.png")
            except:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="올바른 지수명을 입력바랍니다~")
    def help(self,update, context):
        help_msg="price 조회 : /p 종목명\r\n" \
                 "rim 가격 : /r 종목명\r\n" \
                 "조건식리스트 : /a 종목명\r\n" \
                 "조건검색 종목조회 : /s 조건검색식명\r\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg)
        context.bot.send_message(chat_id=update.effective_chat.id, text="지수조회 : /b 지수명_Start_Year")
        for i in list(range(2,10)):
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("fdr_지수_명령어"+str(i)+".png", 'rb'))
            time.sleep(1)

    def Kw_Func_Req(self, update, context):
        #user_id = update.effective_chat.id
        user_text = update.message.text
        temp_str = user_text.split(" ")
        self.temp_update=update
        self.temp_context=context
        self.kw_func_req.emit([temp_str[0],temp_str[1]])

    def Send_Bot_Msg(self, data):
        if data[0] == kw_condition_sort_CMD :
            if len(data)!=0:
                file=self.render_mpl_table(data[1], header_columns=1, col_width=1.5, row_height=0.5, font_size=9)
                self.temp_context.bot.send_photo(chat_id=self.temp_update.effective_chat.id, photo=open(file, 'rb'))
                os.remove(file)
                del(self.temp_update,self.temp_context)
            else:
                self.temp_context.bot.send_message(chat_id=self.temp_update.effective_chat.id, text="검색되는 종목이 없습니다 ㅅㅂ TT")
        elif data[0] == meme_CMD:
            if len(data)!=1:
                df = pd.DataFrame(data=data[1])
                df=df.T
                file=self.render_mpl_table(df, header_columns=1, col_width=1.5, row_height=0.5, font_size=9)
                self.temp_context.bot.send_photo(chat_id=self.temp_update.effective_chat.id, photo=open(file, 'rb'))
                os.remove(file)
                del(self.temp_update,self.temp_context)
            else:
                self.temp_context.bot.send_message(chat_id=self.temp_update.effective_chat.id, text="주문이 전달되지 못했습니다TT")

        elif data[0] == message_CMD:
            self.bot.send_message(chat_id=self.chat_id, text=str(data[1]))

        else:
            pass

    def price(self, update, context):
        user_id = update.effective_chat.id
        user_text = update.message.text
        temp_str = user_text.split(" ")
        if len(temp_str[1].split("_")) != 1:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Price 커맨드에 맞게 다시 입력해주세요!")
            context.bot.send_message(chat_id=update.effective_chat.id, text="/p 종목명")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="종목의 현재가를 Load 합니다^^.....")
            temp=self.DB.DB_LOAD_TABLE_LIST("stocks_rim")
            temp_df=self.DB.DB_LOAD_Table("stocks_rim",temp[-1])
            temp_df = temp_df.reset_index().set_index("종목")
            stock_name=temp_str[1].split("_")
            stock_code=temp_df.loc[stock_name]['CODE'][0]
            df = fdr.DataReader(stock_code.replace("A",""))
            cur_price = str(df['Close'][-1])
            context.bot.send_message(chat_id=update.effective_chat.id, text=cur_price)
            del temp_df

    def rim(self, update, context):
        user_id = update.effective_chat.id
        user_text = update.message.text
        temp_str = user_text.split(" ")
        if len(temp_str[1].split("_")) != 1:
            context.bot.send_message(chat_id=update.effective_chat.id, text="rim 커맨드에 맞게 다시 입력해주세요!")
            context.bot.send_message(chat_id=update.effective_chat.id, text="/rim 종목명")
        else:
            try:
                context.bot.send_message(chat_id=update.effective_chat.id, text="종목의 rim 가치평가액을 Load 합니다^^.....")
                temp = self.DB.DB_LOAD_TABLE_LIST("stocks_가치평가")
                temp_df = self.DB.DB_LOAD_Table("stocks_가치평가", temp[-1])
                temp_df = temp_df.reset_index().set_index("종목")
                temp_df.columns = [x.replace(" ","") for x in temp_df.columns]
                stock_name = temp_str[1].split("_")
                rim_price = temp_df.loc[stock_name]['RIM(원)'][0]
                context.bot.send_message(chat_id=update.effective_chat.id, text=rim_price)
            except:
                context.bot.send_message(chat_id=update.effective_chat.id, text="찾으시는 종목이 목록에 없습니다~!")


    def render_mpl_table(self, data, col_width=3.0, row_height=0.625, font_size=14,
                         header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                         bbox=[0, 0, 1, 1], header_columns=0,
                         ax=None, **kwargs):
        if ax is None:
            size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
            fig, ax = plt.subplots(figsize=size)
            ax.axis('off')

        mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

        mpl_table.auto_set_font_size(False)
        mpl_table.set_fontsize(font_size)

        for k, cell in six.iteritems(mpl_table._cells):
            cell.set_edgecolor(edge_color)
            if k[0] == 0 or k[1] < header_columns:
                cell.set_text_props(weight='bold', color='w')
                cell.set_facecolor(header_color)
            else:
                cell.set_facecolor(row_colors[k[0] % len(row_colors)])
        file = "test.png"
        time.sleep(8)
        plt.savefig(file)
        plt.cla()
        return file

    def run(self):
        while True:
            #self.logging.logger.debug("data acquiring")
            time.sleep(0.5)
            if not self.kw_get_que.empty():
                data = self.kw_get_que.get()
                self.logging.logger.debug("get data type :%s" % data[0])
                # 기본적 매수 조건들
                self.Send_Bot_Msg(data)


if __name__ == "__main__":
    test = TeleBot()


