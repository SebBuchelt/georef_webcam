# georef_webcam <img width="429" align="right" src="https://github.com/SebBuchelt/aux_data/blob/master/hintereisferner_webcam.jpg"> <br /> <br /> <img src="https://github.com/SebBuchelt/aux_data/blob/master/compare.gif" width="420" > 

<img width="300" align="left" src="https://github.com/SebBuchelt/aux_data/blob/master/Revision.png">
<br /> <br />

### Python toolbox to georeference webcam images 
- **Maintainer**: Sebastian Buchelt
- **Citation**: Buchelt, S. (2020-): georef_webcam V.1.0, https://github.com/SebBuchelt/georef_webcam. <br /> More on citation [here](https://github.com/SebBuchelt/georef_webcam/blob/master/README.md#citation)
- **License**: CC-BY-NC-SA 4.0

## Overview

`georef_webcam` is a python package for `python3`. It provides functionalities to georeference oblique camera images in complex terrain without accurate knowlegde about the required input parameters.
The package enables the user to georeference images based on estimations about camera position, system parameters & looking direction. <br /> 
Additionally, Ground Control Points (GCPs) can be added to optimize the projection parameters for a better geolocation accuracy. <br /> <br /> 
`georef_webcam` uses the Matlab scripts of the [`PRACTISE` package](https://github.com/shaerer/PRACTISE) to run the projection procedure. Based on its output, `georef_webcam` generates tif-files in the size of the original image with the coordinate position (Easting & Northing) of each pixel. Furthermore, a mask layer is generated to filter areas above the skyline. Based on those, a projected map of the camera image is produced.

#### Requirements
Please look in [`requirements.txt`](https://github.com/SebBuchelt/georef_webcam/blob/master/requirements.txt) to see, which python libraries are required for the  `georef_webcam` package.
It is also mandatory to download `Octave`, as the core projection procedure is running on Matlab scripts from [`PRACTISE` package](https://github.com/shaerer/PRACTISE). `PRACTISE` itself is downloaded automatically as the code has to be adapted for `georef_webcam`. <br />
So far this tool has been tested in Ubuntu 16.04, 18.04 & Windows 10.
<br /> <br />

## Installation
1. Download the package to the directory you like.
2. Install all required `python` packages to the conda environment you use (see [requirements.txt](https://github.com/SebBuchelt/georef_webcam/blob/master/requirements.txt)).
3. Download and install latest `Octave` version from [here](https://www.gnu.org/software/octave/download.html).
<br /> <br />

## Getting started
#### The following description gives a short idea, how the procedure works and how to get a good georeferencing result.

### Start georef_webcam:

Before starting the execution of the script, you should have the webcam image & the DEM file ready for processing. Then:
1. Activate environment 
2. set directory & start script:
```bash
$ cd /path/to/georef_webcam/
$ cd /python_scripts/
$ python georef_webcam.py in_dir out_dir [-n name_of_run]
```

The script georef_webcam.py requires two input parameter: 
- `in_dir`: directory, where the DEM file, the camera image and the gcp file (optional) are stored. The files can be stored in separate subdirectories.
- `out_dir`: directory, where output of `PRACTISE` and `georef_webcam` will be stored in subfolders.
- _`name_of_run`_ (optional): define a name for projection run to recognize output (default: test_run). <br /> <br />

### Parameter collection:
Two options: 
- Use a previously generated dictionary. The parameters can be read from any json-file in the input directory and also be edited then.
- Otherwise, a new dictionary will be created:
```ba
Do you want to create a new set of projection parameters?  y/n
```

**For further details about input parameters, their definition and requirements, see [Parameters.md](https://github.com/SebBuchelt/georef_webcam/blob/master/Parameters.md).**  <br />
After collecting them, the parameters are stored as json-file under `in_dir/[name_of_run].json`.
<br /> <br />

### Projection:
Parameters are taken from dictionary and passed to `PRACTISE`, which is then executed. 
Afterwards, DEM points projected into image plane are plotted in Octave window and can be checked:
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/Octave_fig.png"></p>
<p align="center"><sub>Figure 1: DEM points projected into image plane. <br /> Left: wrong projection parameters; Right: Corrected projection parameters. </sub></p>

 Then you can decide between the following options:
```ba
Projection has been executed. 
What do you want to do next?
Please select one of the following options:
0: end procedure
1: edit projection input parameters and repeat projection procedure
2: produce georef_webcam output

Which of the options do you want to choose? 
```
- `0`: ends program
- `1`: edits projection parameters, stores them in new json file (optionally) and then repeats the projection
- `2`: moves on to output generation <br /> <br />

### Output generation:
The following output is produced and stored in `outdir/georef_result/name_of_run/` (_italic files are optional_):
- the original image
- `east_raster` & `north_raster`: two tif-files with the size of the image giving the easting, northing coordinate of each pixel
- _`alt_raster`:_ tif-file with altitude of each image pixel
- _`dist_raster`:_ tif-file with distance of each image pixel to camera location
- `mask`: tif-file containing the mask layer
- _`[image_name]_map.tif`:_ projected map of the camera image
<br /><br />

## Output examples
<p align="center"><img width="45%" src="https://github.com/SebBuchelt/aux_data/blob/master/Easting.jpg"> <img width="45%" src="https://github.com/SebBuchelt/aux_data/blob/master/Northing.jpg"> </p>
<p align="center"><sub>Figure 2: Final result - Coordinate rasters. </sub></p>
<br>

<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/hintereisferner_webcam.jpg"></p>
<p align="center"><sub>Figure 3: Used webcam image. </sub></p>
<br>
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/compare.gif"></p>
<p align="center"><sub>Figure 4: Animation showing same-day Sentinel-2 image overlayed with projected webcam image. </sub></p>
<br>

**More examples can be found [here](https://github.com/SebBuchelt/georef_webcam/blob/master/Examples.md).**<br /> <br /> 

## Projecting other data
After a successful georeferencing any data or image with the same acquisition geometry can be projected to map coordinates with the function `project_data2map.py`:

```bash
$ python project_data2map.py coord_dir filename_or_extension pixel_size out_dir 
         [-f IMAGE_FOLDER] [-fill FILL_NODATA]
```
 The following input parameters are required: 
- `coord_dir`: directory, where the output of `georef_webcam` with the coordinate rasters and the mask is stored.
- `filename_or_extension`: select the dataset or image, which should be projected. <br />
If you want to project several files, just insert the file extension (e.g. tif, png, jpg). In this case, the optional variable _`image_folder`_ is required. All dataset with the specified file extension in this folder will be projected.
- `pixel_size`: define spatial resolution of your product.
- `out_dir`: directory, where produced maps should be stored.
- _`fill_nodata`_ (optional): voids in the projected dataset can be filled with interpolation here. <br /> <br />


# Citation
Please cite `georef_webcam` as following:
- Buchelt, S. (2020-): georef_webcam V.1.0, https://github.com/SebBuchelt/georef_webcam.

As this work is primarily based on the [PRACTISE software](https://github.com/shaerer/PRACTISE) and its functionalities, please also cite:
- Härer, S., Bernhardt, M., and Schulz, K.: PRACTISE: PRACTISE V.2.1. Zenodo, doi:10.5281/zenodo.35646, 2015.

I also want to give special thanks to Gerhard Keuschnig & Florian Radlherr from [foto-webcam.eu](https://www.foto-webcam.eu), who provide a great system for high-resolution webcam images. The images used here are provided by their website.
