# Parameters for Projection Procedure
The dict file created for the Projection Procedure contains the following information:
- directories to input files (image, DEM, GCPs).
- projection parameters. <br /> <br /> 

## Input for Projection
`georef_webcam` searches automatically through all subdirectories of `in_dir` to find the needed files.

### Image file
An RGB image is required, all formats supported by [Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) can be used.<br />
So far .jpg, .png & .tif files have been projected successfully.

### DEM file
`PRACTISE` requires a DEM in cartesian coordinates in the ASCII-Grid format. If this is not the case, `georef_webcam` generates this data from the provided input. If the DEM needs to be projected to a cartesian Coordinate Reference System (CRS), the EPSG number of it is asked from the user. <br />
Additionally, the spatial resolution of the DEM can be resampled. We recommend to do so (e.g to 50 or 100m), if a large area is covered by the image and the projection parameters are not accurately known. It is faster to run the projection estimations on the DEM with lower spatial resolution. As soon as the projection accuracy is satisfying, you can change the DEM path variable in the dictionary to the one with full resolution. Use the option to edit the dictionary for that ([here](https://github.com/SebBuchelt/georef_webcam/blob/master/README.md#projection)).

### GCP file (optional)
Ground Control Points (GCPs) can be used to optimize the projection with the DDS optimization, which is incorporated into `PRACTISE`. See [Example](https://github.com/SebBuchelt/aux_data/blob/master/GCP_example.gcp.txt) for the required txt-file formatting.
<br /> <br /> 

## Projection Parameters
After inserting the directories to the input files, the parameters required for the projection procedure are collected. Those parameters can be accounted into 4 different groups:
- camera position
- camera orientation
- sensor parameters
- additional parameters

**Table with overview over all parameters**
| Parameter Type | mandatory for PRACTISE <td colspan=2>&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**additional input variables**  |aux variables |
|------------|----------|----------|
| camera position | <ul><li>`camera_DEMCRS_E`</li><li>`camera_DEMCRS_N`</li><li>`camera_offset`</li></ul>  <td colspan=2> <ul><li>`camera_epsg`</li><li>`camera_Easting`/`camera_longitude`</li><li>`camera_Northing`/`camera_latitude`</li><li>`camera_DEMCRS_Z`</li></ul> | <ul><li>`camera_x`</li><li>`camera_y`</li><li>`camera_DEM_height`</li></ul> |
| camera orientation | <ul><li>`target_DEMCRS_E`</li><li>`target_DEMCRS_N`</li><li>`target_offset`</li><li>`roll_angle_deg`</li></ul> | **Target coordinate approach**: <ul><li>`target_epsg`</li><li>`target_Easting`/<br />`target_longitude`</li><li>`target_Northing`/<br />`target_latitude`</li><li>`target_DEMCRS_Z`</li><li>`height_diff_target_cam`</li></ul> <td colspan=1> **Orientation angle approach**: <ul><li>`yaw_angle_deg`</li><li>`pitch_angle_deg`</li></ul> <br /><br /><br /><br /><br /> <td colspan=1>  <ul><li>`target_x`</li><li>`target_y`</li><li>`target_DEM_height`</li><li>`distance`</li></ul> |
| sensor parameters | <ul><li>`focalLen_mm`</li><li>`sensor_width_mm`</li><li>`sensor_height_mm`</li></ul> <td colspan=2> |
| additional parameters | <ul><li>`buffer_around_camera_m`</li></ul> <td colspan=2> |
<br />

### Planar Camera Position
At first the coordinate position of the camera has to be entered. You can enter the coordinates in any CRS. They will be stored in the following variables: 
- `camera_Easting`/`camera_longitude`
- `camera_Northing`/`camera_latitude`

With information about the EPSG-Nr. of the CRS (`camera_epsg`), `georef_webcam` automatically projects the camera location to the CRS of the DEM: <br /> `camera_DEMCRS_E`, `camera_DEMCRS_N`
<br /><br />

### Planar Camera Orientation
Afterwards the horizontal orientation is defined:
- either by inserting a yaw angle in degree: `yaw_angle_deg`
- or by inserting the coordinates of a target point in the same way as the camera position

_The target point is defined as the geographic position of the landscape feature in the center of the image (see also Figure 2)._

The definition of the planar camera position and orientation parameters are depicted here:
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/Pos_image.png"></p>
<p align="center"><sub>Figure 1: Planar Camera Position and Orientation Parameters. </sub></p>
<br />

### Vertical Camera Position
Two options exist to define the vertical location of the camera:
- relative height of camera above ground / above DEM: `camera_offset`
- absolute height of camera: `camera_DEMCRS_Z`

To support the selection of a reasonable value, the procedure tells the user the DEM height at the camera location (`camera_DEM_height`) before asking a value.
<br /><br />

### Vertical Camera Orientation
Consecutively, you can define the vertical orientation using one of the following ways:
- by inserting a pitch angle in degree: `pitch_angle_deg`
- by defining the height difference between target and camera: `height_diff_target_cam`
- by setting the relative height of the target point above ground / above DEM: `target_offset`
- or defining the absolute target point height: `camera_DEMCRS_Z`

For both, vertical position and orientation, all other parameters are derived from the given input.
The definition of the vertical camera position and orientation parameters are depicted here:
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/Vert_Params.png"></p>
<p align="center"><sub>Figure 2: Vertical Camera Position and Orientation. </sub></p>
<br />

### Adjusting further parameters
All other parameters are set to default values, which however might not be correct.
If values are unknown, keep default for a first try. But change them, if you know them. The predefined parameters are:
- Roll angle of the camera: `roll_angle_deg` (default: 0°)
- Sensor parameters given in mm: 
<br />`focalLen_mm` (14 mm) 
<br /> `sensor_width_mm` (22.3 mm) 
<br /> `sensor_height_mm` (14.9 mm) 
- Buffer range: `buffer_around_camera_m` (100m) <br />
This buffer variable is implemented in `PRACTISE` to make close range topography transparent for viewshed calculation and to avoid, that close slopes wrongly obscure the panoramic view.

_Sensor size parameters can possibly be found on [digicamdb.com](https://www.digicamdb.com/)._
<br /><br />

## Execution of Projection
After the collection of all required variables, parameters are passed to `PRACTISE` and projection is executed (see [Readme](https://github.com/SebBuchelt/georef_webcam/blob/master/README.md#projection)).
