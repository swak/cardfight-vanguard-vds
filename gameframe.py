# -*- coding: utf-8 -*-

#   This file is part of CFVVDS.
#
#    CFVVDS is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    CFVVDS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with CFVVDS; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import wx, sys, os
from gamecontrols import *
import settings
from win32api import GetSystemMetrics

class GameFrame(wx.Frame):
    
    def GetSetting(self, name):
        self.BaseDirectory = os.getcwd()
        self.Settings = settings.LoadSettings(self.BaseDirectory)
        if self.Settings.has_key(name):
            return self.Settings[name]
        else:
            return ''
        
    def __init__(self, engine):
        self._engine = engine
        wx.Frame.__init__(self, parent=None, title="CRAY ONLINE", size=(1024,768), style=wx.MINIMIZE_BOX | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.SetIcon(wx.IconFromLocation(wx.IconLocation(os.path.join(self._engine.BaseDirectory,'mooseduel16x16.ico'))))
        self.CenterOnScreen()
        self.Game = GamePanel(self, self._engine)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        if self.GetSetting('ShowFaceUpCardName') == 'Yes':
            self.ShowFullScreen(True, style=wx.FULLSCREEN_NOCAPTION |wx.FULLSCREEN_NOBORDER|wx.FULLSCREEN_NOSTATUSBAR)
        if GetSystemMetrics (0) == 1024 and GetSystemMetrics (1) == 768 or GetSystemMetrics (1) == 720:
            if wx.MessageDialog(None,'Your screen resolution is low. Would you like to run in Full Screen Mode?','',wx.YES_NO | wx.ICON_QUESTION | wx.YES_DEFAULT).ShowModal() == wx.ID_YES:
                self.ShowFullScreen(True, style=wx.FULLSCREEN_NOCAPTION |wx.FULLSCREEN_NOBORDER|wx.FULLSCREEN_NOSTATUSBAR)
        if GetSystemMetrics (0) < 1024 and GetSystemMetrics (1) < 768:
            wx.MessageDialog(None,'Your Screen Resolution is too low. Change Your Screen Resolution to at least 1024x720.','',wx.OK | wx.ICON_INFORMATION).ShowModal()
    def OnExit(self, event=None):
        self.Game.OnClose()
        self.Destroy()
    