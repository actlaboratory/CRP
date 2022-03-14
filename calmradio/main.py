# main module of Calmradio

from re import I
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
        metadata = self.api.getMetadata()
        if metadata == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        try:
            categories = metadata["metadata"]["categories"]
        except Exception as e:
            self.log.error(e)
            return ret
        for i in categories:
            ret.append(Category(i))
        return ret

    def getAllChannels(self):
        ret = {}
        channels = self.api.getChannels()
        if channels == errorCodes.CONNECTION_ERROR:
            return errorCodes.CONNECTION_ERROR
        try:
            channels = channels["channels"]
        except Exception as e:
            self.log.error(e)
            return ret
        channels = [Channel(i) for i in channels]
        for category in self.getCategories():
            ret[category] = [channel for channel in channels if channel.getId() in category.getChannels()]
        return ret

class Category:
    def __init__(self, data):
        self._data = data

    def getId(self):
        return self._data["id"]

    def getName(self):
        return self._data["title"]

    def getChannels(self):
        return self._data["channels"]

class Channel:
    def __init__(self, data):
        self._data = data

    def getName(self):
        return self._data["title"]

    def getStreams(self):
        return self._data["streams"]

    def getDescription(self):
        return self._data["description"]

    def getRecentTracks(self):
        return self._data["recent_tracks"]

    def getCategory(self):
        return self._data["category"]

    def getId(self):
        return self._data["id"]
