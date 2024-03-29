# -*- coding: utf-8 -*-

#   This file is part of CRAY ONLINE.
#
#    CRAY ONLINE is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    CRAY ONLINE is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with CRAY ONLINE; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import wx, sys, os, webbrowser
from wx import richtext
import engine, network, dialogs, gameframe, room, updater
from printer import DeckPrinter

ID_NEW = 10001
ID_OPEN = 10002
ID_SAVE = 10003
ID_SAVEAS = 10004
ID_PRINT = 10005
ID_CLOSE = 10006
ID_ABOUT = 10007
ID_ADD = 10008
ID_POPUP_REMOVE = 10009
ID_REMOVE = 10010
ID_POPUP_ADD = 10011
ID_CONNECT = 10013
ID_LISTEN = 10014
ID_PLAY = 10015
ID_ADVANCED = 10016
ID_ROOMS = 10017
ID_WEB = 10018
ID_SETTINGS = 10019
ID_UPDATE = 10020


class MainFrame(wx.Frame):
    def __init__(self, engine, *args, **kwargs):
        
        wx.Frame.__init__(self, *args, **kwargs)

        self.Centre() # Centro il frame nello screen
        self.Engine = engine # Creo una variabile che punta all'engine
        self.SelectedFromDeck = ''
        self.SelectedFromSide = False
        self.panel = wx.Panel(self) # Creo il Panel che conterrà i controlli ed i sizer
        self.vbox1 = wx.BoxSizer(wx.VERTICAL) # Sizer Verticale n°1
        self.vbox2 = wx.BoxSizer(wx.VERTICAL) # Sizer Verticale n°2
        self.vbox3 = wx.BoxSizer(wx.VERTICAL) # Sizer Verticale n°3
        self.vbox4 = wx.BoxSizer(wx.VERTICAL) # Sizer Verticale n°4
        self.vbox5 = wx.BoxSizer(wx.VERTICAL) # Sizer Verticale n°5
        self.hbox = wx.BoxSizer(wx.HORIZONTAL) # Sizer Orizzontale che contiene quelli verticali
        self.hmbox1 = wx.BoxSizer(wx.HORIZONTAL) # Sizer per la parte centrale
        self.hmbox2 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox3 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox4 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox5 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox6 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox7 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox8 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox9 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox10 = wx.BoxSizer(wx.HORIZONTAL) # *
        self.hmbox11 = wx.BoxSizer(wx.VERTICAL) # *
        self.hvbox1 = wx.BoxSizer(wx.HORIZONTAL)
        #self.Bind(wx.EVT_SHOW, self.OnUpdate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # Menu
        self.Menu = wx.MenuBar()
        
        self.CardCount = wx.StaticText(self.panel, -1, 'Cards Total: 0')
        
        # Status Bar
        self.StatusBar = wx.StatusBar(self,-1) 
        self.SetStatusBar(self.StatusBar) 
        self.StatusBar.SetStatusText(self.Engine.GetNameVersion(), 0) 
        # End Status Bar

        # CardSearch Control
        self.CardSearchCtrl = wx.TextCtrl(self.panel, -1, "") 
        self.CardSearchCtrl.Bind(wx.EVT_TEXT, self.OnSearchInput, self.CardSearchCtrl) 
        # End CardSearch Control

        # CardList Control
        li = self.Engine.GetAllCards() 
        self.DatabaseCardCount = len(li)
        self.CardListCtrl = wx.ListCtrl(parent = self.panel, style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_HRULES ) 
        
        self.CardListCtrl.InsertColumn(0, 'Name') 
        self.CardListCtrl.InsertColumn(1, 'CardID')
        n = 0 
        for c in li:
            idx = self.CardListCtrl.InsertStringItem(n, c.Name)
            self.CardListCtrl.SetStringItem(idx, 1, c.CardID)
            n += 1
        self.CardCount.SetLabel('Cards Total: ' + str(n))
        self.CardListCtrl.SetColumnWidth(0, 175) 
        self.CardListCtrl.SetColumnWidth(1, 0) 
        self.CardListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCardSelected)
        self.CardListCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnCardListItemRClick)
        self.CardListCtrl.Bind(wx.EVT_LEFT_DCLICK, self.OnAddCard)
        # End CardList Control
        

        
        self.MonsterHeaderText = wx.StaticText(self.panel, -1, 'Normal Units: 0')
        self.MonsterListCtrl = wx.ListCtrl(self.panel, -1, style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_HRULES)
        self.MonsterListCtrl.InsertColumn(0, 'Normal Units')
        self.MonsterListCtrl.SetColumnWidth(0, 175)
        self.MonsterListCtrl.InsertColumn(1, 'CardID')
        self.MonsterListCtrl.SetColumnWidth(1, 0)
        self.MonsterListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnMonsterCardSelected)
        self.MonsterListCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnMonsterListItemRClick)
        self.MonsterListCtrl.Bind(wx.EVT_LEFT_DCLICK, self.OnRemoveCard)
        
        self.TriggerHeaderText = wx.StaticText(self.panel, -1, 'Trigger Units: 0')
        self.TriggerListCtrl = wx.ListCtrl(self.panel, -1, style = wx.LC_REPORT |  wx.LC_SINGLE_SEL | wx.LC_NO_HEADER | wx.LC_HRULES)
        self.TriggerListCtrl.InsertColumn(0, 'Trigger Units')
        self.TriggerListCtrl.SetColumnWidth(0, 175)
        self.TriggerListCtrl.InsertColumn(1, 'CardID')
        self.TriggerListCtrl.SetColumnWidth(1, 0)
        self.TriggerListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTriggerCardSelected)
        self.TriggerListCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnTriggerListItemRClick)
        self.TriggerListCtrl.Bind(wx.EVT_LEFT_DCLICK, self.OnRemoveCard)
        
        self.DeckCountText = wx.StaticText(self.panel, -1, 'Deck: 0')
        
        self.G0CountText = wx.StaticText(self.panel, -1, 'G0: 0')
        self.G1CountText = wx.StaticText(self.panel, -1, 'G1: 0')
        self.G2CountText = wx.StaticText(self.panel, -1, 'G2: 0')
        self.G3CountText = wx.StaticText(self.panel, -1, 'G3: 0')
        
        self.HTCountText = wx.StaticText(self.panel, -1, 'HT: 0')
        self.STCountText = wx.StaticText(self.panel, -1, 'ST: 0')
        self.CTCountText = wx.StaticText(self.panel, -1, 'CT: 0')
        self.DTCountText = wx.StaticText(self.panel, -1, 'DT: 0')
        
        #Monsterlist Popup
        self.MonsterListPopupMenu = wx.Menu()
        item = wx.MenuItem(self.MonsterListPopupMenu,ID_POPUP_REMOVE,self.Engine.GetLangString('Remove'))
        item.SetBitmap(self.Engine.GetSkinImage('Totrunk'))
        self.Bind(wx.EVT_MENU, self.OnRemoveCard, item)
        self.MonsterListPopupMenu.AppendItem(item)
        # End Listbox

        self.TriggerListPopupMenu = wx.Menu()
        item = wx.MenuItem(self.TriggerListPopupMenu,ID_POPUP_REMOVE,self.Engine.GetLangString('Remove'))
        item.SetBitmap(self.Engine.GetSkinImage('Totrunk'))
        self.Bind(wx.EVT_MENU, self.OnRemoveCard, item)
        self.TriggerListPopupMenu.AppendItem(item)
        
        self.CardNameCtrl = wx.StaticText(self.panel, -1, style=wx.ALIGN_CENTRE)
        self.CardImageCtrl = wx.StaticBitmap(self.panel, -1, size=(165,240))
        self.CardDescriptionCtrl = wx.TextCtrl(self.panel, -1,size=(330,140), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP)
        # End
        
        self.BuildUI()

        # Layout
        
        self.vbox1.Add(self.hvbox1, 0, wx.ALL | wx.EXPAND, 2) # Aggiungo il CardSearchCtrl al vbox1 (control,proprortions,styles,margins)
        self.hvbox1.Add(self.CardSearchCtrl, 1, wx.ALL | wx.EXPAND, 2) # Aggiungo il CardSearchCtrl al vbox1 (control,proprortions,styles,margins)
        self.hvbox1.Add(self.CardReloadCtrl, 0, wx.ALL | wx.EXPAND, 2)
        self.vbox1.Add(self.CardListCtrl, 1, wx.ALL | wx.EXPAND, 0) # Aggiungo il CardListCtrl al vbox1 (control,proprortions,styles,margins)
        self.vbox1.Add(self.CardCount, 0, wx.ALL | wx.EXPAND, 2)
        
        self.vbox2.Add(self.hmbox1, 0, wx.ALL | wx.EXPAND, 2) # Parte Centrale del Layout
        self.vbox2.Add(self.hmbox2, 1, wx.ALL | wx.EXPAND, 2) # *
        self.vbox3.Add(self.hmbox3, 0, wx.ALL | wx.EXPAND, 2) # *
        self.vbox3.Add(self.hmbox4, 1, wx.ALL | wx.EXPAND, 2) # *
        self.vbox4.Add(self.hmbox5, 0, wx.ALL | wx.EXPAND, 2) # *
        self.vbox4.Add(self.hmbox6, 1, wx.ALL | wx.EXPAND, 2) # *
        #self.vbox2.Add(self.hmbox7, 0, wx.ALL | wx.EXPAND, 2) # *
        #self.vbox2.Add(self.hmbox8, 1, wx.ALL | wx.EXPAND, 2) # *
        #self.vbox3.Add(self.hmbox9, 0, wx.ALL | wx.EXPAND, 2) # *
        #self.vbox3.Add(self.hmbox10, 1, wx.ALL | wx.EXPAND, 2) # *
        self.vbox4.Add(self.hmbox11, 1, wx.ALL | wx.EXPAND, 2) # *
        self.vbox4.AddSpacer(25,0) # *
        self.vbox4.AddSpacer(25,0) # *
        self.vbox4.AddSpacer(25,0) # *
        self.hmbox1.Add(self.MonsterHeaderText, 1, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox2.Add(self.MonsterListCtrl, 1, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox3.Add(self.TriggerHeaderText, 1, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox4.Add(self.TriggerListCtrl, 1, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.DeckCountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.G0CountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.G1CountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.G2CountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.G3CountText, 0, wx.ALL | wx.EXPAND, 2) # *
        
        self.hmbox11.Add(self.HTCountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.STCountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.CTCountText, 0, wx.ALL | wx.EXPAND, 2) # *
        self.hmbox11.Add(self.DTCountText, 0, wx.ALL | wx.EXPAND, 2) # *

        self.vbox5.Add(self.CardNameCtrl, 0, wx.ALL | wx.ALIGN_CENTER , 4)
        self.vbox5.Add(self.CardImageCtrl, 0, wx.ALL | wx.ALIGN_CENTER, 4)
        self.vbox5.Add(self.CardDescriptionCtrl, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 4)
        
        self.hbox.Add(self.vbox1, 1, wx.EXPAND | wx.ALL, 2) # Aggiungo il VBox1 al HBox (control,proprortions,styles,margins)
        self.hbox.Add(self.vbox2, 1, wx.EXPAND | wx.ALL, 2) # Aggiungo il VBox2 al HBox (control,proprortions,styles,margins)
        self.hbox.Add(self.vbox3, 1, wx.EXPAND | wx.ALL, 2) # Aggiungo il VBox3 al HBox (control,proprortions,styles,margins)
        self.hbox.Add(self.vbox4, 0, wx.EXPAND | wx.ALL, 2) # Aggiungo il VBox3 al HBox (control,proprortions,styles,margins)
        self.hbox.Add(self.vbox5, 0, wx.EXPAND | wx.ALL, 2) # Aggiungo il VBox3 al HBox (control,proprortions,styles,margins)
        self.panel.SetSizer(self.hbox) # Setto il sizer del panel
        self.panel.Layout() # Layout del panel
        
        # End Layout
        
        self.AdvancedSearchFrame = dialogs.AdvancedSearch(self)
        self.CardSearchCtrl.SetFocus()

    def BuildUI(self, changes=0):
        if changes:
            self.CardReloadCtrl.Destroy()
            self.GetToolBar().Destroy()
            self.CardListPopupMenu.Destroy()
            self.MonsterListPopupMenu.Destroy()
        
        # Menu
        self.Menu = wx.MenuBar()

        self.mFile = wx.Menu()
        self.mGame = wx.Menu()
        self.mTools = wx.Menu()
        self.mHelp = wx.Menu()

        # File Menu
        item = wx.MenuItem(self.mFile,ID_NEW,self.Engine.GetLangString('New'))
        item.SetBitmap(self.Engine.GetSkinImage('New'))
        self.Bind(wx.EVT_MENU, self.OnNew, item)
        self.mFile.AppendItem(item)

        item = wx.MenuItem(self.mFile,ID_OPEN,self.Engine.GetLangString('Open'))
        item.SetBitmap(self.Engine.GetSkinImage('Open'))
        self.Bind(wx.EVT_MENU, self.OnOpen, item)
        self.mFile.AppendItem(item)

        item = wx.MenuItem(self.mFile,ID_SAVE,self.Engine.GetLangString('Save'))
        item.SetBitmap(self.Engine.GetSkinImage('Save'))
        self.Bind(wx.EVT_MENU, self.OnSave, item)
        self.mFile.AppendItem(item)

        item = wx.MenuItem(self.mFile,ID_SAVEAS,self.Engine.GetLangString('SaveAs'))
        item.SetBitmap(self.Engine.GetSkinImage('SaveAs'))
        self.Bind(wx.EVT_MENU, self.OnSaveAs, item)
        self.mFile.AppendItem(item)
        
        item = wx.MenuItem(self.mFile,ID_ADVANCED,self.Engine.GetLangString('Advanced Search'))
        item.SetBitmap(self.Engine.GetSkinImage('Find'))
        self.Bind(wx.EVT_MENU, self.OnAdvancedSearchMenu, item)
        self.mFile.AppendItem(item)

        item = wx.MenuItem(self.mFile,ID_PRINT,self.Engine.GetLangString('Print'))
        item.SetBitmap(self.Engine.GetSkinImage('Print'))
        self.Bind(wx.EVT_MENU, self.OnPrint, item)
        self.mFile.AppendItem(item)

        item = wx.MenuItem(self.mFile,ID_CLOSE,self.Engine.GetLangString('Close'))
        item.SetBitmap(self.Engine.GetSkinImage('Close'))
        self.Bind(wx.EVT_MENU, self.OnMenuClose, item)
        self.mFile.AppendItem(item)
        # End File Menu        
         
        # Game Menu
        
        item = self.mGame.Append(ID_CONNECT, text = self.Engine.GetLangString('Connect'))
        self.Bind(wx.EVT_MENU, self.OnConnectMenu, item)
        
        item = self.mGame.Append(ID_LISTEN, text = self.Engine.GetLangString('Listen'))
        self.Bind(wx.EVT_MENU, self.OnListenMenu, item)

        item = self.mGame.Append(ID_PLAY, text = self.Engine.GetLangString('Test'))
        self.Bind(wx.EVT_MENU, self.OnPlayMenu, item)

        item = wx.MenuItem(self.mGame,-1,self.Engine.GetLangString('Rooms'))
        item.SetBitmap(self.Engine.GetSkinImage('Chat'))
        self.Bind(wx.EVT_MENU, self.OnRoomsMenu, item)
        self.mGame.AppendItem(item)
        # End Game Menu

        # Help
        item = wx.MenuItem(self.mHelp,ID_SETTINGS,self.Engine.GetLangString('Preferences'))
        item.SetBitmap(self.Engine.GetSkinImage('Preferences'))
        self.Bind(wx.EVT_MENU, self.OnSettings, item)
        self.mHelp.AppendItem(item)

        item = wx.MenuItem(self.mHelp,ID_UPDATE,self.Engine.GetLangString('Update'))
        item.SetBitmap(self.Engine.GetSkinImage('Update'))
        self.Bind(wx.EVT_MENU, self.OnUpdate, item)
        self.mHelp.AppendItem(item)
    #TO DO: Fix images updater
        #item = wx.MenuItem(self.mHelp,-1,self.Engine.GetLangString('Images Update'))
        #item.SetBitmap(self.Engine.GetSkinImage('Update'))
        #self.Bind(wx.EVT_MENU, self.OnImagesUpdate, item)
        #self.mHelp.AppendItem(item)
    
        item = wx.MenuItem(self.mHelp,ID_WEB,self.Engine.GetLangString('CRAY ONLINE.Web'))
        item.SetBitmap(self.Engine.GetSkinImage('Web'))
        self.Bind(wx.EVT_MENU, self.OnWeb, item)
        self.mHelp.AppendItem(item)


        item = wx.MenuItem(self.mHelp,ID_ABOUT,self.Engine.GetLangString('About'))
        item.SetBitmap(self.Engine.GetSkinImage('About'))
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        self.mHelp.AppendItem(item)
        # End Help Menu

        self.Menu.Append(self.mFile, self.Engine.GetLangString('File'))
        self.Menu.Append(self.mGame, self.Engine.GetLangString('Game'))
        self.Menu.Append(self.mHelp, self.Engine.GetLangString('Help'))
        self.SetMenuBar(self.Menu)
        
        # ToolBar
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16,16))
        self.toolbar.AddLabelTool(ID_NEW, 'New', self.Engine.GetSkinImage('New'), shortHelp = self.Engine.GetLangString('New'), longHelp = self.Engine.GetLangString('Create a new deck'))
        self.toolbar.AddLabelTool(ID_OPEN, 'Open', self.Engine.GetSkinImage('Open'), shortHelp = self.Engine.GetLangString('Open'), longHelp = self.Engine.GetLangString('Open an existent deck'))
        self.toolbar.AddLabelTool(ID_SAVE, 'Save', self.Engine.GetSkinImage('Save'), shortHelp = self.Engine.GetLangString('Save'), longHelp = self.Engine.GetLangString('Save current deck'))
        self.toolbar.AddLabelTool(ID_SAVEAS, 'Save As...', self.Engine.GetSkinImage('SaveAs'), shortHelp = self.Engine.GetLangString('Save As...'), longHelp = self.Engine.GetLangString('Save current deck to a new path'))
        self.toolbar.AddLabelTool(ID_PRINT, 'Print', self.Engine.GetSkinImage('Print'), shortHelp = self.Engine.GetLangString('Print'), longHelp = self.Engine.GetLangString('Print current deck'))
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(ID_ADVANCED, 'Advanced Search', self.Engine.GetSkinImage('Find'), shortHelp = self.Engine.GetLangString('Advanced Search'), longHelp = self.Engine.GetLangString('Open the Advanced Search Form'))
        self.toolbar.Realize()
        # End ToolBar
        
        # CardReload Control
        self.CardReloadCtrl = wx.BitmapButton(self.panel, -1, self.Engine.GetSkinImage('Reload'))
        self.CardReloadCtrl.SetToolTipString(self.Engine.GetLangString('Reload'))
        self.CardReloadCtrl.Bind(wx.EVT_BUTTON, self.OnCardReload)
        # EndCardRefresh Control
        
        # CardList Popup
        self.CardListPopupMenu = wx.Menu()
        item = wx.MenuItem(self.CardListPopupMenu,ID_POPUP_ADD,self.Engine.GetLangString('Add'))
        item.SetBitmap(self.Engine.GetSkinImage('Todeck'))
        self.Bind(wx.EVT_MENU, self.OnAddCard, item)
        self.CardListPopupMenu.AppendItem(item)
        
        if changes:
            self.hvbox1.Add(self.CardReloadCtrl, 0, wx.ALL | wx.EXPAND, 2)

    def RefreshCardList(self):
        self.MonsterListCtrl.DeleteAllItems()
        self.TriggerListCtrl.DeleteAllItems()
        mo = self.Engine.Deck.GetMonsters()
        mo.sort(lambda x, y: cmp(x.Name, y.Name))
        for c in mo:
            idx = self.MonsterListCtrl.InsertStringItem(self.MonsterListCtrl.GetItemCount(), c.Name)
            self.MonsterListCtrl.SetStringItem(idx, 1, c.CardID)
        sp = self.Engine.Deck.GetTrigger()
        sp.sort(lambda x, y: cmp(x.Name, y.Name))
        for c in sp:
            idx = self.TriggerListCtrl.InsertStringItem(self.TriggerListCtrl.GetItemCount(), c.Name)
            self.TriggerListCtrl.SetStringItem(idx, 1, c.CardID)
        self.MonsterListCtrl.SetColumnWidth(0, 200)
        self.TriggerListCtrl.SetColumnWidth(0, 200)
        self.MonsterHeaderText.SetLabel('Normal Units: ' + str(self.MonsterListCtrl.GetItemCount()))
        self.TriggerHeaderText.SetLabel('Trigger Units: ' + str(self.TriggerListCtrl.GetItemCount()))
        self.DeckCountText.SetLabel('Deck: %s' % str(self.MonsterListCtrl.GetItemCount()+self.TriggerListCtrl.GetItemCount()))
        g0 = self.Engine.Deck.GetG0()
        self.G0CountText.SetLabel('G0: %s' % str(g0))
        g1 = self.Engine.Deck.GetG1()
        self.G1CountText.SetLabel('G1: %s' % str(g1))
        g2 = self.Engine.Deck.GetG2()
        self.G2CountText.SetLabel('G2: %s' % str(g2))
        g3 = self.Engine.Deck.GetG3()
        self.G3CountText.SetLabel('G3: %s' % str(g3))
        
        ht = self.Engine.Deck.CheckHT2()
        self.HTCountText.SetLabel('HT: %s' % str(ht))
        st = self.Engine.Deck.CheckST()
        self.STCountText.SetLabel('ST: %s' % str(st))
        ct = self.Engine.Deck.CheckCT()
        self.CTCountText.SetLabel('CT: %s' % str(ct))
        dt = self.Engine.Deck.CheckDT()
        self.DTCountText.SetLabel('DT: %s' % str(dt))

    def ShowDialog(self, message, title, style, parent=None):
        if parent == None:
            parent = self
        dialog = wx.MessageDialog(parent,message,title,style)
        return dialog.ShowModal()
    
    def OnConnectMenu(self, event):
        tu = self.TriggerListCtrl.GetItemCount()
        nu = self.MonsterListCtrl.GetItemCount()
        if tu !=16 or nu !=34:
            self.ShowDialog('Your deck is not ready!', '', wx.OK | wx.ICON_ERROR, self)
            self.OkButton.Enable()
        else:
            self.Engine.GameFrame = gameframe.GameFrame(self.Engine)
            self.Engine.Game = self.Engine.GameFrame.Game
            self.Engine.Network = network.Network(self.Engine.Game)
            dialog = dialogs.ConnectionDialog(self)
            dialog.ShowModal()

    
    def OnListenMenu(self, event):
        tu = self.TriggerListCtrl.GetItemCount()
        nu = self.MonsterListCtrl.GetItemCount()
        if tu !=16 or nu !=34:
            self.ShowDialog('Your deck is not ready!', '', wx.OK | wx.ICON_ERROR, self)
            self.OkButton.Enable()
        else:
            self.Engine.GameFrame = gameframe.GameFrame(self.Engine)
            self.Engine.Game = self.Engine.GameFrame.Game
            self.Engine.Network = network.Network(self.Engine.Game)
            dialog = dialogs.ListenDialog(self)
            dialog.ShowModal()

    def OnPlayMenu(self, event):
        self.Engine.GameFrame = gameframe.GameFrame(self.Engine)
        self.Engine.Game = self.Engine.GameFrame.Game
        self.Engine.Network = network.Network(self.Engine.Game)
        self.Engine.Game._nick = self.Engine.GetSetting('Nick')
        self.Engine.Game.Shuffle()
        self.Engine.GameFrame.Show()

    def OnRoomsMenu(self, event):
        tu = self.TriggerListCtrl.GetItemCount()
        nu = self.MonsterListCtrl.GetItemCount()
        if tu !=16 or nu !=34:
            self.ShowDialog('Your deck is not ready!', '', wx.OK | wx.ICON_ERROR, self)
            self.OkButton.Enable()
        else:
            self.Engine.GameFrame = gameframe.GameFrame(self.Engine)
            self.Engine.Game = self.Engine.GameFrame.Game
            self.Engine.Network = network.Network(self.Engine.Game)
            dialog = room.Login(self)
            dialog.ShowModal()
            try: dialog.EndTimer()
            except: pass 
    
    def OnAdvancedSearchMenu(self, event):
        self.AdvancedSearchFrame.Show()
    
    def OnCardListItemRClick(self,event):
        self.panel.PopupMenu(self.CardListPopupMenu)
    
    def OnMonsterListItemRClick(self,event):
        self.panel.PopupMenu(self.MonsterListPopupMenu)
    
    def OnTriggerListItemRClick(self,event):
        self.panel.PopupMenu(self.TriggerListPopupMenu)

    def OnSearchInput(self, event):
        input = self.CardSearchCtrl.GetValue()
        if len(input) < 3: #Optimal choice is 3 letters. Less can slow down pc.
            return
        li = self.Engine.FindCardByNameLike(input)
        self.CardListCtrl.DeleteAllItems()
        n=0
        for c in li:
            idx = self.CardListCtrl.InsertStringItem(n,c.Name)
            self.CardListCtrl.SetStringItem(idx, 1, c.CardID)
            n+=1
    
    def OnCardReload(self, event):
        li = self.Engine.GetAllCards()
        self.CardListCtrl.DeleteAllItems()
        n=0
        for c in li:
            idx = self.CardListCtrl.InsertStringItem(n,c.Name)
            self.CardListCtrl.SetStringItem(idx, 1, c.CardID)
            n+=1
        self.CardListCtrl.SetColumnWidth(0, 200)
        self.CardSearchCtrl.SetValue('')

    def OnCardSelected(self, event):
        cardID = self.CardListCtrl.GetItem(event.m_itemIndex, 1).GetText()
        card = self.Engine.FindCardByCardID(cardID)
        self.SelectedFromDeck = cardID
        self.ShowCardInfo(card)

    def OnMonsterCardSelected(self, event):
        cardID = self.MonsterListCtrl.GetItem(event.m_itemIndex, 1).GetText()
        card = self.Engine.FindCardByCardID(cardID)
        self.SelectedFromDeck = cardID
        self.ShowCardInfo(card)
    
    def OnTriggerCardSelected(self, event):
        cardID = self.TriggerListCtrl.GetItem(event.m_itemIndex, 1).GetText()
        card = self.Engine.FindCardByCardID(cardID)
        self.SelectedFromDeck = cardID
        self.ShowCardInfo(card)

    # TO DO: 
    def ShowCardInfo(self,card):
        self.CardNameCtrl.SetLabel(card.Name)
        self.CardImageCtrl.SetBitmap(self.Engine.GetBigCardImage(card))
        desc = card.Class + '/'
        desc +=  card.Nation + '/'
        desc += card.Clan + '/'
        desc +=  card.Race + '\n'
        desc += 'GRADE:' + card.Grade + '\n'
        if card.Skill != '':
            desc += 'SKILL: ' + card.Skill + '\n'
        if card.Class == 'Trigger Unit':
            desc += 'TRIGGER: ' + card.Trigger + '\n'
        desc += 'POWER:' + card.Power + ' CRITICAL:' + card.Critical +' SHIELD:' + card.Shield + '\n'
        if card.Effect != '':
            desc +=  '\n' + card.Effect + '\n'
        if card.Illustrator != '?' and card.Illustrator != '':
            desc += '\n' + 'Illustrator: ' + card.Illustrator
        if card.Text != '?' and card.Text != '':
            desc += '\n' + 'Card text: ' + card.Text + '\n'
        desc += '\n'+card.CardID + '\n'
        self.CardDescriptionCtrl.SetValue(desc)
        self.panel.SendSizeEvent()

    def OnAddCard(self, event):
        if self.SelectedFromDeck == '':
            return
        c = self.Engine.FindCardByCardID(self.SelectedFromDeck)
        cc = self.Engine.Deck.CheckCard(self.SelectedFromDeck)
        ht = self.Engine.Deck.CheckHT(self.SelectedFromDeck)
        #ct = self.Engine.Deck.CheckTrigers(self.SelectedFromDeck)
        if cc < 4:
            if c.Trigger == '+5000 Power, Heal':
                if ht < 4:
                    self.Engine.Deck.Add(c)
            else:
                self.Engine.Deck.Add(c)
        self.RefreshCardList()

    def OnRemoveCard(self, event):
        if self.SelectedFromDeck == '':
            return
        self.Engine.Deck.RemoveCardID(self.SelectedFromDeck)
        self.SelectedFromDeck = ''
        self.RefreshCardList()

    def OnNew(self, event):
        self.Engine.NewDeck()
        self.SelectedFromDeck = ''
        self.RefreshCardList()

    def OnOpen(self, event=None, path=''):
        if path == '':
            dialog = wx.FileDialog(self, self.Engine.GetLangString('Open...'), "", "", "XML Deck files (*.xml)|*.xml", wx.FD_OPEN)
            dialog.SetPath(os.path.join(self.Engine.DecksDirectory,'deck.xml'))
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                return
            else:
                name = dialog.GetFilename()
                dir = dialog.GetDirectory()
                path = os.path.join(dir,name)
                dialog.Destroy()
        self.Engine.OpenDeck(path)
        self.Engine.DeckPath = path
        self.RefreshCardList()

    def OnSave(self, event):
        if self.Engine.DeckPath != '':
            self.Engine.SaveDeck(self.Engine.Deck,self.Engine.DeckPath)
        else:
            self.OnSaveAs(event)

    def OnSaveAs(self, event):
        dialog = wx.FileDialog(self, self.Engine.GetLangString("Save As..."), "", "", "XML Deck files (*.xml)|*.xml", wx.FD_SAVE)
        dialog.SetPath(os.path.join(self.Engine.DecksDirectory,'deck.xml'))
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetFilename()
            dir = dialog.GetDirectory()
            path = os.path.join(dir,name)
            if not path.endswith('.xml'):
                path += '.xml'
            self.Engine.SaveDeck(self.Engine.Deck,path)
            self.Engine.DeckPath = path
        dialog.Destroy()

    def OnPrint(self, event):
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_A4)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        pdd = wx.PrintDialogData(self.printData)
        pdd.SetToPage(1)
        printer = wx.Printer(pdd)
        printout = DeckPrinter(self.Engine.Deck)
        if not printer.Print(self, printout, True):
            pass
        else:
            self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()

    def OnMenuClose(self, event):
        self.Close()

    def OnClose(self, event):
        if self.ShowDialog(self.Engine.GetLangString('Are you sure to quit?'), '?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.ID_YES:
            try: self.Engine.GameFrame.Close()
            except: pass
            self.Engine.SaveSettings({'LastDeckPath':self.Engine.DeckPath})
            sys.exit()

    def OnWeb(self, event=None):
        try:
            webbrowser.open_new_tab('http://vanguard.jproject.xz.lt/')
        except: pass

    def OnSettings(self, event=None):
        dialogs.SettingsDialog(self).ShowModal()
        self.BuildUI(1)

    def OnImportDeck(self, event=None):
        dialogs.ImportDeckDialog(self).ShowModal()

    # Update Check
    def OnUpdate(self, event=None):
        ud = updater.UpdateDialog(self, self.Engine)
        toupdate = updater.CheckUpdate(self.Engine.BaseDirectory)
        ''''if len(toupdate) > 0:
            if self.ShowDialog(self.Engine.GetLangString('An update is avaible, would you like to update now?'),'',wx.YES_NO | wx.ICON_QUESTION | wx.YES_DEFAULT) == wx.ID_YES:
                updater.Update(self.Engine.BaseDirectory,toupdate)
                self.ShowDialog(self.Engine.GetLangString('Now you can restart the application.'),'',wx.OK | wx.ICON_INFORMATION)
                sys.exit()
        else:
            self.ShowDialog(self.Engine.GetLangString('No update needed.'), '', wx.OK | wx.ICON_INFORMATION)'''

    def OnImagesUpdate(self, event=None):
        '''Images Updating'''
        updater.ImagesUpdateDialog(self, self.Engine)

    # Mostra la finestra About
    def OnAbout(self, event = None):
        info = wx.AboutDialogInfo()
        info.SetName(self.Engine.GetName())
        info.SetWebSite('http://code.google.com/p/cardfight-vanguard-vds/')
        info.SetWebSite('http://vanguard.jproject.xz.lt')
        info.SetVersion(self.Engine.GetVersion())
        info.SetDescription('CRAY ONLINE is a multi-platform Cardfight!! Vanguard Dueling and Deck Building application written in Python and using wxPython as GUI Library.')
        info.SetLicense("""CRAY ONLINE is free software; you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) any later version.

CRAY ONLINE is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. You should have received a copy of 
the GNU General Public License along with J_PROJECT; if not, write to 
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA""")
        info.AddDeveloper("J_BYYX (code, database, images), FelGrand (database)")
        info.AddArtist("J_BYYX, Jovan Dmitrović")
        wx.AboutBox(info)