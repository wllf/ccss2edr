from cgats import CGATS
from csv_correlation import CSVCorrelation
from edr import EDRSpectralDataHeader


import colour.algebra.interpolation as ci
import numpy as np


from dataclasses import dataclass


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
    # Sets of spectral data (in W/nm/m^2)
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
    
    @staticmethod
    def from_csv(csv: CSVCorrelation):
        start_nm = csv.start_nm
        end_nm = csv.end_nm
        num_bands = csv.num_bands
        num_sets = csv.num_sets
        space_nm = (end_nm - start_nm) / (num_bands - 1)
        norm = float(1)
        sets = csv.data

        return SpectralData(start_nm, end_nm, space_nm, norm, num_bands, num_sets, sets)


    def edr_spectral_data_header(self):
        header = EDRSpectralDataHeader()
        header.num_samples = self.num_bands
        return header