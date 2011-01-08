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
import engine, xmlhandler

class language():

    def __init__(self,p):
        self.path = p
        self.props = dict()
        self.name = ''
        xmldoc = xmlhandler.LoadXml(self.path)
        for node in xmldoc.firstChild.childNodes:
            if not node.getAttribute('name') == 'Name':
                self.props[node.getAttribute('name')] = node.getAttribute('value')
            else:
                self.name = node.getAttribute('value')
    
    def GetString(self,name):
        if not self.props.has_key(name):
            return name
        return self.props[name]

    def Exists(self,name):
        return self.props.has_key(name)

def LoadLanguages(dir):
    langs = dict()
    files = engine.ListFiles(dir) 
    for s in files: 
        ln = language(s) 
        langs[ln.name] = ln 
    return langs