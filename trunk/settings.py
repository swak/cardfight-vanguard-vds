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

import os, sys
import xmlhandler


def LoadSettings(path): 
    settings = dict()
    xmldoc = xmlhandler.LoadXml(os.path.join(path, 'settings.xml'))
    if xmldoc == False: 
        f = open(os.path.join(path, 'settings.xml'),'w')
        f.write(defaultsettings)
        f.close()
        xmldoc = xmlhandler.LoadXml(os.path.join(path, 'settings.xml'))
    for node in xmldoc.firstChild.childNodes:
            settings[node.getAttribute('name')] = node.getAttribute('value')  
    return settings

defaultsettings = '''<?xml version="1.0" ?>
<settings><node name="Hotkey-Next Phase" value="CTRL+SPACE"/><node name="Full Screen" value="No"/><node name="Hotkey-RollD6" value="CTRL+R"/><node name="Language" value="English"/><node name="Hotkey-Reset Game" value="ALT+CTRL+G"/><node name="Hotkey-Flip Coin" value="CTRL+F"/><node name="Hotkey-Draw" value="CTRL+D"/><node name="Hotkey-Draw and Show" value="CTRL+W"/><node name="Update" value="Yes"/><node name="Nick" value="n00b"/><node name="Hotkey-Shuffle" value="CTRL+S"/><node name="Skin" value="Default"/><node name="Hotkey-End Turn" value="CTRL+E"/><node name="LastDeckPath" value=""/><node name="OpenLastDeck" value="Yes"/><node name="ShowFaceUpCardName" value="No"/></settings>'''