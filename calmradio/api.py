# calmradio api wrapper

import constants
import errorCodes
import logging
import requests
import traceback


class Api:
    def __init__(self):
        self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "calmradio.api"))

    def _getJson(self, url, *args, **kwargs):
        self.log.debug("Connecting to %s" % url)
        try:
            response = requests.get(url, *args, **kwargs)
            self.log.debug("code: %s, url: %s" % (response.status_code, response.url))
        except Exception as e:
            self.log.error("Connection error:\n" + traceback.format_exc())
            return errorCodes.CONNECTION_ERROR
        try:
            ret = response.json()
            self.log.debug("response: %s" % ret)
            return ret
        except Exception as e:
            self.log.error("Failed to get json data from URL %s. Response: %s" % (url, response.text))
            return errorCodes.CONNECTION_ERROR

    def getCategories(self):
        return self._getJson("https://api.calmradio.com/categories.json")

    def getChannels(self):
        return self._getJson("https://api.calmradio.com/channels.json")

    def getToken(self, user, pass_):
        params = {
            "user": user,
            "pass": pass_,
        }
        return self._getJson("https://api.calmradio.com/get_token", params)
