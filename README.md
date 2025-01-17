# ccss2edr

This tool converts Argyll .ccss (Colorimeter Calibration Spectral Set) files to
the X-Rite .edr format.

The motivation is to get more accurate color calibration using the i1Display Pro
(i1d3) colorimeter in software that uses the X-Rite SDK, like Calman or X-Rite
i1Profiler. The SDK ships with some generic EDRs that may not accurately match
the spectral distribution of your display. Converting a .ccss correction file
for your specific device (for example, from the [DisplayCAL corrections
database](https://colorimetercorrections.displaycal.net/)) and replacing the
generic EDR should yield better results.

A Sprague (1880) interpolation to 1nm spacing is performed on .ccss with spacing >1nm

## Usage

ccss2edr.py in.ccss out.edr` to convert the CCSS file `in.ccss`
   in the current working directory to `out.edr`

ccss2csv.py in.ccss out.csv` to convert the CCSS file `in.ccss`
   in the current working directory to `out.csv`
