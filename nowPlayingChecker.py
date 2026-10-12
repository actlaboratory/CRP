# now playing checker

import constants
import globalVars
import logging
import requests
import time
import threading
import traceback
import wx


interval = 15


class NowPlayingChecker(threading.Thread):
    def __init__(self, url, onChange, onExit):
        super().__init__(daemon=True)
        self.url = url
        self.onChange = onChange
        self.onExit = onExit
        self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "nowPlayingChecker"))
        self.log.debug("Nowplaying checker created. URL: %s" % self.url)
        self.running = False
        self.oldData = {}
        self.timeout = globalVars.app.config.getint("general", "timeout", 3)

    def run(self):
        self.running = True
        while self.running:
            self.log.debug("Getting data...")
            # 失敗した場合も、次の取得まではintervalだけ待つ
            try:
                req = requests.get(self.url, timeout=self.timeout)
                if req.status_code != 200:
                    self.log.error("Failed to get data: %s" % req.text)
                else:
                    data = req.json()
                    data = data["now_playing"]
                    if data != self.oldData:
                        self.log.debug("New data")
                        wx.CallAfter(self.onChange, data)
                        self.oldData = data
            except Exception as e:
                self.log.error(traceback.format_exc())
            time.sleep(interval)

    def exit(self):
        self.log.debug("exitting...")
        self.running = False
        wx.CallAfter(self.onExit)
