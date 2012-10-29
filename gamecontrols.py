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

import wx, random, sys, wx.html, wx.richtext, os, webbrowser
import network, engine, packets, keyhandler, dialogs
from deck import Deck

POS_FIELD = 0
POS_HAND = 1
POS_DECK = 2
POS_GRAVE = 3
POS_DAMAGE = 4
POS_RFG = 6
POS_OPP_FIELD = 7
POS_OPP_HAND = 8
POS_OPP_GRAVE = 9
POS_OPP_RFG = 10
POS_OPP_DECK = 11
POS_OPP_DAMAGE = 12

FACE_DOWN = 0
FACE_UP = 1

CARD_VERTICAL = 0
CARD_HORIZONTAL = 1

CHAT_GAME = 0
CHAT_PLAYER = 1
CHAT_OPPONENT = 2
CHAT_CONSOLE = 3

LOOK_DECK_YES = 0
LOOK_DECK_NO = 1
LOOK_GRAVE_YES = 2
LOOK_GRAVE_NO = 3
LOOK_DAMAGE_YES = 19
LOOK_DAMAGE_NO = 20
LOOK_RFG_YES = 4
LOOK_RFG_NO = 5
LOOK_OPPONENT_GRAVE_YES = 8
LOOK_OPPONENT_GRAVE_NO = 9
LOOK_OPPONENT_DAMAGE_YES = 21
LOOK_OPPONENT_DAMAGE_NO = 22
LOOK_OPPONENT_RFG_YES = 10
LOOK_OPPONENT_RFG_NO = 11

ACTION_DISCARDTOP = 0
ACTION_REVEALTOP = 1
ACTION_CHECKTOP = 2
ACTION_SCTOP = 3


class GameObject(wx.Window):
    def __init__(self, parent, pos, texture, size=-1):
        self._texture = texture
        if size == -1:
            size = (self._texture.GetWidth(), self._texture.GetHeight())
        wx.Window.__init__(self, parent=parent, id=-1, pos=pos, size=size)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)

    def SetTexture(self, texture):
        self._texture = texture
        self.Refresh()
        

class ConsoleCtrl(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, pos=(710,680), size=(300,-1), style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnPressEnter)

    def OnPressEnter(self, event):
        if len(self.GetValue()) < 1:
            return
        m = self.GetValue()
        self.SetValue('')
        self.Parent.ProcessMessage(m)

class GamePanel(wx.Panel):
    def __init__(self, parent, engine):
        wx.Panel.__init__(self, parent)
        self._engine = engine
        self._noneparent = wx.Panel(self,-1,(0,0),(0,0))
        self._noneparent.Hide()
        self._nick = ''
        self._opponentnick = ''
        self._origdeck = None
        self._field = []
        self._deck = []
        self._grave = []
        self._damage = []
        self._rfg = []
        self._hand = []
        self._consolectrl = ConsoleCtrl(self)
        # Menu
        self._menu = wx.MenuBar()
        
        self._menufile = wx.Menu()
        item = wx.MenuItem(self._menufile,-1,self._engine.GetLangString('Game Reset'))
        item.SetBitmap(self._engine.GetSkinImage('Reload'))
        self.Parent.Bind(wx.EVT_MENU, self.OnGamePopupResetGame, item)
        self._menufile.AppendItem(item)
        item = wx.MenuItem(self._menufile,-1,self._engine.GetLangString('Close'))
        item.SetBitmap(self._engine.GetSkinImage('Close'))
        self.Parent.Bind(wx.EVT_MENU, self.Parent.OnExit, item)
        self._menufile.AppendItem(item)
        self._menu.Append(self._menufile, self._engine.GetLangString('File'))
        
        self._menuactions = wx.Menu()
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Drop Zone'))
        item.SetBitmap(self._engine.GetSkinImage('DropIco'))
        self.Parent.Bind(wx.EVT_MENU, self.OnGraveLClick, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Damage Zone'))
        item.SetBitmap(self._engine.GetSkinImage('DamageIco'))
        self.Parent.Bind(wx.EVT_MENU, self.OnDamageLClick, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Soul'))
        item.SetBitmap(self._engine.GetSkinImage('SoulIco'))
        self.Parent.Bind(wx.EVT_MENU, self.OnGamePopupRFG, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Search Deck'))
        self.Parent.Bind(wx.EVT_MENU, self.OnPopupDeckSearch, item)
        item.SetBitmap(self._engine.GetSkinImage('SearchDeck'))
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString("Opponent's Drop Zone"))
        item.SetBitmap(self._engine.GetSkinImage('DropIco'))
        self.Parent.Bind(wx.EVT_MENU, self.OnOpponentGraveLClick, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString("Opponent's Soul"))
        item.SetBitmap(self._engine.GetSkinImage('SoulIco'))
        self.Parent.Bind(wx.EVT_MENU, self.OnGamePopupOpponentRFG, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Roll a D6'))
        item.SetBitmap(self._engine.GetSkinImage('Luck'))
        self.Parent.Bind(wx.EVT_MENU, self.RollD6, item)
        self._menuactions.AppendItem(item)
        item = wx.MenuItem(self._menuactions,-1,self._engine.GetLangString('Flip a Coin'))
        item.SetBitmap(self._engine.GetSkinImage('Luck'))
        self.Parent.Bind(wx.EVT_MENU, self.FlipCoin, item)
        self._menuactions.AppendItem(item)
        self._menu.Append(self._menuactions, self._engine.GetLangString('Actions'))
        
        self._menuhelp = wx.Menu()
        item = wx.MenuItem(self._menuhelp,-1,self._engine.GetLangString('Preferences'))
        item.SetBitmap(self._engine.GetSkinImage('Preferences'))
        self.Parent.Bind(wx.EVT_MENU, self.OnMenuSettings, item)
        self._menuhelp.AppendItem(item)
        item = wx.MenuItem(self._menuhelp,-1,self._engine.GetLangString('Smiles'))
        item.SetBitmap(self._engine.GetSkinImage('Smile'))
        self.Parent.Bind(wx.EVT_MENU, self.OnMenuSmiles, item)
        self._menuhelp.AppendItem(item)
        #item = wx.MenuItem(self._menuhelp,-1,self._engine.GetLangString('J_PROJECT.Web'))
       # item.SetBitmap(self._engine.GetSkinImage('Web'))
        #self.Parent.Bind(wx.EVT_MENU, self.OnMenuWeb, item)
       # self._menuhelp.AppendItem(item)
        #item = wx.MenuItem(self._menuhelp,-1,self._engine.GetLangString('About'))
        #item.SetBitmap(self._engine.GetSkinImage('About'))
        #self.Parent.Bind(wx.EVT_MENU, self.OnMenuAbout, item)
        #self._menuhelp.AppendItem(item)
        self._menu.Append(self._menuhelp, self._engine.GetLangString('Help'))
        self.Parent.SetMenuBar(self._menu)

        # Message
        #self._messagectrl = wx.html.HtmlWindow(self, pos=(703,370), size=(154,330))
        #self._messagectrl.SetFonts('Tahoma','Tahoma',[8,8,8,8,8,8,8])
        #self._messagetext = ''
        self._messagectrl = wx.richtext.RichTextCtrl(self, pos=(710,510), size=(300,170), style=wx.richtext.RE_MULTILINE|wx.richtext.RE_READONLY|wx.NO_BORDER)
        self._messagectrl.BeginFont(wx.Font(pointSize=8,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        # Smiles
        #self._smiles = ['angel','angry','asd','baby','bana','bhua','biggrin','biglaugha','coffee','censored','byebye','confused','deer','disgust','eek','elf1','elf2','elf3','flamed1','flamed2','freddy','frown','frusta','ghgh','girl','goccia','guns','hammer','hippy','ghgh2','rofl','glass','blush','king','kiss','laugh','lingua','lol','lolly','look','love','mad','metal','ass','nono','no','o','oink','omg','ahsi','laughs','up','down','puke','rain','read','woot','rofl','roll','rolly','rosik','rotfl','sad','saint','sbang','sbav','scratch','ass2','ser','shocked','sigh','silly','smile','smoke','smokin','sheep','spiny','study','sure','talk','tongue','sad2','ueee','wave','woot','yuppi','zzz','afraid']
        self._smiles = ['angel','baby','X','S','D','deer','disgust','down','elf','flame','(','girl','goccia','hippy','king','kiss','laughs','lingua','look','love','mad','metal','no','nu','O','oink','omg','rain','sad','saint','I',')','sheep','shocked','sigh','silly','smoke','smokin','sure','P','up','wave','zzz']
        # Console
        self._consolectrl.SetFont(wx.Font(pointSize=8,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        self._consolectrl.SetFocus()
        self._gravelistctrl = GraveListControl(self)
        self._damagelistctrl = DamageListControl(self)
        self._decklistctrl = DeckListControl(self)
        self._rfglistctrl = RFGListControl(self)
        self._opponentgravelistctrl = OpponentGraveListControl(self)
        self._opponentdamagelistctrl = OpponentDamageListControl(self)
        self._opponentdecklistctrl = OpponentDeckListControl(self)
        self._opponentrfglistctrl = OpponentRFGListControl(self)
        self._cmdhandlers = {}
        self._cardsize=wx.Size(62,88)
        self.CommandHandlers()
        self._opponentorigdeck = None
        self._opponentfield = []
        self._opponentdeck = []
        self._opponentgrave = []
        self._opponentdamage = []
        self._opponentrfg = []
        self._opponenthand = []
        self._notes = []
        self._serial = 0
        self._opponentserial = 0
        # Field
        self._fieldctrl = FieldControl(self)
        self._fieldctrl.Bind(wx.EVT_RIGHT_UP, self.OnFieldLeftUp)
        # OpponentField
        self._opponentfieldctrl = OpponentFieldControl(self)
        # Deck
        self._deckctrl = DeckControl(self._fieldctrl, (619,206), self._engine.GetSkinImage('Deck'))
        self._deckctrl.Bind(wx.EVT_LEFT_DCLICK, self.OnDeckDClick)
        self._deckctrl.Bind(wx.EVT_RIGHT_UP, self.OnDeckRClick)
        self._deckcounttext = wx.StaticText(self._fieldctrl, -1, '0', pos=(640,230))
        # Grave
        self._gravectrl = GraveControl(self._fieldctrl, (619,109), self._engine.GetSkinImage('Drop'), self)
        self._gravectrl.Bind(wx.EVT_LEFT_UP, self.OnGraveLClick)
        self._gravectrl.UpdateCardTooltip(self._grave)
        # Damage
        self._damagectrl = DamageControl(self._fieldctrl, (20,30), self._engine.GetSkinImage('Damage'), self)
        self._damagectrl.Bind(wx.EVT_LEFT_UP, self.OnDamageLClick)
        self._damagectrl.UpdateCardTooltip(self._damage)
        # RFG
        self._rfgctrl = RFGControl(self._fieldctrl, (304,20), self._engine.GetSkinImage('Soul'), self)
        self._rfgctrl.Bind(wx.EVT_LEFT_UP, self.OnGamePopupRFG)
        self._rfgctrl.UpdateCardTooltip(self._rfg)
        # OpponentGrave
        self._opponentgravectrl = OpponentGraveControl(self._opponentfieldctrl, (20,102), self._engine.GetSkinImage('Drop'), self)
        self._opponentgravectrl.Bind(wx.EVT_LEFT_UP, self.OnOpponentGraveLClick)
        self._opponentgravectrl.UpdateCardTooltip(self._opponentgrave)
        # OpponentDamage
        self._opponentdamagectrl = OpponentDamageControl(self._opponentfieldctrl, (618,170), self._engine.GetSkinImage('Damage'), self)
        self._opponentdamagectrl.Bind(wx.EVT_LEFT_UP, self.OnOpponentDamageLClick)
        self._opponentdamagectrl.UpdateCardTooltip(self._opponentdamage)
        # OpponentRFG
        self._opponentrfgctrl = OpponentRFGControl(self._opponentfieldctrl, (304,250), self._engine.GetSkinImage('Soul'), self)
        self._opponentrfgctrl.Bind(wx.EVT_LEFT_UP, self.OnGamePopupOpponentRFG)
        self._opponentrfgctrl.UpdateCardTooltip(self._opponentrfg)
        # OpponentDeck
        self._opponentdeckctrl = OpponentDeckControl(self._opponentfieldctrl, (20,4), self._engine.GetSkinImage('Deck'))
        # Hand
        self._handctrl = HandControl(self)
        self.RefreshHand()
        # OpponentHand
        self._opponenthandctrl = OpponentHandControl(self)
        self.RefreshOpponentHand()
        # Score
        self._scorectrl = ScoreControl(self)
        # Phases
        self._drawphasectrl = DrawPhaseControl(self)
        self._standbyphasectrl = StandbyPhaseControl(self)
        self._mainphase1ctrl = MainPhase1Control(self)
        self._battlephasectrl = BattlePhaseControl(self)
        self._mainphase2ctrl = MainPhase2Control(self)
        self._endphasectrl = EndPhaseControl(self)
        # Menu 2
        self._hand_monster_menu = wx.Menu()
        item = wx.MenuItem(self._hand_monster_menu, -1, self._engine.GetLangString('Call/Ride'))
        item.SetBitmap(self._engine.GetSkinImage('Call'))
        self._hand_monster_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnHandMonsterSummon, item)
        item = wx.MenuItem(self._hand_monster_menu, -1, self._engine.GetLangString('Guard'))
        item.SetBitmap(self._engine.GetSkinImage('Guard'))
        self._hand_monster_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnHandMonsterPosition, item)
        item = wx.MenuItem(self._hand_monster_menu, -1, self._engine.GetLangString('Set'))
        item.SetBitmap(self._engine.GetSkinImage('Setst'))
        self._hand_monster_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnHandMTPosition, item)
        # Menu 3
        self._game_menu = wx.Menu()
        #item = wx.MenuItem(self._game_menu, -1, 'New Note')
        #self._game_menu.AppendItem(item)
        #self.Bind(wx.EVT_MENU, self.OnNewNote, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Drop Zone'))
        item.SetBitmap(self._engine.GetSkinImage('DropIco'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnGraveLClick, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Damage Zone'))
        item.SetBitmap(self._engine.GetSkinImage('DamageIco'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnGraveLClick, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Soul'))
        item.SetBitmap(self._engine.GetSkinImage('SoulIco'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnGamePopupRFG, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Search Deck'))
        item.SetBitmap(self._engine.GetSkinImage('SearchDeck'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckSearch, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString("Opponent's Soul"))
        item.SetBitmap(self._engine.GetSkinImage('SoulIco'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnGamePopupOpponentRFG, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Roll a d6'))
        item.SetBitmap(self._engine.GetSkinImage('Luck'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupRollD6, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Flip a Coin'))
        item.SetBitmap(self._engine.GetSkinImage('Luck'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupFlipCoin, item)
        item = wx.MenuItem(self._game_menu, -1, self._engine.GetLangString('Reset Game'))
        item.SetBitmap(self._engine.GetSkinImage('Reload'))
        self._game_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnGamePopupResetGame, item)
        # Card Visualization
        self._cardimagectrl = wx.StaticBitmap(self, -1, size=(165,240), pos=(780,10))
        self._carddescriptionctrl = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP, size=(300,260), pos=(710,260))
        # Hotkeys
        self._keyhandler = keyhandler.KeyHandler()
        self._hotkeys = {}
        self.LoadHotkeys()
        self._consolectrl.Bind(wx.EVT_KILL_FOCUS, self.OnConsoleLostFocus)
        self._consolectrl.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self._smilesdialog = dialogs.SmilesDialog(self.Parent, self._engine, self._smiles)
        #
        self.UseDeck(self._engine.Deck)

    # Apre il dialogo delle impostazioni
    def OnMenuSettings(self, event=None):
        dialogs.SettingsDialog(self.Parent,self._engine.Frame).ShowModal()

    def OnMenuSmiles(self, event=None):
        if not self._smilesdialog.IsShown():
            self._smilesdialog.Show()

    # Apre il browser predefinito alla homepage di CFVVDS
    def OnMenuWeb(self, event=None):
        try:
            webbrowser.open_new_tab('http://vanguard.jprject.xz.lt')
        except:
            pass

    

    def OnConsoleLostFocus(self, event):
        if self.IsShown() and self.IsShownOnScreen() and not self._decklistctrl.IsActive() and not self._opponentdecklistctrl.IsActive() and not self._gravelistctrl.IsActive() and not self._damagelistctrl.IsActive() and not self._opponentgravelistctrl.IsActive() and not self._opponentdamagelistctrl.IsActive() and not self._rfglistctrl.IsActive() and not self._opponentrfglistctrl.IsActive() and not self._smilesdialog.IsActive():
            self._consolectrl.SetFocus()

    def Pass(self):
        pass

    def GetHotkeyHandler(self, name):
        if self._hotkeys.has_key(name):
            return self._hotkeys[name]
        else:
            return self.Pass

    def LoadHotkeys(self):
        self._hotkeys['Shuffle'] = self.Shuffle
        self._hotkeys['RollD6'] = self.RollD6
        self._hotkeys['Next Phase'] = self.NextPhase
        self._hotkeys['End Turn'] = self.EndTurn
        self._hotkeys['Draw'] = self.OnDeckDraw
        self._hotkeys['Draw and Show'] = self.OnDeckDrawShow
        self._hotkeys['Flip Coin'] = self.FlipCoin
        self._hotkeys['Reset Game'] = self.ResetGame

        hotkeysdict = self._engine.GetAllHotkeys()
        for handler, code in hotkeysdict.items():
            if not code == '':
                self._keyhandler.AddHandler(code, self.GetHotkeyHandler(handler))

    def OnKeyUp(self, event):
        self._keyhandler.OnKeyEvent(event.GetKeyCode(), event.GetModifiers())
        self._consolectrl.SetFocus()

    def ClearPhases(self):
        self._standbyphasectrl._sel = False
        self._standbyphasectrl.Hide()
        self._standbyphasectrl.Show()
        self._drawphasectrl._sel = False
        self._drawphasectrl.Hide()
        self._drawphasectrl.Show()
        self._mainphase1ctrl._sel = False
        self._mainphase1ctrl.Hide()
        self._mainphase1ctrl.Show()
        self._battlephasectrl._sel = False
        self._battlephasectrl.Hide()
        self._battlephasectrl.Show()
        self._mainphase2ctrl._sel = False
        self._mainphase2ctrl.Hide()
        self._mainphase2ctrl.Show()
        self._endphasectrl._sel = False
        self._endphasectrl.Hide()
        self._endphasectrl.Show()
    
    def OnFieldLeftUp(self, event):
        self.PopupMenu(self._game_menu)

    def OnGamePopupRFG(self, event=None):
        if self._rfglistctrl.IsShown():
            self._rfglistctrl.Hide()
            self.WriteLookPacket(LOOK_RFG_NO)
            self.WriteGameMessage(self._engine.GetLangString("end looking at his Soul."), CHAT_PLAYER)
        else:
            self._rfglistctrl.Show()
            self.WriteLookPacket(LOOK_RFG_YES)
            self.WriteGameMessage(self._engine.GetLangString("is looking at his Soul"), CHAT_PLAYER)

    def OnGamePopupOpponentRFG(self, event=None):
        if self._opponentrfglistctrl.IsShown():
            self._opponentrfglistctrl.Hide()
            self.WriteLookPacket(LOOK_OPPONENT_RFG_NO)
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Soul."), CHAT_PLAYER)
        else:
            self._opponentrfglistctrl.Show()
            self.WriteLookPacket(LOOK_OPPONENT_RFG_YES)
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Soul."), CHAT_PLAYER)

    def OnGamePopupResetGame(self, event=None):
        self.ResetGame()
    
    def GetOrigDeck(self):
        return self._origdeck

    def ClearGame(self):
        self._deck = []
        self._hand = []
        self._grave = []
        self._damage = []
        self._rfg = []
        self._opponentdeck = []
        self._opponenthand = []
        self._opponentgrave = []
        self._opponentdamage = []
        self._opponentrfg = []

    def UseDeck(self, deck):
        self._origdeck = deck
        self.ClearGame()
        deck = self._origdeck.GetGameCards()
        for c in deck:
            g = CardControl(self._decklistctrl, c.Duplicate(), self._engine, self, self.NewCardSerial(), cpos=POS_DECK)
            self.AddCardToBottom(self._deck, g)
        self.RefreshDeck()
        self.RefreshHand()
        self.RefreshRFG()
        self.RefreshGrave()
        self.RefreshDamage()
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.RefreshOpponentRFG()
        self.RefreshOpponentGrave()
        self.RefreshOpponentDamage()
    
    def OnCardTarget(self, event=None):
        card = self._currentcard
        card.Target()
        card.Hide()
        card.Show()
        self.WriteTargetPacket(0, card.GetSerial())

    def OnCardAddCounter(self, event=None):
        card = self._currentcard
        card.AddCounters(1)
        self.WriteGameMessage(' %s %s' % (self._engine.GetLangString("add a counter to"), card.GetCardName()), CHAT_PLAYER)
        self.WriteCardCounterPacket(card.GetSerial(), 0, 1)

    def OnCardRemoveCounter(self, event=None):
        card = self._currentcard
        card.RemoveCounters(1)
        self.WriteGameMessage(' %s %s' % (self._engine.GetLangString("removed a counter from"), card.GetCardName()), CHAT_PLAYER)
        self.WriteCardCounterPacket(card.GetSerial(), 1, 1)
    
    def OnCardChangeControl(self, event=None):
        card = self._currentcard
        self.WriteGameMessage(' %s %s' % (self._engine.GetLangString("changed control..."), card.GetCardName()), CHAT_PLAYER)
        self.WriteChangeControlPacket(card.GetSerial(), 1, 1)

    def OnOpponentCardTarget(self, event=None):
        card = self._opponentcurrentcard
        card.Target()
        card.Hide()
        card.Show()
        self.WriteTargetPacket(1, card.GetSerial())

    def OnCardPopup(self, c):
        pos = c.GetCardPosition()
        if pos == POS_FIELD:
            self.OnCardFieldPopup(c)
        elif pos == POS_HAND:
            self.OnCardHandPopup(c)
        elif pos == POS_GRAVE:
            self.OnCardGravePopup(c)
        elif pos == POS_DAMAGE:
            self.OnCardDamagePopup(c)
        elif pos == POS_RFG:
            self.OnCardRFGPopup(c)
        elif pos == POS_DECK:
            self.OnCardDeckPopup(c)
    
    def OnCardDClick(self, c):
        pos = c.GetCardPosition()
        if pos == POS_FIELD:
            self.OnCardFieldDClick(c)
        else:
            return

    def OnCardHandPopup(self, c):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Hand Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('ShHand'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardShuffleHand, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Drop Zone'))
        item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToGrave, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Damage Zone'))
        item.SetBitmap(self._engine.GetSkinImage('ToDamage'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToDamage, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
        item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToRFG, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck/Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToTopDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToBottomDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck Hidden'))
        item.SetBitmap(self._engine.GetSkinImage('TotopdeckH'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToTopDeckH, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck Hidden'))
        item.SetBitmap(self._engine.GetSkinImage('TobottomdeckH'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardHandToBottomDeckH, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Target'))
        item.SetBitmap(self._engine.GetSkinImage('Targetsm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardTarget, item)
        self._currentcard = c
        c.PopupMenu(menu)

    def OnCardHandToGrave(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_GRAVE)
        self.MoveCard(self._hand, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        self.RefreshHand()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_PLAYER)
    
    def OnCardHandToDamage(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DAMAGE)
        self.MoveCard(self._hand, self._damage, card)
        card.SetCardState(POS_DAMAGE)
        card.Reparent(self._damagelistctrl)
        self.RefreshDamage()
        self.RefreshHand()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName()), CHAT_PLAYER)  
    

    def OnCardHandToRFG(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_RFG)
        self.MoveCard(self._hand, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_PLAYER)

    def OnCardHandToDeckShuffle(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 2) # Deck-Shuffle
        self.MoveCard(self._hand, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.Shuffle()
        #self.RefreshDeck()
        self.RefreshHand()
 
    def OnCardShuffleHand(self, arg=None):
        self.ShuffleHand()
        self.RefreshHand()

    
    def OnCardHandToTopDeck(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 1) # Top-Deck
        self.MoveCardToTop(self._hand, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardHandToBottomDeck(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 0) # Bottom-Deck
        self.MoveCardToBottom(self._hand, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.') + ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
    
    
    def OnCardHandToTopDeckH(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 3) # Top-Deck
        self.MoveCardToTop(self._hand, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('sent card ')  + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardHandToBottomDeckH(self, arg=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 4) # Bottom-Deck
        self.MoveCardToBottom(self._hand, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('sent card ') + self._engine.GetLangString(' to the bottom of his deck.') + ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        
    def OnHandMTActivate(self, arg=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 0, x, y)
        card.SetCardState(POS_FIELD)
        self.MoveCard(self._hand, self._field, card)
        card.Reparent(self._fieldctrl)
        self.RefreshHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_PLAYER)
    
    def OnHandMTPosition(self, arg=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 1, x, y)
        card.SetCardState(POS_FIELD, face=FACE_DOWN)
        self.MoveCard(self._hand, self._field, card)
        card.Reparent(self._fieldctrl)
        self.RefreshHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('place card on the field.'), CHAT_PLAYER)
    
    def OnHandMonsterSummon(self, arg=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 0, x, y)
        card.SetCardState(POS_FIELD)
        self.MoveCard(self._hand, self._field, card)
        card.Reparent(self._fieldctrl)
        self.RefreshHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_PLAYER)
    
    def OnHandMonsterPosition(self, arg=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 2, x, y)
        card.SetCardState(POS_FIELD, CARD_HORIZONTAL)
        self.MoveCard(self._hand, self._field, card)
        card.Reparent(self._fieldctrl)
        self.RefreshHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('guards with ')  + card.GetCardName() +'. ' +  card.GetCardShield(), CHAT_PLAYER)

    def OnOpponentCardHandToGrave(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponenthand, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.RefreshOpponentHand()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_OPPONENT)
    
    def OnOpponentCardHandToDamage(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponenthand, self._opponentdamage, card)
        card.SetCardState(POS_OPP_DAMAGE)
        card.Reparent(self._opponentdamagelistctrl)
        self.RefreshOpponentDamage()
        self.RefreshOpponentHand()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName()), CHAT_OPPONENT)

    def OnOpponentCardHandToRFG(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponenthand, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_OPPONENT)

    def OnOpponentCardHandToDeckShuffle(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponenthand, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardHandToTopDeck(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCardToTop(self._opponenthand, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardHandToBottomDeck(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponenthand, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
    
    def OnOpponentCardHandToTopDeckH(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCardToTop(self._opponenthand, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent card') + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardHandToBottomDeckH(self, arg=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponenthand, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('sent card') + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
    
    def OnOpponentCardHandToBottomDeckH2(self, arg=None):
        card = self._opponentdeck[0]
        self.MoveCardToBottom(self._opponentdeck, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('Sent top card to the bottom.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        
    def OnOpponentHandMTActivate(self, arg=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        card.SetCardState(POS_OPP_FIELD)
        self.MoveCard(self._opponenthand, self._opponentfield, card)
        card.Reparent(self._opponentfieldctrl)
        self.RefreshOpponentHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_OPPONENT)
    
    def OnOpponentHandMTPosition(self, arg=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        card.SetCardState(POS_OPP_FIELD, face=FACE_DOWN)
        self.MoveCard(self._opponenthand, self._opponentfield, card)
        card.Reparent(self._opponentfieldctrl)
        self.RefreshOpponentHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('placed card on the field.'), CHAT_OPPONENT)
    
    def OnOpponentHandMonsterSummon(self, arg=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        card.SetCardState(POS_OPP_FIELD)
        self.MoveCard(self._opponenthand, self._opponentfield, card)
        card.Reparent(self._opponentfieldctrl)
        self.RefreshOpponentHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_OPPONENT)
    
    def OnOpponentHandMonsterPosition(self, arg=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        card.SetCardState(POS_OPP_FIELD, CARD_HORIZONTAL)
        self.MoveCard(self._opponenthand, self._opponentfield, card)
        card.Reparent(self._opponentfieldctrl)
        self.RefreshOpponentHand()
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('guards with ') + card.GetCardName() + '. ' + card.GetCardShield(), CHAT_OPPONENT)

    def OnCardFieldPopup(self, c):
        menu = wx.Menu()
        if c.IsMonster():
            if c.IsVertical():
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Attack'))
                item.SetBitmap(self._engine.GetSkinImage('Attack'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldAttack, item)
                '''item = wx.MenuItem(menu, -1, self._engine.GetLangString('Flip/Horiz'))
                item.SetBitmap(self._engine.GetSkinImage('Flip'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldFlipHorizontal, item)
            else:
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Flip/Vert'))
                item.SetBitmap(self._engine.GetSkinImage('Flip'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldFlipVertical, item)'''
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Drop Zone'))
            item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToGrave, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
            item.SetBitmap(self._engine.GetSkinImage('Tohand'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToHand, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
            item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToRFG, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Damage Zone'))
            item.SetBitmap(self._engine.GetSkinImage('ToDamage'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToDamage, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
            item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToTopDeck, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
            item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToBottomDeck, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck-Shuffle'))
            item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToDeckShuffle, item)
            '''if c.IsVertical():
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Horizontal'))
                item.SetBitmap(self._engine.GetSkinImage('Horiz'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldHorizontal, item)
            else:
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Vertical'))
                item.SetBitmap(self._engine.GetSkinImage('Vert'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldVertical, item)'''
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('Flip'))
            item.SetBitmap(self._engine.GetSkinImage('Setst'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldFlip, item)
        else:
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('Activate'))
            item.SetBitmap(self._engine.GetSkinImage('Activate'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldFlip, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Drop Zone'))
            item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToGrave, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
            item.SetBitmap(self._engine.GetSkinImage('Tohand'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToHand, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
            item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToRFG, item)
            if c.IsVertical():
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Horizontal'))
                item.SetBitmap(self._engine.GetSkinImage('Horiz'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldHorizontal, item)
            else:
                item = wx.MenuItem(menu, -1, self._engine.GetLangString('Vertical'))
                item.SetBitmap(self._engine.GetSkinImage('Vert'))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnCardFieldVertical, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
            item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToTopDeck, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
            item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToBottomDeck, item)
            item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck-Shuffle'))
            item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
            menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnCardFieldToDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Target'))
        item.SetBitmap(self._engine.GetSkinImage('Targetsm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardTarget, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Add Counter'))
        item.SetBitmap(self._engine.GetSkinImage('Counter'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardAddCounter, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Remove Counter'))
        item.SetBitmap(self._engine.GetSkinImage('Counterm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRemoveCounter, item)
       # Not working.
       # item = wx.MenuItem(menu, -1, self._engine.GetLangString('Change Control'))
       # item.SetBitmap(self._engine.GetSkinImage('Counterm'))
       # menu.AppendItem(item)
       # self.Bind(wx.EVT_MENU, self.OnCardChangeControl, item)
        self._currentcard = c
        self.PopupMenu(menu)
        
        
    def OnCardFieldDClick(self, c):
        self._currentcard = c
        if c.IsVertical():
            self.OnCardFieldHorizontal()
        else:
            self.OnCardFieldVertical()


    def OnCardFieldAttack(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 3)
        card.Horizontal()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteChatPacket(self._engine.GetLangString('Attack with ') + card.GetCardName())
        self.WriteChatMessage(self._engine.GetLangString('Attack with ')+card.GetCardName(), CHAT_PLAYER)

    def OnCardFieldFlip(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 0)
        if card.IsFaceUp():
            card.FaceDown()
            self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face down.'), CHAT_PLAYER)
        else:
            card.FaceUp()
            self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face up.'), CHAT_PLAYER)
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
    
    def OnCardFieldActivate(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 0)
        if card.IsFaceUp():
            card.FaceDown()
            self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face down.'), CHAT_PLAYER)
        else:
            card.FaceUp()
            self.WriteGameMessage(self._engine.GetLangString('activated ') + card.GetCardName() + self._engine.GetLangString(' .'), CHAT_PLAYER)
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()

    def OnCardFieldFlipHorizontal(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 1)
        card.FaceDown()
        card.Horizontal()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face-down horizontal.'), CHAT_PLAYER)

    def OnCardFieldFlipVertical(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 2)
        card.FaceUp()
        card.Vertical()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face-up vertical.'), CHAT_PLAYER)

    def OnCardFieldHorizontal(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 3)
        card.Horizontal()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('turned ') + card.GetCardName() + self._engine.GetLangString(' horizontal.'), CHAT_PLAYER)

    def OnCardFieldVertical(self, event=None):
        card = self._currentcard
        self.WriteFlipCardPacket(card, 4)
        card.Vertical()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('turned ') + card.GetCardName() + self._engine.GetLangString(' vertical.'), CHAT_PLAYER)

    def OnCardFieldToGrave(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_GRAVE)
        self.MoveCard(self._field, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_PLAYER)
        
    def OnCardFieldToDamage(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DAMAGE)
        self.MoveCard(self._field, self._damage, card)
        card.SetCardState(POS_DAMAGE)
        card.Reparent(self._damagelistctrl)
        self.RefreshDamage()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his graveyard.', card.GetCardName()), CHAT_PLAYER)
    
    def OnCardFieldToRFG(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_RFG)
        self.MoveCard(self._field, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_PLAYER)

    def OnCardFieldToTopDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 1)
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)+1) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to the top of his deck.')+ ' ' + str(len(self._deck)+1) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.MoveCardToTop(self._field, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()

    def OnCardFieldToBottomDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 0)
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._deck)+1) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to the bottom of his deck.')+ ' ' + str(len(self._deck)+1) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.MoveCardToBottom(self._field, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()

    def OnCardFieldToDeckShuffle(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 2)
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.MoveCard(self._field, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.Shuffle()
        #self.RefreshDeck()

    def OnCardFieldToHand(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_HAND)
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to his hand.'), CHAT_PLAYER)
        self.MoveCardToBottom(self._field, self._hand, card)
        card.SetCardState(POS_HAND)
        card.Reparent(self._handctrl)
        self.RefreshHand()

    # Opponent Field
    def OnOpponentCardFieldFlip(self, event=None):
        card = self._opponentcurrentcard
        if card.IsFaceUp():
            card.FaceDown()
            self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face down.'), CHAT_OPPONENT)
        else:
            card.FaceUp()
            self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face up.'), CHAT_OPPONENT)
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()

    def OnOpponentCardFieldFlipHorizontal(self, event=None):
        card = self._opponentcurrentcard
        card.FaceDown()
        card.Horizontal()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face-down horizontal.'), CHAT_OPPONENT)

    def OnOpponentCardFieldFlipVertical(self, event=None):
        card = self._opponentcurrentcard
        card.FaceUp()
        card.Vertical()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('flipped ') + card.GetCardName() + self._engine.GetLangString(' face-up vertical.'), CHAT_OPPONENT)

    def OnOpponentCardFieldHorizontal(self, event=None):
        card = self._opponentcurrentcard
        card.Horizontal()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('turned ') + card.GetCardName() + self._engine.GetLangString(' horizontal.'), CHAT_OPPONENT)

    def OnOpponentCardFieldVertical(self, event=None):
        card = self._opponentcurrentcard
        card.Vertical()
        card.RefreshTexture()
        card.SetPosition(self.PositionCard(card, card.GetPositionTuple()[0], card.GetPositionTuple()[1]))
        card.Hide()
        card.Show()
        self.WriteGameMessage(self._engine.GetLangString('turned ') + card.GetCardName() + self._engine.GetLangString(' vertical.'), CHAT_OPPONENT)
    
    
    def OnOpponentCardFieldToGrave(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentfield, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_OPPONENT)
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)

    def OnOpponentCardFieldToDamage(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentfield, self._opponentdamage, card)
        card.SetCardState(POS_OPP_DAMAGE)
        card.Reparent(self._opponentdamagelistctrl)
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his damage.', card.GetCardName()), CHAT_OPPONENT)

    def OnOpponentCardFieldToRFG(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentfield, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_OPPONENT)

    def OnOpponentCardFieldToTopDeck(self, event=None):
        card = self._opponentcurrentcard
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to the top of his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        self.MoveCardToTop(self._opponentfield, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()

    def OnOpponentCardFieldToBottomDeck(self, event=None):
        card = self._opponentcurrentcard
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        self.MoveCardToBottom(self._opponentfield, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()

    def OnOpponentCardFieldToDeckShuffle(self, event=None):
        card = self._opponentcurrentcard
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to his deck.')+ ' ' + str(len(self._opponentdeck)+1) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        self.MoveCard(self._opponentfield, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()

    def OnOpponentCardFieldToHand(self, event=None):
        card = self._opponentcurrentcard
        if card.IsFaceUp():
            self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('sent a card to his hand.'), CHAT_OPPONENT)
        self.MoveCardToBottom(self._opponentfield, self._opponenthand, card)
        card.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        card.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()

    #Grave
    def OnCardGravePopup(self, c):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
        item.SetBitmap(self._engine.GetSkinImage('Tohand'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardGraveToHand, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
        item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardGraveToRFG, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck/Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardGraveToDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardGraveToTopDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardGraveToBottomDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Target'))
        item.SetBitmap(self._engine.GetSkinImage('Targetsm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardTarget, item)
        self._currentcard = c
        c.PopupMenu(menu)
        
    def OnCardGraveToHand(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_HAND)
        self.MoveCardToBottom(self._grave, self._hand, card)
        card.SetCardState(POS_HAND)
        card.Reparent(self._handctrl)
        self.RefreshHand()
        self.RefreshGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_PLAYER)

    def OnCardGraveToTopDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 1)
        self.MoveCardToTop(self._grave, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardGraveToBottomDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 0)
        self.MoveCardToBottom(self._grave, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardGraveToDeckShuffle(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 2)
        self.MoveCard(self._grave, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.Shuffle()
        #self.RefreshDeck()
        self.RefreshGrave()

    def OnCardGraveToRFG(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_RFG)
        self.MoveCard(self._grave, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.RefreshGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_PLAYER)

    def OnCardGraveToField(self, event=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 0, x, y)
        self.MoveCard(self._grave, self._field, card)
        card.SetCardState(POS_FIELD)
        card.Reparent(self._fieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshGrave()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_PLAYER)


    #Damage
    def OnCardDamagePopup(self, c):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
        item.SetBitmap(self._engine.GetSkinImage('Tohand'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDamageToHand, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
        item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDamageToRFG, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck/Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDamageToDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDamageToTopDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDamageToBottomDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Mark Flipped'))
        item.SetBitmap(self._engine.GetSkinImage('Targetsm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardTarget, item)
        self._currentcard = c
        c.PopupMenu(menu)
    
    def OnCardDamageToHand(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DAMAGE)
        self.MoveCardToBottom(self._damage, self._hand, card)
        card.SetCardState(POS_HAND)
        card.Reparent(self._handctrl)
        self.RefreshHand()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_PLAYER)

    def OnCardDamageToTopDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 1)
        self.MoveCardToTop(self._damage, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardDamageToBottomDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 0)
        self.MoveCardToBottom(self._damage, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardDamageToDeckShuffle(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 2)
        self.MoveCard(self._damage, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.Shuffle()
        #self.RefreshDeck()
        self.RefreshDamage()

    def OnCardDamageToRFG(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_RFG)
        self.MoveCard(self._damage, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_PLAYER)

    def OnCardDamageToField(self, event=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 0, x, y)
        self.MoveCard(self._damage, self._field, card)
        card.SetCardState(POS_FIELD)
        card.Reparent(self._fieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_PLAYER)
   
    #Opponent Grave
    def OnOpponentCardGraveToHand(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentgrave, self._opponenthand, card)
        card.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        card.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_OPPONENT)

    def OnOpponentCardGraveToTopDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToTop(self._opponentgrave, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardGraveToBottomDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentgrave, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshopponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardGraveToDeckShuffle(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentgrave, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)


    def OnOpponentCardGraveToRFG(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentgrave, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_OPPONENT)
    
    def OnOpponentCardDamageToRFG(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdamage, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_OPPONENT)
    
    def OnOpponentCardGraveToField(self, event=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        self.MoveCard(self._opponentgrave, self._opponentfield, card)
        card.SetCardState(POS_OPP_FIELD)
        card.Reparent(self._opponentfieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshOpponentGrave()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_OPPONENT)

    #Opponent Damage
    def OnOpponentCardDamageToHand(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentdamage, self._opponenthand, card)
        card.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        card.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_OPPONENT)

    def OnOpponentCardDamageToTopDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToTop(self._opponentdamage, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardDamageToBottomDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentdamage, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardDamageToDeckShuffle(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdamage, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)


    def OnOpponentCardDamageToRFG(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdamage, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.'), CHAT_OPPONENT)
    
    def OnOpponentCardDamageToField(self, event=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        self.MoveCard(self._opponentdamage, self._opponentfield, card)
        card.SetCardState(POS_OPP_FIELD)
        card.Reparent(self._opponentfieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshOpponentDamage()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_OPPONENT)
   
    #RFG
    def OnCardRFGPopup(self, c):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
        item.SetBitmap(self._engine.GetSkinImage('Tohand'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRFGToHand, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Drop Zone'))
        item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRFGToGrave, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Deck/Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('Todecksh'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRFGToDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Top-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Totopdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRFGToTopDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Bottom-Deck'))
        item.SetBitmap(self._engine.GetSkinImage('Tobottomdeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardRFGToBottomDeck, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Target'))
        item.SetBitmap(self._engine.GetSkinImage('Targetsm'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardTarget, item)
        self._currentcard = c
        c.PopupMenu(menu)

    def OnCardRFGToHand(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_HAND)
        self.MoveCardToBottom(self._rfg, self._hand, card)
        card.SetCardState(POS_HAND)
        card.Reparent(self._handctrl)
        self.RefreshHand()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_PLAYER)

    def OnCardRFGToTopDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 1)
        self.MoveCardToTop(self._rfg, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardRFGToBottomDeck(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 0)
        self.MoveCardToBottom(self._rfg, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardRFGToDeckShuffle(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 2)
        self.MoveCard(self._rfg, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        self.Shuffle()
        #self.RefreshDeck()
        self.RefreshRFG()

    def OnCardRFGToGrave(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_GRAVE)
        self.MoveCard(self._rfg, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_PLAYER)
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        
    
    def OnCardRFGToDamage(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DAMAGE)
        self.MoveCard(self._rfg, self._damage, card)
        card.SetCardState(POS_DAMAGE)
        card.Reparent(self._damagelistctrl)
        self.RefreshDamage()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName()), CHAT_PLAYER)
      
    def OnCardDamageToGrave(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_GRAVE)
        self.MoveCard(self._damage, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        self.RefreshDamage()
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_PLAYER)
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)

    def OnCardRFGToField(self, event=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 0, x, y)
        self.MoveCard(self._rfg, self._field, card)
        card.SetCardState(POS_FIELD)
        card.Reparent(self._fieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshRFG()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_PLAYER)

    # Opponent RFG
    def OnOpponentCardRFGToHand(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentrfg, self._opponenthand, card)
        card.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        card.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.'), CHAT_OPPONENT)

    def OnOpponentCardRFGToTopDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToTop(self._opponentrfg, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardRFGToBottomDeck(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentrfg, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to the bottom of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardRFGToDeckShuffle(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentrfg, self._opponentdeck, card)
        card.SetCardState(POS_OPP_DECK)
        card.Reparent(self._opponentdecklistctrl)
        self.RefreshOpponentDeck()
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardRFGToGrave(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentrfg, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.RefreshOpponentRFG()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_OPPONENT)
    
    def OnOpponentCardRFGToDamage(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentrfg, self._opponentdamage, card)
        card.SetCardState(POS_OPP_DAMAGE)
        card.Reparent(self._opponentdamagelistctrl)
        self.RefreshOpponentDamage()
        self.RefreshOpponentRFG()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName()), CHAT_OPPONENT)
    
    def OnOpponentCardDamageToGrave(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdamage, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.RefreshOpponentDamage()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName()), CHAT_OPPONENT)

    def OnOpponentCardRFGToField(self, event=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        self.MoveCard(self._opponentrfg, self._opponentfield, card)
        card.SetCardState(POS_OPP_FIELD)
        card.Reparent(self._opponentfieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshOpponentRFG()
        self.WriteGameMessage(self._engine.GetLangString('place ') + card.GetCardName() + self._engine.GetLangString(' on the field.'), CHAT_OPPONENT)

    #Deck
    def OnCardDeckPopup(self, c):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Hand'))
        item.SetBitmap(self._engine.GetSkinImage('Tohand'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDeckToHand, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Damage'))
        item.SetBitmap(self._engine.GetSkinImage('ToDamage'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDeckToDamage, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Drop Zone'))
        item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDeckToGrave, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('To Soul'))
        item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnCardDeckToRFG, item)
        self._currentcard = c
        c.PopupMenu(menu)
        
    def OnCardDeckToHand(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_HAND)
        self.MoveCardToBottom(self._deck, self._hand, card)
        card.SetCardState(POS_HAND)
        card.Reparent(self._handctrl)
        self.RefreshHand()
        self.RefreshDeck()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardDeckToGrave(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_GRAVE)
        self.MoveCard(self._deck, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        self.RefreshDeck()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName())+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardDeckToDamage(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_DAMAGE)
        self.MoveCard(self._deck, self._damage, card)
        card.SetCardState(POS_DAMAGE)
        card.Reparent(self._damagelistctrl)
        self.RefreshDamage()
        self.RefreshDeck()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_PLAYER)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName())+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
    
    def OnCardDeckToRFG(self, event=None):
        card = self._currentcard
        self.WriteMoveCardPacket(card, POS_OPP_RFG)
        self.MoveCard(self._deck, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.RefreshDeck()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnCardDeckToField(self, event=None):
        card = self._currentcard[0]
        x = self._currentcard[1]
        y = self._currentcard[2]
        self.WriteMoveCardPacket(card, POS_OPP_FIELD, 1, x, y)
        self.MoveCard(self._deck, self._field, card)
        card.SetCardState(POS_FIELD, face= FACE_DOWN)
        card.Reparent(self._fieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshDeck()
        self.WriteGameMessage(self._engine.GetLangString('placed Vanguard ') + self._engine.GetLangString(' on the field.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
    #End

    # Opponent Deck
    def OnOpponentCardDeckToHand(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCardToBottom(self._opponentdeck, self._opponenthand, card)
        card.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        card.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his hand.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardDeckToGrave(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdeck, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.RefreshOpponentDeck()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Drop Zone.', card.GetCardName())+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardDeckToDamage(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdeck, self._opponentdamage, card)
        card.SetCardState(POS_OPP_DAMAGE)
        card.Reparent(self._opponentdamagelistctrl)
        self.RefreshOpponentDamage()
        self.RefreshOpponentDeck()
        #self.WriteGameMessage(self._engine.GetLangString('sent ') + card.GetCardName() + self._engine.GetLangString(' to his graveyard.'), CHAT_OPPONENT)
        self.WriteGameMessage(self._engine.GetLangString('sent %s to his Damage Zone.', card.GetCardName())+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
   
    def OnOpponentCardDeckToRFG(self, event=None):
        card = self._opponentcurrentcard
        self.MoveCard(self._opponentdeck, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('sent') + card.GetCardName() + self._engine.GetLangString(' to Soul.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)

    def OnOpponentCardDeckToField(self, event=None):
        card = self._opponentcurrentcard[0]
        x = self._opponentcurrentcard[1]
        y = self._opponentcurrentcard[2]
        self.MoveCard(self._opponentdeck, self._opponentfield, card)
        card.SetCardState(POS_OPP_FIELD, face=FACE_DOWN)
        card.Reparent(self._opponentfieldctrl)
        card.SetPosition(self.PositionCard(card, x, y))
        card.Hide()
        card.Show()
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('placed Vanguard ') + self._engine.GetLangString(' on the field.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
    #End

    def OnDeckDClick(self, event):
        self.OnDeckDraw()

    def OnDeckRClick(self, event):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Search Deck'))
        item.SetBitmap(self._engine.GetSkinImage('SearchDeck'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckSearch, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Shuffle'))
        item.SetBitmap(self._engine.GetSkinImage('Shuffle'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckShuffle, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Draw and Reveal'))
        item.SetBitmap(self._engine.GetSkinImage('Drawsh'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckDrawReveal, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Soulcharge Top Card'))
        item.SetBitmap(self._engine.GetSkinImage('ToSoul'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckSoulChargeTopCard, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Discard Top Card'))
        item.SetBitmap(self._engine.GetSkinImage('ToDrop'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckDiscardTopCard, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Reveal Top Card'))
        item.SetBitmap(self._engine.GetSkinImage('Vert'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckRevealTopCard, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Check Top Card'))
        item.SetBitmap(self._engine.GetSkinImage('Vert'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckCheckTopCard, item)
        item = wx.MenuItem(menu, -1, self._engine.GetLangString('Top to Bottom'))
        item.SetBitmap(self._engine.GetSkinImage('TopBottom'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPopupDeckTopCardToBottom, item)
        self.PopupMenu(menu)
    
    def OnPopupDeckDrawReveal(self, event):
        self.OnDeckDraw(1)
    
    def OnPopupDeckDiscardTopCard(self, event):
        card = self._deck[0]
        self.MoveCard(self._deck, self._grave, card)
        card.SetCardState(POS_GRAVE)
        card.Reparent(self._gravelistctrl)
        self.RefreshGrave()
        self.RefreshDeck()
        self.WriteCardActionPacket(ACTION_DISCARDTOP)
        self.WriteGameMessage(self._engine.GetLangString('discarded ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
    
    def OnPopupDeckSoulChargeTopCard(self, event):
        card = self._deck[0]
        self.MoveCard(self._deck, self._rfg, card)
        card.SetCardState(POS_RFG)
        card.Reparent(self._rfglistctrl)
        self.RefreshRFG()
        self.RefreshDeck()
        self.WriteCardActionPacket(ACTION_SCTOP)
        self.WriteGameMessage(self._engine.GetLangString('soulcharged ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        
    
    def OnPopupDeckTopCardToBottom(self, event):
        card = self._deck[0]
        self.WriteMoveCardPacket(card, POS_OPP_DECK, 4) # Bottom-Deck
        self.MoveCardToBottom(self._deck, self._deck, card)
        card.SetCardState(POS_DECK)
        card.Reparent(self._decklistctrl)
        self.RefreshDeck()
        self.WriteGameMessage(self._engine.GetLangString('Sent top card to the bottom.')+ ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        
    def OnPopupDeckRevealTopCard(self, event):
        card = self._deck[0]
        self.WriteCardActionPacket(ACTION_REVEALTOP)
        self.WriteGameMessage(self._engine.GetLangString('revealed ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.'), CHAT_PLAYER)
    
    def OnPopupDeckCheckTopCard(self, event):
        card = self._deck[0]
        self.WriteCardActionPacket(ACTION_CHECKTOP)
        self.WriteGameMessage(self._engine.GetLangString('Your top card is ') + card.GetCardName(), CHAT_PLAYER)
    
    def OnPopupDeckSearch(self, event=None):
        if self._decklistctrl.IsShown():
            self._decklistctrl.Hide()
            self.WriteLookPacket(LOOK_DECK_NO)
            self._deckctrl.SetTexture(self._engine.GetSkinImage('Deck'))
            self.WriteGameMessage(self._engine.GetLangString('end looking at his deck.'), CHAT_PLAYER)
        else:
            self._decklistctrl.Show()
            self.WriteLookPacket(LOOK_DECK_YES)
            self._deckctrl.SetTexture(self._engine.GetSkinImage('LookDeck'))
            self.WriteGameMessage(self._engine.GetLangString('is looking at his deck.'), CHAT_PLAYER)

    def OnPopupDeckShuffle(self, event):
        self.Shuffle()
    
    def OnOpponentActionDiscardTop(self, event = None):
        card = self._opponentdeck[0]
        self.MoveCard(self._opponentdeck, self._opponentgrave, card)
        card.SetCardState(POS_OPP_GRAVE)
        card.Reparent(self._opponentgravelistctrl)
        self.RefreshOpponentGrave()
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('discarded ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
    
    def OnOpponentActionSCTop(self, event = None):
        card = self._opponentdeck[0]
        self.MoveCard(self._opponentdeck, self._opponentrfg, card)
        card.SetCardState(POS_OPP_RFG)
        card.Reparent(self._opponentrfglistctrl)
        self.RefreshOpponentRFG()
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('soulcharged ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        
    def OnOpponentActionRevealTop(self, event=None):
        card = self._opponentdeck[0]
        self.WriteGameMessage(self._engine.GetLangString('revealed ') + card.GetCardName() + self._engine.GetLangString(' from the top of his deck.'), CHAT_OPPONENT)
    
    def OnOpponentActionCheckTop(self, event=None):
        card = self._opponentdeck[0]
        self.WriteGameMessage(self._engine.GetLangString('Checked top card of his deck.'), CHAT_OPPONENT)

    def OnGraveLClick(self, event=None):
        if self._gravelistctrl.IsShown():
            self._gravelistctrl.Hide()
            self.WriteLookPacket(LOOK_GRAVE_NO)
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Drop Zone.'), CHAT_PLAYER)
        else:
            self._gravelistctrl.Show()
            self.WriteLookPacket(LOOK_GRAVE_YES)
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Drop Zone.'), CHAT_PLAYER)
    
    def OnDamageLClick(self, event=None):
        if self._damagelistctrl.IsShown():
            self._damagelistctrl.Hide()
            self.WriteLookPacket(LOOK_DAMAGE_NO)
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Damage Zone.'), CHAT_PLAYER)
        else:
            self._damagelistctrl.Show()
            self.WriteLookPacket(LOOK_DAMAGE_YES)
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Damage Zone.'), CHAT_PLAYER)

    def OnOpponentGraveLClick(self, event=None):
        if self._opponentgravelistctrl.IsShown():
            self._opponentgravelistctrl.Hide()
            self.WriteLookPacket(LOOK_OPPONENT_GRAVE_NO)
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Drop Zone."), CHAT_PLAYER)
        else:
            self._opponentgravelistctrl.Show()
            self.WriteLookPacket(LOOK_OPPONENT_GRAVE_YES)
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Drop Zone."), CHAT_PLAYER)
    
    def OnOpponentDamageLClick(self, event=None):
        if self._opponentdamagelistctrl.IsShown():
            self._opponentdamagelistctrl.Hide()
            self.WriteLookPacket(LOOK_OPPONENT_DAMAGE_NO)
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Damage Zone."), CHAT_PLAYER)
        else:
            self._opponentdamagelistctrl.Show()
            self.WriteLookPacket(LOOK_OPPONENT_DAMAGE_YES)
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Damage Zone."), CHAT_PLAYER)

    def OnNewNote(self, event):
        pos = self._fieldctrl.ScreenToClient(wx.GetMousePosition())
        Note(self._fieldctrl, (pos.x-25, pos.y-25), self)

    def OnDeckDraw(self, reveal=0):
        if len(self._deck) < 1:
            return
        c = self.RemoveCardFromTop(self._deck)
        c.SetCardState(POS_HAND)
        self.AddCardToBottom(self._hand, c)
        c.Reparent(self._handctrl)
        self.RefreshHand()
        self.RefreshDeck()
        self.WritePacket(packets.DrawPacket(reveal))
        if reveal:
            c.SetCardState(POS_HAND, face=FACE_DOWN)
            self.WriteGameMessage(self._engine.GetLangString('drew ') + c.GetCardName() + '. ' + c.GetCardTrigger()+ '. \n' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('drew a card.') + ' ' + str(len(self._deck)) +self._engine.GetLangString(' cards left.'), CHAT_PLAYER)

    def OnDeckDrawShow(self):
        self.OnDeckDraw(1)
    
    def OnHandHide(self):
        c.SetCardState(POS_HAND, face=FACE_UP)
        self.RefreshHand()
        

    def OnOpponentDeckDraw(self, reveal=0):
        c = self.RemoveCardFromTop(self._opponentdeck)
        c.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        self.AddCardToBottom(self._opponenthand, c)
        c.Reparent(self._opponenthandctrl)
        self.RefreshOpponentHand()
        self.RefreshOpponentDeck()
        if reveal:
            c.SetCardState(POS_OPP_HAND, face=FACE_UP)
            self.WriteGameMessage(self._engine.GetLangString('drew ') + c.GetCardName() + '. '+ c.GetCardTrigger() + '. \n' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('drew a card.')+ ' ' + str(len(self._opponentdeck)) +self._engine.GetLangString(' cards left.'), CHAT_OPPONENT)
    
    def OnOpponentHandShuffle(self):
        for c in self._opponenthand:
            c.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        self.RefreshOpponentHand()
    
    def OnCardFieldMove(self, c, x, y):
        c.SetPosition(self.PositionCard(c, x, y))
        self.WriteMoveCardPacket(c, POS_OPP_FIELD, 0, x, y)
        c.Hide()
        c.Show()
    
    def OnOpponentCardFieldMove(self, c, x, y):
        c.SetPosition(self.PositionCard(c, x, y))
        c.Hide()
        c.Show()
        
    def PositionCard(self, card, x, y):
        adj = True
        if self.Hit(x, y, wx.Rect(108,48,96,96)):
            x = 108
            y = 48
        elif self.Hit(x, y, wx.Rect(205,48,96,96)):
            x = 205
            y = 48
        elif self.Hit(x, y, wx.Rect(302,48,96,96)):
            x = 302
            y = 48
        elif self.Hit(x, y, wx.Rect(399,48,96,96)):
            x = 399
            y = 48
        elif self.Hit(x, y, wx.Rect(496,48,96,96)):
            x = 496
            y = 48
        elif self.Hit(x, y, wx.Rect(108,145,96,96)):
            x = 108
            y = 145
        elif self.Hit(x, y, wx.Rect(205,145,96,96)):
            x = 205
            y = 145
        elif self.Hit(x, y, wx.Rect(302,145,96,96)):
            x = 302
            y = 145
        elif self.Hit(x, y, wx.Rect(399,145,96,96)):
            x = 399
            y = 145
        elif self.Hit(x, y, wx.Rect(496,145,96,96)):
            x = 496
            y = 145
        elif self.Hit(x, y, wx.Rect(21,33,60,88)) and type(card) is CardControl:
            x = 21
            y = 33
            adj = False
        elif self.Hit(x, y, wx.Rect(618,168,60,88)) and type(card) is OpponentCardControl:
            x = 618
            y = 168
            adj = False
        else:
            x -= 30
            y -= 44
            adj = False 

        if adj:
            if card.IsHorizontal():
                x += 4
                y += 18
            else:
                x += 18
                y += 4
        return wx.Point(x,y)

    def OnCardDropOnField(self, x, y, data):
        c = self.GetCardFromSerial(data)
        self._currentcard = c
        if self.Hit(x, y, self._gravectrl.GetRect()):
            self.OnCardDropOnGrave(x, y, data)
        elif self.Hit(x, y, self._rfgctrl.GetRect()):
            self.OnCardDropOnRFG(x, y, data)
        elif self.Hit(x, y, self._damagectrl.GetRect()):
            self.OnCardDropOnDamage(x, y, data)
        elif self.Hit(x, y, wx.Rect(0,0,self._fieldctrl.GetSize().GetWidth(),self._fieldctrl.GetSize().GetHeight())):
            self._currentcard = (c,x,y)
            if c.GetCardPosition() == POS_FIELD:
                self.OnCardFieldMove(c, x, y)
            elif c.GetCardPosition() == POS_GRAVE:
                self.OnCardGraveToField()
            elif c.GetCardPosition() == POS_DAMAGE:
                self.OnCardDamageToField()
            elif c.GetCardPosition() == POS_RFG:
                self.OnCardRFGToField()
            elif c.GetCardPosition() == POS_HAND:
                att = c.GetCardClan()
                if att == 'Trap' or att == 'Spell':
                    self.PopupMenu(self._hand_mt_menu)
                else:
                    self.PopupMenu(self._hand_monster_menu)
            elif c.GetCardPosition() == POS_DECK:
                self.OnCardDeckToField()
        self._consolectrl.SetFocus()

    def OnCardDropOnGrave(self, x, y, data):
        c = self.GetCardFromSerial(data)
        self._currentcard = c
        if c.GetCardPosition() == POS_HAND:
            self.OnCardHandToGrave()
        elif c.GetCardPosition() == POS_FIELD:
            self.OnCardFieldToGrave()
        elif c.GetCardPosition() == POS_DECK:
            self.OnCardDeckToGrave()
        elif c.GetCardPosition() == POS_RFG:
            self.OnCardRFGToGrave()
        elif c.GetCardPosition() == POS_DAMAGE:
            self.OnCardDamageToGrave()
    
    def OnCardDropOnDamage(self, x, y, data):
        c = self.GetCardFromSerial(data)
        self._currentcard = c
        if c.GetCardPosition() == POS_HAND:
            self.OnCardHandToDamage()
        elif c.GetCardPosition() == POS_FIELD:
            self.OnCardFieldToDamage()
        elif c.GetCardPosition() == POS_DECK:
            self.OnCardDeckToDamage()
        elif c.GetCardPosition() == POS_RFG:
            self.OnCardRFGToDamage()

    def OnCardDropOnRFG(self, x, y, data):
        c = self.GetCardFromSerial(data)
        self._currentcard = c
        if c.GetCardPosition() == POS_HAND:
            self.OnCardHandToRFG()
        elif c.GetCardPosition() == POS_FIELD:
            self.OnCardFieldToRFG()
        elif c.GetCardPosition() == POS_DECK:
            self.OnCardDeckToRFG()
        elif c.GetCardPosition() == POS_GRAVE:
            self.OnCardGraveToRFG()
        elif c.GetCardPosition() == POS_DAMAGE:
            self.OnCardDamageToRFG()

    def OnCardDropOnHand(self, x, y, data):
        c = self.GetCardFromSerial(data)
        self._currentcard = c
        if c.GetCardPosition() == POS_FIELD:
            self.OnCardFieldToHand()
        elif c.GetCardPosition() == POS_GRAVE:
            self.OnCardGraveToHand()
        elif c.GetCardPosition() == POS_DAMAGE:
            self.OnCardDamageToHand()
        elif c.GetCardPosition() == POS_RFG:
            self.OnCardRFGToHand()
        elif c.GetCardPosition() == POS_DECK:
            self.OnCardDeckToHand()

    def RefreshGrave(self):
        self._gravectrl.UpdateCardTooltip(self._grave)
        l = self._grave
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._gravelistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._gravelistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._gravelistctrl.Scroll.SetScrollbars(0, 11, 0, n)

    def RefreshOpponentGrave(self):
        self._opponentgravectrl.UpdateCardTooltip(self._opponentgrave)
        l = self._opponentgrave
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._opponentgravelistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._opponentgravelistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._opponentgravelistctrl.Scroll.SetScrollbars(0, 11, 0, n)
    
    def RefreshDamage(self):
        self._damagectrl.UpdateCardTooltip(self._damage)
        l = self._damage
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._damagelistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._damagelistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._damagelistctrl.Scroll.SetScrollbars(0, 11, 0, n)

    def RefreshOpponentDamage(self):
        self._opponentdamagectrl.UpdateCardTooltip(self._opponentdamage)
        l = self._opponentdamage
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._opponentdamagelistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._opponentdamagelistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._opponentdamagelistctrl.Scroll.SetScrollbars(0, 11, 0, n)

    def RefreshRFG(self):
        self._rfgctrl.UpdateCardTooltip(self._rfg)
        l = self._rfg
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._rfglistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._rfglistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._rfglistctrl.Scroll.SetScrollbars(0, 11, 0, n)

    def RefreshOpponentRFG(self):
        l = self._opponentrfg
        self._opponentrfgctrl.UpdateCardTooltip(self._opponentrfg)
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        xtmp = 0
        ytmp = 0
        self._opponentrfglistctrl.Scroll.Scroll(0,0)
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._opponentrfglistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._opponentrfglistctrl.Scroll.SetScrollbars(0, 11, 0, n)

    def RefreshDeck(self):
        l = self._deck
        n = len(l)
        if n == 0:
            return
        x_pos = 0
        x_move = 64
        y_pos = 0
        y_move = 90
        self._decklistctrl.Scroll.Scroll(0,0)
        xtmp = 0
        ytmp = 0
        for c in l:
            if xtmp == 10:
                xtmp = 0
                ytmp = ytmp+1
            c.RefreshTexture()
            c.SetPosition((x_move*xtmp,ytmp*y_move))
            c.Reparent(self._decklistctrl.Scroll)
            c.Hide()
            c.Show()
            xtmp= xtmp+1
        self._decklistctrl.Scroll.SetScrollbars(0, 11, 0, n)
        self._deckcounttext.SetLabel(str(len(self._deck)))

    def RefreshOpponentDeck(self):
        l = self._opponentdeck
        n = len(l)
        if n == 0:
            return
        y_pos = 0
        y_move = 12
        self._opponentdecklistctrl.Scroll.Scroll(0,0)
        for c in l:
            c.RefreshTexture()
            c.SetPosition((0,y_pos))
            c.Reparent(self._opponentdecklistctrl.Scroll)
            c.Hide()
            c.Show()
            y_pos += y_move
        self._opponentdecklistctrl.Scroll.SetScrollbars(0, 12, 0, n)

    def RefreshHand(self):
        l = self._hand
        n = len(l)
        if n < 1:
            return
        card_width = self.GetCardSize().GetWidth() + 2
        self_width = self._handctrl.GetSize().GetWidth()
        self_mid = self_width/2
        x_pos = 0
        if n > 10:
            card_width = self_width/n
        elif n%2 == 0:
            x_pos = self_mid - (card_width*(n/2))
        else:
            x_pos = self_mid - ((card_width*(n/2)) + card_width/2)
        for c in l:
            c.SetPosition((x_pos,0))
            x_pos += card_width
            c.Hide()
            c.Show()
            if sys.platform == "win32":
                c.Lower()

    def RefreshOpponentHand(self):
        l = self._opponenthand
        n = len(l)
        if n < 1:
            return
        card_width = self.GetCardSize().GetWidth() + 2
        self_width = self._handctrl.GetSize().GetWidth()
        self_mid = self_width/2
        x_pos = 0
        if n > 10:
            card_width = self_width/n
        elif n%2 == 0:
            x_pos = self_mid - (card_width*(n/2))
        else:
            x_pos = self_mid - ((card_width*(n/2)) + card_width/2)
        for c in l:
            c.SetPosition((x_pos,0))
            x_pos += card_width
            c.Hide()
            c.Show()
            if sys.platform == "win32":
                c.Lower()

    def Hit(self, x1, y1, r):
        x2 = r.GetX()
        y2 = r.GetY()
        x3 = r.GetX() + r.GetWidth()
        y3 = r.GetY() + r.GetHeight()
        if x1 >= x2 and x1 <= x3 and y1 >= y2 and y1 <= y3:
            return True
        else:
            return False

    def RefreshCardInfo(self, name, bmp, desc):
        self._cardimagectrl.SetBitmap(bmp)
        self._carddescriptionctrl.SetValue(desc)

    def RollDice(self, faces):
        n = random.randint(1,int(faces))
        self.WriteRollPacket(faces, n)
        self.WriteGameMessage('rolled a d%s: %s.' % (faces, n), CHAT_PLAYER)

    def RollD6(self, event=None):
        self.RollDice(6)

    def FlipCoin(self, event=None):
        head = random.randint(0,1)
        self.WriteFlipCoinPacket(head)
        if head:
            self.WriteGameMessage(self._engine.GetLangString('flipped a coin : Heads'), CHAT_PLAYER)
        else:
            self.WriteGameMessage(self._engine.GetLangString('flipped a coin : Tails'), CHAT_PLAYER)

    def NextPhase(self):
        if self._drawphasectrl.IsSelected():
            self._standbyphasectrl.OnLeftUp()
        elif self._standbyphasectrl.IsSelected():
            self._mainphase1ctrl.OnLeftUp()
        elif self._mainphase1ctrl.IsSelected():
            self._battlephasectrl.OnLeftUp()
        elif self._battlephasectrl.IsSelected():
            self._mainphase2ctrl.OnLeftUp()
        elif self._mainphase2ctrl.IsSelected():
            self._endphasectrl.OnLeftUp()
        else:
            self._drawphasectrl.OnLeftUp()

    def EndTurn(self):
        self._endphasectrl.OnLeftUp()

    def OnPopupRollD6(self, event=None):
        self.RollDice(6)

    def OnPopupFlipCoin(self, event=None):
        self.FlipCoin()

    def WriteSmiles(self, msg):
        for smile in self._smiles:
            msg = msg.replace(':%s:' % smile, '<img src=%s>' % self._engine.GetSmile(smile))
        return msg

    '''def WriteMessage(self, msg):
        self._messagetext = msg + '<br>' + self._messagetext
        self._messagectrl.SetPage(self._messagetext)'''

    '''def WriteChatMessage(self, msg, w):
        msg = self.WriteSmiles(msg)
        if w == CHAT_PLAYER:
            self._messagetext = '<font color="Blue">' + self._nick + ': ' + '</font>' + msg.decode('utf-8') + '<br>' + self._messagetext
        elif w == CHAT_OPPONENT:
            self._messagetext = '<font color="Red">' + self._opponentnick + ': ' + '</font>' + msg.decode('utf-8') + '<br>' + self._messagetext
        self._messagectrl.SetPage(self._messagetext)
    '''

    def WriteMessage(self, msg):
        self._messagectrl.SetInsertionPointEnd()
        self._messagectrl.Newline()
        self._messagectrl.BeginTextColour(wx.BLACK)
        self._messagectrl.WriteText(msg)
        self._messagectrl.EndTextColour()
        self._messagectrl.SetInsertionPoint(0)
        while self._messagectrl.ScrollLines(10):
            pass
        
        #self._messagectrl.AppendToPage('<br>'+ msg)
        #self._messagectrl.Scroll(0,32001)
        
        #self._messagetext += '<br>' + msg
        #self._messagectrl.SetPage(self._messagetext)
        #self._messagectrl.Scroll(0,int(self._messagectrl.GetScrollPixelsPerUnit()[0]*self._messagetext.count('<br>')))

    def WriteChatMessage(self, msg, w):
        #msg = self.WriteSmiles(msg)

        self._messagectrl.SetInsertionPointEnd()
        self._messagectrl.Newline()
        if w == CHAT_PLAYER:
            self._messagectrl.BeginTextColour(wx.BLUE)
            self._messagectrl.WriteText(self._nick+': ')
            self._messagectrl.EndTextColour()
        elif w == CHAT_OPPONENT:
            self._messagectrl.BeginTextColour(wx.RED)
            self._messagectrl.WriteText(self._opponentnick+': ')
            self._messagectrl.EndTextColour()

        # Metodo per il parsing degli smiles :)
        self._messagectrl.BeginTextColour(wx.BLACK)
        i = 0
        while 1:
            if i >= len(msg):
                break
            w = 1
            if msg[i] == ':':
                for smile in self._smiles:
                    sl = len(smile)
                    if msg[i+1:i+1+len(smile)] == smile:
                        self._messagectrl.WriteImageFile(self._engine.GetSmile(smile), wx.BITMAP_TYPE_GIF)
                        i += len(smile)+1
                        w = 0
                        break
            if w:
                self._messagectrl.WriteText(msg[i])
                i += 1
        self._messagectrl.EndTextColour()

        while self._messagectrl.ScrollLines(10):
            pass
        self._messagectrl.SetInsertionPoint(0)
            
            #msg = '<br><font color="Blue">' + self._nick + ': ' + '</font>' + msg
            
            #msg = '<br><font color="Red">' + self._opponentnick + ': ' + '</font>' + msg.decode('utf-8')
            #msg = '<br><font color="Red">' + self._opponentnick + ': ' + '</font>' + msg
        #self._messagectrl.AppendToPage(msg)
        #self._messagectrl.Scroll(0,32001)
        #if w == CHAT_PLAYER:
        #    self._messagetext += '<br><font color="Blue">' + self._nick + ': ' + '</font>' + msg.decode('utf-8')
        #elif w == CHAT_OPPONENT:
        #    self._messagetext += '<br><font color="Red">' + self._opponentnick + ': ' + '</font>' + msg.decode('utf-8')
        #self._messagectrl.SetPage(self._messagetext)
        #self._messagectrl.Scroll(0,int(self._messagectrl.GetScrollPixelsPerUnit()[0]*self._messagetext.count('<br>')))

    def WriteGameMessage(self, msg, s):
        self._messagectrl.SetInsertionPointEnd()
        self._messagectrl.Newline()
        self._messagectrl.BeginTextColour(wx.GREEN)
        self._messagectrl.WriteText('Game: ')
        self._messagectrl.EndTextColour()
        if s == CHAT_GAME:
            self._messagectrl.BeginTextColour(wx.BLACK)
            self._messagectrl.WriteText(msg)
            self._messagectrl.EndTextColour()
        elif s == CHAT_PLAYER:
            self._messagectrl.BeginTextColour(wx.BLUE)
            self._messagectrl.WriteText(self._nick)
            self._messagectrl.EndTextColour()
            self._messagectrl.BeginTextColour(wx.BLACK)
            self._messagectrl.WriteText(' ' + msg)
            self._messagectrl.EndTextColour()
        elif s == CHAT_OPPONENT:
            self._messagectrl.BeginTextColour(wx.RED)
            self._messagectrl.WriteText(self._opponentnick)
            self._messagectrl.EndTextColour()
            self._messagectrl.BeginTextColour(wx.BLACK)
            self._messagectrl.WriteText(' ' + msg)
            self._messagectrl.EndTextColour()
        elif s == CHAT_CONSOLE:
            self._messagectrl.BeginTextColour(wx.BLACK)
            self._messagectrl.WriteText(msg)
            self._messagectrl.EndTextColour()
        while self._messagectrl.ScrollLines(10):
            pass
        self._messagectrl.SetInsertionPoint(0)

    def ProcessMessage(self, m):
        if m[0] == '/':
            self.ProcessCommand(m[1:])
        else:
            self.WriteChatPacket(m)
            self.WriteChatMessage(m, CHAT_PLAYER)

    def ProcessCommand(self, cmd):
        cmd = cmd
        args = self.GetArgs(cmd)
        cmd = args.pop(0)
        if self._cmdhandlers.has_key(cmd):
            self._cmdhandlers[cmd](args)
        else:
            self.WriteGameMessage("unknown command '" + cmd + "'", CHAT_CONSOLE)

    def GetArgs(self, cmd):
        args = []
        for a in cmd.split(' '):
            args.append(a)
        return args

    def CommandHandlers(self):
        self._cmdhandlers['print'] = self.OnCmdPrint
        self._cmdhandlers['roll'] = self.OnCmdRoll
        self._cmdhandlers['lp'] = self.OnCmdLP
    

    def OnCmdPrint(self, args):
        if len(args) < 1:
            return
        else:
            self.WriteMessage(args[0])
    
    def OnCmdRoll(self, args):
        try:
            faces = int(args[0])
        except:
            self.WriteMessage('Argument error.')
        finally:
            self.RollDice(faces)
    
    def OnCmdLP(self, args):
        try:
            faces = int(args[0])
        except:
            self.WriteMessage('Argument error.')
        finally:
            self._scorectrl.SetPlayerScoreDiff(faces)
    
    def OnClose(self, event=None):
        self.WriteDisconnectPacket()
        self._engine.Network.Close()
        return True

    def GetCardSize(self):
        return self._cardsize

    def GetHand(self):
        return self._hand.GetCards()

    def RefreshCardPosition(self, pos):
        if pos == POS_HAND:
            self.RefreshHand()
        elif pos == POS_GRAVE:
            self.RefreshGrave()()
        elif pos == POS_DECK:
            self.RefreshDeck()
        elif pos == POS_DAMAGE:
            self.RefreshDamage()
        elif pos == POS_RFG:
            self.RefreshRFG()

    def GetCardList(self, pos):
        if pos == POS_FIELD:
            return self._field
        elif pos == POS_HAND:
            return self._hand
        elif pos == POS_GRAVE:
            return self._grave
        elif pos == POS_DAMAGE:
            return self._damage
        elif pos == POS_DECK:
            return self._deck
        elif pos == POS_RFG:
            return self._rfg
        elif pos == POS_OPP_FIELD:
            return self._opponentfield
        elif pos == POS_OPP_HAND:
            return self._opponenthand
        elif pos == POS_OPP_GRAVE:
            return self._opponentgrave
        elif pos == POS_OPP_DAMAGE:
            return self._opponentdamage
        elif pos == POS_OPP_DECK:
            return self._opponentdeck
        elif pos == POS_OPP_RFG:
            return self._opponentrfg
        return -1

    def GetCardFromSerial(self, serial):
        for c in self._grave:
            if c.GetSerial() == serial:
                return c
        for c in self._damage:
            if c.GetSerial() == serial:
                return c
        for c in self._field:
            if c.GetSerial() == serial:
                return c
        for c in self._hand:
            if c.GetSerial() == serial:
                return c
        for c in self._deck:
            if c.GetSerial() == serial:
                return c
        for c in self._rfg:
            if c.GetSerial() == serial:
                return c
        return -1

    def NewCardSerial(self):
        s = str(self._serial)
        self._serial += 1
        return s

    def GetOpponentCardFromSerial(self, serial):
        for c in self._opponentgrave:
            if c.GetSerial() == serial:
                return c
        for c in self._opponentdamage:
            if c.GetSerial() == serial:
                return c
        for c in self._opponentfield:
            if c.GetSerial() == serial:
                return c
        for c in self._opponenthand:
            if c.GetSerial() == serial:
                return c
        for c in self._opponentdeck:
            if c.GetSerial() == serial:
                return c
        for c in self._opponentrfg:
            if c.GetSerial() == serial:
                return c
        return -1

    def NewOpponentCardSerial(self):
        s = str(self._opponentserial)
        self._opponentserial += 1
        return s

    def MoveCard(self, source, dest, card):
        self.MoveCardToTop(source, dest, card)

    def MoveCardToTop(self, source, dest, card):
        source.remove(card)
        dest.insert(0, card)

    def MoveCardToBottom(self, source, dest, card):
        source.remove(card)
        dest.append(card)

    def MoveCardTo(self, source, dest, card, pos):
        source.remove(card)
        dest.insert(pos, card)

    def AddCardTo(self, l, c, n):
        l.insert(n, c)

    def AddCardToTop(self, l, c):
        l.insert(0, c)

    def AddCardToBottom(self, l, c):
        l.append(c)

    def AddCardListToBottom(self, l, o):
        o.reverse()
        for c in o:
            l.append(c)

    def AddCardListToTop(self, l, o):
        o.reverse()
        for c in o:
            l.insert(0, c)
    
    def RemoveCard(self, l, c):
        l.remove(c)

    def RemoveCardFrom(self, l, n):
        return l.pop(n)

    def RemoveCardFromTop(self, l):
        return l.pop(0)

    def RemoveCardFromBottom(self, l):
        return l.pop(len(l)-1)

    def Shuffle(self):
        random.shuffle(self._deck)
        self.RefreshDeck()
        self.WriteGameMessage(self._engine.GetLangString('shuffled his deck.'), CHAT_PLAYER)
        self.WriteShufflePacket()
    
    def ShuffleHand(self):
        for c in self._hand:
            c.SetCardState(POS_HAND, face=FACE_UP)
        random.shuffle(self._hand)
        self.RefreshHand()
        self.WriteGameMessage(self._engine.GetLangString('shuffled his hand.'), CHAT_PLAYER)
        self.WriteShuffleHandPacket()

    def ResetGame(self):
        while len(self._field) > 0:
            c = self._field[0]
            self.MoveCard(self._field, self._deck, c)
            c.SetCardState(POS_DECK)
            c.Reparent(self._decklistctrl)
            c.Hide()
            c.Show()
        while len(self._grave) > 0:
            c = self._grave[0]
            self.MoveCard(self._grave, self._deck, c)
            c.SetCardState(POS_DECK)
            c.Reparent(self._decklistctrl)
            c.Hide()
            c.Show()
        while len(self._damage) > 0:
            c = self._damage[0]
            self.MoveCard(self._damage, self._deck, c)
            c.SetCardState(POS_DECK)
            c.Reparent(self._decklistctrl)
            c.Hide()
            c.Show()
        while len(self._rfg) > 0:
            c = self._rfg[0]
            self.MoveCard(self._rfg, self._deck, c)
            c.SetCardState(POS_DECK)
            c.Reparent(self._decklistctrl)
            c.Hide()
            c.Show()
        while len(self._hand) > 0:
            c = self._hand[0]
            self.MoveCard(self._hand, self._deck, c)
            c.SetCardState(POS_DECK)
            c.Reparent(self._decklistctrl)
            c.Hide()
            c.Show()
        self.RefreshAll()
        self.WriteGameMessage('Game Reset.', CHAT_PLAYER)
        self._scorectrl.SetPlayerScore(0)
        self.WriteResetGamePacket()
        self.Shuffle()

    def ResetOpponentGame(self):
        while len(self._opponentfield) > 0:
            c = self._opponentfield[0]
            self.MoveCard(self._opponentfield, self._opponentdeck, c)
            c.SetCardState(POS_OPP_DECK)
            c.Reparent(self._opponentdecklistctrl)
            c.Hide()
            c.Show()
        while len(self._opponentgrave) > 0:
            c = self._opponentgrave[0]
            self.MoveCard(self._opponentgrave, self._opponentdeck, c)
            c.SetCardState(POS_OPP_DECK)
            c.Reparent(self._opponentdecklistctrl)
            c.Hide()
            c.Show()
        while len(self._opponentdamage) > 0:
            c = self._opponentdamage[0]
            self.MoveCard(self._opponentdamage, self._opponentdeck, c)
            c.SetCardState(POS_OPP_DECK)
            c.Reparent(self._opponentdecklistctrl)
            c.Hide()
            c.Show()
        while len(self._opponentrfg) > 0:
            c = self._opponentrfg[0]
            self.MoveCard(self._opponentrfg, self._opponentdeck, c)
            c.SetCardState(POS_OPP_DECK)
            c.Reparent(self._opponentdecklistctrl)
            c.Hide()
            c.Show()
        while len(self._opponenthand) > 0:
            c = self._opponenthand[0]
            self.MoveCard(self._opponenthand, self._opponentdeck, c)
            c.SetCardState(POS_OPP_DECK)
            c.Reparent(self._opponentdecklistctrl)
            c.Hide()
            c.Show()
        self.RefreshOpponentAll()
        self._scorectrl.SetOpponentScore(0)
        self.WriteGameMessage('Game Reset.', CHAT_OPPONENT)

    def RefreshAll(self):
        self.RefreshHand()
        self.RefreshGrave()
        self.RefreshDamage()
        self.RefreshRFG()
        self.RefreshDeck()

    def RefreshOpponentAll(self):
        self.RefreshOpponentHand()
        self.RefreshOpponentGrave()
        self.RefreshOpponentDamage()
        self.RefreshOpponentRFG()
        self.RefreshOpponentDeck()

    # Packets
    def WritePacket(self, packet):
        if self._engine.Network.GetState() == network.ID_CONNECTED:
            try:
                self._engine.Network.Write(packet.Build())
            except:
                self.OnDisconnectPacket()

    def WriteChatPacket(self, m):
        self.WritePacket(packets.ChatPacket(m))

    def WriteDeckPacket(self):
        self.WritePacket(packets.DeckPacket(self._origdeck.GetCards()))

    def WriteShufflePacket(self):
        self.WritePacket(packets.ShufflePacket(self._deck))
    
    def WriteShuffleHandPacket(self):
        self.WritePacket(packets.ShuffleHandPacket(self._hand))
    
    def WriteMoveCardPacket(self, card, dest, dest2=0, x=0, y=0):
        x = self._opponentfieldctrl.GetSize().GetWidth() - x
        y = self._opponentfieldctrl.GetSize().GetHeight() - y
        self.WritePacket(packets.CardMovePacket(card.GetSerial(),dest,dest2,x,y))

    def WriteFlipCardPacket(self, card, sta):
        self.WritePacket(packets.CardFlipPacket(card.GetSerial(),sta))
        
    def WriteLifeChangePacket(self, change):
        self.WritePacket(packets.LifeChangePacket(change))
        
    def WritePhasePacket(self, phase):
        self.WritePacket(packets.PhasePacket(phase))
        
    def WriteRollPacket(self, faces, n):
        self.WritePacket(packets.RollPacket(faces, n))
        
    def WriteDisconnectPacket(self):
        self.WritePacket(packets.DisconnectPacket())
        
    def WriteTargetPacket(self, p, serial):
        self.WritePacket(packets.TargetPacket(p, serial))
        
    def WriteFlipCoinPacket(self, h):
        self.WritePacket(packets.FlipCoinPacket(h))
        
    def WriteResetGamePacket(self):
        self.WritePacket(packets.ResetGamePacket())
        
    def WriteLookPacket(self, n):
        self.WritePacket(packets.LookPacket(n))

    def WriteCardActionPacket(self, action):
        self.WritePacket(packets.CardActionPacket(action))

    def WriteCardCounterPacket(self, serial, action, count):
        self.WritePacket(packets.CardCounterPacket(serial, action, count))
    
    def WriteChangeControlPacket(self, serial, action, count):
        self.WritePacket(packets.ChangeControlPacket(serial, action, count))
    
    # Packet Events
    def OnConnectPacket(self, event):
        self.Parent.Show()
        self._opponentnick = event.data.ReadString()
        self._opponentversion = event.data.ReadString()
        self.WriteGameMessage(self._engine.GetLangString('Connected with: ') + self._opponentnick + ' (' + self._opponentversion + ')', CHAT_GAME)
        self.WriteDeckPacket()

    def OnChatPacket(self, event):
        self.WriteChatMessage(': ' + event.data.ReadString(), CHAT_OPPONENT)

    def OnDeckPacket(self, event):
        reader = event.data
        cards = []
        while 1:
            try:
                c = self._engine.FindCardByCardID(reader.ReadString())
            except:
                break
            cards.append(c)
        self._opponentorigdeck = Deck()
        for c in cards:
            self._opponentorigdeck.Add(c)
        deck = self._opponentorigdeck.GetGameCards()
        for c in deck:
            g = OpponentCardControl(self._opponentdecklistctrl, c.Duplicate(), self._engine, self, self.NewOpponentCardSerial(), cpos=POS_OPP_DECK)
            self.AddCardToBottom(self._opponentdeck, g)
        self.RefreshOpponentDeck()
        self.Shuffle()

    def OnDrawPacket(self, event):
        reader = event.data
        self.OnOpponentDeckDraw(reader.ReadBool())

    def OnShufflePacket(self, event):
        reader = event.data
        l = []
        while 1:
            try:
                l.append(self.GetOpponentCardFromSerial(reader.ReadString()))
            except:
               break
        self._opponentdeck = l
        self.RefreshOpponentDeck()
        self.WriteGameMessage(self._engine.GetLangString('shuffled his deck.'), CHAT_OPPONENT)

    def OnShuffleHandPacket(self, event):
        reader = event.data
        l = []
        while 1:
            try:
                l.append(self.GetOpponentCardFromSerial(reader.ReadString()))
            except:
               break
        self._opponenthand = l
        for c in self._opponenthand:
            c.SetCardState(POS_OPP_HAND, face=FACE_DOWN)
        self.RefreshOpponentHand()
        self.WriteGameMessage(self._engine.GetLangString('shuffled his hand'), CHAT_OPPONENT)
    
    def OnChangeControlPacket(self, event):
        reader = event.data
        l = []
        while 1:
            try:
                l.append(self.GetOpponentCardFromSerial(reader.ReadString()))
            except:
               break
        self._opponentfield = l
        self.WriteGameMessage(self._engine.GetLangString('Changed Control'), CHAT_OPPONENT)
    
    def OnCardMovePacket(self, event):
        reader = event.data
        card = self.GetOpponentCardFromSerial(reader.ReadString())
        dest = reader.ReadInt()
        self._opponentcurrentcard = card
        pos = card.GetCardPosition()
        if pos == POS_OPP_HAND: # Hand
            if dest == POS_OPP_DECK: # Deck
                dest2 = reader.ReadInt()
                if dest2 == 0: # Bottom Deck
                    self.OnOpponentCardHandToBottomDeck()
                elif dest2 == 1: # Top Deck
                    self.OnOpponentCardHandToTopDeck()
                elif dest2 == 4: # Bottom Hidden
                    self.OnOpponentCardHandToBottomDeckH()
                elif dest2 == 3: # Top Deck Hidden
                    self.OnOpponentCardHandToTopDeckH()
                else: # Deck
                    self.OnOpponentCardHandToDeckShuffle()
            elif dest == POS_OPP_GRAVE: # Grave
                self.OnOpponentCardHandToGrave()
            elif dest == POS_OPP_DAMAGE:
                self.OnOpponentCardHandToDamage()
            elif dest == POS_OPP_RFG: # RFG
                self.OnOpponentCardHandToRFG()
            elif dest == POS_OPP_FIELD: # Field
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                if dest2 == 0: # Vertical Face-Up
                    if card.IsMonster():
                        self.OnOpponentHandMonsterSummon()
                    else:
                        self.OnOpponentHandMTActivate()
                elif dest2 == 1: # Vertical Face-Down
                    self.OnOpponentHandMTPosition()
                else: # Horizontal Face-Down
                    self.OnOpponentHandMonsterPosition()
        elif pos == POS_OPP_FIELD:
            if dest == POS_OPP_HAND:
                self.OnOpponentCardFieldToHand()
            elif dest == POS_OPP_GRAVE:
                self.OnOpponentCardFieldToGrave()
            elif dest == POS_OPP_DAMAGE:
                self.OnOpponentCardFieldToDamage()
            elif dest == POS_OPP_RFG:
                self.OnOpponentCardFieldToRFG()
            elif dest == POS_OPP_DECK:
                dest2 = reader.ReadInt()
                if dest2 == 0:
                    self.OnOpponentCardFieldToBottomDeck()
                elif dest2 == 1:
                    self.OnOpponentCardFieldToTopDeck()
                else:
                    self.OnOpponentCardFieldToDeckShuffle()
            elif dest == POS_OPP_FIELD:
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                self.OnOpponentCardFieldMove(card, x, y)
        elif pos == POS_OPP_GRAVE:
            if dest == POS_OPP_HAND:
                self.OnOpponentCardGraveToHand()
            elif dest == POS_OPP_RFG:
                self.OnOpponentCardGraveToRFG()
            elif dest == POS_OPP_DAMAGE:
                self.OnOpponentCardGraveToDamage()
            elif dest == POS_OPP_DECK:
                dest2 = reader.ReadInt()
                if dest2 == 0:
                    self.OnOpponentCardGraveToBottomDeck()
                elif dest2 == 1:
                    self.OnOpponentCardGraveToTopDeck()
                elif dest2 == 2:
                    self.OnOpponentCardGraveToDeckShuffle()
            elif dest == POS_OPP_FIELD:
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                self.OnOpponentCardGraveToField()
        elif pos == POS_OPP_DAMAGE:
            if dest == POS_OPP_HAND:
                self.OnOpponentCardDamageToHand()
            elif dest == POS_OPP_RFG:
                self.OnOpponentCardDamageToRFG()
            elif dest == POS_OPP_GRAVE:
                self.OnOpponentCardDamageToGrave()
            elif dest == POS_OPP_DECK:
                dest2 = reader.ReadInt()
                if dest2 == 0:
                    self.OnOpponentCardDamageToBottomDeck()
                elif dest2 == 1:
                    self.OnOpponentCardDamageToTopDeck()
                elif dest2 == 2:
                    self.OnOpponentCardDamageToDeckShuffle()
            elif dest == POS_OPP_FIELD:
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                self.OnOpponentCardDamageToField()
        elif pos == POS_OPP_RFG:
            if dest == POS_OPP_HAND:
                self.OnOpponentCardRFGToHand()
            elif dest == POS_OPP_GRAVE:
                self.OnOpponentCardRFGToGrave()
            elif dest == POS_OPP_DAMAGE:
                self.OnOpponentCardRFGToDamage()
            elif dest == POS_OPP_DECK:
                dest2 = reader.ReadInt()
                if dest2 == 0:
                    self.OnOpponentCardRFGToBottomDeck()
                elif dest2 == 1:
                    self.OnOpponentCardRFGToTopDeck()
                elif dest2 == 2:
                    self.OnOpponentCardRFGToDeckShuffle()
            elif dest == POS_OPP_FIELD:
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                self.OnOpponentCardRFGToField()
        elif pos == POS_OPP_DECK:
            if dest == POS_OPP_HAND:
                self.OnOpponentCardDeckToHand()
            elif dest == POS_OPP_GRAVE:
                self.OnOpponentCardDeckToGrave()
            elif dest == POS_OPP_DECK: # Deck
                    dest2 = reader.ReadInt()
                    if dest2 == 4: # Bottom Hidden
                        self.OnOpponentCardHandToBottomDeckH2()
                    elif dest2 == 3: # Top Deck Hidden
                        self.OnOpponentCardHandToTopDeckH2()
            elif dest == POS_OPP_DAMAGE:
                self.OnOpponentCardDeckToDamage()
            elif dest == POS_OPP_RFG:
                self.OnOpponentCardDeckToRFG()
            elif dest == POS_OPP_FIELD:
                dest2 = reader.ReadInt()
                x = reader.ReadInt()
                y = reader.ReadInt()
                self._opponentcurrentcard = [card,x,y]
                self.OnOpponentCardDeckToField()
        
    def OnCardFlipPacket(self, event):
        reader = event.data
        card = self.GetOpponentCardFromSerial(reader.ReadString())
        self._opponentcurrentcard = card
        state = reader.ReadInt()
        pos = card.GetCardPosition()
        if pos == POS_OPP_FIELD:
            if state == 0:
                self.OnOpponentCardFieldFlip()
            elif state == 1:
                self.OnOpponentCardFieldFlipHorizontal()
            elif state == 2:
                self.OnOpponentCardFieldFlipVertical()
            elif state == 3:
                self.OnOpponentCardFieldHorizontal()
            elif state == 4:
                self.OnOpponentCardFieldVertical()

    def OnLifeChangePacket(self, event):
        change = event.data.ReadInt()
        self._scorectrl.SetOpponentScoreDiff(change)

    def OnPhasePacket(self, event):
        phase = event.data.ReadInt()
        if phase == 0:
            self._drawphasectrl.SelectPhase()
            self.WriteGameMessage('entered Stand Phase.', CHAT_OPPONENT)
        elif phase == 1:
            self._standbyphasectrl.SelectPhase()
            self.WriteGameMessage('entered Draw Phase.', CHAT_OPPONENT)
        elif phase == 2:
            self._mainphase1ctrl.SelectPhase()
            self.WriteGameMessage('entered Ride Phase.', CHAT_OPPONENT)
        elif phase == 3:
            self._battlephasectrl.SelectPhase()
            self.WriteGameMessage('entered Main Phase.', CHAT_OPPONENT)
        elif phase == 4:
            self._mainphase2ctrl.SelectPhase()
            self.WriteGameMessage('entered Battle Phase.', CHAT_OPPONENT)
        elif phase == 5:
            self._endphasectrl.SelectPhase()
            self.WriteGameMessage('ended turn.', CHAT_OPPONENT)

    def OnRollPacket(self, event):
        reader = event.data
        faces = reader.ReadInt()
        n = reader.ReadInt()
        self.WriteGameMessage(self._engine.GetLangString('rolled a d')+str(faces)+': '+str(n), CHAT_OPPONENT)

    def OnDisconnectPacket(self, event=None):
        self.WriteGameMessage('disconnected.', CHAT_OPPONENT)
        self._engine.Network.Close()

    def OnTargetPacket(self, event):
        reader = event.data
        if reader.ReadInt() == 1:
            card = self.GetCardFromSerial(reader.ReadString())
            card.Target()
            card.Hide()
            card.Show()
        else:
            card = self.GetOpponentCardFromSerial(reader.ReadString())
            card.Target()
            card.Hide()
            card.Show()

    def OnFlipCoinPacket(self, event):
        reader = event.data
        head = reader.ReadBool()
        if head:
            self.WriteGameMessage(self._engine.GetLangString('flipped a coin: Heads.'), CHAT_OPPONENT)
        else:
            self.WriteGameMessage(self._engine.GetLangString('flipped a coin: Tails.'), CHAT_OPPONENT)

    def OnResetGamePacket(self, event):
        self.ResetOpponentGame()

    def OnLookPacket(self, event):
        reader = event.data
        n = reader.ReadInt()
        if n == LOOK_DECK_YES:
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Deck'), CHAT_OPPONENT)
            self._opponentdeckctrl.SetTexture(self._engine.GetSkinImage('LookDeck'))
        elif n == LOOK_DECK_NO:
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Deck'), CHAT_OPPONENT)
            self._opponentdeckctrl.SetTexture(self._engine.GetSkinImage('Deck'))
        elif n == LOOK_GRAVE_YES:
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Drop Zone'), CHAT_OPPONENT)
        elif n == LOOK_GRAVE_NO:
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Drop Zone'), CHAT_OPPONENT)
        elif n == LOOK_DAMAGE_YES:
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Damage Zone'), CHAT_OPPONENT)
        elif n == LOOK_DAMAGE_NO:
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Damage Zone'), CHAT_OPPONENT)
        elif n == LOOK_RFG_YES:
            self.WriteGameMessage(self._engine.GetLangString('is looking at his Soul'), CHAT_OPPONENT)
        elif n == LOOK_RFG_NO:
            self.WriteGameMessage(self._engine.GetLangString('end looking at his Soul'), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_GRAVE_YES:
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Drop Zone"), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_GRAVE_NO:
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Drop Zone"), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_DAMAGE_YES:
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Damage Zone"), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_DAMAGE_NO:
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Damage Zone"), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_RFG_YES:
            self.WriteGameMessage(self._engine.GetLangString("is looking at his opponent's Soul"), CHAT_OPPONENT)
        elif n == LOOK_OPPONENT_RFG_NO:
            self.WriteGameMessage(self._engine.GetLangString("end looking at his opponent's Soul"), CHAT_OPPONENT)

    def OnCardActionPacket(self, event):
        reader = event.data
        action = reader.ReadInt()
        if action == ACTION_DISCARDTOP:
            self.OnOpponentActionDiscardTop()
        elif action == ACTION_REVEALTOP:
            self.OnOpponentActionRevealTop()
        elif action == ACTION_CHECKTOP:
            self.OnOpponentActionCheckTop()
        elif action == ACTION_SCTOP:
            self.OnOpponentActionSCTop()

    def OnCardCounterPacket(self, event):
        reader = event.data
        serial = reader.ReadString()
        card = self.GetOpponentCardFromSerial(serial)
        action = reader.ReadInt()
        count = reader.ReadInt()
        if action == 0: # Add Counters
            card.AddCounters(count)
            self.WriteGameMessage(' %s %s' % (self._engine.GetLangString("added a counter to"), card.GetCardName()), CHAT_OPPONENT)
        else: # Remove Counters
            card.RemoveCounters(count)
            self.WriteGameMessage(' %s %s' % (self._engine.GetLangString("removed a counter from"), card.GetCardName()), CHAT_OPPONENT)


class FieldControl(wx.Panel, wx.TextDropTarget):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, pos=(0,375), size=(700,300))
        self.SetDropTarget(FieldDropTarget(parent))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self._background = parent._engine.GetSkinImage('Field')

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._background, 0, 0)
    
class FieldDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnField(x, y, data)

class OpponentFieldControl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, pos=(0,41), size=(700,300))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self._background = parent._engine.GetSkinImage('OpponentField')

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._background, 0, 0)

class DeckListControl(wx.Frame):
    def __init__(self, parent):
        self._game = parent
        wx.Frame.__init__(self, parent, -1, 'Deck', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self._game.OnPopupDeckSearch()

class OpponentDeckListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Opponent Deck', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Hide()
        
'''class DeckListDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnDeck(x, y, data)
        pass'''

class OpponentGraveListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Opponent Drop Zone', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnOpponentGraveLClick()

class OpponentDamageListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Opponent Damage Zone', pos=(400,300), size=(400,130), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnOpponentDamageLClick()

class GraveListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Drop Zone', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.SetDropTarget(GraveListDropTarget(parent))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnGraveLClick()
    
class DamageListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Damage Zone', pos=(400,300), size=(400,130), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.SetDropTarget(DamageListDropTarget(parent))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnDamageLClick()
    
class GraveListDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnGrave(x, y, data)
    
class DamageListDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnDamage(x, y, data)
    
class OpponentRFGListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Opponent Soul', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnGamePopupOpponentRFG()

    def OnClose(self, event=None):
        self.Hide()

class RFGListControl(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Soul', pos=(400,300), size=(670,300), style=wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)
        self.SetDropTarget(RFGListDropTarget(parent))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Scroll = wx.ScrolledWindow(self,-1)
        self.Scroll.SetScrollbars(0, 1, 0, 200)
        self.Scroll.SetBackgroundColour(wx.Colour(33,35,36))

    def OnClose(self, event=None):
        self.Parent.OnGamePopupRFG()

class RFGListDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnRFG(x, y, data)

class DeckControl(GameObject):
    def __init__(self, parent, pos, t):
        GameObject.__init__(self, parent, pos, t)

class OpponentDeckControl(GameObject):
    def __init__(self, parent, pos, t):
        GameObject.__init__(self, parent, pos, t)

class GraveControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._grave) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._grave[0]), 1, 1, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Drop: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()

class DamageControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._damage) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._damage[0]), 1, 1, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Damage: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()
        
class RFGControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._rfg) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._rfg[0]), 1, 1, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Soul: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()

class OpponentGraveControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._opponentgrave) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._opponentgrave[0]), 0, 0, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Drop: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()

class OpponentDamageControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._opponentdamage) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._opponentdamage[0]), 0, 0, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Damage: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()

class OpponentRFGControl(GameObject):
    def __init__(self, parent, pos, t, game):
        self._game = game
        GameObject.__init__(self, parent, pos, t)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        if len(self._game._opponentrfg) > 0:
            dc.DrawBitmap(self._game._engine.GetCardGraveImage(self._game._opponentrfg[0]), 0, 0, True)
        else:
            dc.SetBrush(wx.Brush(wx.Colour(33,35,36)))
            dc.SetPen(wx.Pen(wx.Colour(33,35,36)))
            dc.DrawRectangle(0,0,self._texture.GetWidth(), self._texture.GetHeight())
        dc.DrawBitmap(self._texture, 0, 0, True)

    def UpdateCardTooltip(self, l):
        d = 0
        s = 'Soul: ' + str(len(l))
        if len(l) > 10:
            l = l[:11]
            d = 1
        for c in l:
            s += '\n' + c.GetCardName()
        if d:
            s += '\n...'
        tip = wx.ToolTip(s)
        tip.SetDelay(250)
        self.SetToolTip(tip)
        self.Hide()
        self.Show()

class HandControl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, pos=(1,676), size=(698,100))
        self.SetBackgroundColour(wx.Colour(33,35,36))
        self.SetDropTarget(HandListDropTarget(parent))

class HandListDropTarget(wx.TextDropTarget):
    def __init__(self, game):
        wx.TextDropTarget.__init__(self)
        self._game = game
    
    def OnDropText(self, x, y, data):
        self._game.OnCardDropOnHand(x, y, data)

class OpponentHandControl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, pos=(1,0), size=(698,40))
        self.SetBackgroundColour(wx.Colour(33,35,36))

class ScoreControl(GameObject):
    def __init__(self, parent):
        self._game = parent
        self._engine = self._game._engine
        GameObject.__init__(self, parent, (0,341), self._engine.GetSkinImage('Score'))
        self._player_score = 0
        self._opponent_score = 0
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        # Player
        self._player_menu = wx.Menu()
        item = wx.MenuItem(self._player_menu, -1, '-2')
        self._player_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPlayerPopupSub2000, item)
        item = wx.MenuItem(self._player_menu, -1, '-1')
        self._player_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPlayerPopupSub1000, item)
        item = wx.MenuItem(self._player_menu, -1, '+2')
        self._player_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPlayerPopupAdd1000, item)
        item = wx.MenuItem(self._player_menu, -1, '+1')
        self._player_menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnPlayerPopupAdd500, item)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        font = wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma")
        #font.SetNoAntiAliasing(True)
        dc.SetFont(font)
        dc.SetTextForeground(wx.WHITE)
        dc.DrawText(str(self._player_score), 16, 10)
        dc.DrawText(str(self._opponent_score), 82, 10)

    def OnRightUp(self, event):
        if self._game.Hit(event.GetX(), event.GetY(), wx.Rect(1,1,62,32)):
            self.OnPlayerPopup()
        #elif self._game.Hit(event.GetX(), event.GetY(), wx.Rect(64,1,64,32)):
            #self.OnOpponentPopup()

    def OnPlayerPopup(self):
        self.PopupMenu(self._player_menu)
    
    def OnPlayerPopupSub2000(self, event):
        self.SetPlayerScoreDiff(-2)

    def OnPlayerPopupSub1000(self, event):
        self.SetPlayerScoreDiff(-1)

    def OnPlayerPopupAdd1000(self, event):
        self.SetPlayerScoreDiff(2)

    def OnPlayerPopupAdd500(self, event):
        self.SetPlayerScoreDiff(1)

    def SetPlayerScoreDiff(self, diff):
        self._game.WriteLifeChangePacket(diff)
        self._player_score += diff
        if diff > 0:
            self._game.WriteGameMessage(self._engine.GetLangString("receives ") + str(abs(diff)) + " damage (" + str(self._player_score) + ")" , CHAT_PLAYER)
        else:
            self._game.WriteGameMessage(self._engine.GetLangString("recovers ") + str(abs(diff)) + " damage (" + str(self._player_score) + ")" , CHAT_PLAYER)
        self.Hide()
        self.Show()

    def SetOpponentScoreDiff(self, diff):
        self._opponent_score += diff
        if diff > 0:
            self._game.WriteGameMessage(self._engine.GetLangString("receives ") + str(abs(diff)) + " damage (" + str(self._opponent_score) + ")" , CHAT_OPPONENT)
        else:
            self._game.WriteGameMessage(self._engine.GetLangString("recovers ") + str(abs(diff)) + " life points (" + str(self._opponent_score) + ")" , CHAT_OPPONENT)
        self.Hide()
        self.Show()

    def SetPlayerScore(self, score):
        self._player_score = score
        self._game.WriteGameMessage(self._engine.GetLangString("'s damage is now ") + str(self._player_score) , CHAT_PLAYER)
        self.Hide()
        self.Show()

    def SetOpponentScore(self, score):
        self._opponent_score = score
        self._game.WriteGameMessage(self._engine.GetLangString("'s damage is now ") + str(self._opponent_score) , CHAT_OPPONENT)
        self.Hide()
        self.Show()

class CardControl(GameObject, wx.DataObjectSimple):
    def __init__(self, parent, card, engine, game, serial, cpos=0, cardmode=0, cardface=1):
        self._card = card
        self._cardposition = cpos
        self._cardface = cardface
        self._cardmode = cardmode
        self._engine = engine
        self._game = game
        self._cardtarget = False
        self._counters = 0
        t = self._engine.GetCardImage(self)
        GameObject.__init__(self, parent, (0,0), t)
        wx.DataObjectSimple.__init__(self)
        self.Bind(wx.EVT_MOTION, self.OnDrag)
        self._serial = serial
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOver)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWell)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseDClick)

    def AddCounters(self, n=1):
        self._counters += n
        self.Hide()
        self.Show()


    def RemoveCounters(self, n=1):
        self._counters -= n
        if self._counters < 0:
            self._counters = 0
        self.Hide()
        self.Show()

    def OnMouseWell(self, event):
        self._game._carddescriptionctrl.ScrollLines(-event.GetWheelRotation())

    def Target(self):
        if self._cardtarget:
            self._cardtarget = False
        else:
            self._cardtarget = True

    def IsTarget(self):
        return self._cardtarget

    def OnRightUp(self, event):
        self._game.OnCardPopup(self)
    
    def OnMouseDClick(self, event):
        self._game.OnCardDClick(self)
    
    def OnMouseOver(self, event):
        desc = self._card.Name + '\n'
        desc += self._card.Class + '/'
        desc +=  self._card.Clan + '/'
        desc += self._card.Race + '\n'
        desc += 'GRADE:' + self._card.Grade + '\n'
        if self._card.Skill != '':
            desc += 'SKILL: ' + self._card.Skill + '\n'
        if self._card.Class == 'Trigger Unit':
            desc += 'TRIGGER: ' + self._card.Trigger + '\n'
        desc += '\n' + 'POWER:' + self._card.Power + ' CRITICAL:' + self._card.Critical +' SHIELD:' + self._card.Shield + '\n'
        if self._card.Effect != '':
            desc +=  '\n' + self._card.Effect + '\n'
        if self._card.Illustrator != '?' and self._card.Illustrator != '':
            desc += '\n' + 'Illustrator: ' + self._card.Illustrator  + '\n'
        if self._card.Text != '?' and self._card.Text != '':
            desc += '\n' + 'Card text: ' + self._card.Text + '\n'   
        desc +=  self._card.CardID
        self._game.RefreshCardInfo(self._card.Name, self._engine.GetBigCardImage(self._card), desc)
    
    def RefreshTexture(self):
        self._texture = self._engine.GetCardImage(self)
        self.SetSize((self._texture.GetWidth(), self._texture.GetHeight()))

    def OnDrag(self, event):
        if not event.Dragging():
            return
        if not event.LeftIsDown():
            return
        tt = self.GetSerial()
        tdo = wx.TextDataObject(tt)
        tds = wx.DropSource(self)
        tds.SetData(tdo)
        tds.DoDragDrop(True)
    
    def GetCardName(self):
        return self._card.Name
    
    def GetCardTrigger(self):
        c = 'No Trigger'
        if self._card.Class == 'Trigger Unit':
            c = 'Trigger:' + self._card.Trigger
        return c

    def GetCardShield(self):
        c = '+' + self._card.Shield
        return c
    
    def GetCardEffect(self):
        return self._card.Effect
    
    def GetCardClan(self):
        return self._card.Clan
    
    def GetCardClass(self):
        return self._card.Class
    
    def GetCardPosition(self):
        return self._cardposition
    
    def GetCardFace(self):
        return self._cardface
    
    def GetCardMode(self):
        return self._cardmode

    def GetSerial(self):
        return self._serial

    def IsMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap':
            return True
        else:
            return False

    def IsNormalMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Effect') == 0: return True
        else: return False

    def IsEffectMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Effect') > 0: return True
        else: return False

    def IsSynchro(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Synchro') > 0:
            return True
        else:
            return False
    
    def IsToken(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Token') > 0:
            return True
        else:
            return False

    def IsRitual(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Ritual') > 0: return True
        else: return False

    def IsTrap(self):
        if self._card.Clan == 'Trap': return True
        else: return False

    def IsSpell(self):
        if self._card.Clan == 'Spell': return True
        else: return False

    def IsFaceDown(self):
        if self._cardface == FACE_DOWN:
            return 1
        else:
            return 0

    def IsFaceUp(self):
        if self._cardface == FACE_UP:
            return 1
        else:
            return 0

    def IsHorizontal(self):
        if self._cardmode == CARD_HORIZONTAL:
            return 1
        else:
            return 0

    def IsVertical(self):
        if self._cardmode == CARD_VERTICAL:
            return 1
        else:
            return 0

    def SetCardPosition(self, p):
        if self.IsTarget():
            self.Target()
        self._cardposition = p

    def SetCardState(self, pos=POS_FIELD, mode=CARD_VERTICAL, face=FACE_UP):
        self._cardposition = pos
        self._cardmode = mode
        self._cardface = face
        if self.IsTarget():
            self.Target()
        if not pos == POS_FIELD:
            self.RemoveCounters(self._counters)
        self.RefreshTexture()

    def FaceUp(self):
        if self.IsTarget():
            self.Target()
        self._cardface = FACE_UP

    def FaceDown(self):
        if self.IsTarget():
            self.Target()
        self._cardface = FACE_DOWN

    def Vertical(self):
        if self.IsTarget():
            self.Target()
        self._cardmode = CARD_VERTICAL

    def Horizontal(self):
        if self.IsTarget():
            self.Target()
        self._cardmode = CARD_HORIZONTAL

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._texture, 0, 0, True)
        font = wx.Font(pointSize=8,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma")
        #font.SetNoAntiAliasing(True)
        dc.SetFont(font)
        name = self.GetCardName()
        p = self.GetCardPosition()
        if p == 2 or p == 3 or p == 4 or p == 5 or p == 6:
            name = name[:26]
            nx = 2
            ny = 1
            sx = 10
            sy = 10
            dc.SetTextForeground(wx.BLACK)
            #dc.DrawText(name, nx, ny)
        if self.IsTarget():
            tbmp = self._engine.GetSkinImage('Target')
            if self.IsVertical():
                dc.DrawBitmap(tbmp, 14, 24, True)
            else:
                dc.DrawBitmap(tbmp, 28, 18, True)
        if self._counters > 0:
            dc.SetTextForeground('#000000')
            dc.SetFont(wx.Font(pointSize=10,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_BOLD, faceName="Tahoma"))
            if self.IsVertical():
                dc.GradientFillLinear((8, 55, 14, 14), '#ffffff', '#ffffff', wx.NORTH)
                dc.DrawText(str(self._counters), 8, 55)
            else:
                dc.GradientFillLinear((8, 28, 14, 14), '#ffffff', '#ffffff', wx.NORTH)
                dc.DrawText(str(self._counters), 8, 28)

class OpponentCardControl(GameObject):
    def __init__(self, parent, card, engine, game, serial, cpos=0, cardmode=0, cardface=1):
        self._card = card
        self._cardposition = cpos
        self._cardface = cardface
        self._cardmode = cardmode
        self._engine = engine
        self._game = game
        self._counters = 0
        self._cardtarget = False
        t = self._engine.GetCardImage(self)
        GameObject.__init__(self, parent, (0,0), t)
        self._serial = serial
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOver)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWell)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

    def AddCounters(self, n=1):
        self._counters += n
        self.Hide()
        self.Show()

    def RemoveCounters(self, n=1):
        self._counters -= n
        if self._counters < 0:
            self._counters = 0
        self.Hide()
        self.Show()

    def OnMouseWell(self, event):
        if self.IsFaceUp():
            self._game._carddescriptionctrl.ScrollLines(-event.GetWheelRotation())

    def Target(self):
        if self._cardtarget:
            self._cardtarget = False
        else:
            self._cardtarget = True

    def IsTarget(self):
        return self._cardtarget

    def OnRightUp(self, event):
        self._game._opponentcurrentcard = self
        self._game.OnOpponentCardTarget()
    
    def OnMouseOver(self, event):
        if self.IsFaceDown():
            return
        desc = self._card.Name + '\n'
        desc += self._card.Class + '/'
        desc +=  self._card.Race + '/'
        desc += self._card.Clan + '\n'
        desc += 'GRADE:' + self._card.Grade + '\n'
        if self._card.Skill != '':
            desc += 'SKILL: ' + self._card.Skill + '\n'
        if self._card.Class == 'Trigger Unit':
            desc += 'TRIGGER: ' + self._card.Trigger + '\n'
        desc += '\n' + 'POWER:' + self._card.Power + ' CRITICAL:' + self._card.Critical +' SHIELD:' + self._card.Shield + '\n'
        if self._card.Effect != '':
            desc +=  '\n' + self._card.Effect
        if self._card.Illustrator != '?' and self._card.Illustrator != '':
            desc += '\n' + 'Illustrator: ' + self._card.Illustrator + '\n'   
        desc +=  self._card.CardID
        self._game.RefreshCardInfo(self._card.Name, self._engine.GetBigCardImage(self._card), desc)
    
    def RefreshTexture(self):
        self._texture = self._engine.GetCardImage(self)
        self.SetSize((self._texture.GetWidth(), self._texture.GetHeight()))
    
    def GetCardName(self):
        return self._card.Name
    
    def GetCardTrigger(self):
        c = 'No Trigger'
        if self._card.Class == 'Trigger Unit':
            c = 'Trigger:' + self._card.Trigger
        return c
    
    def GetCardShield(self):
        c = '+' + self._card.Shield
        return c
    
    def GetCardEffect(self):
        return self._card.Effect
    
    def GetCardClan(self):
        return self._card.Clan
    
    def GetCardClass(self):
        return self._card.Class
    
    def GetCardPosition(self):
        return self._cardposition
    
    def GetCardFace(self):
        return self._cardface
    
    def GetCardMode(self):
        return self._cardmode

    def GetSerial(self):
        return self._serial

    def IsMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap': return True
        else: return False

    def IsNormalMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Effect') == 0: return True
        else: return False

    def IsEffectMonster(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Effect') > 0: return True
        else: return False
    
    def IsSynchro(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Synchro') > 0: return True
        else: return False
    
    def IsToken(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Token') > 0: return True
        else: return False

    def IsRitual(self):
        if self._card.Clan != 'Spell' and self._card.Clan != 'Trap' and self._card.Class.count('Ritual') > 0: return True
        else: return False

    def IsTrap(self):
        if self._card.Clan == 'Trap': return True
        else: return False

    def IsSpell(self):
        if self._card.Clan == 'Spell': return True
        else: return False

    def IsFaceDown(self):
        if self._cardface == FACE_DOWN:
            return 1
        else:
            return 0

    def IsFaceUp(self):
        if self._cardface == FACE_UP:
            return 1
        else:
            return 0

    def IsHorizontal(self):
        if self._cardmode == CARD_HORIZONTAL:
            return 1
        else:
            return 0

    def IsVertical(self):
        if self._cardmode == CARD_VERTICAL:
            return 1
        else:
            return 0

    def SetCardPosition(self, p):
        if self.IsTarget():
            self.Target()
        self._cardposition = p

    def SetCardState(self, pos=POS_OPP_FIELD, mode=CARD_VERTICAL, face=FACE_UP):
        self._cardposition = pos
        self._cardmode = mode
        self._cardface = face
        if self.IsTarget():
            self.Target()
        if not pos == POS_FIELD:
            self.RemoveCounters(self._counters)
        self.RefreshTexture()

    def FaceUp(self):
        if self.IsTarget():
            self.Target()
        self._cardface = FACE_UP

    def FaceDown(self):
        if self.IsTarget():
            self.Target()
        self._cardface = FACE_DOWN

    def Vertical(self):
        if self.IsTarget():
            self.Target()
        self._cardmode = CARD_VERTICAL

    def Horizontal(self):
        if self.IsTarget():
            self.Target()
        self._cardmode = CARD_HORIZONTAL

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._texture, 0, 0, True)
        font = wx.Font(pointSize=8,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma")
        #font.SetNoAntiAliasing(True)
        dc.SetFont(font)
        name = self.GetCardName()
        p = self.GetCardPosition()
        if p == 9 or p == 10 or p == 11 or p == 12 or p == 13:
            name = name[:26]
            nx = 2
            ny = 1
            sx = 10
            sy = 10
            dc.SetTextForeground(wx.BLACK)
            #dc.DrawText(name, nx, ny)
        if self.IsTarget():
            tbmp = self._engine.GetSkinImage('Target')
            if self.IsVertical():
                dc.DrawBitmap(tbmp, 14, 24, True)
            else:
                dc.DrawBitmap(tbmp, 28, 18, True)
        if self._counters > 0:
            if self.IsFaceDown():
                dc.SetTextForeground(wx.WHITE)
            else:
                dc.SetTextForeground(wx.BLACK)
            dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_BOLD, faceName="Tahoma"))
            if self.IsVertical():
                dc.DrawText(str(self._counters), 8, 48)
            else:
                dc.DrawText(str(self._counters), 7, 22)

class Note(GameObject):
    def __init__(self, parent, pos, game):
        self._game = game
        self._label = ""
        GameObject.__init__(self, parent, pos, self._game._engine.GetSkinImage('Note'))
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.OnDClick()

    def OnRightUp(self, event=None):
        menu = wx.Menu()
        item = wx.MenuItem(menu, -1, "Delete")
        self.Bind(wx.EVT_MENU, self.OnDelete)
        menu.AppendItem(item)
        self.PopupMenu(menu)

    def OnDelete(self, event=None):
        self.Hide()
        self.Close()

    def OnDClick(self, event=None):
        dialog = wx.TextEntryDialog(self, "Insert the note's text")
        if dialog.ShowModal() == wx.ID_OK:
            self._label = dialog.GetValue()
            tip = wx.ToolTip(self._label)
            tip.SetDelay(250)
            self.SetToolTip(tip)
            self.Hide()
            self.Show()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=7,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Verdana"))
        dc.SetTextForeground(wx.BLACK)
        l = len(self._label)
        if l > 10:
            line1 = self._label[:11]
            dc.DrawText(line1, 2, 2)
            if l > 20:
                line2 = self._label[10:21]
                dc.DrawText(line2, 2, 15)
            else:
                line2 = self._label[11:len(self._label)]
                dc.DrawText(line2, 2, 15)
        else:
            dc.DrawText(self._label, 2, 2)

class DrawPhaseControl(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (241+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(0)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('entered Stand Phase'), CHAT_PLAYER)
        #self._game.OnDeckDraw()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("Stand", 18, 10)

class StandbyPhaseControl(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (304+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(1)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('entered Draw Phase'), CHAT_PLAYER)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("Draw", 10, 10)

class MainPhase1Control(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (367+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(2)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('entered Ride Phase'), CHAT_PLAYER)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("Ride", 14, 10)

class BattlePhaseControl(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (430+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(3)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('entered Main Phase'), CHAT_PLAYER)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("Main", 16, 10)

class MainPhase2Control(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (493+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(4)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('entered Battle Phase'), CHAT_PLAYER)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("Battle", 14, 10)

class EndPhaseControl(GameObject):
    def __init__(self, parent):
        self._game = parent
        GameObject.__init__(self, parent, (556+80,341), self._game._engine.GetSkinImage('PhaseBack'))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._sel = False
        self._opp = False

    def SelectPhase(self):
        self._game.ClearPhases()
        self._sel = True
        self._opp = True
        self.Hide()
        self.Show()

    def IsSelected(self):
        return self._sel

    def OnLeftUp(self, event=None):
        self._game.WritePhasePacket(5)
        self._game.ClearPhases()
        self._sel = True
        self._opp = False
        self.Hide()
        self.Show()
        self._game.WriteGameMessage(self._game._engine.GetLangString('ended turn.'), CHAT_PLAYER)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.SetFont(wx.Font(pointSize=9,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL, faceName="Tahoma"))
        if self._sel:
            if self._opp:
                dc.SetTextForeground(wx.RED)
            else:
                dc.SetTextForeground(wx.BLUE)
        else:
            dc.SetTextForeground(wx.WHITE)
        dc.DrawBitmap(self._texture, 0, 0, True)
        dc.DrawText("End", 20, 10)
        