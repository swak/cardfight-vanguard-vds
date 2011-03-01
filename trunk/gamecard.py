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

class GameCard():

    def __init__(self,cardID,name,uclass,trigger,grade,skillicon,power,critical,shield,clan,race,effect,text,illustrator):
        self.CardID=cardID
        self.Name=name
        self.Class=uclass
        self.Trigger=trigger
        self.Skill=skillicon
        self.Clan=clan
        self.Race=race
        self.Grade=grade
        self.Critical=critical
        self.Power=power
        self.Shield=shield
        self.Effect=effect
        self.Text=text
        self.Illustrator=illustrator

    def IsMonster(self):
      return True
    
    def IsTrigger(self):
        if self.Class == 'Trigger Unit':
            return True
        else:
            return False



    def Duplicate(self):
        return GameCard(self.CardID,self.Name,self.Class,self.Trigger,self.Grade,self.Skill,self.Power,self.Critical,self.Shield,self.Clan,self.Race,self.Effect,self.Text,self.Illustrator)