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

    def _getJson(self, url, *args, sensitive=False, **kwargs):
        """URLからJSONを取得する

        Args:
            sensitive: Trueの場合、パスワードやトークンをログに残さないよう、
                クエリー文字列、レスポンスの値、例外の詳細を記録しない
        """
        self.log.debug("Connecting to %s" % url)
        try:
            response = requests.get(url, *args, **kwargs)
            self.log.debug("code: %s, url: %s" % (response.status_code, url if sensitive else response.url))
        except Exception as e:
            if sensitive:
                # 例外のメッセージには、クエリー文字列を含むURLが入ることがある
                self.log.error("Connection error: %s" % type(e).__name__)
            else:
                self.log.error("Connection error:\n" + traceback.format_exc())
            return errorCodes.CONNECTION_ERROR
        try:
            ret = response.json()
            if sensitive:
                self.log.debug("response keys: %s" % (list(ret.keys()) if isinstance(ret, dict) else type(ret).__name__))
            else:
                self.log.debug("response:\n%s\n" % json.dumps(ret, ensure_ascii=False, indent="\t"))
            return ret
        except Exception as e:
            self.log.error("Failed to get json data from URL %s. Response: %s" % (url, "(omitted)" if sensitive else response.text))
            return errorCodes.CONNECTION_ERROR

    def getMetadata(self, locale):
        return self._getJson("https://api.calmradio.com/v2/metadata.json", {"locale": locale})

    def getChannels(self, locale):
        return self._getJson("https://api.calmradio.com/v2/channels.json", {"locale": locale})

    def getToken(self, user, pass_):
        params = {
            "user": user,
            "pass": pass_,
        }
        return self._getJson("https://api.calmradio.com/get_token", params, sensitive=True)
