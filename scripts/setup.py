'''
=========================================================
setup.py: Automate installation of dependencies required for Python raster function
=========================================================

Installation
------------
**setup.py** has no external library dependencies and should compile on 
most systems that are running Python 2.7, or 3.4.

To execute **setup.py** within the package directory run:
  $ python setup.py
'''

import os
import sys
import subprocess
import time
import urllib2
import logging
import platform

'''
    ERRORLEVEL
        0 - Installation successful.
        1 - PIP installation unsuccessful.
        2 - HTTP 404 Error URL cannot be found.
        3 - File cannot be downloaded.
        4 - VC++ Compiler for Python installation failed.
        5 - Python Window Binary installation failed.
        6 - Python package installation failed.
        7 - Requirements.txt file not found.
'''


# URLs

def log(s):
    print(". {0}\n".format(s))


def die(errorLog, errorCode):
    logging.error(errorLog)
    time.sleep(5)
    exit(errorCode)
    

def downloadFile(url, filePath):
    try:
        urlFile = urllib2.urlopen(urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
    except urllib2.HTTPError:
        die("Unable to load specified URL: {0}".format(url), 2)

    try:
        fileDownload = open(installLoc, 'wb')
        fileDownload.write(urlFile.read())      # Download file
        fileDownload.close()
    except:
        die("File could not be downloaded.", 3)


def locateFile(url, filePath):
    if not os.path.isfile(filePath):
        log("Downloading: {0}".format(url))
        downloadFile(url, filePath)
    log("Located: {0}".format(filePath))


def main():
    pipURL = "http://bootstrap.pypa.io/get-pip.py"
    vcURL = "http://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"

    pipPath = os.path.join(os.path.dirname(sys.executable), r"Scripts\pip.exe")
    setupHome = os.path.abspath(os.path.dirname(__file__))

    try:
        log("Installing PIP")
        getpipPath = os.path.join(setupHome, "get-pip.py")
        locateFile(pipURL, getpipPath)
        subprocess.call([sys.executable, getpipPath])

        if os.path.isfile(pipPath):
            log("PIP installed successfully")
        else:
            die("PIP installation failed!", 1)
    except:
        die("PIP installation failed!", 1)
    
    try:           
        if sys.version_info[0] == 2:
            log("Installing Microsoft Visual C++ Compiler")
            vcSetupPath = os.path.join(setupHome + "VCForPython.msi")
            locateFile(vcURL, vcSetupPath)
            os.system("msiexec /i {0} /qb".format(vcSetupPath))
            log("C++ Compiler for Python installed successfully")
    except:
        die("VC++ Compiler for Python installation failed!.", 4)

    try:
        log("Installing Python dependencies")
        reqFilePath = os.path.join(setupHome, "requirements.txt")
        if os.path.isfile(reqFilePath):
            reqItems = [line.strip() for line in open(reqFilePath)]
            for r in reqItems:
                log("Installing package: {0}".format(r))
                subprocess.call([pipPath, 'install', '-U', '--upgrade', r])
        else:
            die("Dependency listing file not found: {0}".format(reqFilePath), 7)
    except:
        die("Dependency installation failed!", 6)
    
    log("Python Raster Function dependencies installed successfully.")
    time.sleep(5)
    exit(0)


if __name__ == '__main__':
    main()
