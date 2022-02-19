# calmradio player

from soundPlayer import player
from soundPlayer.constants import *


class Player:
	def __init__(self):
		self._player = player.player()

	def exit(self):
		self._player.exit()

	def setPlaybackUrl(self, url):
		return self._player.setSource(url)

	def play(self):
		return self._player.play()

	def stop(self):
		return self._player.stop()

	def setVolume(self, value):
		return self._player.setVolume(value)

	def getVolume(self):
		return self._player.getConfig(PLAYER_CONFIG_VOLUME)
