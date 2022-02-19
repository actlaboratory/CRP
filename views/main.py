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
from views import versionDialog
import calmradio.main


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
		self.chanels = self.app.calmradio.getAllChannels()
		self.treeItems = {}
		self.tree, tmp = self.creator.treeCtrl(_("チャンネル一覧(&C)"))
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.events.onChannelActivated)
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.events.onChannelSelected)
		root = self.tree.AddRoot(_("チャンネル"))
		self.treeItems[root] = None
		for k, v in self.chanels.items():
			category = self.tree.AppendItem(root, k.getName())
			self.treeItems[category] = k
			for i in v:
				channel = self.tree.AppendItem(category, i.getName().replace("CALMRADIO - ", ""))
				self.treeItems[channel] = i
		self.tree.Expand(root)
		self.description, tmp = self.creator.inputbox(_("説明"), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_PROCESS_ENTER)
		self.description.Disable()
		self.description.Bind(wx.EVT_TEXT_ENTER, self.events.onChannelActivated)
		# playback controls
		self.playButton = self.creator.button(_("このチャンネルを再生(&P)"), self.events.onChannelActivated)
		self.playButton.Disable()
		self.stopButton = self.creator.button(_("停止(&S)"), self.events.onStopButton)
		self.stopButton.Disable()
		self.volume, tmp = self.creator.slider(_("音量(&V)"), event=self.events.onVolumeChanged, style=wx.SL_VERTICAL, defaultValue=self.app.config.getint("play", "volume", 100, 0, 100))
		self.volume.Disable()
		# 初期値を再生に反映
		self.events.onVolumeChanged()


class Menu(BaseMenu):
	def Apply(self, target):
		"""指定されたウィンドウに、メニューを適用する。"""

		# メニュー内容をいったんクリア
		self.hMenuBar = wx.MenuBar()

		# メニューの大項目を作る
		self.hFileMenu = wx.Menu()
		self.hOptionMenu = wx.Menu()
		self.hHelpMenu = wx.Menu()

		# ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu, [
			"FILE_CHANNELS",
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
		self.hMenuBar.Append(self.hOptionMenu, _("オプション(&O)"))
		self.hMenuBar.Append(self.hHelpMenu, _("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)


class Events(BaseEvents):
	def OnMenuSelect(self, event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		# ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected = event.GetId()  # メニュー識別しの数値が出る

		if selected == menuItemsStore.getRef("FILE_CHANNELS"):
			self.channelsList()

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
		self.parent.app.config["play"]["volume"] = value

	def onChannelSelected(self, event):
		item = self.parent.treeItems[self.parent.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			self.parent.description.Disable()
			self.parent.playButton.Disable()
		else:
			self.parent.description.Enable()
			self.parent.description.SetValue(item.getDescription())
			self.parent.playButton.Enable()

	def onChannelActivated(self, event):
		item = self.parent.treeItems[self.parent.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			return
		streams = item.getStreams()
		if "free_128" not in streams:
			errorDialog(_("このチャンネルは、フリー版ではご利用いただけません。"))
			return
		globalVars.app.player.setPlaybackUrl(streams["free_128"])
		globalVars.app.player.play()
		self.parent.stopButton.Enable()
		self.parent.volume.Enable()

	def onStopButton(self, event):
		globalVars.app.player.stop()
		self.parent.stopButton.Disable()
		self.parent.volume.Disable()
