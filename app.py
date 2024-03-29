﻿# -*- coding: utf-8 -*-
# Application Main

import os
import AppBase
import update
import globalVars
import proxyUtil
from calmradio.main import Calmradio
from player import Player
import soundPlayer.player


class Main(AppBase.MainBase):
	def __init__(self):
		super().__init__()

	def initialize(self):
		self.setGlobalVars()
		# プロキシの設定を適用
		self.proxyEnviron = proxyUtil.virtualProxyEnviron()
		self.setProxyEnviron()
		# アップデートを実行
		if self.config.getboolean("general", "update"):
			globalVars.update.update(True)
		# メインビューを表示
		from views import main
		self.calmradio = Calmradio()
		self.player = Player()
		self.hMainView = main.MainView()
		self.hMainView.refreshChannels()
		self.hMainView.Show()
		return True

	def setProxyEnviron(self):
		if self.config.getboolean("proxy", "usemanualsetting", False) == True:
			self.proxyEnviron.set_environ(self.config["proxy"]["server"], self.config.getint("proxy", "port", 8080, 0, 65535))
		else:
			self.proxyEnviron.set_environ()
		if "http_proxy" in os.environ:
			soundPlayer.player.setProxy(os.environ["http_proxy"])

	def setGlobalVars(self):
		globalVars.update = update.update()
		return

	def OnExit(self):
		# 設定の保存やリソースの開放など、終了前に行いたい処理があれば記述できる
		# ビューへのアクセスや終了の抑制はできないので注意。

		# アップデート
		globalVars.update.runUpdate()

		# 戻り値は無視される
		return 0
