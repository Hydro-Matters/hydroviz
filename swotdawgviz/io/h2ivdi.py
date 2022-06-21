import geopandas as gpd
import netCDF4 as nc
import numpy as np
from shapely.geometry import LineString


class OutputH2iVDI:
    
    def __init__(self, fname):
        """Load a output file produced by H2iVDI Discharge Algorithm
        
        Parameters
        ----------
        fname : str
            Sword file
        """
        
        self._nc_dataset = nc.Dataset(fname, "r")
        
        
        # Retrieve status attributes
        self._status = self._nc_dataset.status
        self._vda_status = self._nc_dataset.VDA_status
        
        # Retrieve results
        self._t = self._nc_dataset.variables["nt"][:]
        group = self._nc_dataset.groups["reach"]
        self._A0 = group.variables["A0"][:]
        if isinstance(self._A0, np.ma.core.MaskedArray):
            self._A0 = self._A0.filled(fill_value=np.nan)
        self._A0 = float(self._A0)
        self._alpha = group.variables["alpha"][:]
        if isinstance(self._alpha, np.ma.core.MaskedArray):
            self._alpha = self._alpha.filled(fill_value=np.nan)
        self._alpha = float(self._alpha)
        self._beta = group.variables["beta"][:]
        if isinstance(self._beta, np.ma.core.MaskedArray):
            self._beta = self._beta.filled(fill_value=np.nan)
        self._beta = float(self._beta)
        self._Q = group.variables["Q"][:]
        if isinstance(self._Q, np.ma.core.MaskedArray):
            self._Q = self._Q.filled(fill_value=np.nan)
            
    def status(self, which="global"):
        if which == "vda":
            return self._vda_status
        else:
            return self._status
            
    @property
    def t(self):
        return self._t
            
    @property
    def A0(self):
        return self._A0
            
    @property
    def alpha(self):
        return self._alpha
            
    @property
    def beta(self):
        return self._beta
            
    @property
    def Q(self):
        return self._Q
            
    @property
    def discharge(self):
        return self._Q
