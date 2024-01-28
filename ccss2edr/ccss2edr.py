#!/usr/bin/env python3
import argparse
import locale
import struct
import time
import numpy as np
import colour.algebra.interpolation as ci
from dataclasses import dataclass
from cgats import CGATS
from edr import (
    EDRHeader,
    EDRDisplayDataHeader,
    EDRSpectralDataHeader,
    TECH_STRINGS_TO_INDEX,
)
from spectral_data import SpectralData


def main():
    parser = argparse.ArgumentParser(
        description="Convert a .ccss file to .edr")

    parser.add_argument("ccss",
                        type=argparse.FileType("r"),
                        help=".ccss input filename")
    parser.add_argument("--tech-type", type=int, help="technology type")
    parser.add_argument("out",
                        type=argparse.FileType("wb"),
                        help=".edr output filename")

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
    if args.tech_type:
        edr_header.tech_type = args.tech_type
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

    edr_header.spectral_start_nm = spectral_data.start_nm
    edr_header.spectral_end_nm = spectral_data.end_nm
    edr_header.spectral_norm = spectral_data.norm
    edr_header.num_sets = spectral_data.num_sets

    args.out.write(edr_header.pack())

    display_data_header = EDRDisplayDataHeader()
    spectral_data_header = spectral_data.edr_spectral_data_header()

    for spectral_set in spectral_data.sets:
        args.out.write(display_data_header.pack())
        args.out.write(spectral_data_header.pack())

        for val in spectral_set:
            # Convert mW/nm/m^2 to W/nm/m^2
            args.out.write(struct.pack("<d", val / 1000))


def unasctime(timestr):
    locale.setlocale(locale.LC_TIME, "C")

    st = time.strptime(timestr)

    locale.setlocale(locale.LC_TIME, '')

    return st


if __name__ == "__main__":
    main()
