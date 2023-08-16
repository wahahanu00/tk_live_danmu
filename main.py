import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow
from qt_material import apply_stylesheet
from UI import BT, LineText, Log, Message
import time
from driver import driver1
from websocket_ import WebSocket


def gettime():
    t = time.localtime()

    time_ = '【' + str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec) + '】'

    return time_


class UI_(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pool = ThreadPoolExecutor(max_workers=100)
        self.url_list = []
        self.ws_list = []
        self.initui()
        self.init_text()
        self.btclick()
        self.def_init()
        self.show()

    def initui(self):
        self.setFixedSize(480, 700)
        self.setWindowTitle('秋恋猫dy弹幕')
        self.setWindowIcon(QIcon("setting/app.ico"))

        self.lb_key = BT(self)
        self.lb_key.init_ui('密钥', 50, 28)

        self.line_key = LineText(self)

        self.line_key.init_ui(159, 28)

        self.lb_url = BT(self)
        self.lb_url.init_ui('直播地址', 50, 71)

        self.line_url = LineText(self)
        self.line_url.init_ui(159, 71)

        self.bt_save_setting = BT(self)
        self.bt_save_setting.init_ui('操作:', 50, 114)

        self.bt_begin_ws = BT(self)
        self.bt_begin_ws.init_ui('开启监控', 196, 114)

        self.bt_close_ws = BT(self)
        self.bt_close_ws.init_ui('关闭监控', 342, 114)

        self.lb_ws_url = BT(self)
        self.lb_ws_url.init_ui('ws地址', 50, 157)

        self.line_ws_url = LineText(self)
        self.line_ws_url.init_ui(159, 157)

        self.lb_ws_port = BT(self)
        self.lb_ws_port.init_ui('ws端口', 50, 200)

        self.line_ws_port = LineText(self)
        self.line_ws_port.init_ui(159, 200)

        self.text_message = Message(self)
        self.text_message.init_ui()

        self.text_log = Log(self)
        self.text_log.init_ui()

    def init_text(self):
        with open('setting/init.txt', 'r', encoding='utf-8') as f:
            res = f.readlines()
            f.close()
            print(res)
            if len(res) == 4:
                self.line_key.setText(res[0].replace('\n', ''))
                self.line_url.setText(res[1].replace('\n', ''))
                self.line_ws_url.setText(res[2].replace('\n', ''))
                self.line_ws_port.setText(res[3].replace('\n', ''))

    def def_init(self):
        self.deriver = driver1()
        self.deriver.log1.connect(self.log)
        self.deriver.data1.connect(self.Message)
        self.websocket = WebSocket()
        self.websocket.ws_single.connect(self.log)

    def log(self, message):
        self.text_log.append(gettime() + message)

    def Message(self, message):
        if len(self.text_message.toPlainText()) > 10000:
            self.text_message.clear()
        nickname = message['nickname']
        content = message['content1']
        res = '{0:}【{1:}】:{2:}'.format(gettime(), nickname, content)
        print(json.dumps(message, ensure_ascii=True))
        self.pool.submit(self.websocket.append_message, str(message))
        self.text_message.append(res)

    def save_setting(self):
        key = self.line_key.text() + '\n'
        url = self.line_url.text() + '\n'
        ws_url = self.line_ws_url.text() + '\n'
        ws_port = self.line_ws_port.text() + '\n'
        with open('setting/init.txt', 'w', encoding='utf-8') as f:
            f.write(key + url + ws_url + ws_port)
            self.text_log.append(
                '---' + gettime() + '保存配置---\n' + '密钥：' + key + '直播地址：' + url + 'ws地址：' + ws_url + 'ws端口' + ws_port + '---' + gettime() + '保存成功---')
            f.close()

    def btclick(self):
        self.line_ws_url.textChanged.connect(self.save_setting)
        self.line_url.textChanged.connect(self.save_setting)
        self.line_ws_port.textChanged.connect(self.save_setting)

        def begin_ws():
            if len(self.line_url.text()) > 3 and len(self.url_list) == 0 and round(time.time()*1000)<1674870176000:

                self.text_log.append(gettime() + '开始监控直播间')
                self.url_list.append(self.line_url.text())
                b = threading.Thread(target=self.deriver.browser_launch, args=(self.line_url.text(),))
                b.daemon = True
                b.start()

                if len(self.ws_list) == 0:
                    self.ws_list.append('ws')
                    self.websocket.init_ws(self.line_ws_url.text(), self.line_ws_port.text())
                    a = threading.Thread(target=self.websocket.start_ws, args=())
                    a.daemon = True
                    a.start()
            else:
                self.text_log.append(gettime() + '请输入地址，或者程序已经开始')
        self.bt_begin_ws.clicked.connect(begin_ws)

        def close_ws():
            if len(self.url_list) > 0:
                self.url_list = []
                self.pool.submit(self.deriver.browser_close)
                self.websocket.close_loop()
            else:
                self.text_log.append(gettime() + '请先开始监控直播间')
        self.bt_close_ws.clicked.connect(close_ws)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    a = UI_()
    sys.exit(app.exec_())
