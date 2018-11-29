# PyPF
                                        #---------------#
                                        #     PyPF      #
                                        #---------------#

This program is a PILOT project.
It is a trial of the Python programming language possibilities in the framework of a move towards open source.
It could be used instead of the presently used RATS program to compute indicators needed for assessing both the productive capacity
(i.e. potential output) and cyclical position (i.e. output gaps) of EU economies.

Python is open source and royalty-free.
-> https://www.python.org/
-> https://wiki.python.org/moin/BeginnersGuide

Created on Fri Oct 26 18:34:27 2018
@author: François Blondeau (European Commisssion, Directorate-General for Economic and Financial Affairs)

Reference :

    - Similar code in RATS and MATLAB (Valerie Vandermeulen)
    
    - OGWG commonly agreed production function (PF) methodology :
    
        "The Production Function Methodology for Calculating Potential Growth Rates & Output Gaps", Havik et al. (2014)
        European Commission Economic Paper 535 | November 2014

*************************************************
**********  ENVIRONMENT CONFIGURATION  **********
*************************************************

1 - Go to the official miniconda download page : https://conda.io/miniconda.html

2 - Download the version of miniconda adapted to your system.

3 - Run the installer you just downloaded.

4 - When prompted to add anaconda to your path environment and to register anaconda as your default Python X.X, check the boxes and click “install”

5 - Once the installation is completed, you should be able to launch these two commands in a cmd.exe  :

        python -V : should display the version of python you just installed
        conda -V : should display the version of conda you just installed   
        
6 - You should then update conda by running this command : 

        conda update conda
        
7 - Run this command : 

        conda install --file {spec-file-path}
        where {spec-file-path} is the path to the specification file included in this bundle. 
        Make sure you are using the spec file which is compliant with your installation of miniconda.
        
8 - Your newly installed python/miniconda is now able to run this project. 
