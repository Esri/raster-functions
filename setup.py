'''
====================================================================================
setup.py: Automated installation of dependencies required for Python raster function
====================================================================================

Installation
------------

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
    ErrorLevel on exit:
        0  :    Installation successful.
        1  :    PIP installation unsuccessful.
        2  :    HTTP 404 Error URL cannot be found.
        3  :    File cannot be downloaded.
        4  :    VC++ Compiler for Python installation failed.
        5  :    Requirements.txt file not found.
        6  :    Python package installation failed.
        99 :    ArcGIS 10.3.1 or above not found.
'''

def log(s):
    print(">>> {0}".format(s))


def die(errorLog, errorCode):
    print("\n\n")
    logging.error(errorLog)
    print("\n")
    time.sleep(2)
    exit(errorCode)
    

def downloadFile(url, filePath):
    try:
        urlFile = urllib2.urlopen(urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
    except urllib2.HTTPError:
        die("Unable to load specified URL: {0}".format(url), 2)

    try:
        with open(filePath, 'wb') as f:
            f.write(urlFile.read())
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

    pipExePath = os.path.join(os.path.dirname(sys.executable), r"Scripts\pip.exe")
    setupHome = os.path.join(os.path.abspath(os.path.dirname(__file__)), "scripts")
    distHome = os.path.join(os.path.abspath(os.path.dirname(__file__)), "dist")

    try:
        arcpy = __import__('arcpy')
        info = arcpy.GetInstallInfo()
        if tuple(map(int, (info['Version'].split(".")))) < tuple(map(int, ("10.3.1".split(".")))):
            raise Exception("No ArcGIS")
    except:
        die("Unable to find ArcGIS 10.3.1 or above. Cannot proceed.", 99)

    try:
        log("Installing PIP")
        pipPyPath = os.path.join(setupHome, "get-pip.py")
        locateFile(pipURL, pipPyPath)
        subprocess.call([sys.executable, pipPyPath])

        if os.path.isfile(pipExePath):
            log("PIP installed successfully")
        else:
            raise Exception("PIP failed")

        subprocess.call([pipExePath, "install", "--upgrade", "pip"])
        subprocess.call([pipExePath, "install", "--upgrade", "wheel"])
    except:
        die("PIP installation failed!", 1)
    
    try:           
        if sys.version_info[0] == 2:
            log("Installing Microsoft Visual C++ Compiler")
            vcSetupPath = os.path.join(distHome, "VCForPython27.msi")
            locateFile(vcURL, vcSetupPath)
            c = ["msiexec", "/i", vcSetupPath, "/qb-"]
            log("Executing: {0}".format(" ".join(c)))
            subprocess.call(c)
            log("C++ Compiler for Python installed successfully")
    except:
        die("VC++ Compiler for Python installation failed!.", 4)

    try:
        log("Installing Python dependencies")
        reqFilePath = os.path.join(setupHome, "requirements.txt")
        if not os.path.isfile(reqFilePath):
            die("Dependency listing file not found: {0}".format(reqFilePath), 5)

        c = [pipExePath, "install", "--find-links={0}".format(distHome), "-r", reqFilePath]
        log("Executing: {0}".format(" ".join(c)))
        subprocess.call(c)
    except:
        die("Dependency installation failed!", 6)
    
    print("\n\n")
    log("Python Raster Function dependencies installed successfully.")
    log("Done.")
    time.sleep(2)
    exit(0)


if __name__ == '__main__':
    main()
