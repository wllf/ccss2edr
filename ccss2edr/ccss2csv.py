#!/usr/bin/env python3
import argparse
import locale
import struct
import time
import numpy as np
import colour.algebra.interpolation as ci
import csv
from dataclasses import dataclass
from cgats import CGATS
from edr import (
    EDRHeader,
    EDRDisplayDataHeader,
    EDRSpectralDataHeader,
    TECH_STRINGS_TO_INDEX,
)


@dataclass
class SpectralData:
    # Wavelength of the first spectral band, in nanometers
    start_nm: float
    # Wavelength of the last spectral band, in nanometers
    end_nm: float
    # Width of each spectral band, in nanometers
    space_nm: float
    # Spectral norm
    norm: float
    # Number of samples in each spectral data set
    num_bands: int
    # Number of spectral data sets
    num_sets: int
    # Sets of spectral data
    sets: np.ndarray

    @staticmethod
    def from_ccss(ccss: CGATS):
        num_bands = int(ccss["SPECTRAL_BANDS"])
        start_nm = float(ccss["SPECTRAL_START_NM"])
        end_nm = float(ccss["SPECTRAL_END_NM"])
        norm = float(ccss["SPECTRAL_NORM"])
        space_nm = (end_nm - start_nm) / (num_bands - 1)

        # Always skip the first field, SAMPLE_ID
        skip_fields = 1

        if start_nm > 380.0:
            raise Exception(
                "spectral data start must be <= 380.0 nm, is {}".format(
                    start_nm))
        elif start_nm < 380.0:
            skip_samples = int((380.0 - start_nm) / space_nm)
            # Skip bands so the data starts at 380 nm
            skip_fields += skip_samples
            num_bands -= skip_samples
            start_nm = 380.0
            print("Warning: spectral data does not start at 380 nm, "
                  "skipping {} leading bands".format(skip_samples))

        num_sets = int(ccss["NUMBER_OF_SETS"])

        setslist = []
        for data in ccss.data:
            setslist.append([
                # convert from mW/nm/m^2 to W/nm/m^2
                float(val) for val in data[skip_fields:]
            ])
        sets = np.array(setslist)
        
        #Interpolate to 1nm using CIE recommended Sprague (1880) method
        if space_nm > 1:
            x = np.arange(start_nm, end_nm + 1, space_nm)
            x[-1] = end_nm
            xi = np.arange(start_nm, end_nm + 1, 1)
            setsi = xi
            for set in sets:
                y = np.array(set)
                si = ci.SpragueInterpolator(x, y)
                yi = si(xi)
                setsi = np.vstack((setsi, yi))
            space_nm = 1
            num_bands = int(end_nm - start_nm + 1)
            sets = setsi

        return SpectralData(start_nm, end_nm, space_nm, norm, num_bands,
                            num_sets, sets)

    def edr_spectral_data_header(self):
        header = EDRSpectralDataHeader()
        header.num_samples = self.num_bands
        return header


def main():
    parser = argparse.ArgumentParser(
        description="Convert a .ccss file to .csv")

    parser.add_argument("ccss",
                        type=argparse.FileType("r"),
                        help=".ccss input filename")
    parser.add_argument("-n", "--norm", action="store_true", help="normalize")
    parser.add_argument("out",
                        help=".csv output filename")

    args = parser.parse_args()

    ccss = CGATS(args.ccss)

    # EDR DATA header

    edr_header = EDRHeader()

    if "DESCRIPTOR" in ccss and ccss["DESCRIPTOR"] != "Not specified":
        edr_header.display_description = ccss["DESCRIPTOR"].encode()
    elif "DISPLAY" in ccss:
        edr_header.display_description = ccss["DISPLAY"].encode()
    if "ORIGINATOR" in ccss:
        edr_header.creation_tool += " ({})".format(ccss["ORIGINATOR"]).encode()
    if "CREATED" in ccss:
        edr_header.creation_time = int(time.mktime(unasctime(ccss["CREATED"])))
    if "MANUFACTURER_ID" in ccss:
        edr_header.display_manufacturer_id = ccss["MANUFACTURER_ID"].encode()
    if "MANUFACTURER" in ccss:
        edr_header.display_manufacturer = ccss["MANUFACTURER"].encode()
    elif "TECHNOLOGY" in ccss:
        tech = ccss["TECHNOLOGY"]
        if tech not in TECH_STRINGS_TO_INDEX and tech[-4:] in (" IPS", " VPA",
                                                               " TFT"):
            tech = tech[:-4]
        if tech in TECH_STRINGS_TO_INDEX:
            edr_header.tech_type = TECH_STRINGS_TO_INDEX[tech]
        else:
            print("Warning: Unknown technology %r" % tech)

    spectral_data = SpectralData.from_ccss(ccss)

    sd = np.arange(spectral_data.start_nm, spectral_data.end_nm + 1, 1)
    print(sd)
    print(spectral_data.sets)
    sd = np.vstack((sd, spectral_data.sets))
    print(sd)
#    sd = spectral_data.sets
    if args.norm:
        sdm = np.amax(sd, axis=1)
        sd = sd / sdm
    sd = sd.transpose()
    
    print(sd)
    np.savetxt(args.out, sd, delimiter = ',')


def unasctime(timestr):
    loc = locale.getlocale()
    locale.setlocale(locale.LC_TIME, "C")

    st = time.strptime(timestr)

    locale.setlocale(locale.LC_TIME, loc)

    return st


if __name__ == "__main__":
    main()