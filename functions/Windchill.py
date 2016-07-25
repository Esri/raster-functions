import numpy as np


class Windchill():

    def __init__(self):
        self.name = "Windchill Function"
        self.description = ("This function computes windchill given "
                            "wind speed and air temperature.")
        self.tUnits = 'f'
        self.wUnits = 'M'
        self.oUnits = 'f'

    def getParameterInfo(self):
        return [
            {
                'name': 'temperature',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Temperature Raster",
                'description': ("A single-band raster where pixel values represent "
                                "ambient air temperature in a specified units.")
            },
            {
                'name': 'tunits',
                'dataType': 'string',
                'value': 'Fahrenheit',
                'required': True,
                'domain': ('Celsius', 'Fahrenheit', 'Kelvin'),
                'displayName': "Temperature Units",
                'description': "The unit of measurement associated with the input temperature raster."
            },
            {
                'name': 'ws',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Wind-speed Raster",
                'description': ("A single-band raster where pixel values represent wind speed "
                                "measured in a specified units.")
            },
            {
                'name': 'wunits',
                'dataType': 'string',
                'value': 'mph',
                'required': True,
                'domain': ('mph', 'kph', 'm/s', 'ft/s', 'knots'),
                'displayName': "Wind-speed Units",
                'description': "The unit of measurement associated with the input wind-speed raster."
            },
            {
                'name': 'ounits',
                'dataType': 'string',
                'value': 'Fahrenheit',
                'required': True,
                'domain': ('Celsius', 'Fahrenheit', 'Kelvin'),
                'displayName': "Output Wind Chill Units",
                'description': "The unit of measurement associated with the output wind chill raster."
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,               # inherit all but the pixel type and NoData from the input raster
          'invalidateProperties': 2 | 4 | 8,        # invalidate statistics & histogram on the parent dataset because we modify pixel values. 
          'inputMask': True                         # Need input raster mask in .updatePixels()
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1      # output is a single band raster
        kwargs['output_info']['statistics'] = ()    # we know nothing about the stats of the outgoing raster. 
        kwargs['output_info']['histogram'] = ()     # we know nothing about the histogram of the outgoing raster.
        kwargs['output_info']['pixelType'] = 'f4'   

        self.tUnits = (kwargs.get('tunits', None) or 'Fahrenheit').lower()[0] 
        self.oUnits = (kwargs.get('ounits', None) or 'Fahrenheit').lower()[0] 
        self.wUnits = (kwargs.get('wunits', None) or 'mph').lower()

        if self.wUnits == "m/s":
            self.wUnits = 'm'
        elif self.wUnits == "kph":
            self.wUnits = 'k'
        elif self.wUnits == "knots":
            self.wUnits = 'n'
        elif self.wUnits == "ft/s":
            self.wUnits = 'f'
        else:
            self.wUnits = 'M'

        return kwargs

    def updatePixels(self, tlc, size, props, **pixelBlocks):
        ws = np.array(pixelBlocks['ws_pixels'], dtype='f4', copy=False)[0]
        t = np.array(pixelBlocks['temperature_pixels'], dtype='f4', copy=False)[0]

        m =  np.array(pixelBlocks['temperature_mask'], dtype=bool, copy=False)[0]
        m &= np.array(pixelBlocks['ws_mask'], dtype=bool, copy=False)[0]
        m &= (ws >= 0)

        # transform t to Fahrenheit
        if self.tUnits == 'k':
            t = (1.8 * t) - 459.67
        elif self.tUnits == 'c':
            t = (1.8 * t) + 32.

        # transform ws to mph
        if self.wUnits == 'm':
            ws *= (3600./1609.344)
        elif self.wUnits == 'k':
            ws /= 1.609344
        elif self.wUnits == 'n':
            ws /= 1.15077945
        elif self.wUnits == 'f':
            ws *= (5280. / 3600)

        wc = 35.74 + (0.6215 * t)
        ws16 = np.power(ws[m], 0.16)
        wc[m] += (0.4275 * t[m] * ws16) - (35.75 * ws16)

        # transform output wind-chill index to desired output units
        if self.oUnits == 'k':
            wc = (wc + 459.67) / 1.8
        elif self.oUnits == 'c':
            wc = (wc - 32.) / 1.8

        pixelBlocks['output_pixels'] = wc.astype(props['pixelType'], copy=False)
        pixelBlocks['output_mask'] = m.astype(dtype='u1', copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'Windchill'
            if self.oUnits == 'k':
                keyMetadata['unit'] = 'esriKelvin'
            elif self.oUnits == 'c':
                keyMetadata['unit'] = 'esriCelsius'
            else:
                keyMetadata['unit'] = 'esriFahrenheit'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None     # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'Winchill'
        return keyMetadata

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1] Steadman, Robert G. "Indices of windchill of clothed persons." 
        Journal of Applied Meteorology 10.4 (1971): 674-683.

    [2] National Weather Service. "NWS Wind Chill Index".
        http://www.nws.noaa.gov/om/winter/windchill.shtml

"""
