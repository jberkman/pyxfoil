# pyxfoil
PYXFOIL: XFOIL AUTOMATION USING PYTHON
Logan Halstrom
EAE 127
UCD
CREATED:  15 SEP 2015
MODIFIED: 17 OCT 2018

DESCRIPTION: Provides functions for automating XFOIL runs.Each function will iteratively build a list of inputs. When you are ready,use the RunXfoil command to run the input list.

NOTE: Since input list is predetermined, runs cannot be reiterated.Make sure to set the iter limit high enough, that each simulation willwork on the first try.

TO CALL IN A SCRIPT:
import sys
sys.path.append('path/to/pyxfoil.py')
import pyxfoil
