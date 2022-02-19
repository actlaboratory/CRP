# -*- coding: utf-8 -*-
# sample

import wx
import globalVars
import views.ViewCreator
import calmradio.main
from logging import getLogger
from views.baseDialog import *
import simpleDialog


class Dialog(BaseDialog):
	def __init__(self):
		super().__init__("channelsDialog")
		self.data = None

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame, _("チャンネル一覧"))
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.VERTICAL, 20, style=wx.ALL, margin=20)

	def onSelectionChanged(self, event):
		item = self.treeItems[self.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			self.description.Disable()
		else:
			self.description.Enable()
			self.description.SetValue(item.getDescription())

	def onOkButton(self, event):
		item = self.treeItems[self.tree.GetFocusedItem()]
		if type(item) != calmradio.main.Channel:
			simpleDialog.errorDialog(_("チャンネルが選択されていません。"))
			self.tree.SetFocus()
			return
		self.data = item
		self.wnd.EndModal(wx.ID_OK)

	def getData(self):
		return self.data
