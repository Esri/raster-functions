import numpy as np
from datetime import datetime
from calendar import monthrange

class ConvertPerSecondToPerMonth():

    def __init__(self):
        self.name = "Convert Per-Second To Per-Month"
        self.description = ("This function converts a raster containing values "
                            "in units-per-second to a raster representing units-per-month.")
        self.scaleFactor = 1.0
        self.unit = "units per month"

    def getParameterInfo(self):
        return [
            {
                'name': 'raster',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Raster",
                'description': "The primary input raster."
            },
            {
                'name': 'units',
                'dataType': 'string',
                'value': "per month",
                'required': False,
                'displayName': "Output Units",
                'description': "Description of the units associated with the outgoing raster."
            },
        ]

    def getConfiguration(self, **scalars):
        return {
            'compositeRasters': False,              # input is a single raster, band compositing doesn't apply.
            'inheritProperties': 1 | 2 | 4 | 8,     # inherit everything
            'invalidateProperties': 2 | 4 | 8,      # reset statistics and histogram
            'keyMetadata': ('stdtime', 'acquisitiondate'),  # we can use this key property in .updateRasterInfo()
        }

    def updateRasterInfo(self, **kwargs):
        if kwargs['raster_info']['pixelType'] != 'f8':
            kwargs['output_info']['pixelType'] = 'f4'

        kwargs['output_info']['statistics'] = ()
        kwargs['output_info']['histogram'] = ()

        d = kwargs['raster_keyMetadata'].get('acquisitiondate', None)
        d = kwargs['raster_keyMetadata'].get('stdtime', d)
        if d is None:
            raise Exception("Unable to obtain date-time associated with the input raster using "
                            "key metadata 'AcquisitionDate' or 'StdTime'.")

        dt, r = None, None
        if isinstance(d, float):
            dt = datetime.utcfromtimestamp((d - 25569.) * 86400.)   # convert from variant time to Unix time
        elif isinstance(d, str) and d is not None and len(d) > 0:
            dt = datetime.strptime(d[:18], "%Y-%m-%dT%H:%M:%S")

        if dt is None:
            raise Exception("Unable to compute scale factor using the date '{0}' obtained from the input raster.".format(d))

        r = monthrange(dt.year, dt.month)
        if len(r) != 2 or not isinstance(r[1], int):
            raise Exception("Unable to compute scale factor using the date '{0}' obtained from the input raster.".format(d))

        self.scaleFactor = float(r[1]) * 86400.
        self.unit = kwargs.get('units', "per month")
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        inBlock = pixelBlocks['raster_pixels']
        pixelBlocks['output_pixels'] = (inBlock * self.scaleFactor).astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:
            keyMetadata['unit'] = self.unit
        return keyMetadata
