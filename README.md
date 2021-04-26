# ArcGIS Raster Functions

This repository houses modern image processing and analytic tools called **raster functions**. 
Raster functions are *lightweight* and process only the pixels visible on your screen, in memory, without creating intermediate files. 
They are *powerful* because you can chain them together and apply them on huge rasters and mosaics on the fly. 

In this repository, you will find useful **function chains** (*.rft.xml) created by the Esri community. 
You can also create custom raster functions in Python that work seamlessly with the several dozen functions that ship with ArcGIS. 


## Getting Started

1. Install [ArcGIS for Desktop 10.4 or higher or pro 1.2 or higher](https://www.esri.com/en-us/store/overview), or [ArcGIS for Server 10.4 or higher](https://enterprise.arcgis.com/en/server/). 
2. Install the [latest release](https://github.com/Esri/raster-functions/releases/latest) of prerequisite *Python extension packages* if you are setting up for the first time:
   - Download [Python extensions binaries](https://github.com/Esri/raster-functions/releases/download/v1.0-beta.1/python-extensions-1.0-beta.1.zip).
   - Unzip the contents to a temporary local folder.
   - Run `<local-folder>/setup.py` with administrator privileges.
4. Install the **[latest release](https://github.com/Esri/raster-functions/releases/latest)** of *custom raster functions*:
   - Download all custom raster functions.
   If you are using pro use the [master branch](https://github.com/Esri/raster-functions).
   If you are using arcmap use the [arcmap107 branch](https://github.com/Esri/raster-functions/tree/arcmap107) 
   - Unzip the contents locally to a home folder.
   - You'll find ready-to-use `templates` and `functions` in their own subfolders.
6. Learn more about raster functions, function chains, and templates using the [Resources](#resources) below.
7. Learn how you can create new raster functions using the [Python API](https://github.com/Esri/raster-functions/wiki/PythonRasterFunction#anatomy-of-a-python-raster-function).


## Resources

* ##### Fundamentals
  * [ArcGIS Pro Help](https://pro.arcgis.com/en/pro-app/latest/help/main/welcome-to-the-arcgis-pro-app-help.htm)
  * [The raster functions **Wiki**](https://github.com/Esri/raster-functions/wiki)
  * [Python in ArcGIS Pro](https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/installing-python-for-arcgis-pro.htm)

* ##### Raster Functions
  * [What are raster functions?](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/raster-functions.htm)
  * [List of raster functions in ArcGIS Pro](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/list-of-raster-functions.htm)
  * [Editing functions on a raster dataset](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/overview-of-the-function-editor.htm)
  * [Creating custom raster functions](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/custom-raster-functions.htm)
  * [Using raster functions on Portal for ArcGIS](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/raster-analysis-with-portal.htm)

* ##### Raster Function Templates
  * [Applying raster function template for image analysis](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/raster-function-template.htm)
  * [Understanding raster function template properties](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/raster-function-template-properties.htm)
  * [Editing raster function templates in a mosaic dataset](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/using-mosaic-dataset-items-in-raster-function-templates.htm)
  * [Applying raster function templates](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/processing-template-manager.htm)
  * [Deploying custom python raster functions and templates](https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/python-raster-function-deployment.htm)

* ##### Scientific Computing in Python
  * [Scientific Computing Tools for Python](http://www.scipy.org/about.html)
  * [Python Scientific Lecture Notes](http://scipy-lectures.github.io/)
  
## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/Esri/raster-functions/issues).


## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).


## Featured Raster Functions and Templates

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

* #### Select By Pixel Size

  [SelectByPixelSize.py](https://github.com/Esri/raster-functions/blob/master/functions/SelectByPixelSize.py) accepts two 
  overlapping rasters and a threshold value indicating the resolution at which the function switches from returning 
  the first raster to returning the second raster as output. If unspecified, the `threshold` parameter defaults to the 
  average cell size of the two input rasters.
  
  [SelectByPixelSize.rft.xml](https://github.com/Esri/raster-functions/blob/master/templates/SelectByPixelSize.rft.xml) is a *grouping* 
  raster function template that accepts two rasters as input and leaves `threshold` unspecified. 

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


