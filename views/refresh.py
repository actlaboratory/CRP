# -*- coding: utf-8 -*-
# dialog box for refresh channels

import wx
import globalVars
import views.ViewCreator
from logging import getLogger
from views.baseDialog import *


class Dialog(BaseDialog):
	def __init__(self):
		super().__init__("refreshDialog")

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame, _("チャンネル一覧を更新"))
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.VERTICAL, 20, style=wx.ALL, margin=20)
		self.static = self.creator.staticText(_("チャンネル一覧を取得しています..."))
