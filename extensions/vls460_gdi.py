#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
vls460_gdi.py
adapted from print_Inkscape/extensions/win32_vector.py
This extension will generate vector graphics printout, specifically for Windows GDI32.

Copyright (C) 2019 SCRIPT@Paris Diderot, inge@script.univ-paris-diderot.fr
Copyright (C) 2012 Alvin Penner, penner@vaxxine.com

This is a modified version of the file dxf_outlines.py by Aaron Spike, aaron@ekips.org
It will write only to the default printer.
The printing preferences dialog will be called.
In order to ensure a pure vector output, use a linewidth < 1 printer pixel

- see http://www.lessanvaezi.com/changing-printer-settings-using-the-windows-api/
- get GdiPrintSample.zip at http://archive.msdn.microsoft.com/WindowsPrintSample

TODO: use the new inkex.elements.ShapeElement.get_path() from the new incoming version 1.0 Inkscape.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''
# standard library
from ctypes import *
import sys

if not sys.platform.startswith('win'):
    exit("sorry, this will run only on Windows, exiting...")

LASER_PRINTER="VLS4.60"
GDI32 = WinDLL("gdi32.dll")
SPOOL = WinDLL("winspool.drv")
LOGBRUSH = c_long*3
DM_IN_PROMPT = 4 # call printer property sheet
DM_OUT_BUFFER = 2 # write to DEVMODE structure

# From inkex.errormsg
def errormsg(msg):
    if isinstance(msg, unicode):
        sys.stderr.write(msg.encode("utf-8") + "\n")
    else:
        sys.stderr.write((unicode(msg, "utf-8", errors='replace') + "\n").encode("utf-8"))

class GdiPrinter():

    def __init__(self):
        pname, hPrinter = self.open_printer(LASER_PRINTER)
        if pname is None:
            pname, hPrinter = self.open_printer()
            errormsg('Falling back to default printer "{}"'.format(pname.value))
        if pname is None:
            exit('Failed to open the "{}" or default printer'.format(LASER_PRINTER))

        # get printer properties dialog
        #FIXME: hWnd = windll.user32.GetForegroundWindow()
        hWnd = 0
        pcchBuffer = c_long()
        pcchBuffer = SPOOL.DocumentPropertiesA(hWnd, hPrinter, pname, None, None, 0)
        #FIXME: pDevMode = create_string_buffer(pcchBuffer + 100) # allocate extra just in case
        pDevMode = create_string_buffer(pcchBuffer)
        pcchBuffer = SPOOL.DocumentPropertiesA(hWnd, hPrinter, pname, byref(pDevMode), None, DM_IN_PROMPT + DM_OUT_BUFFER)
        if pcchBuffer != 1: # user clicked Cancel
            exit()

        self.pname = pname
        self.hPrinter = hPrinter
        self.pDevMode = pDevMode

    def open_printer(self, name=None):
        if name is None:
            pcchBuffer = c_ulong()
            SPOOL.GetDefaultPrinterA(None, byref(pcchBuffer))     # get length of printer name
            pname = create_string_buffer(pcchBuffer.value)
            SPOOL.GetDefaultPrinterA(pname, byref(pcchBuffer))    # get printer name
        else:
            pname = create_string_buffer(LASER_PRINTER)

        hPrinter = c_long()
        if SPOOL.OpenPrinterA(pname.value, byref(hPrinter), None) == 0:
            return None, None

        return pname, hPrinter

    def create_document(self, docname):
        pname = self.pname
        hPrinter = self.hPrinter
        pDevMode = self.pDevMode

        self.hDC = GDI32.CreateDCA(None, pname, None, byref(pDevMode))

        class DOCINFO(Structure):
            _fields_ = [
                ("cbSize", c_long),
                ("lpszDocName", c_char_p),
                ("lpszOutput", c_char_p),
                ("lpszDataType", c_char_p),
                ("fwType", c_ulong),
            ]
        docInfo = DOCINFO(sizeof(DOCINFO), docname, None, "raw", 0)
        if GDI32.StartDocA(self.hDC, byref(docInfo)) < 0:
            exit() # user clicked Cancel
        self.scale = (ord(pDevMode[58]) + 256.0*ord(pDevMode[59]))/96 # use PrintQuality from DEVMODE

    def close(self):
        GDI32.EndDoc(self.hDC)
        SPOOL.ClosePrinter(self.hPrinter)

    def rectangle_path(self, x, y, width, height):
        p = [[[x, y],[x, y],[x, y]]]
        p.append([[x + width, y],[x + width, y],[x + width, y]])
        p.append([[x + width, y + height],[x + width, y + height],[x + width, y + height]])
        p.append([[x, y + height],[x, y + height],[x, y + height]])
        p.append([[x, y],[x, y],[x, y]])
        return [p]

    def draw_path(self, p, color=None, stroke=1, fillcolor=None):
        if color is not None:
            hPen = GDI32.CreatePen(0, stroke, color)
            GDI32.SelectObject(self.hDC, hPen)
            self.emit_path(p)
        if fillcolor is not None:
            brush = LOGBRUSH(0, fillcolor, 0)
            hBrush = GDI32.CreateBrushIndirect(addressof(brush))
            GDI32.SelectObject(self.hDC, hBrush)
            GDI32.BeginPath(self.hDC)
            self.emit_path(p)
            GDI32.EndPath(self.hDC)
            GDI32.FillPath(self.hDC)

    def emit_path(self, p):
        for sub in p:
            GDI32.MoveToEx(self.hDC, int(sub[0][1][0]), int(sub[0][1][1]), None)
            POINTS = c_long*(6*(len(sub)-1))
            points = POINTS()
            for i in range(len(sub)-1):
                points[6*i]     = int(sub[i][2][0])
                points[6*i + 1] = int(sub[i][2][1])
                points[6*i + 2] = int(sub[i + 1][0][0])
                points[6*i + 3] = int(sub[i + 1][0][1])
                points[6*i + 4] = int(sub[i + 1][1][0])
                points[6*i + 5] = int(sub[i + 1][1][1])
            GDI32.PolyBezierTo(self.hDC, addressof(points), 3*(len(sub)-1))
        return

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
