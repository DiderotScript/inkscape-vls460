#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
vls460_print.py
adapted from print_win32_vector.py
This extension will generate vector graphics printout, specifically for Windows GDI32.

Copyright (C) 2019 SCRIPT@Paris Diderot, inge@script.univ-paris-diderot.fr
Copyright (C) 2012 Alvin Penner, penner@vaxxine.com

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
# local library
import inkex
# from inkex.elements import ShapeElement
import simplestyle
import simpletransform
import cubicsuperpath
from vls460_gdi import GdiPrinter

inkex.localize() # Initialize gettext
if not inkex.sys.platform.startswith('win'):
    exit(_("sorry, this will run only on Windows, exiting..."))

class Vls460Printer(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.not_converted = []
        self.groupstyle = {}

        self.OptionParser.add_option(
            '--ignore-stroke-width', type="inkbool", action='store',
            dest='ignoreStrokeWidth', default=True,
            help='Ignore stroke-width')

    def process_shape(self, node, mat):
        readStrokeWidth = not self.options.ignoreStrokeWidth
        color = None                    # stroke color
        fillcolor = None                # fill color
        stroke = 1                      # pen width in printer pixels
        # Very NB : If the pen width is greater than 1 then the output will Not be a vector output !
        node_style = node.get('style')
        if node_style:
            style = self.groupstyle.copy()
            style.update( simplestyle.parseStyle(node_style) )
            if style.has_key('stroke'):
                if style['stroke'] and style['stroke'] != 'none' and style['stroke'][0:3] != 'url':
                    rgb = simplestyle.parseColor(style['stroke'])
                    color = rgb[0] + 256*rgb[1] + 256*256*rgb[2]
            if readStrokeWidth and style.has_key('stroke-width'):
                stroke = self.unittouu(style['stroke-width'])/self.unittouu('1px')
                stroke = int(stroke*self.scale)
            if style.has_key('fill'):
                if style['fill'] and style['fill'] != 'none' and style['fill'][0:3] != 'url':
                    fill = simplestyle.parseColor(style['fill'])
                    fillcolor = fill[0] + 256*fill[1] + 256*256*fill[2]
        if node.tag == inkex.addNS('path','svg'):
            d = node.get('d')
            if not d:
                self.not_converted.append(node.get('id'))
                return
            p = cubicsuperpath.parsePath(d)
        elif node.tag == inkex.addNS('rect','svg'):
            x = float(node.get('x'))
            y = float(node.get('y'))
            width = float(node.get('width'))
            height = float(node.get('height'))
            p = self.printer.rectangle_path(x, y, width, height)
        elif node.tag == inkex.addNS('defs','svg') or node.tag == inkex.addNS('metadata','svg'):
            # ignore svg:defs and svg:metadata
            return
        elif node.tag.startswith('{'+inkex.NSS['svg']) == False:
            # ignore non-SVG elements
            return
        else:
            self.not_converted.append(node.get('id'))
            return
        trans = node.get('transform')
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        simpletransform.applyTransformToPath(mat, p)
        self.printer.draw_path(p, color, stroke, fillcolor)

    def process_clone(self, node):
        trans = node.get('transform')
        x = node.get('x')
        y = node.get('y')
        mat = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        if x:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, float(x)], [0.0, 1.0, 0.0]])
        if y:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, 0.0], [0.0, 1.0, float(y)]])
        # push transform
        if trans or x or y:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], mat))
        # get referenced node
        refid = node.get(inkex.addNS('href','xlink'))
        refnode = self.getElementById(refid[1:])
        if refnode is not None:
            if refnode.tag == inkex.addNS('g','svg'):
                self.process_group(refnode)
            elif refnode.tag == inkex.addNS('use', 'svg'):
                self.process_clone(refnode)
            else:
                self.process_shape(refnode, self.groupmat[-1])
        # pop transform
        if trans or x or y:
            self.groupmat.pop()

    def process_group(self, group):
        style = group.get('style')
        if style:
            style = simplestyle.parseStyle(style)

        if group.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
            if style:
                if style.has_key('display'):
                    if style['display'] == 'none' and self.visibleLayers:
                        return

        #stack the style of each group
        prevstyle = self.groupstyle.copy()
        if style:
            self.groupstyle.update(style)

        trans = group.get('transform')
        if trans:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], simpletransform.parseTransform(trans)))
        for node in group:
            if node.tag == inkex.addNS('g','svg'):
                self.process_group(node)
            elif node.tag == inkex.addNS('use', 'svg'):
                self.process_clone(node)
            else:
                self.process_shape(node, self.groupmat[-1])
        if trans:
            self.groupmat.pop()

        #pop the current group style
        self.groupstyle = prevstyle

    def effect(self):
        # Start GDI printing
        self.printer = GdiPrinter()

        # Create GDI document
        docname = self.document.getroot().xpath('@sodipodi:docname', namespaces=inkex.NSS) or ['VLS460 Inkscape document.svg']
        self.printer.create_document(docname[0])
        self.scale = self.printer.scale / self.unittouu('1px')

        # Recalculate the scale
        h = self.unittouu(self.getDocumentHeight())
        doc = self.document.getroot()
        # process viewBox height attribute to correct page scaling
        viewBox = doc.get('viewBox')
        if viewBox:
            viewBox2 = viewBox.split(',')
            if len(viewBox2) < 4:
                viewBox2 = viewBox.split(' ')
            self.scale *= h / self.unittouu(self.addDocumentUnit(viewBox2[3]))

        # Init matrix, start processing the SVG document
        self.groupmat = [[[self.scale, 0.0, 0.0], [0.0, self.scale, 0.0]]]
        self.process_group(doc)

        # Send to printer
        self.printer.close()

        # Information message
        if len(self.not_converted):
            inkex.errormsg(_('Total number of non-converted objects: {}').format(len(self.not_converted)))
            # return list of IDs in case the user needs to find a specific object
            inkex.errormsg('IDs = ' + ','.join(self.not_converted))

if __name__ == '__main__':
    e = Vls460Printer()
    e.affect()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
