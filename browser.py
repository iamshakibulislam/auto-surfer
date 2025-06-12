import sys
import random
import time
from PyQt5 import QtNetwork
from PyQt5.QtWebEngineCore import QWebEngineHttpRequest
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QSpinBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer, QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

class NWUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):

    def __init__(self, headers):
        super().__init__()
        self.headers = headers

    def set_headers(self, headers):
        self.headers = headers

    def interceptRequest(self, info):
        info.setHttpHeader(b'Referer', str(self.headers).encode('ASCII'))

class BrowserWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt5 Auto-Reload Browser')
        self.resize(1100, 700)
        # Main vertical layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header
        header = QLabel('PyQt5 Auto-Reload Browser')
        header.setStyleSheet('font-size: 28px; font-weight: bold; color: #fff; padding: 18px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a7bd5, stop:1 #00d2ff); border-radius: 12px; margin-bottom: 18px;')
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(18)
        controls_row.setContentsMargins(10, 10, 10, 10)

        # URL
        url_col = QVBoxLayout()
        url_label = QLabel('URL:')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Enter URL')
        url_col.addWidget(url_label)
        url_col.addWidget(self.url_input)
        controls_row.addLayout(url_col)

        # Duration
        dur_col = QVBoxLayout()
        dur_label = QLabel('Duration (s):')
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 9999)
        self.duration_input.setValue(50)
        dur_col.addWidget(dur_label)
        dur_col.addWidget(self.duration_input)
        controls_row.addLayout(dur_col)

        # Visits
        visit_col = QVBoxLayout()
        visit_label = QLabel('Visits:')
        self.visit_input = QSpinBox()
        self.visit_input.setRange(1, 9999)
        self.visit_input.setValue(5)
        visit_col.addWidget(visit_label)
        visit_col.addWidget(self.visit_input)
        controls_row.addLayout(visit_col)

        # User agent section
        ua_col = QVBoxLayout()
        ua_label = QLabel('User Agents:')
        self.user_agent_input = QTextEdit()
        self.user_agent_input.setPlaceholderText('Enter user agents, one per line')
        self.user_agent_input.setFixedHeight(50)
        self.user_agent_input.setFixedWidth(220)
        self.load_ua_btn = QPushButton('Load User Agents from File')
        ua_col.addWidget(ua_label)
        ua_col.addWidget(self.user_agent_input)
        ua_col.addWidget(self.load_ua_btn)
        controls_row.addLayout(ua_col)

        # Proxy section
        proxy_col = QVBoxLayout()
        proxy_label = QLabel('Proxies:')
        self.proxy_display = QTextEdit()
        self.proxy_display.setPlaceholderText('No proxies loaded')
        self.proxy_display.setReadOnly(True)
        self.proxy_display.setFixedHeight(50)
        self.proxy_display.setFixedWidth(220)
        self.load_proxy_btn = QPushButton('Load Proxies from File')
        proxy_col.addWidget(proxy_label)
        proxy_col.addWidget(self.proxy_display)
        proxy_col.addWidget(self.load_proxy_btn)
        controls_row.addLayout(proxy_col)

        # Start/Stop buttons
        btn_col = QVBoxLayout()
        self.start_btn = QPushButton('Start')
        self.stop_btn = QPushButton('Stop')
        self.stop_btn.setEnabled(False)
        btn_col.addWidget(self.start_btn)
        btn_col.addWidget(self.stop_btn)
        btn_col.addStretch()
        controls_row.addLayout(btn_col)

        main_layout.addLayout(controls_row)

        # Browser view
        self.browser = QWebEngineView()
        self.browser.setStyleSheet('border-radius: 10px; background: #f7fafd;')
        main_layout.addWidget(self.browser, stretch=1)

        # Timer and state
        self.timer = QTimer()
        self.timer.timeout.connect(self.reload_browser)
        self.current_visit = 0
        self.max_visits = 0
        self.user_agents = []
        self.proxies = []

        # Connections
        self.start_btn.clicked.connect(self.start_visits)
        self.stop_btn.clicked.connect(self.stop_visits)
        self.load_ua_btn.clicked.connect(self.load_user_agents_from_file)
        self.load_proxy_btn.clicked.connect(self.load_proxies_from_file)

        # Apply a modern stylesheet
        self.setStyleSheet('''
            QWidget {
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 16px;
            }
            QLineEdit, QTextEdit, QSpinBox {
                background: #f7fafd;
                border: 1.5px solid #b2becd;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QLabel {
                color: #2d3a4a;
                font-weight: 500;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a7bd5, stop:1 #00d2ff);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 22px;
                font-weight: bold;
                font-size: 16px;
                margin: 4px;
            }
            QPushButton:disabled {
                background: #b2becd;
                color: #f7fafd;
            }
            QSpinBox {
                min-width: 70px;
            }
            QTextEdit[readOnly="true"] {
                background: #e0eafc;
                color: #3a7bd5;
            }
        ''')

    def start_visits(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.max_visits = self.visit_input.value()
        self.current_visit = 0
        self.user_agents = [ua.strip() for ua in self.user_agent_input.toPlainText().splitlines() if ua.strip()]
        if not self.user_agents:
            self.user_agents = [self.default_user_agent()]
        self.duration = self.duration_input.value() * 1000  # ms
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # Pick one proxy for the session (auto-detect protocol)
        self.session_proxy = None
        if self.proxies:
            self.session_proxy = random.choice(self.proxies)
            import re
            proxy_re = re.compile(r'^(socks5|http|https)://([^:@]+):(\d+)$', re.IGNORECASE)
            m = proxy_re.match(self.session_proxy)
            print("proxy found and set")
            if m:
                scheme = m.group(1).lower()
                host = m.group(2)
                port = m.group(3)
                import os
                os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = f'--proxy-server={scheme}://{host}:{port}'
                
                proxy = QtNetwork.QNetworkProxy()
                proxy.setType(QtNetwork.QNetworkProxy.Socks5Proxy)
                proxy.setHostName(host)
                proxy.setPort(int(port))
                QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

                
            else:
                import os
                os.environ.pop('QTWEBENGINE_CHROMIUM_FLAGS', None)
                QMessageBox.warning(self, 'Proxy Error', 'Selected proxy is not a valid format. Please load a valid proxy (protocol://host:port).')
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                return
        else:
            import os
            print("no proxy added")
            os.environ.pop('QTWEBENGINE_CHROMIUM_FLAGS', None)
            QMessageBox.warning(self, 'No Proxy', 'No proxy loaded. Please load a proxy file with at least one valid proxy before starting.')
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return
        self.reload_browser(first=True)

    def stop_visits(self):
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    
    def reload_browser(self, first=False):
        if not first:
            self.current_visit += 1
        if self.current_visit >= self.max_visits:
            self.stop_visits()
            return

        url = self.url_input.text().strip()
        if not url:
            return

        # Pick a random user-agent and referer
        user_agent = random.choice(self.user_agents)
        referer = random.choice([
            "https://l.facebook.com/",
            "https://lm.facebook.com/"
        ])

        # Create a new QWebEngineView (or reuse self.browser)
        #self.browser = QWebEngineView()

        # Set custom user-agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent(user_agent)

        # Set up your working interceptor class with referer header
        self.request_interceptor = NWUrlRequestInterceptor(referer)
        profile.setUrlRequestInterceptor(self.request_interceptor)

        # Optional: clear cookies if needed
        cookie_store = profile.cookieStore()
        cookie_store.deleteAllCookies()

        # Attach a new page with profile to the browser
        page = QWebEnginePage(profile, self.browser)
        self.browser.setPage(page)

        # Load the URL
        QTimer.singleShot(300, lambda: self.browser.load(QUrl(url)))
        #self.browser.load(QUrl(url))

        # Start the timer for reload
        self.timer.start(self.duration)


 



    def default_user_agent(self):
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    def load_user_agents_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open User Agent File', '', 'Text Files (*.txt)')
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    user_agents = f.read().strip().splitlines()
                self.user_agent_input.setPlainText('\n'.join(user_agents))
            except Exception as e:
                self.user_agent_input.setPlainText(f'Error loading file: {e}')

    def load_proxies_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open Proxy File', '', 'Text Files (*.txt)')
        if file_path:
            try:
                import re
                proxy_re = re.compile(r'^(socks5|http|https)://([^:@]+):(\d+)$', re.IGNORECASE)
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.proxies = [line.strip() for line in f if line.strip() and proxy_re.match(line.strip())]
                display_lines = self.proxies[:3]
                if len(self.proxies) > 3:
                    display_lines.append('...')
                self.proxy_display.setPlainText('\n'.join(display_lines))
                if not self.proxies:
                    self.proxy_display.append('\nNo valid proxies found! (protocol://host:port)')
            except Exception as e:
                self.proxy_display.setPlainText(f'Error loading file: {e}')


def main():
    app = QApplication(sys.argv)
    w = BrowserWidget()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
