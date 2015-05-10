"""
Name    : setup.py
Usage   : {python-home}/python setup.py
Purpose : Automate installation of dependencies required for Python raster function
"""

import os
import sys
import subprocess
import time
import urllib2
import platform

"""
ERRORLEVEL
0 - Installation successful.
1 - pip installation unsuccessful.
2 - File could not be downloaded.
3 - VC++ Compiler for Python installation unsuccessful.
4 - Numpy installation unsuccessful.
5 - Scipy installation unsuccessful.
6 - Python package could not be installed.
7 - requirements.txt file not found.
"""

# Paths to neccessary files
PY2             = True if sys.version_info[0] == 2 else False
pyPath          = sys.executable                               # ArcGIS Python Module
setupPath       = os.path.dirname(os.path.abspath(__file__))   # setup.py
pipPath         = os.path.dirname(pyPath) + "\Scripts\pip.exe" # pip.exe

# Address to download files
getpipURL       = "http://bootstrap.pypa.io/get-pip.py"        # get-pip.py
getVCURL        = "http://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"  # VCForPython27.msi

# Numpy 1.9.2+ MKL Binaries
numpy27_32URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/numpy-1.9.2+mkl-cp27-none-win32.whl"
numpy27_64URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/numpy-1.9.2+mkl-cp27-none-win_amd64.whl"
numpy34_64URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/numpy-1.9.2+mkl-cp34-none-win_amd64.whl"

# Scipy 0.15.1 Window Binaries
scipy27_32URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/scipy-0.15.1-cp27-none-win32.whl"
scipy27_64URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/scipy-0.15.1-cp27-none-win_amd64.whl"
scipy34_64URL   = "http://www.lfd.uci.edu/~gohlke/pythonlibs/r7to5k3j/scipy-0.15.1-cp34-none-win_amd64.whl"

def downloadFile(filename, installURL, path):
    try:
        req           = urllib2.Request(installURL, headers={ 'User-Agent': 'Mozilla/5.0 '})
        HTML          = urllib2.urlopen(req)
        fileDownload  = open(path,'wb')
        fileDownload.write(HTML.read())
        fileDownload.close()
        time.sleep(5)   # Save file on system
    except Exception:
        print Exception.message
        print ("Error: File could not be downloaded.\n")
        time.sleep(5)
        exit(2)

def locateFile(filename, installURL, path):
    if (os.path.isfile(path)):
        print ("File located. Starting installation.\n")

    else:
        print ("File not found. Downloading file.\n")
        downloadFile(filename, installURL, path)
        print ("File succesfully downloaded. Starting installation.\n")

def main():
    # Step 1. Install pip
    print ("1. pip Installation.\n") + ("Locating get-pip.py in ") + setupPath + "\n"

    locateFile("get-pip.py", getpipURL, (setupPath + "\get-pip.py"))

    try:
        subprocess.call([pyPath, (setupPath + "\get-pip.py")])
        print "\nInstallation successful.\n"
    except:
        print ("Error: pip installation unsuccessful.\n")
        time.sleep(5)
        exit(1)

    # Step 2. Install Microsoft Visual C++ Compiler for Python
    print ("2. Microsoft Visual C++ Compiler Installation.\n") + ("Locating file in ") + setupPath + "\n"

    locateFile("VCForPython.msi", getVCURL, (setupPath + "\VCForPython.msi"))

    try:
        os.system('msiexec /i VCForPython.msi /qb')
        print "\nInstallation successful.\n"
    except:
        print ("Error: VC++ Compiler for Python installation unsuccessful.\n")
        time.sleep(5)
        exit(3)


    # Step 3. Install Numpy 1.9.2+ MKL
    print ("\n3. Numpy 1.9.2+ MKL Installation.\n") + ("Locating File in ") + setupPath + "\n"

    if PY2:
        if platform.architecture()[0] == "32bit":
            locateFile("numpy-1.9.2+mkl-cp27-none-win32.whl", numpy27_32URL, (setupPath + "\\numpy-1.9.2+mkl-cp27-none-win32.whl"))
            numpyPath = (setupPath + "\\numpy-1.9.2+mkl-cp27-none-win32.whl")
        else:
            locateFile("numpy-1.9.2+mkl-cp27-none-win_amd64.whl", numpy27_64URL, (setupPath + "\\numpy-1.9.2+mkl-cp27-none-win_amd64.whl"))
            numpyPath = (setupPath + "\\numpy-1.9.2+mkl-cp27-none-win_amd64.whl")

    else:
        locateFile("numpy-1.9.2+mkl-cp34-none-win_amd64.whl", numpy27_32URL, (setupPath + "\\numpy-1.9.2+mkl-cp34-none-win_amd64.whl"))
        numpyPath = (setupPath + "\\numpy-1.9.2+mkl-cp34-none-win_amd64.whl")

    try:
        subprocess.call([pipPath, 'install','-U','--upgrade', numpyPath])

    except:
        print ("Error: Numpy installation unsuccessful.\n")
        time.sleep(5)
        exit(4)

    # Step 4. Install Scipy 0.15.1
    print ("\n4. Scipy 0.15.1 Installation.\n") + ("Locating File in ") + setupPath + "\n"

    if PY2:
        if platform.architecture()[0] == "32bit":
            locateFile("scipy-0.15.1-cp27-none-win32.whl", scipy27_32URL, (setupPath + "\scipy-0.15.1-cp27-none-win32.whl"))
            scipyPath = (setupPath + "\scipy-0.15.1-cp27-none-win32.whl")
        else:
            locateFile("scipy-0.15.1-cp27-none-win_amd64.whl", scipy27_64URL, (setupPath + "\scipy-0.15.1-cp27-none-win_amd64.whl"))
            scipyPath = (setupPath + "\scipy-0.15.1-cp27-none-win_amd64.whl")

    else:
        locateFile("scipy-0.15.1-cp34-none-win_amd64.whl", scipy34_64URL, (setupPath + "\scipy-0.15.1-cp34-none-win_amd64.whl"))
        scipyPath = (setupPath + "\scipy-0.15.1-cp34-none-win_amd64.whl.whl")

    try:
        subprocess.call([pipPath, 'install','-U','--upgrade', scipyPath])

    except:
        print ("Error: Scipy installation unsuccessful.\n")
        time.sleep(5)
        exit(5)

    # Step 5. Install Python Dependencies
    print ("\n5. Install Python Dependencies.\n") +("Locating requirements.txt in ") + setupPath + "\n"

    if (os.path.isfile((setupPath + "\\requirements.txt"))):
        install_require = [line.strip() for line in open((setupPath + "\\requirements.txt"))]

        for package in install_require:
            print ("Installing ") + package + (" package.\n")

            try:
                subprocess.call([pipPath, 'install','-U','--upgrade', package])

            except:
                print ("Error: ") + package + " could not be downloaded.\n"
                time.sleep(5)
                exit(5)

            print package + (" successfully installed.\n")
            time.sleep(1)

    else:
        print ("Error: requirements.txt not found.\n")
        time.sleep(5)
        exit(6)

    print ("Installation successful.\n")
    time.sleep(5)
    exit(0)


if __name__ == '__main__':
    main()
