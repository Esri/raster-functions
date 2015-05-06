import subprocess , sys
import os , re
import urllib, time

def main(ver):
    driveLetters = re.findall(r"[A-Z]+:.*$",os.popen("mountvol /").read(),re.MULTILINE)

    # Locate Python Module for ArcGIS
    for letter in driveLetters:
        path      = letter + "Python27\ArcGIS" + ver + ";" + letter + "Python27\ArcGIS" + ver + "\Scripts"
        if os.path.exists(path.split(';')[0]):
            python_Path = path.split(';')[0] + "\python.exe"
            pip_Path    = path.split(';')[1] + "\pip.exe"
            break;

    try:
        print "ArcGIS Python Module Located at: " + python_Path

    except:
        print ("ArcGIS Python Module could not be located. Please specify correct ArcGIS version\n")
        time.sleep(2)
        exit(0)

    # Install pip to download dependencies
    print ("Installing pip\n")

    URL_Pip = "http://bootstrap.pypa.io/get-pip.py"
    urllib.urlretrieve(URL_Pip, "get-pip.py")
    time.sleep(2)
    subprocess.call([python_Path, 'get-pip.py'])

    print ("pip successfully installed.\n")

    # Install Microsoft Visual C++ Compiler for Python 2.7

    print ("Dependencies require Microsoft Visual C++ Compiler for Python 2.7.\nDo you want to download? (y/n)")
    choice = str(raw_input())
    if choice.lower == "y":
        print ("\nDownloading Microsoft Visual C++ Compiler for Python 2.7 \nThis will take a moment.\n")

        URL_VCPython = "http://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"
        urllib.urlretrieve(URL_VCPython, "VCForPython27.msi")
        time.sleep(2)
        os.system('msiexec /i VCForPython27.msi /qf')

        print ("Microsoft Visual C++ Compiler for Python 2.7 successfully installed.")

    # Install scipy externally
##    print ("\nInstall Scipy Scientific Library for Python (y/n) ?")
##    choice = str(raw_input())
##    if choice.lower == "y":
##        print ("Downloading Scipy Scientific Library for Python")
##        URL_Scipy = "http://downloads.sourceforge.net/project/scipy/scipy/0.15.1/scipy-0.15.1-win32-superpack-python2.7.exe?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fscipy%2F&ts=1430904154&use_mirror=liquidtelecom"
##        urllib.urlretrieve(URL_Scipy, "ScipyPython27.exe")
##       time.sleep(2)
##        os.system('ScipyPython27.exe')

    print ("\nInstalling Python Dependencies using pip.")
    time.sleep(1)

    # Required dependencies
    install_require = ['matplotlib','numpy', 'pyparsing', 'pyproj', 'python-dateutil', 'pytz', 'six','scikit-image', 'scipy', 'scikit-learn','cython']

    for package in install_require:
        print ("Install ") + str(package) + (" package\n")
        try:
            subprocess.call([pip_Path, 'install','--upgrade', package])
            print str(package) + " successfully installed\n"
        except:
            print "\n" + str(package) + " not successfully installed.\n Exiting"
            exit(0)

    print ("Dependencies installed - Ready to use Python raster functions.")
    time.sleep(5)

if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except:
        main(raw_input("Enter ArcGIS Version: "))
