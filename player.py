# calmradio player

from soundPlayer import player
from soundPlayer.constants import *
import globalVars
from ConfigManager import ConfigManager


class Player:
	def __init__(self):
		self._player = player.player()
		self.config: ConfigManager = globalVars.app.config

	def exit(self):
		self._player.exit()

	def setPlaybackUrl(self, url):
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
