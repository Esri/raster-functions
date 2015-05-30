""" 
    Compute symmetric radial distortion coefficients given radial distance-distortion pairs.
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys
import os


def loadString(distances="", distortions=""):
    r = [float(v) for v in distances.split(";")]
    d = [float(v)*1e-3 for v in distortions.split(";")]
    return (np.array(r, np.float), np.array(d, np.float))

def loadFile(filePath):
    rd = np.loadtxt(filePath, ndmin=2)
    return (rd[:,0], rd[:,1]*1e-3)

def estimateCoefficients(distances, distortions, nK=5):
    """ returns K using that solves: D[N,1] = X[N,nK] * K[nK,1] using least-squares regression"""
    z = np.max(np.abs(distances))
    r = distances / z
    X = np.vstack([np.power(r, (i*2)-1) for i in range(1, nK+1)]).T
    Z = [np.power(z, (i*2)-1) for i in range(1, nK+1)]
    (K, residuals, _, _) = np.linalg.lstsq(X, distortions)
    return (K, K/Z, residuals, X)

def log(message):
    print("> {0}".format(message))

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

if __name__=="__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('distortionFile', nargs='?',
                           help="text file containing radial distance to distortion mapping")
        parser.add_argument('--distances', 
                           help="semicolon delimited string containing radial distances in millimeters")
        parser.add_argument('--distortions',
                           help="semicolon delimited string containing distortion values in microns corresponding to each radial distance value")
        parser.add_argument('-p', '--plot', action='store_true',
                           help="displays a plot")        
        parser.add_argument('-v', '--verbose', action='store_true',
                           help="verbose")        
        args = parser.parse_args()
    except Exception as e:
        print(e.message)

    print("\n")
    if not args.distances is None and len(args.distances) > 0 and not args.distortions is None and len(args.distortions) > 0:
        r, d = loadString(args.distances, args.distortions)
    elif not args.distortionFile is None and len(args.distortionFile) > 0:
        log("Loading radial distortion vales from file: {0}".format(args.distortionFile))
        if not os.path.exists(args.distortionFile):
            print("")
            sys.exit(1)
        r, d = loadFile(args.distortionFile)
    else:
        parser.print_help()
        exit(100)

    log("Loaded {0} data points".format(r.size))
    (K, Kz, sqError, X) = estimateCoefficients(r, d, nK=3)
    residuals = np.abs(d - X.dot(K))
    sFormat = "{0:>20} {1:>20} {2:>20}"

    log("Coefficients [mm-based]: {}".format("   ".join([str(k) for k in Kz])))
    log("RMSE: {}".format((sqError**0.5)[0]))
    log("Residuals (mm)...")
    log(sFormat.format("Distance", "Distortion", "Residual"))
    for m in [sFormat.format(u, v, w) for (u, v, w) in zip(r, d, residuals)]:
        log(m)
   
    #log("Design matrix: \n{0}".format(X))

    if args.plot:    
        plt.scatter(r, d)
        plt.plot(r, X.dot(K), c="red")
        plt.show()

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1]. https://calval.cr.usgs.gov/osl/smaccompen.pdf

"""
