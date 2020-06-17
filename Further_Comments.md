# Additional Comments

To improve the geolocation accuracy please consider the following circumstances:

### Lens distorsions

One major source for inaccuracies in the projection procedure is the lens distorsions of the camera system. If you can correct these errors in the image beforehand and run the projection on a distorsion corrected image, the georeferencing accuracy of your orthorectified product might improve. So far, this issue was handled by coregistering the image manually after projecting (see [Examples.md](https://github.com/SebBuchelt/georef_webcam/blob/master/Examples.md) for that).<br /> <br /> 

### Earth curvature

If the image you use covers a great area with a large distance range, Earth curvature can cause some missalignments. Due to the curvature, far distant landscape features appear at lower location in the image as the projected cartesian DEM point. Therefore, it is recommened to correct this error, by decreasing the DEM height based on a distance dependent offset. The function for that can be provided upon request.<br /> <br /> <br /> 

_(Back to [Readme](https://github.com/SebBuchelt/georef_webcam/blob/master/README.md))_
