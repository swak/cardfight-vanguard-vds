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
            li.append(c)
        return li

    def GetCards(self):
        return self.Cards

    def GetGameCards(self):
        li = []
        for c in self.Cards:
            li.append(c)
        return li