# main module of Calmradio

from calmradio.api import Api
from ConfigManager import ConfigManager
import constants
import errorCodes
import globalVars
import logging


class Calmradio:
    def __init__(self):
        self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "calmradio.main"))
        self.api = Api()
        self.config: ConfigManager = globalVars.app.config
        self._user = ""
        self._isActive = False
        self._token = ""

    def auth(self):
        self.log.debug("Authorization started.")
        user = self.config["user"]["user"]
        pass_ = self.config["user"]["pass"]
        if not user or not pass_:
            # not configured
            self.log.debug("Username or password is not configured.")
            self._user = ""
            self._isActive = False
            self._token = ""
            return
        data = self.api.getToken(user, pass_)
        if data == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        if "error" in data:
            self.log.debug("API returned error.")
            self._user = ""
            self._isActive = False
            self._token = ""
            return errorCodes.LOGIN_FAILED
        self._user = user
        self._isActive = data["membership"] == "active"
        self._token = data["token"]
        self.log.debug("user: %s, isActive: %s, token: %s" % (self._user, self._isActive, self._token))

    def isActive(self):
        return self._isActive

    def getToken(self):
        return self._token

    def getUser(self):
        return self._user

    def getCategories(self):
        ret = []
        categories = self.api.getCategories()
        if categories == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        for section in categories:
            ret += section["categories"]
        ret = [Category(i) for i in ret]
        if globalVars.app.config.getboolean("view", "sort", False):
            ret = sorted(ret, key=lambda x: x.getName().lower())
        return ret

    def getAllChannels(self):
        ret = {}
        channels = self.api.getChannels()
        if channels == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        for category in self.getCategories():
            for group in channels:
                if group["category"] == category.getId():
                    lst = [Channel(i) for i in group["channels"]]
                    if globalVars.app.config.getboolean("view", "sort", False):
                        lst = sorted(lst, key=lambda x: x.getName().lower())
                    ret[category] = lst
        return ret

class Category:
    def __init__(self, data):
        self._data = data

    def getId(self):
        return self._data["id"]

    def getName(self):
        return self._data["name"]

class Channel:
    def __init__(self, data):
        self._data = data

    def getName(self):
        return self._data["title"].replace("CALMRADIO - ", "")

    def getStreams(self):
        return self._data["streams"]

    def getDescription(self):
        return self._data["description"]

    def getRecentTracks(self):
        return self._data["recent_tracks"]

    def generatePlaybackUrl(self, calmradio, config):
        """再生URLを生成する
        
        Args:
            calmradio: Calmradioオブジェクト（認証情報を取得するため）
            config: ConfigManagerオブジェクト（設定を取得するため）
        
        Returns:
            tuple: (url, recentKey, errorCode)
            - url: 生成されたURL（エラー時はNone）
            - recentKey: "vip"または"free"（エラー時はNone）
            - errorCode: エラーコード（成功時はNone）
        """
        import urllib.parse
        
        streams = self.getStreams()
        result = calmradio.auth()
        if result == errorCodes.CONNECTION_ERROR:
            return None, None, errorCodes.CONNECTION_ERROR
        if result == errorCodes.LOGIN_FAILED:
            return None, None, errorCodes.LOGIN_FAILED
        
        if calmradio.isActive():
            # premium
            bitrate = config.getstring("play", "bitrate", "320", constants.AVAILABLE_BITRATE)
            url = streams[bitrate]
            recentKey = "vip"
        else:
            if "free_128" not in streams:
                return None, None, errorCodes.NOT_SUPPORTED
            url = streams["free_128"]
            recentKey = "free"
        
        if calmradio.getUser():
            url = url.replace("https://", "https://%s:%s@" % (urllib.parse.quote(calmradio.getUser()), urllib.parse.quote(calmradio.getToken())))
        
        return url, recentKey, None
