# playback status checker

import constants
import globalVars
import logging
import player
from soundPlayer.constants import *
import threading
import time
import wx


interval = 1
deviceErrorMax = 10
deviceErrorCount = 0


class PlaybackStatusChecker(threading.Thread):
    def __init__(self, player, onStop):
        super().__init__(daemon=True)
        self._player = player
        self.onStop = onStop
        self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "playStatusChecker"))

    def run(self):
        self.log.debug("started")
        while True:
            status = self._player.getPlayer().getStatus()
            self.log.debug("status: %s" % status)
            if status == PLAYER_STATUS_DEVICEERROR:
                global deviceErrorCount
                deviceErrorCount += 1
                self.log.debug("deviceErrorCount: %s" % deviceErrorCount)
                if deviceErrorCount < deviceErrorMax:
                    time.sleep(interval)
                    continue
                deviceErrorCount = 0
            if status == PLAYER_STATUS_PAUSED:
                self._player.getPlayer().play()
            if status not in (PLAYER_STATUS_PLAYING, PLAYER_STATUS_LOADING):
                self.log.debug("stopping")
                wx.CallAfter(self.onStop)
                break
            time.sleep(interval)
        self.log.debug("exitting...")
