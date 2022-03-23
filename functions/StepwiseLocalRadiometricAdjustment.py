import numpy as np
from numba import njit, jit, prange
import cv2


class StepwiseLocalRadiometricAdjustment:
    def __init__(self):
        self.name = "Stepwise Local Radiometric Adjustment"
        self.window_size = None
        self.description = "Python raster function for blending areas using Stepwise Local Radiometric Adjustment algorithm.The stepwise local radiometric adjustment is undertaken to fill contaminated areas and is conducted on each mask region of the target image"

    def getParameterInfo(self):
        required_parameters = [
            {
                "name": "input_raster",
                "dataType": "raster",
                "value": None,
                "required": True,
                "displayName": "Input Raster",
                "description": "Input raster with clouds to be removed",
            },
            {
                "name": "input_replacement_raster",
                "dataType": "raster",
                "value": None,
                "required": True,
                "displayName": "Input Replacement Raster",
                "description": "Input raster used to replace pixels with clouds",
            },
            {
                "name": "input_mask",
                "dataType": "raster",
                "value": None,
                "required": True,
                "displayName": "Input Mask",
                "description": "Mask raster",
            },
            {
                "name": "size_of_window",
                "dataType": "numeric",
                "value": 80,
                "required": True,
                "displayName": "Size of Window",
                "description": "Size of window to be used in stepwise adjustment (integer). 80 and 40 are generally used based on the cloud cover",
            },
        ]
        return required_parameters

    def getConfiguration(self, **scalars):
        return {
            "compositeRasters": False,
            "ProcessFullImage": True,
            "inheritProperties": 1 | 2 | 4 | 8,
            "invalidateProperties": 2 | 4 | 8,
            "resampling": False,
            "inputMask": False,
            "fixedTileSize": 0,
        }

    def updateRasterInfo(self, **kwargs):
        self.Window_size = int(kwargs.get("size_of_window", 80))
        kwargs["output_info"]["histogram"] = ()
        kwargs["output_info"]["pixelType"] = "f4"
        kwargs["output_info"]["resampling"] = False
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        raster_clouds_pixels1 = np.array(
            pixelBlocks["input_raster_pixels"], dtype="f4", copy=False
        )
        xs, ys, zs = np.where(raster_clouds_pixels1 != 0)

        raster_clouds_pixels = zeroCrop(raster_clouds_pixels1, xs, ys, zs)
        raster_noclouds_pixels = zeroCrop(
            np.array(
                pixelBlocks["input_replacement_raster_pixels"], dtype="f4", copy=False
            ),
            xs,
            ys,
            zs,
        )
        raster_mask_pixels = zeroCrop(
            np.array(pixelBlocks["input_mask_pixels"], copy=False), xs, ys, zs
        )[0, :, :]

        win_size = self.Window_size

        kernel = np.ones((5, 5), np.uint8)
        clouds_img_arr = cv2.dilate(raster_mask_pixels, kernel, iterations=10)

        targ_img_arr = raster_clouds_pixels * (1 - clouds_img_arr[None, :, :])
        replace_img_arr = raster_noclouds_pixels * (clouds_img_arr[None, :, :])

        image = 1 - clouds_img_arr
        cnt_cycles = 0
        while np.any((image == 0)) == True:
            kernel = np.ones((5, 5), np.uint8)
            expand = cv2.dilate(image, kernel, iterations=1)
            cnt_cycles += 1
            image = expand

        n_bands = targ_img_arr.shape[0]
        kernel_radius = win_size
        num_cycles = cnt_cycles

        filled_img_arr = np.zeros(
            (n_bands, targ_img_arr.shape[1], targ_img_arr.shape[2])
        )

        for k in range(n_bands):
            test_targ = np.pad(
                targ_img_arr[k, :, :],
                ((kernel_radius, kernel_radius), (kernel_radius, kernel_radius)),
                "constant",
                constant_values=(0,),
            )
            test_replace = np.pad(
                replace_img_arr[k, :, :],
                ((kernel_radius, kernel_radius), (kernel_radius, kernel_radius)),
                "constant",
                constant_values=(0,),
            )
            test_clouds = clouds_img_arr[:, :]
            test_clouds = np.pad(
                1 - test_clouds,
                ((kernel_radius, kernel_radius), (kernel_radius, kernel_radius)),
                "constant",
            )
            radio_norms = computeRadiometricAdjustment(
                test_targ,
                test_replace,
                test_clouds,
                kernel_radius,
                num_cycles,
                targ_img_arr.shape[2],
                targ_img_arr.shape[1],
            )
            crop_test_targ = cropCenterNorm(
                radio_norms, targ_img_arr.shape[2], targ_img_arr.shape[1]
            )
            filled_img_arr[k, :, :] = crop_test_targ

        results_final = np.zeros((raster_clouds_pixels1.shape))
        results_final[
            min(xs) : max(xs) + 1, min(ys) : max(ys) + 1, min(zs) : max(zs) + 1
        ] = filled_img_arr
        xx = results_final.astype(props["pixelType"], copy=False)
        pixelBlocks["output_pixels"] = xx
        return pixelBlocks


@njit
def zeroCrop(d, xs, ys, zs):
    return d[min(xs) : max(xs) + 1, min(ys) : max(ys) + 1, min(zs) : max(zs) + 1]


@njit
def numbaNormCalc(ker_targ, ker_replace, test_replace, x, y):
    sigma_std_targ = ker_targ.std()
    sigma_std_replace = ker_replace.std()
    mu_mean_targ = ker_targ.mean()
    mu_mean_replace = ker_replace.mean()
    norm = (
        ((sigma_std_targ / sigma_std_replace) * test_replace[x, y])
        + mu_mean_targ
        - ((sigma_std_targ / sigma_std_replace) * mu_mean_replace)
    )
    return norm


@njit
def numbaExtract(arr, x, y, ker_radius):
    return arr[x - ker_radius : x + ker_radius + 1, y - ker_radius : y + ker_radius + 1]


@njit
def cropCenterNorm(img, cropx, cropy):
    y, x = img.shape
    startx = x // 2 - (cropx // 2)
    starty = y // 2 - (cropy // 2)
    return img[starty : starty + cropy, startx : startx + cropx]


@njit(parallel=True)
def stepwiseAdjustment(cnts_list_, test_targ, test_replace, new_targ, ker_radius):
    for i in prange(cnts_list_.shape[0]):
        x, y = cnts_list_[i][0], cnts_list_[i][1]
        ker_targ = numbaExtract(test_targ, x, y, ker_radius)
        ker_replace = numbaExtract(test_replace, x, y, ker_radius)
        ker_targ1 = np.reshape(ker_targ.copy(), (ker_targ.shape[0] * ker_targ.shape[1]))
        ker_replace2 = np.reshape(
            ker_replace.copy(), (ker_replace.shape[0] * ker_replace.shape[1])
        )
        norm = numbaNormCalc(
            ker_targ1[ker_targ1 != 0],
            ker_replace2[ker_replace2 != 0],
            test_replace,
            x,
            y,
        )
        new_targ[x, y] = norm
    return new_targ


def computeRadiometricAdjustment(
    test_targ,
    test_replace,
    test_clouds,
    kernel_radius,
    num_cycles,
    org_shp_1,
    org_shp_2,
):
    for i in range(num_cycles):
        kernel = np.ones((5, 5), np.uint8)
        dilation_test_clouds = cv2.dilate(test_clouds, kernel, iterations=1)
        boundry_no_pad = dilation_test_clouds - test_clouds
        boundry_croped = cropCenterNorm(boundry_no_pad, org_shp_1, org_shp_2)
        boundry = np.pad(
            boundry_croped,
            ((kernel_radius, kernel_radius), (kernel_radius, kernel_radius)),
            "constant",
            constant_values=(0,),
        )
        locs = np.where(boundry == 1)
        cnts_list_ = np.transpose(np.array((locs[0], locs[1])), (1, 0))
        new_targ = np.zeros((test_targ.shape[0], test_targ.shape[1]))
        ker_radius = kernel_radius
        new_targ = stepwiseAdjustment(
            cnts_list_, test_targ, test_replace, new_targ, ker_radius
        )
        test_clouds = dilation_test_clouds
        test_targ = test_targ + new_targ
    return test_targ
