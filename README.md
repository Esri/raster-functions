# ArcGIS Raster Functions

This repository houses modern image processing and analytic tools called **raster functions**. 
Raster functions are *lightweight* and process only the pixels visible on your screen, in memory, without creating intermediate files. 
They are *powerful* because you can chain them together and apply them on huge rasters and mosaics on the fly. 

In this repository, you will find useful **function chains** (*.rft.xml) created by the Esri community. 
You can also create custom raster functions in Python that work seamlessly with the several dozen functions that ship with ArcGIS. 


## Getting Started

1. Install [ArcGIS for Desktop 10.3](http://desktop.arcgis.com/en/desktop/) or [ArcGIS Pro 1.0](http://pro.arcgis.com/en/pro-app). 
   ArcGIS comes with [Python](http://desktop.arcgis.com/en/desktop/latest/analyze/python/what-is-python-.htm).
3. [Download](https://github.com/Esri/raster-functions/archive/master.zip) and unzip this repo.
4. Install Python dependencies:
```
    $ cd scripts
    $ python get-pip.py
    $ pip install -r requirements.txt
```
4. Ready-to-use function templates are in the `templates/` folder. Implementation of raster functions live under `functions/`. 
5. Learn about functions, function chains, and templates by browsing the links under [Resources](#resources).
6. Learn how to create new raster functions using the [Python API](https://github.com/Esri/raster-functions/wiki/PythonRasterFunction#anatomy-of-a-python-raster-function).


## Resources

* [ArcGIS 10.3 Help](http://resources.arcgis.com/en/help/)
* [Rasters with functions](http://resources.arcgis.com/en/help/main/10.2/index.html#//009t0000000m000000)
* [A blog on raster functions](http://blogs.esri.com/esri/arcgis/2010/08/10/raster-functions/)
* [Editing functions on a raster dataset](http://resources.arcgis.com/en/help/main/10.2/index.html#/Editing_functions_on_a_raster_dataset/009t000001zs000000/)
* [Image Analysis window: Processing section](http://resources.arcgis.com/en/help/main/10.2/index.html#//009t000000m7000000)
* [Create new raster function templates](http://resources.arcgis.com/en/help/main/10.2/index.html#//009t00000234000000)
* [Editing function templates](http://resources.arcgis.com/en/help/main/10.2/index.html#//009t000001zn000000)
* [*ArcGIS Pro*: Using raster functions](http://pro.arcgis.com/en/pro-app/help/data/imagery/apply-functions-to-a-dataset.htm)

* [The raster functions **Wiki**](https://github.com/Esri/raster-functions/wiki)

## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/Esri/raster-functions/issues).


## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

------------

## Featured Raster Functions and Templates


* #### Normalized Difference Vegetation Index
  [NDVI.py](https://github.com/Esri/raster-functions/blob/master/functions/NDVI.py) serves as a reference 
  Python rendition of the [stock NDVI raster function](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/ndvi-function.htm).
  It accepts one multi-band raster as input, and one-based indices corresponding to the Red and Infrared bands of 
  the input raster. An additional `method` parameter controls whether the output NDVI raster contains
  raw, scaled, or color-mapped values.
  
  Supporting templates:
  - [NDVI-Raw](https://github.com/Esri/raster-functions/blob/master/templates/NDVI.rft.xml):
    Returns raw NDVI values in the range [-1.0, +1.0] as a one-band, floating-point raster.
  - [NDVI-Grayscale](https://github.com/Esri/raster-functions/blob/master/templates/NDVI-Grayscale.rft.xml):
    Returns NDVI values scaled to the range [0, 200] as one-band, 8-bit raster.
  - [NDVI-Colormap](https://github.com/Esri/raster-functions/blob/master/templates/NDVI-Colormap.rft.xml):
    Returns *scaled* NDVI values as color-mapped raster.

  Learn more about NDVI on [Wikipedia](http://en.wikipedia.org/wiki/Normalized_Difference_Vegetation_Index) 
  or in the [Documentation for ArcGIS](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/ndvi-function.htm). 

* #### Wind Chill

  TODO
  
  Learn more about Wind Chill on [Wikipedia](http://en.wikipedia.org/wiki/Wind_chill).
  
* #### Heat Index

  [HeatIndex.py](https://github.com/Esri/raster-functions/blob/LinearUnmixing/functions/HeatIndex.py) computes 
  apparent temperature (as perceived by us) given two rasters corresponding to ambient air temperature and relative humidity. 
  An additional string parameter 'units' controls whether the air temperature values are assumed to be in Celsius or Fahrenheit.
  
  [HeatIndex.rft.xml](https://github.com/Esri/raster-functions/blob/LinearUnmixing/templates/HeatIndex.rft.xml) is a *grouping* 
  raster function template. The 'units' parameter remains unmodified by the template and defaults to `Fahrenheit`. 
  
  Learn more about Heat Index on [Wikipedia](http://en.wikipedia.org/wiki/Heat_index).

* #### Key Metadata

  TODO

* #### Mask Raster

  TODO

* #### Arithmetic

  TODO

* #### Aggregate

  TODO

* #### Deviation from Mean

  TODO

* #### Select By Pixel Size

  TODO


* #### Convert Per Second to Per Month

  TODO

* #### Composite Bands

  TODO

* #### Hillshade

  TODO

* #### Multidirectional Hillshade

  TODO

* #### Vineyard Analysis

  TODO

* #### Fish Habitat Suitability

  TODO


------------

## Licensing
Copyright 2014 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [License.txt](License.txt?raw=true) file.

[](Esri Tags: ArcGIS Raster Function Chain On-the-fly Image Processing Samples)
[](Esri Language: Python)​
