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

import sys, os, wx, time, re, urllib
from xml.dom import minidom
from sqlite3 import dbapi2
import version, mainform, gamecard, settings, skin, language, deck, xmlhandler
import network, gameframe, dialogs, updater, keyhandler

def ListDirs(path):
    
    rd = os.listdir(path) 
    dirs = [] 
    for s in rd:
        dp = os.path.join(path,s) 
        if os.path.isdir(dp): 
            dirs.append(dp) 
    return dirs 

def ListFiles(path):
    
    rd = os.listdir(path) 
    files = []
    for s in rd:
        dp = os.path.join(path,s) 
        if os.path.isfile(dp):
            files.append(dp)
    return files

# Class engine
class Engine():

    
    def __init__(self):
        self._dev = False
        self.Application = wx.App()
        self.BaseDirectory = os.getcwd()

        #splash = wx.SplashScreen(wx.Bitmap(os.path.join(self.BaseDirectory, 'splash.png'), wx.BITMAP_TYPE_PNG), wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT, 0, None, -1)
        self.SkinsDirectory = os.path.join(self.BaseDirectory, 'Skins') # Skins Directory
        self.LanguagesDirectory = os.path.join(self.BaseDirectory, 'Languages') # Languages Directory
        self.DecksDirectory = os.path.join(self.BaseDirectory, 'Decks') # Decks Directory
        self.ImagesDirectory = os.path.join(self.BaseDirectory, 'Images') # Images Directory

        if not os.path.exists(self.SkinsDirectory):
            os.mkdir(self.SkinsDirectory)
        if not os.path.exists(self.LanguagesDirectory):
            os.mkdir(self.LanguagesDirectory)
        if not os.path.exists(self.DecksDirectory):
            os.mkdir(self.DecksDirectory)
        if not os.path.exists(self.ImagesDirectory):
            os.mkdir(self.ImagesDirectory)

        # Variabile che contiene l'ip
        self._ip = ''
    
        self.Settings = settings.LoadSettings(self.BaseDirectory)

        # Update Check
        if self.GetSetting('Update') == 'Yes':
            if updater.CheckVersionUpdate(self.GetVersion()):
                toupdate = updater.CheckUpdate(self.BaseDirectory)
                if len(toupdate) > 0:
                    if wx.MessageDialog(None,'An update is avaible,\nwould you like to update now?','',wx.YES_NO | wx.ICON_QUESTION | wx.YES_DEFAULT).ShowModal() == wx.ID_YES:
                        updater.Update(self.BaseDirectory,toupdate)
                        wx.MessageDialog(None,'Now you can restart the application.','',wx.OK | wx.ICON_INFORMATION).ShowModal()
                        sys.exit()

        self.Skins = skin.LoadSkins(self.SkinsDirectory) 
        self.Languages = language.LoadLanguages(self.LanguagesDirectory) 

        self.Deck = deck.Deck()
        self.DeckPath = ''

        self.DatabaseCardsCount = len(self.GetAllCards())
        
        self.Frame = mainform.MainFrame(engine=self, parent=None, title="CRAY ONLINE Deck Construction",size=(1024,600))
        self.Frame.SetIcon(wx.IconFromLocation(wx.IconLocation(os.path.join(self.BaseDirectory,'J_16x16.ico'))))
        
        if self.GetSetting('OpenLastDeck') == 'Yes':
            lastdeckpath = self.GetSetting('LastDeckPath')
            if lastdeckpath and os.path.exists(lastdeckpath):
                self.Frame.OnOpen(path=lastdeckpath)

        #splash.Refresh() # Refresh Splash
        #time.sleep(1) # Sleep di 1 secondo per mostrare lo splash :P
        #splash.Close() # Chiudo lo splash
        self.Frame.Show() # Mostro il frame
        self.Application.MainLoop() # Loop dell'applicazione
    
    def CheckMissingImages(self):
        '''Check for missing images'''
        cards = self.GetAllCards()
        l = self.DownloadImageList()
        m = []
        for c in cards:
            if not os.path.exists(os.path.join(self.ImagesDirectory, c.Name + '.jpg')) and l.count(c.Name + '.jpg') > 0:
                m.append(c.Name)
        return m
    
    def DownloadImage(self, n):
        '''Download missing images'''
        if not self.CheckConnection():
            return 0
        url = 'http://jproject.xz.lt/vanguard/updates/images/%s.jpg' % n
        try:
            urllib.urlretrieve(url, os.path.join(self.ImagesDirectory,'%s.jpg'%n))
            return 1
        except: pass
        return 0

    def DownloadImageList(self):
        if not self.CheckConnection():
            return ''
        url = 'http://jproject.xz.lt/vanguard/updates/images/'
        s = ''
        try: 
            u = urllib.urlopen(url)
            while 1:
                r = u.read()
                if r == '': break
                else: s += r
        except: pass
        return s
    
    def CheckConnection(self):
        '''Checks if an internet connection is avaible'''
        if self.GetIp():
            return True
        else:
            return False
    

    def GetIp(self):
        if not self._ip:
            try:
                l = re.findall('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', urllib.urlopen("http://checkip.dyndns.org/").read())[0]
                self._ip = '%s.%s.%s.%s' % (l[0],l[1],l[2],l[3])
            except:
                self._ip == ''
        return self._ip

    def GetSmile(self, name):
        #if os.path.exists(os.path.join(self.SmilesDirectory,name + '.gif')):
        #    return os.path.join(self.SmilesDirectory,name + '.gif')
        #else:
        #    return os.path.join(self.SmilesDirectory,'none.gif')
        return self.GetSkin().GetPath(name)

    def GetName(self):
        return version.GetName()

    def GetVersion(self):
        return version.GetVersion()

    def GetChangelog(self):
        return version.GetChangelog()

    def GetNameVersion(self):
        return '%s %s' % (version.GetName(), version.GetVersion())

    #Metodo che ritorna una carta dato il suo codice
    def FindCardByCardID(self, cardID):
        con = dbapi2.connect(os.path.join(self.BaseDirectory, 'cards.db')) #Mi connetto al db
        c = con.cursor() #Creo un oggetto cursor
        c.execute('SELECT * FROM cards WHERE cardID="'+cardID+'"') #Eseguo la query
        row = c.fetchone() #Ottengo i valori trovati
        card = gamecard.GameCard(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14]) #Creo la carta
        return card

    #Metodo che ritorna una lista di carte data parte del suo nome
    def FindCardByNameLike(self, name):
        con = dbapi2.connect(os.path.join(self.BaseDirectory, 'cards.db')) #Mi connetto al db
        c = con.cursor() #Creo un oggetto cursor
        c.execute('SELECT * FROM cards WHERE name LIKE "%'+name+'%"') #Eseguo la query
        data = c.fetchall() #Ottengo tutti i valori trovati
        li = list() #Creo la lista che conterra' le carte
        for row in data:
            card = gamecard.GameCard(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14]) #Creo la carta
            li.append(card) #Aggiungo alla lista ogni carta
        li.sort(lambda x, y: cmp(x.Name, y.Name))
        return li
    
    def FindCardByName(self, name):
        con = dbapi2.connect(os.path.join(self.BaseDirectory, 'cards.db')) #Mi connetto al db
        c = con.cursor() #Creo un oggetto cursor
        c.execute('SELECT * FROM cards WHERE name="'+name+'"') #Eseguo la query
        row = c.fetchone() #Ottengo i valori trovati
        card = gamecard.GameCard(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14]) #Creo la carta
        return card

    def FinCardByNameAndExp(self, exp, name):
        li = self.FindCardByNameLike(name)
        for c in li:
            print c.Name
            if c.CardID.upper().count(exp.upper()):
                card = c
                break
        return card

    def AdvancedSearch(self, li):
        if li[0]:
            cards = self.FindCardByNameLike(li[0])
        else:
            cards = self.GetAllCards()
        
        se = []
        if li[1]:
            for c in cards:
                if c.Effect.lower().count(li[1].lower()):
                    se.append(c)
        else:
            se = cards
        
        if li[2] == 'Any':
            return se
        # Monster
        elif li[2] == 'Unit':
            s1 = []
            for c in se:
                if not c.IsMonster():
                    continue
                if li[3] == 'Any':
                    s1.append(c)
                elif li[3] == 'Normal Unit':
                    if not c.Class.count('Trigger Unit'):
                        s1.append(c)
                elif li[3] == 'Trigger Unit':
                    if c.Class.count('Trigger Unit'):
                        s1.append(c)
            s2 = []
            if li[4] == 'Any':
                s2 = s1
            else:
                for c in s1:
                    if li[4] == c.Race:
                        s2.append(c)
            s3 = []
            if li[5] == '1' and li[6] == '3':
                s3 = s2
            else:
                for c in s2:
                    if int(c.Grade) >= int(li[5]) and int(c.Grade) <= int(li[6]):
                        s3.append(c)
            s4 = []
            if li[7] == '0' and li[8] == '20000':
                s4 = s3
            else:
                for c in s3:
                    if c.Power.count('?') or c.Power.count('x') or c.Power.count('X'):
                        continue
                    if int(c.Power) >= int(li[7]) and int(c.Power) <= int(li[8]):
                        s4.append(c)
            s5 = []
            if li[9] == 'Any':
                s5 = s4
            else:
                for c in s4:
                    if c.Clan.count(li[9]):
                        s5.append(c)
            return s5

    def GetAllCards(self):
        
        con = dbapi2.connect(os.path.join(self.BaseDirectory, 'cards.db')) #Mi connetto al db
        c = con.cursor() #Creo un oggetto cursor
        c.execute('SELECT * FROM cards') #Eseguo la query
        data = c.fetchall() #Ottengo tutti i valori trovati
        li = list() #Creo la lista che conterra' le carte
        for row in data:
            card = gamecard.GameCard(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14]) #Creo la carta
            li.append(card) #Aggiungo alla lista ogni carta
        li.sort(lambda x, y: cmp(x.Name, y.Name))
        return li

    def GetCardImage(self, c):
        p = c.GetCardPosition()
        if p == 2 or p == 3 or p == 4 or p == 5 or p == 6 or p == 9 or p == 10 or p == 11 or p == 12 or p == 13:
            if not os.path.exists('Images/' + c.GetCardName() + '.jpg'):
                b = self.ResizeBitmap(self.GetSkinImage('MonsterEffect'), 62, 88)
                return b
            img = self.GetImageCardScaled(c.GetCardName())
            return img
        if c.IsFaceDown():
            bmp = self.GetSkinImage('CardBack')
            if c.IsHorizontal():
                bmp = self.Rotate90Bitmap(bmp)
            return bmp
        att = c.GetCardClan()
        ty = c.GetCardClass()
        if att != 'Spell' and att != 'Trap':# Scelgo lo sfondo adatto
            if ty.find('Fusion') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Fusion'), 62, 88)
            elif ty.find('Synchro') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Synchro'), 62, 88)              
            elif ty.find('Ritual') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Ritual'), 62, 88)
            elif ty.find('Token') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Token'), 62, 88)
            elif ty.find('Effect') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('MonsterEffect'), 62, 88)
            else:
                b = self.ResizeBitmap(self.GetSkinImage('Monster'), 62, 88)
        elif att == 'Trap':
            b = self.ResizeBitmap(self.GetSkinImage('Trap'), 62, 88)
        elif att == 'Spell':
            b = self.ResizeBitmap(self.GetSkinImage('Spell'), 62, 88)
        bmp = self.GetImageCardScaled(c.GetCardName())
        if not bmp is -1:
            dc = wx.MemoryDC()
            dc.SelectObject(b)
            dc.DrawBitmap(bmp, 0, 0)
        if c.IsHorizontal():
            b = self.Rotate90Bitmap(b)
        return b

    def GetCardGraveImage(self, c):
        att = c.GetCardClan()
        ty = c.GetCardClass()
        if att != 'Spell' and att != 'Trap':# Scelgo lo sfondo adatto
            if ty.find('Fusion') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Fusion'), 62, 88)
            elif ty.find('Synchro') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Synchro'), 62, 88)     
            elif ty.find('Ritual') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Ritual'), 62, 88)
            elif ty.find('Token') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('Token'), 62, 88)
            elif ty.find('Effect') > -1:
                b = self.ResizeBitmap(self.GetSkinImage('MonsterEffect'), 62, 88)
            else:
                b = self.ResizeBitmap(self.GetSkinImage('Monster'), 62, 88)
        elif att == 'Trap':
            b = self.ResizeBitmap(self.GetSkinImage('Trap'), 62, 88)
        elif att == 'Spell':
            b = self.ResizeBitmap(self.GetSkinImage('Spell'), 62, 88)
        bmp = self.GetImageCardScaled(c.GetCardName())
        if not bmp is -1:
            dc = wx.MemoryDC()
            dc.SelectObject(b)
            dc.DrawBitmap(bmp, 0, 0)
        return b

    def GetBigCardImage(self, c):
        dc = wx.MemoryDC()

        BackSkin = self.GetSkinImage('MonsterEffect')
        
        dc.SelectObject(BackSkin) # Carico lo sfondo
        
        dc.SetFont(wx.Font(pointSize=8,family=wx.FONTFAMILY_DEFAULT,style=wx.FONTSTYLE_NORMAL,weight=wx.FONTWEIGHT_NORMAL,faceName='Tahoma'))
        dc.DrawText(c.Name[:21], 14,12)# Nome carta, limitato ai primi 20 caratteri
       
        cbmp = self.GetImageCard(c.Name)
        if not cbmp is -1:
            dc.DrawBitmap(cbmp, 0, 0)
        
        return dc.GetAsBitmap()

    def ResizeBitmap(self, bmp, w, h, q=wx.IMAGE_QUALITY_HIGH):
        img = wx.ImageFromBitmap(bmp)
        img.Rescale(w, h, q)
        return wx.BitmapFromImage(img)
    
    def Rotate90Bitmap(self, bmp):
        img = wx.ImageFromBitmap(bmp)
        return wx.BitmapFromImage(img.Rotate90())

    def GetImageCardScaled(self, name):
        path = os.path.join(self.ImagesDirectory, name + '.jpg')
        if os.path.exists(path):
            image = wx.Image(path)
            image.Rescale(62, 88, wx.IMAGE_QUALITY_HIGH)
            return wx.BitmapFromImage(image)
        return -1

    def GetImageCard(self, name):
        path = os.path.join(self.ImagesDirectory, name + '.jpg')
        if os.path.exists(path):
            return wx.Bitmap(path)
        return -1

    def GetSkin(self): # Metodo che ritorna la skin usata
        key = self.GetSetting('Skin')
        if self.Skins.has_key(key):
            return self.Skins[key]
        else:
            return self.Skins['Default']

    def GetAllSkinName(self):
        li = []
        for sk in self.Skins.keys():
            li.append(sk)
        return li

    def GetSkinName(self):
        return self.GetSetting('Skin')

    def GetLang(self):
        key = self.GetSetting('Language')
        if self.Languages.has_key(key):
            return self.Languages[key]
        else:
            return self.Languages['English']

    def GetAllLangName(self):
        li = []
        for la in self.Languages.keys():
            li.append(la)
        return li

    def GetLangName(self):
        return self.GetSetting('Language')

    def GetAllHotkeys(self):
        d = {}
        for k in self.Settings.keys():
            if k.startswith('Hotkey-'):
                d[k[7:]] = self.Settings[k]
        return d

    def GetAllHotkeysName(self):
        l = []
        for k in self.Settings.keys():
            if k.startswith('Hotkey-'):
                l.append(k[7:])
        return l

    def SetHotkey(self, name, cardID):
        if self.Settings.has_key('Hotkey-' + name):
            self.Settings['Hotkey-' + name] = cardID

    def GetHotkeyCode(self, name):
        return self.GetSetting('Hotkey-'+name)

    def GetSkinImage(self, name): # Ritorna un immagine della skin data la sua key
         skin = self.GetSkin()
         if skin.Exists(name):
             return skin.GetImage(name)
         elif self.Skins['Default'].Exists(name):
             return self.Skins['Default'].GetImage(name)
         else:
             return self.Skins['Default'].GetImage('none')

    def GetSetting(self, name):
        if self.Settings.has_key(name):
            return self.Settings[name]
        else:
            return ''

    def SaveSettings(self, st={}):
        for key,value in st.items():
            self.Settings[key] = value
        path = os.path.join(self.BaseDirectory,'settings.xml')
        if os.path.exists(path):
            os.remove(path)
        handle = open(path,'w')
        doc = minidom.Document()
        element = doc.createElement("settings")
        doc.appendChild(element)
        for key,value in self.Settings.items():
            node = doc.createElement("node")
            node.setAttribute('name',key)
            element.appendChild(node)
            node.setAttribute('value',value)
            element.appendChild(node)
        data = doc.toxml()
        handle.write(data)
        handle.close()
        self.Settings = settings.LoadSettings(self.BaseDirectory)

    def GetLangString(self,name, *args):
        lang = self.GetLang()
        if lang.Exists(name):
            s = lang.GetString(name)
        else:
            s = self.Languages['English'].GetString(name)
        for a in args:
            s = s.replace('%s', a, 1)
        return s

    def SaveDeck(self,deck,path):
        handle = open(path,'w')
        doc = minidom.Document()
        element = doc.createElement("deck")
        doc.appendChild(element)
        for c in deck.Cards:
            node = doc.createElement("card")
            node.setAttribute('cardID',c.CardID)
            element.appendChild(node)
        data = doc.toxml()
        handle.write(data)
        handle.close()

    def OpenDeck(self,path):
        xmldoc = xmlhandler.LoadXml(path)
        self.Deck = deck.Deck()
        for node in xmldoc.firstChild.childNodes:
            c = self.FindCardByCardID(node.getAttribute('cardID'))
            c.IsSide = 0
            self.Deck.Add(c)

    def NewDeck(self):
        self.Deck = deck.Deck()
        self.DeckPath = ''

if __name__ == "__main__":
    e = Engine() # Richiamo il metodo principale dell'applicazione