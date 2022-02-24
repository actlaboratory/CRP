# calmradio player

from soundPlayer import player
from soundPlayer.constants import *
import globalVars
from ConfigManager import ConfigManager
import logging
import constants


class Player:
	def __init__(self):
		self._player = player.player()
		self.config: ConfigManager = globalVars.app.config
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "player"))
		self.setDevice(self.config["play"]["device"])

	def exit(self):
		self._player.exit()

	def setPlaybackUrl(self, url):
		self.log.debug("playback URL: %s" % url)
		return self._player.setSource(url)

	def play(self):
		return self._player.play()

	def stop(self):
		return self._player.stop()

	def setVolume(self, value):
		result = self._player.setVolume(value)
		if result:
			self.config["play"]["volume"] = value
		return result

	def getVolume(self):
		return self._player.getConfig(PLAYER_CONFIG_VOLUME)

	def getDeviceList(self):
		result = self._player.getDeviceList()
		del result[result.index("No sound")]
		result.insert(0, _("規定のデバイス"))
		self.log.debug("available devices: %s" % result)
		return result

	def setDevice(self, name=""):
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
