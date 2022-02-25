# main module of Calmradio

from calmradio.api import Api

class Calmradio:
    def __init__(self):
        self.api = Api()

    def getCategories(self):
        ret = []
        categories = self.api.getCategories()
        for section in categories:
            ret += section["categories"]
        return [Category(i) for i in ret]

    def getAllChannels(self):
        ret = {}
        channels = self.api.getChannels()
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
