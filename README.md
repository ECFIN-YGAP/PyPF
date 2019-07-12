# PyPF
                                        #---------------#
                                        #     PyPF      #
                                        #---------------#

@author: François Blondeau (European Commisssion, Directorate-General for Economic and Financial Affairs)

References :
    - Similar code in WinRATS (Cécile Denis, Werner Röger and Valerie Vandermeulen)
        and MATLAB (Valerie Vandermeulen)
    - OGWG commonly agreed production function (PF) methodology :
        "The Production Function Methodology
for Calculating Potential Growth Rates & Output Gaps", Havik et al. (2014)
European Commission Economic Paper 535 | November 2014

This program is a PILOT project.
It is a trial of the Python programming language possibilities in the framework of a move towards open source.
It could be used instead of the presently used WinRATS program to compute indicators needed for assessing both
the productive capacity (i.e. potential output) and cyclical position (i.e. output gaps) of EU economies.

Python is open source and royalty-free.
-> https://www.python.org/
-> https://wiki.python.org/moin/BeginnersGuide


*************************************************
**********  ENVIRONMENT CONFIGURATION  **********
*************************************************

Disclaimer : The current version of the program installation process only supports the Windows platform.

IMPORTANT : The GAP dll is only 64-bit and works only with 64-bit Python...
The program will run in Python 32-bit version if you provide Trend TFP and NAWRU exogenously and do not specify their estimations to be made by the program.

1 - Go to the official miniconda download page : https://conda.io/miniconda.html

2 - Download the version of python3/miniconda adapted to your system.

3 - As an administrator, run the installer you just downloaded.

4 - When prompted to add anaconda to your path environment and to register anaconda as your default Python 3.X, check the boxes and click “install”

5 - Once the installation is completed, you should be able to launch these two commands in a cmd.exe  :

        python -V : should display the version of python you just installed
        conda -V : should display the version of conda you just installed   

6 - You should then update conda by running this command :

        conda update conda
    NB : conda commands may take a fair amount of time to complete 
    
7 - Run this command : 

        conda install --file {spec-file-path}
       
    where {spec-file-path} is the path to the specification file included in this bundle. 
    Make sure you are using the specification file which is compliant with your installation of miniconda. 
    
8 - Your newly installed python/miniconda is now able to run this project. To do so you simply have to open the Excel file "start.xlsm", set your interpreter path in the "general" sheet and launch the program with the button from "main" sheet. 
