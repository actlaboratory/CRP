﻿# -*- coding: utf-8 -*-
# main view
# Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
# Copyright (C) 2019-2021 yamahubuki <itiro.ishino@gmail.com>

import pyperclip
import urllib.parse
import wx

import ConfigManager
import constants
import globalVars
import hotkeyHandler
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
			self.app.config.getint(self.identifier, "positionY", 50, 0),
			space=5,
			margin=20
		)
		self.InstallMenuEvent(Menu(self.identifier, self.events), self.events.OnMenuSelect)
		self.applyHotKey()
		self.InstallControls()

	def applyHotKey(self):
		self.hotkey = hotkeyHandler.HotkeyHandler(None, hotkeyHandler.HotkeyFilter().SetDefault())
		if self.hotkey.addFile(constants.KEYMAP_FILE_NAME, ["HOTKEY"]) == errorCodes.OK:
			errors = self.hotkey.GetError("HOTKEY")
			if errors:
				tmp = _(constants.KEYMAP_FILE_NAME + "で設定されたホットキーが正しくありません。キーの重複、存在しないキー名の指定、使用できないキーパターンの指定などが考えられます。以下のキーの設定内容をご確認ください。\n\n")
				for v in errors:
					tmp += v + "\n"
				dialog(_("エラー"), tmp)
			self.hotkey.Set("HOTKEY", self.hFrame)

	def InstallControls(self):
		horizontalCreator = views.ViewCreator.ViewCreator(self.viewMode, self.creator.GetPanel(), self.creator.GetSizer(), wx.HORIZONTAL, style=wx.ALL | wx.EXPAND, space=20)

		# channels
		self.tree, tmp = self.creator.treeCtrl(_("チャンネル一覧(&C)"), sizerFlag=wx.EXPAND, proportion=2)
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.events.onChannelActivated)
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.events.onChannelSelected)
		self.description, tmp = self.creator.inputbox(_("説明"), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_PROCESS_ENTER, proportion=1)
		self.description.Disable()
		self.description.Bind(wx.EVT_TEXT_ENTER, self.events.onChannelActivated)

		# playback controls
		self.playButton = horizontalCreator.button(_("選択中のチャンネルを再生"), self.events.onChannelActivated)
		self.playButton.Disable()
		self.menu.EnableMenu("PLAY_PLAY", False)
		self.stopButton = horizontalCreator.button(_("停止(&S)"), self.events.onStopButton)
		self.stopButton.Disable()
		self.menu.EnableMenu("PLAY_STOP", False)
		horizontalCreator.GetSizer().AddStretchSpacer(1)
		self.mute = horizontalCreator.button("", self.events.onMuteButton, style=wx.BU_NOTEXT | wx.BU_EXACTFIT | wx.BORDER_NONE, sizerFlag=wx.ALL | wx.ALIGN_CENTER, enableTabFocus=False)
		if globalVars.app.config.getstring("view", "colorMode", "white", ("white", "dark")) == "white":
			self.setBitmapButton(self.mute, self.hPanel, wx.Bitmap("./resources/volume.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオンにする"))
		else:
			self.setBitmapButton(self.mute, self.hPanel, wx.Bitmap("./resources/volume_bk.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオンにする"))
		self.volume, tmp = horizontalCreator.slider(_("音量(&V)"), event=self.events.onVolumeChanged, defaultValue=self.app.config.getint("play", "volume", 100, 0, 100), textLayout=None)

		# now playing
		self.nowPlaying, tmp = self.creator.listCtrl(_("現在再生中(&N)"), sizerFlag=wx.EXPAND)
		self.nowPlaying.AppendColumn(_("項目"), width=200)
		self.nowPlaying.AppendColumn(_("内容"), width=1600)
		self.nowPlaying.Append([_("タイトル"), ""])
		self.nowPlaying.Append([_("アーティスト"), ""])
		self.nowPlaying.Append([_("アルバム"), ""])
		self.nowPlaying.Disable()
		self.nowPlaying.Append([_("チャンネル"), ""])
		self.menu.keymap.Set("nowPlaying", self.nowPlaying)

		# 初期値を再生に反映
		self.events.onVolumeChanged()

	def setBitmapButton(self, button, backgroundWindow, bitmap, label):
		if backgroundWindow != None:
			button.SetBackgroundColour(backgroundWindow.GetBackgroundColour())
		button.SetBitmap(bitmap)
		button.SetLabel(label)
		button.setToolTip()

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
		root = self.tree.AddRoot(_("チャンネル"), data=None)
		for k, v in self.channels.items():
			category = self.tree.AppendItem(root, k.getName(), data=k)
			for i in v:
				channel = self.tree.AppendItem(category, i.getName(), data=i)
		self.tree.Expand(root)
		d.Destroy()
		self.tree.SelectItem(root)


class Menu(BaseMenu):
	def __init__(self, identifier, event):
		super().__init__(identifier)
		self.event = event

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
			"PLAY_MUTE",
		])
		self.hDeviceMenu = wx.Menu()
		self.RegisterMenuCommand(self.hPlayMenu, "PLAY_CHANGE_DEVICE", subMenu=self.hDeviceMenu)
		self.hPlayMenu.Bind(wx.EVT_MENU_OPEN, self.event.OnMenuOpen)

		# オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu, [
			"OPTION_OPTION",
			"OPTION_KEY_CONFIG",
			"OPTION_HOTKEY",
		])

		# ヘルプメニュー
		self.RegisterMenuCommand(self.hHelpMenu, [
			"HELP_UPDATE",
			"HELP_VERSIONINFO",
		])

		# メニューバーの生成
		self.hMenuBar.Append(self.hFileMenu, _("ファイル(&F)"))
		self.hMenuBar.Append(self.hPlayMenu, _("再生(&P)"))
		self.hMenuBar.Append(self.hOptionMenu, _("オプション(&O)"))
		self.hMenuBar.Append(self.hHelpMenu, _("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)


class Events(BaseEvents):
	def __init__(self, parent, identifier):
		super().__init__(parent, identifier)
		self.nowPlayingChecker = None
		self.playbackStatusChecker = None
		self.devices = {}
		self.muteFlag = False

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

		if selected == menuItemsStore.getRef("PLAY_MUTE"):
			self.onMuteButton()

		if selected == menuItemsStore.getRef("PLAY_COPY_URL"):
			url = globalVars.app.player.getPlaybackUrl()
			if len(url) == 0:
				return
			pyperclip.copy(url)
			dialog(_("再生URLのコピー"), _("コピーしました。"))

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

		if selected == menuItemsStore.getRef("OPTION_HOTKEY"):
			if self.setKeymap("HOTKEY", _("グローバルホットキーの設定"), self.parent.hotkey, filter=self.parent.hotkey.filter):
				# 変更適用
				self.parent.hotkey.UnSet("HOTKEY", self.parent.hFrame)
				self.parent.applyHotKey()

		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			update.checkUpdate()

		if selected == menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()

		if selected == menuItemsStore.getRef("NOWPLAYING_COPY"):
			idx = self.parent.nowPlaying.GetFocusedItem()
			if idx < 0:
				return
			text = self.parent.nowPlaying.GetItemText(idx, 1)
			if text:
				pyperclip.copy(text)
				self.log.debug("copied: %s" % text)

		elif selected >= constants.DEVICE_MENU_START:
			name = self.devices[selected]
			if name == _("規定のデバイス"):
				globalVars.app.player.setDevice("")
			else:
				globalVars.app.player.setDevice(name)

	def OnMenuOpen(self, event):
		menu = event.GetMenu()
		if menu == self.parent.menu.hDeviceMenu:
			# clear
			for i in range(menu.GetMenuItemCount()):
				menu.DestroyItem(menu.FindItemByPosition(0))
			self.devices = {}
			# get new data
			devices = globalVars.app.player.getDeviceList()
			for i in range(len(devices)):
				menu.AppendCheckItem(i + constants.DEVICE_MENU_START, devices[i])
				self.devices[i + constants.DEVICE_MENU_START] = devices[i]
			current = self.parent.app.config["play"]["device"]
			if current and (current in devices):
				menu.Check(devices.index(current) + constants.DEVICE_MENU_START, True)
			else:
				menu.Check(devices.index(_("規定のデバイス")) + constants.DEVICE_MENU_START, True)

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

	def onMuteButton(self, event=None):
		if not self.muteFlag:
			globalVars.app.player.setVolume(0, False)
			self.muteFlag = True
			self.parent.volume.Disable()
			if globalVars.app.config.getstring("view", "colorMode", "white", ("white", "dark")) == "white":
				self.parent.setBitmapButton(self.parent.mute, None, wx.Bitmap("./resources/mute.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオフにする"))
			else:
				self.parent.setBitmapButton(self.parent.mute, None, wx.Bitmap("./resources/mute_bk.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオフにする"))
			self.parent.menu.SetMenuLabel("PLAY_MUTE", _("ミュート解除(&M)"))
		else:
			val = self.parent.volume.GetValue()
			globalVars.app.player.setVolume(val, False)
			self.muteFlag = False
			self.parent.volume.Enable()
			if globalVars.app.config.getstring("view", "colorMode", "white", ("white", "dark")) == "white":
				self.parent.setBitmapButton(self.parent.mute, None, wx.Bitmap("./resources/volume.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオンにする"))
			else:
				self.parent.setBitmapButton(self.parent.mute, None, wx.Bitmap("./resources/volume_bk.dat", wx.BITMAP_TYPE_GIF), _("ミュートをオンにする"))
			self.parent.menu.SetMenuLabel("PLAY_MUTE", _("ミュート(&M)"))

	def onVolumeChanged(self, event=None):
		value = self.parent.volume.GetValue()
		self.parent.app.player.setVolume(value)

	def onChannelSelected(self, event):
		item = self.parent.tree.GetItemData(self.parent.tree.GetFocusedItem())
		if type(item) != calmradio.main.Channel:
			self.parent.description.Clear()
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
		item = self.parent.tree.GetItemData(self.parent.tree.GetFocusedItem())
		if type(item) != calmradio.main.Channel:
			event.Skip()
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
			recentKey = "vip"
		else:
			if "free_128" not in streams:
				errorDialog(_("このチャンネルは、フリー版ではご利用いただけません。"))
				return
			url = streams["free_128"]
			recentKey = "free"
		if self.parent.app.calmradio.getUser():
			url = url.replace("https://", "https://%s:%s@" % (urllib.parse.quote(self.parent.app.calmradio.getUser()), urllib.parse.quote(self.parent.app.calmradio.getToken())))
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

	def onNowPlayingChanged(self, data):
		self.parent.nowPlaying.Enable()
		self.parent.nowPlaying.SetItem(0, 1, data["title"])
		self.parent.nowPlaying.SetItem(1, 1, data["artist"])
		self.parent.nowPlaying.SetItem(2, 1, data["album"])

	def onNowPlayingExit(self):
		self.parent.nowPlaying.SetItem(0, 1, "")
		self.parent.nowPlaying.SetItem(1, 1, "")
		self.parent.nowPlaying.SetItem(2, 1, "")
