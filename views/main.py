# -*- coding: utf-8 -*-
# main view
# Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
# Copyright (C) 2019-2021 yamahubuki <itiro.ishino@gmail.com>

import wx

import constants
import globalVars
import menuItemsStore
import update

from .base import *
from simpleDialog import *

from views import globalKeyConfig
from views import settingsDialog
from views import refresh
from views import versionDialog
import calmradio.main
from nowPlayingChecker import NowPlayingChecker
from playbackStatusChecker import PlaybackStatusChecker


class MainView(BaseView):
	def __init__(self):
		super().__init__("mainView")
		self.log.debug("created")
		self.events = Events(self, self.identifier)
		title = constants.APP_NAME
		super().Initialize(
			title,
			self.app.config.getint(self.identifier, "sizeX", 800, 400),
			self.app.config.getint(self.identifier, "sizeY", 600, 300),
			self.app.config.getint(self.identifier, "positionX", 50, 0),
			self.app.config.getint(self.identifier, "positionY", 50, 0)
		)
		self.InstallMenuEvent(Menu(self.identifier), self.events.OnMenuSelect)
		self.InstallControls()

	def InstallControls(self):
		# channels
		self.tree, tmp = self.creator.treeCtrl(_("チャンネル一覧(&C)"))
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.events.onChannelActivated)
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.events.onChannelSelected)
		self.description, tmp = self.creator.inputbox(_("説明"), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_PROCESS_ENTER)
		self.description.Disable()
		self.description.Bind(wx.EVT_TEXT_ENTER, self.events.onChannelActivated)
		# playback controls
		self.playButton = self.creator.button(_("選択中のチャンネルを再生"), self.events.onChannelActivated)
		self.playButton.Disable()
		self.menu.EnableMenu("PLAY_PLAY", False)
		self.stopButton = self.creator.button(_("停止(&S)"), self.events.onStopButton)
		self.stopButton.Disable()
		self.menu.EnableMenu("PLAY_STOP", False)
		self.volume, tmp = self.creator.slider(_("音量(&V)"), event=self.events.onVolumeChanged, style=wx.SL_VERTICAL, defaultValue=self.app.config.getint("play", "volume", 100, 0, 100))
		self.deviceButton = self.creator.button(_("再生デバイスの変更(&D)"), self.events.onDeviceButtonPressed)
		# now playing
		self.nowPlaying, tmp = self.creator.listCtrl(_("現在再生中(&N)"))
		self.nowPlaying.AppendColumn(_("項目"))
		self.nowPlaying.AppendColumn(_("内容"))
		self.nowPlaying.Append([_("タイトル"), ""])
		self.nowPlaying.Append([_("アーティスト"), ""])
		self.nowPlaying.Append([_("アルバム"), ""])
		self.nowPlaying.Append([_("チャンネル"), ""])
		# 初期値を再生に反映
		self.events.onVolumeChanged()

	def refreshChannels(self):
		d = refresh.Dialog()
		d.Initialize()
		d.Show(False)
		self.tree.DeleteAllItems()
		self.channels = self.app.calmradio.getAllChannels()
		if self.channels == errorCodes.CONNECTION_ERROR:
			d.Destroy()
			errorDialog(_("チャンネル一覧の取得に失敗しました。\nインターネット接続をご確認の上、しばらくたってから再度お試しください。\nこの問題が繰り返し発生する場合は、開発者までご連絡ください。"))
			return
		self.treeItems = {}
		root = self.tree.AddRoot(_("チャンネル"))
		self.treeItems[root] = None
		for k, v in self.channels.items():
			category = self.tree.AppendItem(root, k.getName())
			self.treeItems[category] = k
			for i in v:
				channel = self.tree.AppendItem(category, i.getName())
				self.treeItems[channel] = i
		self.tree.Expand(root)
		d.Destroy()
		self.tree.SelectItem(root)

class Menu(BaseMenu):
	def Apply(self, target):
		"""指定されたウィンドウに、メニューを適用する。"""

		# メニュー内容をいったんクリア
		self.hMenuBar = wx.MenuBar()

		# メニューの大項目を作る
		self.hFileMenu = wx.Menu()
		self.hPlayMenu = wx.Menu()
		self.hOptionMenu = wx.Menu()
		self.hHelpMenu = wx.Menu()

		# ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu, [
			"FILE_REFRESH_CHANNELS",
			"FILE_EXIT",
		])

		# 再生メニュー
		self.RegisterMenuCommand(self.hPlayMenu, [
			"PLAY_PLAY",
			"PLAY_STOP",
		])

		# オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu, [
			"OPTION_OPTION",
			"OPTION_KEY_CONFIG",
		])

		# ヘルプメニュー
		self.RegisterMenuCommand(self.hHelpMenu, [
			"HELP_UPDATE",
			"HELP_VERSIONINFO",
		])

		# メニューバーの生成
		self.hMenuBar.Append(self.hFileMenu, _("ファイル(&F))"))
		self.hMenuBar.Append(self.hPlayMenu, _("再生(&P)"))
		self.hMenuBar.Append(self.hOptionMenu, _("オプション(&O)"))
		self.hMenuBar.Append(self.hHelpMenu, _("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)


class Events(BaseEvents):
	def __init__(self, parent, identifier):
		super().__init__(parent, identifier)
		self.nowPlayingChecker = None
		self.playbackStatusChecker = None

	def OnMenuSelect(self, event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		# ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected = event.GetId()  # メニュー識別しの数値が出る

		if selected == menuItemsStore.getRef("FILE_REFRESH_CHANNELS"):
			self.parent.refreshChannels()

		if selected == menuItemsStore.getRef("FILE_EXIT"):
			self.parent.hFrame.Close()

		if selected == menuItemsStore.getRef("PLAY_PLAY"):
			self.onChannelActivated(event)

		if selected == menuItemsStore.getRef("PLAY_STOP"):
			self.onStopButton(event)

		if selected == menuItemsStore.getRef("OPTION_OPTION"):
			d = settingsDialog.Dialog()
			d.Initialize()
			d.Show()

		if selected == menuItemsStore.getRef("OPTION_KEY_CONFIG"):
			if self.setKeymap(self.parent.identifier, _("ショートカットキーの設定"), filter=keymap.KeyFilter().SetDefault(False, False)):
				# ショートカットキーの変更適用とメニューバーの再描画
				self.parent.menu.InitShortcut()
				self.parent.menu.ApplyShortcut(self.parent.hFrame)
				self.parent.menu.Apply(self.parent.hFrame)

		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			update.checkUpdate()

		if selected == menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()

	def setKeymap(self, identifier, ttl, keymap=None, filter=None):
		if keymap:
			try:
				keys = keymap.map[identifier.upper()]
			except KeyError:
				keys = {}
		else:
			try:
				keys = self.parent.menu.keymap.map[identifier.upper()]
			except KeyError:
				keys = {}
		keyData = {}
		menuData = {}
		for refName in defaultKeymap.defaultKeymap[identifier].keys():
			title = menuItemsDic.getValueString(refName)
			if refName in keys:
				keyData[title] = keys[refName]
			else:
				keyData[title] = _("なし")
			menuData[title] = refName

		d = globalKeyConfig.Dialog(keyData, menuData, [], filter)
		d.Initialize(ttl)
		if d.Show() == wx.ID_CANCEL:
			return False

		keyData, menuData = d.GetValue()

		# キーマップの既存設定を置き換える
		newMap = ConfigManager.ConfigManager()
		newMap.read(constants.KEYMAP_FILE_NAME)
		for name, key in keyData.items():
			if key != _("なし"):
				newMap[identifier.upper()][menuData[name]] = key
			else:
				newMap[identifier.upper()][menuData[name]] = ""
		newMap.write()
		return True

	def OnExit(self, event):
		globalVars.app.player.exit()
		event.Skip()

	def onVolumeChanged(self, event=None):
		value = self.parent.volume.GetValue()
		self.parent.app.player.setVolume(value)

	def onChannelSelected(self, event):
		item = self.parent.treeItems[self.parent.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			self.parent.description.Disable()
			self.parent.playButton.Disable()
			self.parent.menu.EnableMenu("PLAY_PLAY", False)
			return
		self.parent.description.Enable()
		description = item.getDescription()
		if description is None:
			description = ""
		self.parent.description.SetValue(description)
		self.parent.playButton.Enable()
		self.parent.menu.EnableMenu("PLAY_PLAY", True)

	def onChannelActivated(self, event):
		item = self.parent.treeItems[self.parent.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			return
		streams = item.getStreams()
		result = self.parent.app.calmradio.auth()
		if result == errorCodes.CONNECTION_ERROR:
			errorDialog(_("ログインに失敗しました。\nインターネット接続をご確認の上、しばらくたってから再度お試しください。\nこの問題が繰り返し発生する場合は、開発者までご連絡ください。"))
			return
		if result == errorCodes.LOGIN_FAILED:
			errorDialog(_("ログインに失敗しました。ユーザ名／パスワードの設定内容をご確認ください。"))
			return
		if self.parent.app.calmradio.isActive():
			# premium
			bitrate = self.parent.app.config.getstring("play", "bitrate", "320", constants.AVAILABLE_BITRATE)
			url = streams[bitrate]
			url = url.replace("https://", "https://%s:%s@" % (self.parent.app.calmradio.getUser().replace("@", "%40"), self.parent.app.calmradio.getToken()))
			recentKey = "vip"
		else:
			if "free_128" not in streams:
				errorDialog(_("このチャンネルは、フリー版ではご利用いただけません。"))
				return
			url = streams["free_128"]
			recentKey = "free"
		globalVars.app.player.setPlaybackUrl(url)
		if self.nowPlayingChecker:
			self.nowPlayingChecker.exit()
		self.nowPlayingChecker = NowPlayingChecker(item.getRecentTracks()[recentKey], self.onNowPlayingChanged, self.onNowPlayingExit)
		self.nowPlayingChecker.start()
		globalVars.app.player.play()
		if self.playbackStatusChecker:
			self.playbackStatusChecker.exit()
		self.playbackStatusChecker = PlaybackStatusChecker(self.parent.app.player, self.onStopButton)
		self.playbackStatusChecker.start()
		self.parent.stopButton.Enable()
		self.parent.menu.EnableMenu("PLAY_STOP", True)
		self.parent.nowPlaying.SetItem(3, 1, item.getName())

	def onStopButton(self, event=None):
		if event:
			# command event
			globalVars.app.player.stop()
		self.parent.stopButton.Disable()
		self.parent.menu.EnableMenu("PLAY_STOP", False)

	def onDeviceButtonPressed(self, event):
		devices = globalVars.app.player.getDeviceList()
		menu = wx.Menu()
		for i in range(len(devices)):
			menu.AppendCheckItem(i, devices[i])
		current = self.parent.app.config["play"]["device"]
		if current and (current in devices):
			menu.Check(devices.index(current), True)
		else:
			menu.Check(devices.index(_("規定のデバイス")), True)
		ret = self.parent.deviceButton.GetPopupMenuSelectionFromUser(menu)
		name = devices[ret]
		if name == _("規定のデバイス"):
			name = ""
		globalVars.app.player.setDevice(name)

	def onNowPlayingChanged(self, data):
		self.parent.nowPlaying.SetItem(0, 1, data["title"])
		self.parent.nowPlaying.SetItem(1, 1, data["artist"])
		self.parent.nowPlaying.SetItem(2, 1, data["album"])

	def onNowPlayingExit(self):
		self.parent.nowPlaying.SetItem(0, 1, "")
		self.parent.nowPlaying.SetItem(1, 1, "")
		self.parent.nowPlaying.SetItem(2, 1, "")
