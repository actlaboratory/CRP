# calmradio player

import re
import time
from soundPlayer import player
from soundPlayer.constants import *
import globalVars
from ConfigManager import ConfigManager
import logging
import constants

# BASSが返す、既定の出力先に追従する仮想デバイスの名前
BASS_DEFAULT_DEVICE_NAME = "Default"


class Player:
	def __init__(self):
		self._player = player.player()
		self.config: ConfigManager = globalVars.app.config
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "player"))
		self.setDevice(self.config["play"]["device"])
		self._url = ""

	def exit(self):
		self._player.exit()

	def setPlaybackUrl(self, url):
		# URLに埋め込まれたユーザー名とトークンはログに残さない
		self.log.debug("playback URL: %s" % re.sub(r"//[^/@]*@", "//***:***@", url))
		self._url = url
		return self._player.setSource(url)

	def getPlaybackUrl(self):
		return self._url

	def play(self):
		return self._player.play()

	def stop(self):
		return self._player.stop()

	def setVolume(self, value, save=True):
		result = self._player.setVolume(value)
		if result and save:
			self.config["play"]["volume"] = value
		return result

	def getVolume(self):
		return self._player.getConfig(PLAYER_CONFIG_VOLUME)

	def getDeviceList(self):
		result = self._player.getDeviceList()
		del result[result.index("No sound")]
		# BASS 2.4.16以降の「Default」は既定の出力先に追従する仮想デバイス。
		# 「既定のデバイス」と同じものなので、一覧には出さない
		if BASS_DEFAULT_DEVICE_NAME in result:
			del result[result.index(BASS_DEFAULT_DEVICE_NAME)]
		result.insert(0, _("既定のデバイス"))
		self.log.debug("available devices: %s" % result)
		return result

	def setDevice(self, name=""):
		if name == BASS_DEFAULT_DEVICE_NAME:
			# 以前のバージョンで「Default」を選んで保存した設定は、既定のデバイスとして扱う
			name = ""
		if name:
			self.log.debug("changing device to %s" % name)
			result = self._player.setDeviceByName(name)
			if not result:
				# デバイスが見つからなかった
				self.log.debug("device %s could not be found" % name)
				result = self._player.setDevice(PLAYER_DEFAULT_SPEAKER)
				name = ""
		else:
			self.log.debug("set to default device")
			result = self._player.setDevice(PLAYER_DEFAULT_SPEAKER)
		if result:
			self.config["play"]["device"] = name

	def getPlayer(self):
		return self._player

	def reload(self):
		self.log.debug("reloading...")
		count = 0
		while True:
			self.setPlaybackUrl(self._url)
			self.play()
			time.sleep(5)
			count += 1
			self.log.debug("retried %d times" % count)
			if self._player.getStatus() in (PLAYER_STATUS_PLAYING, PLAYER_STATUS_LOADING):
				self.log.debug("Playback has been successfully started")
				break
			if count > 5:
				self.log.debug("Failed to start playback")
				break
