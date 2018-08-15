# ArcGIS Raster Functions

This repository houses modern image processing and analytic tools called **raster functions**. 
Raster functions are *lightweight* and process only the pixels visible on your screen, in memory, without creating intermediate files. 
They are *powerful* because you can chain them together and apply them on huge rasters and mosaics on the fly. 

In this repository, you will find useful **function chains** (*.rft.xml) created by the Esri community. 
You can also create custom raster functions in Python that work seamlessly with the several dozen functions that ship with ArcGIS. 


## Getting Started

1. Install [ArcGIS for Desktop 10.4](http://desktop.arcgis.com/en/desktop/), or [ArcGIS for Server 10.4](https://server.arcgis.com/en/server/). 
2. Install the [latest release](https://github.com/Esri/raster-functions/releases/latest) of prerequisite *Python extension packages* if you are setting up for the first time:
   - Download [Python extensions binaries](https://github.com/Esri/raster-functions/releases/download/v1.0-beta.1/python-extensions-1.0-beta.1.zip).
   - Unzip the contents to a temporary local folder.
   - Run `<local-folder>/setup.py` with administrator privileges.
4. Install the **[latest release](https://github.com/Esri/raster-functions/releases/latest)** of *custom raster functions*:
   - Download all [custom raster functions](https://github.com/Esri/raster-functions/releases/download/v1.0-beta.1/raster-functions-1.0-beta.1.zip).
   - Unzip the contents locally to a home folder.
   - You'll find ready-to-use `templates` and `functions` in their own subfolders.
6. Learn more about raster functions, function chains, and templates using the [Resources](#resources) below.
7. Learn how you can create new raster functions using the [Python API](https://github.com/Esri/raster-functions/wiki/PythonRasterFunction#anatomy-of-a-python-raster-function).


## Resources

* ##### Fundamentals
  * [ArcGIS 10.4 Help](http://resources.arcgis.com/en/help/)
  * [The raster functions **Wiki**](https://github.com/Esri/raster-functions/wiki)
  * [What's Python](http://desktop.arcgis.com/en/desktop/latest/analyze/python/what-is-python-.htm)

* ##### Raster Functions
  * [What are raster functions?](http://blogs.esri.com/esri/arcgis/2010/08/10/raster-functions/)
  * [Rasters with functions](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/rasters-with-functions.htm)
  * [Editing functions on a raster dataset](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/editing-functions-on-a-raster-dataset.htm)
  * [Editing function chains in a mosaic dataset](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/editing-function-chains-in-md.htm)
  * [Image Analysis window: Processing section](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/image-analysis-window-processing-section.htm)
  * [*ArcGIS Pro*: Using raster functions](http://pro.arcgis.com/en/pro-app/help/data/imagery/apply-functions-to-a-dataset.htm)

* ##### Raster Function Templates
  * [Creating new raster function templates](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/accessing-the-raster-function-template-editor.htm)
  * [Saving a function chain as a raster function template](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/editing-function-chain-templates.htm#ESRI_SECTION1_0A062EDFA12B4F07BA04F567C7132C18)
  * [Applying function templates](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/applying-a-function-template.htm)
  * [Editing function templates](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/editing-function-chain-templates.htm)
  * [Resolving template variables using attribute table](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/wkflw-populating-functions-with-values-from-attrib-table.htm)
  * [Adding a processing template to a mosaic dataset](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/adding-a-processing-template-to-a-mosaic-dataset.htm)
  * [Configuring an image service to use a raster function template](http://server.arcgis.com/en/server/latest/publish-services/windows/server-side-raster-functions.htm#ESRI_SECTION1_8E7C2EADF7504674B168453B71F400F2)

* ##### Scientific Computing in Python
  * [Scientific Computing Tools for Python](http://www.scipy.org/about.html)
  * [Python Scientific Lecture Notes](http://scipy-lectures.github.io/)
  
## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/Esri/raster-functions/issues).


## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).


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

  [WindChill.py](https://github.com/Esri/raster-functions/blob/TintedHillshade/functions/Windchill.py) computes 
  wind chill given two rasters representing wind speed in miles-per-hour and ambient air temperature in Fahrenheit.
  
  [Windchill.rft.xml](https://github.com/Esri/raster-functions/blob/LinearUnmixing/templates/Windchill.rft.xml) is a *grouping* 
  raster function template.

  Learn more about Wind Chill on [Wikipedia](http://en.wikipedia.org/wiki/Wind_chill).
  
* #### Heat Index

  [HeatIndex.py](https://github.com/Esri/raster-functions/blob/LinearUnmixing/functions/HeatIndex.py) computes 
  apparent temperature (as perceived by us) given two rasters corresponding to ambient air temperature and relative humidity. 
  An additional string parameter `units` controls whether the air temperature values are assumed to be in Celsius or Fahrenheit.
  
  [HeatIndex.rft.xml](https://github.com/Esri/raster-functions/blob/LinearUnmixing/templates/HeatIndex.rft.xml) is a *grouping* 
  raster function template. The `units` parameter remains unmodified by the template and defaults to `Fahrenheit`. 
  
  Learn more about Heat Index on [Wikipedia](http://en.wikipedia.org/wiki/Heat_index).

* #### Key Metadata

  [KeyMetadata.py](https://github.com/Esri/raster-functions/blob/TintedHillshade/functions/KeyMetadata.py) demonstrates
  how [*key properties*](https://github.com/Esri/raster-functions/wiki/KeyMetadata#key-metadata) 
  can be introduced or overridden by a raster function. These are the inputs to the function:

  - `Property Name`, `Property Value`&mdash;The name and value of the dataset-level key property to update or introduce.
  - `Band Names`&mdash;Band names of the outgoing raster specified as a CSV. 
  - `Metadata JSON`&mdash;Key metadata to be injected into the outgoing raster described as a JSON string representing a collection of key-value pairs. 
    Learn more [here](http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000p3000000).
  
  This function serves as an example of one that doesn't need to implement 
  the [`.updatePixels()`](https://github.com/Esri/raster-functions/wiki/PythonRasterFunction#updatepixels) method. 

* #### Mask Raster

  [MaskRaster.py](https://github.com/Esri/raster-functions/blob/master/functions/MaskRaster.py) enables you to apply
  the input mask raster as the [NoData mask](https://github.com/Esri/raster-functions/wiki/EffectiveFunctions#nodata) 
  on the primary input raster.
  
  [MaskRaster.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/MaskRaster.rft.xml) is a *grouping* 
  raster function template where the inputs are the primary raster and the mask raster (in that order).

* #### Arithmetic

  [Arithmetic.py](https://github.com/Esri/raster-functions/blob/master/functions/Arithmetic.py) demonstrates the application 
  of simple arithmetic operations on two rasters. It's not meant to replace the functionality provided by the built-in 
  [Local Function](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/local-function.htm)
  or the [Math toolset](http://desktop.arcgis.com/en/desktop/latest/tools/spatial-analyst-toolbox/an-overview-of-the-math-tools.htm). 
  You can, however, use it as a springboard to building custom mathematical or analytical operations. 

* #### Aggregate

  [Aggregate.py](https://github.com/Esri/raster-functions/blob/master/functions/Aggregate.py) serves to demonstrates the application 
  of simple aggregation along each pixel over a collection of overlapping rasters. The primary input to the function is of type 
  `rasters` representing an array of rasters. The `method` string parameter enables a user or template to choose the specific operation 
  (from `Sum`, `Average`, `Standard Deviation`, `Minimum`, and `Maximum`) to perform. The parameter defaults to `Sum`. 
  The output is a raster containing values corresponding to the chosen statistic. 

  [Aggregate.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/Aggregate.rft.xml) is a sample *grouping* 
  raster function template with only one input: the collection of rasters to aggregate. The template leaves the `method` parameter unmodified. 
  
* #### Deviation from Mean

  [DeviationFromMean.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/DeviationFromMean.rft.xml) helps 
  with anomaly detection by calculating the deviation of the primary raster from the mean computed over a collection of 
  overlapping rasters. This *grouping* raster function template demonstrates how complex operations can be constructed by 
  *chaining* simple functions. The template computes the mean over a collection of rasters using the [Aggregate](#aggregate) 
  function and then subtracts that result from the pixels values of the primary raster. 
  
  It's interesting to note that this template could be rewritten as a single Python raster function that accepts a raster array
  and compute deviation from the group mean of the first (or some user-specified) raster in that group. 

* #### Select By Pixel Size

  [SelectByPixelSize.py](https://github.com/Esri/raster-functions/blob/master/functions/SelectByPixelSize.py) accepts two 
  overlapping rasters and a threshold value indicating the resolution at which the function switches from returning 
  the first raster to returning the second raster as output. If unspecified, the `threshold` parameter defaults to the 
  average cell size of the two input rasters.
  
  [SelectByPixelSize.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/SelectByPixelSize.rft.xml) is a *grouping* 
  raster function template that accepts two rasters as input and leaves `threshold` unspecified. 

* #### Convert Per Second to Per Month

  [ConvertPerSecondToPerMonth.py](https://github.com/Esri/raster-functions/blob/master/functions/ConvertPerSecondToPerMonth.py)
  accepts a raster containing pixels values representing observations in some units per-second, and converts it to a raster 
  representing the observation in units per-month. For this conversion to be a accurate, the function needs to know the month associated with 
  acquisition of the input raster. This function demonstrates effective use of [*key metadata*](https://github.com/Esri/raster-functions/wiki/EffectiveFunctions) 
  in processing and analysis. 

* #### Composite Bands

  [CompositeBands.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/CompositeBands.rft.xml) and 
  [CompositeBands-4Bands-Ordered.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/CompositeBands-4Bands-Ordered.rft.xml) 
  are raster function templates that demonstrate *grouping* with `rasters` (an array of raster objects) and with four individual 
  rasters, respectively. The output is a single raster generated by compositing all bands of all overlapping input rasters. The template uses 
  the built-in [composite bands raster function](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/composite-bands-function.htm). 
  
* #### Hillshade

  [Hillshade.py](https://github.com/Esri/raster-functions/blob/master/functions/Hillshade.py) is reference Python implementation 
  designed to emulate the built-in 
  [Hillshade raster function](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/hillshade-function.htm) 
  while serving to demonstrate effective use of [SciPy](http://www.scipy.org/about.html), 
  [NumPy](http://www.numpy.org/#), and the helper functions implemented in the 
  [`utils` module](https://github.com/Esri/raster-functions/blob/master/functions/utils.py). This is an example of a 
  [neighborhood](http://en.wikipedia.org/wiki/Neighborhood_operation) or 
  [focal](http://desktop.arcgis.com/en/desktop/latest/guide-books/extensions/spatial-analyst/performing-analysis/the-types-of-operations-in-spatial-analyst.htm#GUID-6776230A-E6CD-477B-8C77-E8B14CA052E1) 
  operation. 
  
  The [Scale-adjusted Hillshade](https://github.com/Esri/raster-functions/blob/master/templates/Hillshade-ScaleAdjusted-Py.rft.xml) raster 
  function template applies hillshading on the input elevation raster with a non-linearly adjusted z-factor. 
  
  Learn more about how the hillshade algorithm works [here](http://desktop.arcgis.com/en/desktop/latest/tools/spatial-analyst-toolbox/how-hillshade-works.htm).

* #### Multidirectional Hillshade

  [MultidirectionalHillshade.pyd](https://github.com/Esri/raster-functions/blob/master/functions/MultidirectionalHillshade.pyd)
  and the accompanying [MultidirectionalHillshade.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/MultidirectionalHillshade.rft.xml)
  raster function template applies Hillshading from multiple directions for improved visualization. 
  Learn more [here](http://blogs.esri.com/esri/arcgis/2014/07/14/introducing-esris-next-generation-hillshade/).

* #### Fish Habitat Suitability

  [FishHabitatSuitability.py](https://github.com/Esri/raster-functions/blob/master/functions/FishHabitatSuitability.py) returns a raster representing suitability 
  of fish habitat at a user-specified ocean depth given two rasters representing water temperature and salinity.  This function demonstrates 
  how raster functions can be exploited in analytic workflows.
  
  [FishHabitatSuitability.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/FishHabitatSuitability.rft.xml) is a *grouping* 
  raster function template that accepts the temperature and salinity rasters (in that order). This template&#8212;when used in the 
  [Add Rasters to Mosaic Dataset tool](http://desktop.arcgis.com/en/desktop/latest/tools/data-management-toolbox/add-rasters-to-mosaic-dataset.htm) 
  with the [Table raster type](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/files-tables-and-web-services-raster-types.htm#ESRI_SECTION1_D8E60C757CA04174BED580F2101443BD)
  or as a [processing template](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/adding-a-processing-template-to-a-mosaic-dataset.htm) 
  on a mosaic dataset&#8212;is capable of obtaining the value of the `depth` parameter from a [specific field](https://github.com/Esri/raster-functions/blob/master/templates/FishHabitatSuitability.rft.xml#L38-L44)
  (`StdZ`, if available) in the table.

* #### Vineyard Analysis

  [VineyardAnalysis.py](https://github.com/Esri/raster-functions/blob/master/functions/VineyardAnalysis.py) serves to demonstrate how 
  you can compute a *suitability* raster given the [elevation](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/wkflw-elevation-part1.htm), 
  [slope](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/slope-function.htm), 
  and [aspect](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/aspect-function.htm) of the region. 
  
  [VineyardAnalysis.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/VineyardAnalysis.rft.xml) accepts the elevation input raster 
  and uses built-in raster functions to compute slope and elevation before feeding the output to the Vineyard Analysis raster function. 

* #### Aspect-Slope
  [AspectSlope.py](https://github.com/Esri/raster-functions/blob/master/functions/AspectSlope.py) generates an aspect slope map i.e. simultaneously
  shows the [aspect](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/aspect-function.htm) (direction) and [slope](http://desktop.arcgis.com/en/desktop/latest/manage-data/raster-and-images/slope-function.htm)  in degree (steepness) for a terrain or other continuous surface.
  
  [AspectSlope.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/AspectSlope.rft.xml) accepts the elevation input raster and creates aspect slope map raster for visualization. 
  
 * #### Topographic C-Correction
   [Topographic c-correction](https://github.com/Esri/raster-functions/blob/master/functions/TopographicCCorrection.py) is used to remove the effects of hillshade on multispectral images. It reduces the effects of reflectance variability in areas of high or rugged terrain, thus improving the consistency of the multispectral image pixel values and the quality of images as additional processing is applied. There are many different topographic correction algorithms. These algorithms have been compared by [Ion Sola et. al (2016)](https://www.researchgate.net/publication/305469055_Multi-criteria_evaluation_of_topographic_correction_methods) and the c-correction proposed in [Teillet, Guindon, and Goodenough (1982)](https://www.tandfonline.com/doi/abs/10.1080/07038992.1982.10855028)  was ranked as one of the best topographic correction methods. 



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


