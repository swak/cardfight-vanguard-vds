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

class Deck():
    def __init__(self):
        self.Cards = []

    def Add(self,card):
        self.Cards.append(card)

    def Remove(self,card):
        if self.Cards.count(card) > 0:
            self.Cards.remove(card)

    def RemoveId(self,id):
        if len(self.Cards)-1 >= id:
            self.Cards.pop(id)

    def RemoveName(self,name,side=False):
        i = 0
        for c in self.Cards:
            if c.Name == name and c.IsSide == side:
                self.Cards.remove(c)
                return
            i += 1

    def RemoveCardID(self,cardID):
        i = 0
        for c in self.Cards:
            if c.CardID == cardID:
                self.Cards.remove(c)
                return
            i += 1

    def GetMonsters(self):
        li = []
        for c in self.Cards:
            if c.Class != 'Trigger Unit':
                li.append(c)
        return li
    
    def GetG0(self):
        g0 = 0
        for c in self.Cards:
            if c.Grade == '0':
                g0+=1
        return g0

    def GetG1(self):
        g1 = 0
        for c in self.Cards:
            if c.Grade == '1':
                g1+=1
        return g1
    
    def GetG2(self):
        g2 = 0
        for c in self.Cards:
            if c.Grade == '2':
                g2+=1
        return g2
    
    def GetG3(self):
        g3 = 0
        for c in self.Cards:
            if c.Grade == '3':
                g3+=1
        return g3

    def GetTrigger(self):
        li = []
        for c in self.Cards:
            if c.Class == 'Trigger Unit':
                li.append(c)
        return li

    def GetCards(self):
        return self.Cards

    def GetGameCards(self):
        li = []
        for c in self.Cards:
            li.append(c)
        return li
    
    def CheckCard(self, cardID):
        cc= 0
        for c in self.Cards:
            if c.CardID == cardID:
                cc+=1
        return cc
    
    def CheckHT(self, cardID):
        ht = 0
        for c in self.Cards:
            if c.Trigger == '+5000 Power, Heal':
                ht+=1
        return ht
    
    def CheckHT2(self):
        ht2 = 0
        for c in self.Cards:
            if c.Trigger == '+5000 Power, Heal':
                ht2+=1
        return ht2
    
    def CheckST(self):
        st = 0
        for c in self.Cards:
            if c.Trigger == '+5000 Power, Stand':
                st+=1
        return st
    
    def CheckCT(self):
        ct = 0
        for c in self.Cards:
            if c.Trigger == '+5000 Power, +1 Critical':
                ct+=1
        return ct
    
    def CheckDT(self):
        dt = 0
        for c in self.Cards:
            if c.Trigger == '+5000 Power, Draw 1':
                dt+=1
        return dt