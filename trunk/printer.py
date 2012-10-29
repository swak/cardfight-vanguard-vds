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

import wx
#Simple printing function. Need more info about vanguard decks.
#TO DO: 
class DeckPrinter(wx.Printout):
    def __init__(self, deck):
        wx.Printout.__init__(self)
        self.Deck = deck
        self.StartX = 40
        self.StartY = 40
        self.VSpacer = 60
        self.CurrentX = self.StartX
        self.CurrentY = self.StartY
        self.FirstFont = wx.Font(pointSize=48, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD, faceName='Arial')
        self.SecondFont = wx.Font(pointSize=48, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL, faceName='Arial')
        self.ThirdFont = wx.Font(pointSize=54, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD, faceName='Arial')

    def OnBeginDocument(self, start, end):
        return super(DeckPrinter, self).OnBeginDocument(start, end)

    def OnEndDocument(self):
        super(DeckPrinter, self).OnEndDocument()

    def OnBeginPrinting(self):
        super(DeckPrinter, self).OnBeginPrinting()

    def OnEndPrinting(self):
        super(DeckPrinter, self).OnEndPrinting()

    def OnPreparePrinting(self):
        super(DeckPrinter, self).OnPreparePrinting()

    def HasPage(self, page):
        if page <= 1:
            return True
        else:
            return False

    def GetPageInfo(self):
        return (1, 1, 1, 1)

#TO DO: Change structure to fit CFV decks
    def OnPrintPage(self, page):
        monsters = self.Deck.GetMonsters()
        triggers = self.Deck.GetTrigger()

        maindeckcount = len(monsters) + len(triggers)

        dc = self.GetDC()

        dc.SetFont(self.ThirdFont)
        dc.DrawText('Main Deck: ' + str(maindeckcount), self.CurrentX, self.CurrentY)
        self.NewLine()
        self.NewLine()

        dc.SetFont(self.FirstFont)
        dc.DrawText('Normal Units: ' + str(len(monsters)), self.CurrentX, self.CurrentY)
        self.NewLine()
        dc.SetFont(self.SecondFont)
        for c in monsters:
            dc.DrawText(c.Name, self.CurrentX, self.CurrentY)
            self.NewLine()

        self.NewLine()
        dc.SetFont(self.FirstFont)
        dc.DrawText('Trigger Units: ' + str(len(triggers)), self.CurrentX, self.CurrentY)
        self.NewLine()
        dc.SetFont(self.SecondFont)
        for c in triggers:
            dc.DrawText(c.Name, self.CurrentX, self.CurrentY)
            self.NewLine()

        return True

    def NewLine(self):
        self.CurrentY += self.VSpacer

    def AddVSpace(self, n):
        self.CurrentY += n

    def AddHSpace(self, n):
        self.CurrentX += n