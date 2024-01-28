#!/usr/bin/env python3
import argparse
import locale
import time
import numpy as np
from spectral_data import SpectralData
from cgats import CGATS
from edr import (
    EDRHeader,
    TECH_STRINGS_TO_INDEX,
)


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
    locale.setlocale(locale.LC_TIME, "C")

    st = time.strptime(timestr)

    locale.setlocale(locale.LC_TIME, '')

    return st


if __name__ == "__main__":
    main()