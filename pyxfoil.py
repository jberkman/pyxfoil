"""PYXFOIL: XFOIL AUTOMATION USING PYTHON
Logan Halstrom
EAE 127
UCD
CREATED:  15 SEP 2015
MODIFIED: 17 OCT 2018

DESCRIPTION: Provides functions for automating XFOIL runs.
Each function will iteratively build a list of inputs. When you are ready,
use the RunXfoil command to run the input list

NOTE: Since input list is predetermined, runs cannot be reiterated.
Make sure to set the iter limit high enough, that each simulation will
work on the first try

TO CALL IN A SCRIPT:
import sys
sys.path.append('path/to/pyxfoil.py')
import pyxfoil

FUTURE IMPROVEMENTS:

------------------------------------------------------------------------
MIT License

Copyright (c) 2017 Logan Halstrom

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------------------------------------------------
"""

import os
import sys
import re
import numpy as np
import subprocess
import pandas as pd

########################################################################
### GENERAL FILE AND PROCESS UTILITIES #################################
########################################################################

def MakeOutputDir(savedir):
    """make results output directory if it does not already exist.
    instring --> directory path from script containing folder
    """
    #split individual directories
    splitstring = savedir.split('/')
    prestring = ''
    for string in splitstring:
        prestring += string + '/'
        try:
            os.mkdir(prestring)
        except Exception:
            pass

def GetParentDir(savename):
    """Get parent directory from path of file"""
    #split individual directories
    splitstring = savename.split('/')
    parent = ''
    #concatenate all dirs except bottommost
    for string in splitstring[:-1]:
        parent += string + '/'
    return parent

def FindBetween(string, before='^', after=None):
    """Search 'string' for characters between 'before' and 'after' characters
    If after=None, return everything after 'before'
    Default before is beginning of line
    """
    if after == None and before != None:
        match = re.search('{}(.*)$'.format(before), string)
        if match != None:
            return match.group(1)
        else:
            return 'No Match'
    else:
        match = re.search('(?<={})(?P<value>.*?)(?={})'.format(before, after), string)
        if match != None:
            return match.group('value')
        else:
            return 'No Match'

def IsItWindows():
    """Return true if operating system is windows"""
    return True if os.name == 'nt' else False

def ErrorMessage(text):
    """Format an error output message
    """
    return "\n\n" \
    "********************************************************************\n" \
    "{}\n" \
    "********************************************************************" \
    "\n\n".format(text)

########################################################################
### XFOIL AUTOMATION CLASS #############################################
########################################################################

class Xfoil:
    def __init__(self, foil='0012', naca=True, Re=0, Iter=100,
        xfoilpath=None, headless=True):
        """Initialize class for specific airfoil.
        foil --> airfoil name, either NACA digits or path to geometry file
        naca --> True for naca digits, False for geometry file
        Re --> Reynolds number (inviscid if zero)
        Iter --> number of iterations per simulation (XFOIL default: 20)
        xfoilpath --> path to xfoil executable file
        headless  --> run xfoil without graphical output (avoids X11/XQuartz dependency)
        """

        #DETERMINE OPERATING SYSTEM
        self.win = IsItWindows()

        #SET PATH TO XFOIL FOR CURRENT OPERATING SYSTEM
        if xfoilpath != None:
            #Manually specify path to Xfoil
            self.xfoilpath = xfoilpath
        elif self.win:
            #Windows default location is in same folder as python script
            self.xfoilpath = 'xfoil.exe'
            #check dependencies
            if not os.path.isfile(self.xfoilpath):
                txt = "PYXFOIL ERROR: Put xfoil.exe in same folder as pyxfoil.py"
                sys.exit(ErrorMessage(txt))
        else:
            #Mac Install location
            self.xfoilpath = "/Applications/Xfoil.app/Contents/Resources/xfoil"
            #check dependencies
            if not os.path.isfile(self.xfoilpath):
                txt = "PYXFOIL ERROR: Xfoil.app is not installed"
                sys.exit(ErrorMessage(txt))
            if not os.path.isfile('/opt/X11/bin/xquartz'):
                txt = "PYXFOIL ERROR: X11/xquartz not installed"
                print(ErrorMessage(txt))


        #SAVE RUN PARAMETERS
        #Reynolds number
        self.Re = Re
        #Maximum iteration
        self.Iter = Iter
        #MAKE AIRFOIL NAME
        self.naca = naca
        if self.naca:
            #4-digit NACA to be loaded from equation
            self.name = 'naca' + foil
        else:
            #Load airfoil from file
            #airfoil name is between parent path and file extension
            parent = GetParentDir(foil)
            self.name = FindBetween(foil, parent, '\.')
        #CREATE SAVE DIRECTORY
            #Save in Data/airfoilname/
        self.savepath = 'Data/{}'.format(self.name)
        MakeOutputDir(self.savepath)

        #INITIALIZE COMMAND INPUT LIST
        self.input = ''

        #TURN OFF GRAPHICS (MAKE XFOIL "HEADLESS")
            #avoids XQuartz incompatibility
        if headless:
            self.TurnOffGraphics()

        #LOAD AIRFOIL (AND START INPUT LIST)
        self.foil = foil
        self.LoadGeom()

    def AddInput(self, cmd):
        """Add input command to command list
        cmd --> string command to add
        """
        self.input += '{}\n'.format(cmd)

    def RunXfoil(self, quiet=True):
        """Once input command list has been built, run all commands with this
        quiet --> true for no XFOIL output to screen
        """
        #Supress output if quiet option, otherwise write XFOIl output to screen
        stdout = open(os.devnull, 'wb') if quiet else None

        #START XFOIL
        xf = subprocess.Popen(self.xfoilpath,
                              stdin=subprocess.PIPE,
                              stdout=stdout,
                              stderr=None,)
        #XFOIL SUBPROCESS
        self.xf = xf
        #Pipe inputs into xfoil
        res = xf.communicate( self.input.encode('utf-8') )
        #Space output with a few newlines
        if not quiet:
            print('\n\n\n')

    def LoadGeom(self):
        """Load given airfoil, either NACA number or file path
        """
        if self.naca:
            #Load NACA airfoil based on given digits
            self.AddInput( 'naca {}'.format(self.foil) )
        else:
            #check dependencies
            if not os.path.isfile(self.foil):
                txt = "PYXFOIL ERROR: Geometry input file does not exist/" \
                "in wrong location\n({})".format(self.foil)
                sys.exit(ErrorMessage(txt))
            if len([l for l in open(self.foil, 'r')]) < 2:
                txt = "PYXFOIL ERROR: Geometry input file is empty (no data)" \
                "\nDownload or create new file: ({})".format(self.foil)
                sys.exit(ErrorMessage(txt))

            #Load geometry from file path
            self.AddInput('load {}'.format( self.foil) )

    def SaveGeom(self, overwrite=True):
        """Save airfoil geometry. MUST BE CALLED IN TOP MENU.
        overwrite --> Overwrite file if it exists
        """
        savename = self.SaveNameGeom()
        if not os.path.isfile(savename) and overwrite:
            self.AddInput( 'save {}'.format( savename ) )

    def EnterOperMenu(self):
        """Set up 'oper' menu for inviscid or viscous operations.
        Call from top menu after loading geometry.
        """
        #ENTER OPERATIONS MENU
        self.AddInput('oper')
        if self.Re != 0:
            #VISCOULS SIMULATION WITH GIVEN REYNOLDS NUMBER
            self.AddInput('visc {}'.format( self.Re ) )
        #SET ITERATION NUMBER
        self.AddInput('iter {}'.format( self.Iter ))

    def SingleAlfa(self, alf, SaveCP=True):
        """Simulate airfoil at a single angle of attack.
        Must be run in 'oper' menu.
        alf --> angle of attack to simulate
        SaveCP --> Save individual surface pressure distributions
        """
        self.AddInput('alfa {}'.format( alf ) )
        if SaveCP:
            savename = self.SaveNameSurfCp(alf)
            self.AddInput('cpwr {}'.format(savename) )

    def Polar(self, alfs, SaveCP=True, overwrite=True):
        """Create and save polar for airfoil. Call in top menu after
        loading geometry.
        alfs --> list of alphas to run
        SaveCP --> Save individual surface pressure distributions
        overwrite --> overwrite polar file (otherwise append new alphas)
        """

        #STORE RUN INFO
        if type(alfs) == float or type(alfs) == int:
            #angle of attack input must be array-like
            alfs = [alfs]
        self.alfs = alfs
        #SET REYNOLDS NUMBER
        self.EnterOperMenu()

        #SET UP POLAR ACCUMULATION
        # if len(alfs) > 1:
        savename = self.SaveNamePolar(alfs)

        if os.path.isfile(savename) and overwrite:
            os.remove(savename) #Remove polar file if starting new
        #TURN POLAR ACCUMULATION ON
        self.AddInput('pacc')
        #Submit Polar File Name
        self.AddInput(savename)
        #Skip Polar Dumpfile Name
        self.AddInput('')
        # self.AddInput(self.savename + 'dump.dat')
        # self.AddInput('pacc'; savename; self.savename + 'dump.dat')

        #SIMULATE EACH ANGLE OF ATTACK
        for alf in alfs:
            self.SingleAlfa(alf, SaveCP)

        # if len(alfs) > 1:
        #TURN POLAR ACCUMULATION OFF
        self.AddInput('pacc')

    def Quit(self):
        """Quit XFOIL by going to top-most menu and issuing 'quit' command
        """
        self.AddInput('')
        self.AddInput('')
        self.AddInput('')
        self.AddInput('')
        self.AddInput('quit')

    def TurnOffGraphics(self,):
        """ Turn off XFOIL graphical output so that XFOIL can run 'headless'.
        Use this to avoid XQuartz compatibility issues and to simplify output to screen.
        """
        #Enter Plotting Options Menu
        self.AddInput('plop')
        #Turn graphics option to False
        self.AddInput('g f')
        #Return to main menu
        self.AddInput('')

    def SaveNameGeom(self,):
        """Make save filename for airfoil geometry
        """
        return '{}/{}.dat'.format(self.savepath, self.name)

    def SaveNameSurfCp(self, alf):
        """Make save filename for airfoil surface pressure based on current
        airfoil, Reynolds number, and angle of attack
        alf --> current angle of attack
        """
        return '{}/{}_surfCP_Re{:1.2e}a{:1.1f}.dat'.format(
                        self.savepath, self.name, self.Re, alf)

    def SaveNamePolar(self, alfs):
        """Make save filename for airfoil polar based on
        airfoil, Reynolds number, and angle of attack
        alfs --> Range of angles of attack to run
        """
        if type(alfs) == float or type(alfs) == int:
            #angle of attack input must be array-like
            alfs = [alfs]
        if len(alfs) == 1:
            #only one provided angle of attack
            alfrange = 'a{:1.2f}'.format(alfs[0])
        else:
            #use least and greatest angle of attack for name
            alfrange = 'a{:1.1f}-{:1.1f}'.format(alfs[0], alfs[-1])
        return '{}/{}_polar_Re{:1.2e}{}.dat'.format(
                        self.savepath, self.name, self.Re, alfrange)



########################################################################
### XFOIL FILE I/O #####################################################
########################################################################

def ReadXfoilAirfoilGeom(filename):
    """Read in XFOIL airfoil geometry file data, skipping title lines
    filename --> path to file
    """
    df = pd.read_csv(filename, delim_whitespace=True, skiprows=1,
                     names=['x', 'z'])
    return df

def ReadXfoilSurfPress(filename):
    """Read in XFOIL surface pressure coefficient data, skipping title lines
    filename --> path to file
    """
    if IsItWindows():
        #Windows file format
        names = ['x', 'y', 'Cp']
        skip = 3
    else:
        #Mac file format
        names = ['x', 'Cp']
        skip = 1
    #read file
    df = pd.read_csv(filename, delim_whitespace=True, skiprows=skip, names=names)
    return df

def ReadXfoilPolar(filename):
    """Read in XFOIL polar file data, skipping title lines
    filename --> path to polar data file
    """
    df = pd.read_csv(filename, delim_whitespace=True, skiprows=12,
            names=['alpha', 'Cl', 'Cd', 'Cdp', 'Cm', 'Top_Xtr', 'Bot_Xtr'])
    return df

def WriteXfoilFile(name, x, z):
    """Write 2-column XFOIL file with fixed-width separation.
    First line is 'name'.  Works best for writting geometry.
    """
    ofile = open(name, 'w')
    ofile.write('foil\n')
    for xx, zz in zip(x, z):
        #XYZ POINTS FORMATED IN 3, 16-WIDE COLUMNS
        #<  : left-aligned,
        #14 : 14 spaces reserved in column,
        #.7 : 7 spaces reserved after decimal point,
        #f  : float
        ofile.write('    {:<14.7f}{:<14.7f}\n'.format(xx, zz))
    ofile.close()

########################################################################
### MAIN ###############################################################
########################################################################

def GetPolar(foil='0012', naca=True, alfs=[0], Re=0,
                SaveCP=True, Iter=100, pane=False,
                overwrite=True, quiet=True):
    """For a single airfoil at a single Reynolds number,
    create a polar with given alphas.
    foil --> naca digits or path to geom file
    naca --> True for naca digits, False for file path
    alfs --> list of alphas to run
    Re --> Reynolds number (default invisc)
    SaveCp --> save each individual pressure distribution
    pane --> smooth geometry before simulation (can cause instability)
    overwrite --> overwrite existing save files
    quiet --> Supress XFOIL output
    """
    #INITIALIZE XFOIL OBJECT
    obj = Xfoil(foil, naca, Re, Iter=Iter)
    #GEOMETRY
    #condition panel geometry (use for rough shapes, not on smooth shapes)
    if pane:
        obj.AddInput('pane')
    #Save geometry for later slope calculations
    obj.SaveGeom()
    #RUN AND SAVE ALL POLAR CASES
    obj.Polar(alfs, SaveCP=SaveCP, overwrite=overwrite)
    #Quit XFOIL
    obj.Quit()
    #Run Input List In XFOIL
    obj.RunXfoil(quiet=quiet)

    return obj




def main(foil, naca, alfs, Re, Iter=30):
    """
    foil --> path to airfoil file or naca 4-digit number
    naca --> boolean if naca or not
    alfs --> list of angle of attacks for airfoils (deg)
    Re --> Reynolds number to run
    Iter --> maximum number of iterations for each simulation
    """

    obj = Xfoil(foil, naca, Re, Iter) #initialize xfoil
    obj.SaveGeom() #save airfoil geometry
    obj.EnterOperMenu() #set up operations, reynolds, iteration number
    obj.SingleAlfa(alfs[0]) #command to run single alpha case
    obj.Polar(alfs) #Command to run polar case
    obj.Quit() #command to quit XFOIL when done

    obj.RunXfoil() #Run all commands at once

    print('done')

if __name__ == "__main__":

    foils = ['0012', 'Data/s1223.dat']
    nacas = [True, False]
    alfs = [0, 10]
    Re = 2e5

    for foil, naca in zip(foils, nacas):
        main(foil, naca, alfs, Re)







