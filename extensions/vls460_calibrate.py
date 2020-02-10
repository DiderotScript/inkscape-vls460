#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
vls460_calibrate.py
This extension will print a small calibration image.

Copyright (C) 2020 SCRIPT@Paris Diderot, inge@script.univ-paris-diderot.fr

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
from os.path import expanduser
from optparse import OptionParser
import sys
# local library
from vls460_gdi import GdiPrinter, errormsg

LASER_TEMPLATE="""[VLS4.60]
VectorPerformance=1 
VectorOptimizer=3 
RasterOptimizer=2 
DitherType=1 
MechTweak=0 
PrintMode=0 
PrintDir=68 
FixtureType=0 
ShoulderResourceID=0 
ImageDensity=53 
RastMarkingAdj=0 
VectMarkingAdj=0 
VectCuttingAdj=0 
FrameRasters=0 
LaserWatts1=60 
LaserWatts2=0 
LaserMode=0 
PageHeight=6096 
PageWidth=4572 
RotaryOverlap=19200 
RotorCircumference=0 
RotaryFactor=10000 
VectorXScale=10000 
VectorYScale=10000 
Enhanced=0 
Definition=0 
Contrast=0 
Density=0 
MaterialCode=0 
MaterialOrigin=0 
ShoulderMils=0 
CustomHeightMils=0 
MaterialThickness=0 
Texture=0 0 
3DPwrCalib=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile00=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile10=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile20=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile30=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile40=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile50=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile60=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile70=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile80=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfile90=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileA0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileB0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileC0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileD0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileE0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderProfileF0=0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0                
ShoulderName= 
InvertColor=0 
MetricPage=1 
Mirror=0 
DualHeadInstalled=0 
SuperMode=0 
UseZPos=1 
PenPowers={powers}
PenSpeedsCips={speeds}
PenRates={rates}
PenKHz=0 0 0 0 0 0 0 0        
PenSimmer=200 200 200 200 200 200 200 200        
PenWaveform=0 0 0 0 0 0 0 0        
PenZDisp={zdisp}
PenColorOrder=0 1 2 3 4 5 6 7        
PenAirAssist=0 0 0 0 0 0 0 0        
PenLaser=1 1 1 1 1 1 1 1        
PenMode={modes}
Language=Français
LLTweak=0 
RasterDir=66 
Compress=0 
"""

class Vls460Calibrate():
    def __init__(self):
        optionParser = OptionParser()

        # emulate inkex.Effect.OptionParser(--id)
        optionParser.add_option(
            "--id", action="append", type="string",
            dest="ids", default=[],
            help="-ignored-")
        # emulate inkex.Effect.OptionParser(--selected-nodes)
        optionParser.add_option(
            "--selected-nodes", action="append", type="string",
            dest="selected_nodes", default=[],
            help="-ignored-")

        optionParser.add_option(
            '--operation', action='store', type='choice',
            dest='operation', choices=['engraving', 'cutting'],
            default='engraving', help='Engraving or cutting')
        optionParser.add_option(
            '--thickness', action='store', type='float',
            dest='thickness', default=3, help='Thickness in millimeters')
        optionParser.add_option(
            '--min_power', action='store', type='int',
            dest='min_power', default=60, help='Minimum power')
        optionParser.add_option(
            '--max_power', action='store', type='int',
            dest='max_power', default=80, help='Maximum power')
        optionParser.add_option(
            '--min_speed', action='store', type='int',
            dest='min_speed', default=30, help='Minimum speed')
        optionParser.add_option(
            '--max_speed', action='store', type='int',
            dest='max_speed', default=100, help='Maximum speed')
        optionParser.add_option(
            '--file', action='store', type='string',
            dest='file', default="~\\Desktop\\calibration.las", help='Laser configuration file')

        self.OptionParser = optionParser

    def draw_rectangle(self, x, y, width, height, color="#000000", cut=False):
        # assuming that color is a string like "#ff6600"
        # red = color[1:3]
        # green = color[3:5]
        # blue = color[5:7]
        color = int(color[1:3], 16) \
                + (int(color[3:5], 16)<<8) \
                + (int(color[5:7], 16)<<16)

        p = self.printer.rectangle_path(x, y, width, height)

        if cut:
            self.printer.draw_path(p, color=color)
        else:
            self.printer.draw_path(p, fillcolor=color)

    def affect(self, args=sys.argv[1:], output=True):
        options, args = self.OptionParser.parse_args(sys.argv[1:])

        operation = options.operation
        min_power = options.min_power * 10
        max_power = options.max_power * 10
        min_speed = options.min_speed * 10
        max_speed = options.max_speed * 10
        thickness = options.thickness
        output_las = options.file

        steps = 8 # number of different colors (including the first color "black")

        inch = 25.4 # 1 inch = 25,4 mm
        zdisp = [int(1000 * thickness / inch)] * steps

        d_power = (max_power - min_power) / (steps - 1)
        d_speed = (max_speed - min_speed) / (steps - 1)

        powers = [int(min_power + d_power * i) for i in range(0, steps)]
        speeds = [int(min_speed + d_speed * i) for i in range(0, steps)]

        modes = [1 if operation == 'engraving' else 2] * steps
        rates = [500 if operation == 'engraving' else 250] * steps

        # Write laser configuration file NOW
        laser_config = LASER_TEMPLATE.format(
            powers=" ".join(str(i) for i in powers),
            speeds=" ".join(str(i) for i in speeds),
            zdisp=" ".join(str(i) for i in zdisp),
            modes=" ".join(str(i) for i in modes),
            rates=" ".join(str(i) for i in rates))
        with open(expanduser(output_las), 'w') as fh:
            fh.write(laser_config)

        # Start GDI printing
        self.printer = GdiPrinter()

        # Create GDI document
        self.printer.create_document('VLS460 {} p{:d}-{:d} v{:d}-{:d}'.format(
            operation,
            min_power,
            max_power,
            min_speed,
            max_speed))
        #self.scale = self.printer.scale / self.unittouu('1px')
        millimeter = 3.77952755913 # from inkex.Effect.__uuconv['mm']
        self.scale = self.printer.scale * millimeter

        # Rectangles
        d, width, height = 20, 30, 65
        colors = [
            ["#000000", 'black'],
            ["#ff0000", 'red'],
            ["#00ff00", 'green'],
            ["#ffff00", 'yellow'],
            ["#0000ff", 'blue'],
            ["#ff00ff", 'pink'],
            ["#00ffff", 'cyan'],
            ["#ff6600", 'orange'],
        ]
        for i, color in enumerate(colors):
            x = d + (width + d) * (i % 4)
            y = d + (height+ d) * (i / 4)
            self.draw_rectangle(x, y, width, height, color[0], modes[i]==2)


        # Send to printer
        self.printer.close()

        # Postlude : information message
        errormsg("\n".join([
                ' Power |  Speed | DPI | Z axis |  Mode | Color',
                '----------------------------------------------',
            ] + [
                '{p:5.1f}% | {v:5.1f}% | {r:3d} | {z:6.2f} | {m:5} | {c}'.format(
                    c=colors[i][1],
                    m=('Trame' if modes[i]==1 else 'Vect'),
                    p=(powers[i]/10.0),
                    v=(speeds[i]/10.0),
                    r=rates[i],
                    z=thickness
                ) for i in range(0, len(powers))
            ]))


if __name__ == '__main__':
    e = Vls460Calibrate()
    e.affect()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
