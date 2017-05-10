from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtNetwork import QNetworkRequest
 
class Client(QWebPage):
 
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebPage.__init__(self)
         
        self.loadFinished.connect(self.on_page_load)
         
        self.load
         
        self.mainFrame().load(QUrl(url))
                    
        self.app.exec_()
         
    def on_page_load(self):
        print("page loaded")
        self.app.quit()
         
    def userAgentForUrl(self, *args, **kwargs):
        print("custom user agent")
        return user_agent