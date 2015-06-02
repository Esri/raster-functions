"""
    ComputeDistortionCoefficients.py [-h] [--distances R] [--distortions D]
                                     [--coefficients nK] [-p] [-v]
                                     [distortionFile]

    Estimate coefficients of symmetric radial distortion based on the Brown-
    Conrady model given a set of distortion values at corresponding radial
    distances.

    positional arguments:
      distortionFile     text file containing radial distance to distortion
                         mapping

    optional arguments:
      -h, --help         show this help message and exit
      --distances R      semicolon- or space-delimited string containing radial
                         distances in millimeters
      --distortions D    semicolon- or space-delimited string containing
                         distortion values in microns corresponding to each radial
                         distance value
      --coefficients nK  Number of coefficients in the estimated Brown-Conrady
                         model for symmetric radial distortion. Defaults to 3.
      -p, --plot         display the distance-distortion relationship using
                         observed data-points and the predictor function.
      -v, --verbose      Turn on verbose messages. Outputs design matrix and
                         residuals associated with the least-squares regression.
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys
import os
import re


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
def loadString(distances="", distortions=""):
    """Parse semicolon- or space-delimited distances and distortions and return a tuple of two floating-point arrays.

    - Radial distances are presumed to be in millimeters.
    - Distortions are presumed to be in microns and are converted to millimeters.
    """
    r = [float(v) for v in re.split(";| ", distances)]            # distances are in mm
    d = [float(v)*1e-3 for v in re.split(";| ", distortions)]     # distortions: from microns to mm
    return (np.array(r, np.float), np.array(d, np.float))


def loadFile(filePath):
    """ Parse the first two columns of a file for distance-distortion pairs and return a tuple of two floating-point arrays.

        - Radial distances are presumed to be in millimeters.
        - Distortions are presumed to be in microns and are converted to millimeters.
    """
    rd = np.loadtxt(filePath, ndmin=2)
    return (rd[:, 0], rd[:, 1]*1e-3)


def estimateCoefficients(distances, distortions, nK=5):
    """ Estimate coefficients of symmetric radial distortion given distances and distortions

        Arguments:
        - distances: radial distances in mm.
        - distortions: distortion values in mm corresponding to the each specified distance.
        - nK: nummber of coefficients in the model.

        Returns:
        - K: an array of size nK containing the coefficients estimated using LLS.
        - RMSE: root-mean-square deviation of the estimator defined by K.
        - R: the design (power) matrix derived using input radial distances.
        - D: the relative radial distortion corresponding to each data point.
    """
    R = getDesignMatrix(distances, nK)
    D = np.array([d/r if r else 0 for (r, d) in zip(distances.tolist(), distortions.tolist())])
    (K, sqError, _, _) = np.linalg.lstsq(R, D)
    return (K, (sqError**0.5)[0] if sqError else 0.0, R, D)


def getDesignMatrix(distances, nK):
    """ Return the design (power) matrix associated with the model"""
    return np.vstack([np.power(distances, 2*i) for i in range(0, nK)]).T


def predictDistortion(distances, K):
    """ Apply the distortion model defined by the coefficients in K to the specified distances (in mm)
        and return predicted (absolute) distortion values.
    """
    return getDesignMatrix(distances, K.size).dot(K) * distances


def log(message):
    print("{0}".format(message))


# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##
def main():
    try:
        parser = argparse.ArgumentParser(description=("Estimate coefficients of symmetric radial distortion based on the Brown-Conrady model "
                                                      "given a set of distortion values at corresponding radial distances."))
        parser.add_argument('distortionFile', nargs='?',
                           help="text file containing radial distance to distortion mapping")
        parser.add_argument('--distances', metavar='R', 
                           help="semicolon- or space-delimited string containing radial distances in millimeters")
        parser.add_argument('--distortions', metavar='D',
                           help="semicolon- or space-delimited string containing distortion values in microns corresponding to each radial distance value")
        parser.add_argument('--K', metavar='nK', type=int, default=3, choices=range(1, 8),
                           help="Number of coefficients in the estimated Brown-Conrady model for symmetric radial distortion. Defaults to 3.")
        parser.add_argument('-p', '--plot', action='store_true',
                           help="display the distance-distortion relationship using observed data-points and the predictor function.")
        parser.add_argument('-v', '--verbose', action='store_true',
                           help="Turn on verbose messages. Outputs design matrix and residuals associated with the least-squares regression.")
        args = parser.parse_args()
    except Exception as e:
        print(e.message)

    print("\n")
    if args.distances and args.distortions:
        r, d = loadString(args.distances, args.distortions)
        log("Loading radial distortion vales from command-line")
    elif args.distortionFile:
        log("Loading radial distortion vales from file: {0}".format(args.distortionFile))
        if not os.path.exists(args.distortionFile):
            print("")
            sys.exit(1)
        r, d = loadFile(args.distortionFile)
    else:
        parser.print_help()
        exit(100)

    nK = args.K
    log("Loaded {0} data points".format(r.size))
    (K, rmse, R, D) = estimateCoefficients(r, d, nK=nK)
    Y = predictDistortion(r, K)
    residuals = np.abs(d - Y)

    log("Estimated coefficients [mm-based]: {}".format(" ".join(["{0:>20e}".format(k) for k in K])))
    log("RMSE: {:e} mm".format(rmse))
    log("Normalized RMSE: {:.2}%".format(100. * rmse / np.ptp(D)))

    if args.verbose:
        log("")
        log("Residuals (mm)...")
        log("{0:>10} {1:>30} {2:>30} {3:>20}".format("Distance", "Distortion (observed)", "Distortion (predicted)", "Residual"))
        for m in ["{0:>10} {1:>30e} {2:>30e} {3:>20e}".format(v1, v2, v3, v4) for (v1, v2, v3, v4) in zip(r, d, Y, residuals)]:
            log(m)
        log("")
        log("Design matrix: \n{0}".format(R))

    U = np.linspace(np.min(r), np.max(r), 100)
    if args.plot:
        f = plt.figure()
        f.suptitle("Radial Distance vs. Radial Distortion", fontsize=14, fontweight='bold')
        plt.scatter(r, d)
        plt.plot(U, predictDistortion(U, K), c="red")
        plt.xlabel("Radial distance [mm]")
        plt.ylabel("Distortion [mm]")
        plt.gca().grid(True)
        plt.legend(['Predicted', 'Observed'])
        plt.show()

if __name__=="__main__":
    main()

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1]. https://calval.cr.usgs.gov/osl/smaccompen.pdf
    [2]. http://en.wikipedia.org/wiki/Distortion_(optics)
    
"""
