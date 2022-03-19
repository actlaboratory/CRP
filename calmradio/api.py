# calmradio api wrapper

import constants
import errorCodes
import json
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
            self.log.debug("response:\n%s\n" % json.dumps(ret, ensure_ascii=False, indent="\t"))
            return ret
        except Exception as e:
            self.log.error("Failed to get json data from URL %s. Response: %s" % (url, response.text))
            return errorCodes.CONNECTION_ERROR

    def getMetadata(self, locale):
        if locale:
            return self._getJson("https://api.calmradio.com/v2/metadata.json?locale=%s" % locale)
        else:
            return self._getJson("https://api.calmradio.com/v2/metadata.json")

    def getChannels(self, locale):
        if locale:
            return self._getJson("https://api.calmradio.com/v2/channels.json?locale=%s" % locale)
        else:
            return self._getJson("https://api.calmradio.com/v2/channels.json")

    def getToken(self, user, pass_):
        params = {
            "user": user,
            "pass": pass_,
        }
        return self._getJson("https://api.calmradio.com/get_token", params)
