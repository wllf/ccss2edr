import os.path
import numpy as np

class CSVCorrelation():
    min_num_sets = 3
    num_bands = 401
    start_nm = 380
    end_nm = 780

    def __init__(self, file: str):
        self.descriptor = os.path.basename(file).split('.')[0]
        self.read(file)

    def read(self, file):
        self.data = np.genfromtxt(file, delimiter=',')
        
        # Trailing commas lead to a junk column of nan; if this is present, slice it off
        if np.isnan(self.data[:, -1:]).all():
            self.data = self.data[:, :-1]
        
        # Verify that data conforms to the correlation file spec
        assert self.data.shape[0] >= CSVCorrelation.min_num_sets
        assert self.data.shape[1] == CSVCorrelation.num_bands

        self.num_sets = self.data.shape[0]