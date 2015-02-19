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

Find a bug or want to request a new feature?  Please let us know by submitting an issue.


## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).


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
