#!/usr/bin/env python3
import argparse
import struct
import time
from dataclasses import dataclass
from csv_correlation import CSVCorrelation
from edr import (
    TECH_STRINGS_TO_INDEX,
    EDRHeader,
    EDRDisplayDataHeader,
)
from spectral_data import SpectralData


def main():
    parser = argparse.ArgumentParser(
        description="Convert a .csv correlation file to .edr")

    parser.add_argument("csv", type=str, help=".csv input filename")
    parser.add_argument("--tech-type", type=str, help="technology type")
    parser.add_argument("--manu-id", type=str, help="manufacturer ID")
    parser.add_argument("--manu-name", type=str, help="manufacturer name")
    parser.add_argument("out",
                        type=argparse.FileType("wb"),
                        help=".edr output filename")

    args = parser.parse_args()



    csv = CSVCorrelation(args.csv)

    # EDR DATA header

    edr_header = EDRHeader()

    edr_header.display_description = csv.descriptor.encode()
    edr_header.creation_tool += " ({})".format('CSV Correlation File').encode()
    edr_header.creation_time = int(time.time())
    edr_header.display_manufacturer_id = args.manu_id.encode()
    edr_header.display_manufacturer = args.manu_name.encode()
    if args.tech_type:
        tech = args.tech_type
        if tech not in TECH_STRINGS_TO_INDEX and tech[-4:] in (" IPS", " VPA",
                                                               " TFT"):
            tech = tech[:-4]
        if tech in TECH_STRINGS_TO_INDEX:
            edr_header.tech_type = TECH_STRINGS_TO_INDEX[tech]
        else:
            print("Warning: Unknown technology %r" % tech)

    spectral_data = SpectralData.from_csv(csv)

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
            args.out.write(struct.pack("<d", val))

if __name__ == "__main__":
    main()
