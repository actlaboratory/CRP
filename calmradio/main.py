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

    def _getLocale(self):
        # "ja-JP" -> "ja"
        return self.config.getstring("general", "language", "ja-JP").split("-")[0]

    def getAllChannels(self):
        """ジャンル、カテゴリー、チャンネルの一覧を取得する

        Returns:
            dict: {Genre: {Category: [Channel, ...]}}。接続エラー時はerrorCodes.CONNECTION_ERROR
        """
        locale = self._getLocale()
        metadata = self.api.getMetadata(locale)
        if metadata == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        channels = self.api.getChannels(locale)
        if channels == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        sort = self.config.getboolean("view", "sort", False)
        categories = {i["id"]: i for i in metadata["metadata"]["categories"]}
        channels = {i["id"]: Channel(i) for i in channels["channels"]}
        # 「Most Popular Channels」などの特集はジャンル以外のkindなので除外する
        genres = [i for i in metadata["metadata"]["rows"] if i["kind"] == "genre"]
        genres = sorted(genres, key=lambda x: x["position"])
        ret = {}
        for genre in genres:
            categoryDict = {}
            for categoryId in genre["categories"]:
                if categoryId not in categories:
                    continue
                category = categories[categoryId]
                lst = [channels[i] for i in category["channels"] if i in channels]
                if not lst:
                    continue
                if sort:
                    lst = sorted(lst, key=lambda x: x.getName().lower())
                categoryDict[Category(category)] = lst
            if not categoryDict:
                continue
            if sort:
                categoryDict = dict(sorted(categoryDict.items(), key=lambda x: x[0].getName().lower()))
            ret[Genre(genre)] = categoryDict
        return ret

class Genre:
    def __init__(self, data):
        self._data = data

    def getId(self):
        return self._data["id"]

    def getName(self):
        return self._data["title"].strip()

class Category:
    def __init__(self, data):
        self._data = data

    def getId(self):
        return self._data["id"]

    def getName(self):
        return self._data["title"].strip()

class Channel:
    def __init__(self, data):
        self._data = data

    def getName(self):
        return self._data["title"].strip()

    def _getVipStream(self):
        return self._data["vip"][0]

    def _getFreeStream(self):
        if not self._data["free"]:
            return None
        return self._data["free"][0]

    def getDescription(self):
        return self._data["description"]

    def getRecentTracks(self):
        ret = {"vip": self._getVipStream()["recent_tracks"]}
        free = self._getFreeStream()
        if free:
            ret["free"] = free["recent_tracks"]
        return ret

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
        
        result = calmradio.auth()
        if result == errorCodes.CONNECTION_ERROR:
            return None, None, errorCodes.CONNECTION_ERROR
        if result == errorCodes.LOGIN_FAILED:
            return None, None, errorCodes.LOGIN_FAILED
        
        if calmradio.isActive():
            # premium
            bitrate = config.getstring("play", "bitrate", "320", constants.AVAILABLE_BITRATE)
            url = self._getVipStream()["streams"][bitrate]
            recentKey = "vip"
        else:
            free = self._getFreeStream()
            if not free:
                return None, None, errorCodes.NOT_SUPPORTED
            url = free["streams"]["128"]
            recentKey = "free"
        
        if calmradio.getUser():
            url = url.replace("https://", "https://%s:%s@" % (urllib.parse.quote(calmradio.getUser()), urllib.parse.quote(calmradio.getToken())))
        
        return url, recentKey, None
