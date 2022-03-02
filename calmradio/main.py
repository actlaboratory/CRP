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
        if "error" in data:
            self.log.debug("API returned error.")
            self._user = ""
            self._isActive = False
            self._token = ""
            return
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
        return [Category(i) for i in ret]

    def getAllChannels(self):
        ret = {}
        channels = self.api.getChannels()
        if channels == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        for category in self.getCategories():
            for group in channels:
                if group["category"] == category.getId():
                    ret[category] = [Channel(i) for i in group["channels"]]
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
