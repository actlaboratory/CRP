# calmradio api wrapper

import requests


class Api:
    def _getJson(self, url, *args, **kwargs):
        response = requests.get(url, *args, **kwargs)
        return response.json()

    def getCategories(self):
        return self._getJson("http://api.calmradio.com/categories.json")

    def getChannels(self):
        return self._getJson("http://api.calmradio.com/channels.json")
