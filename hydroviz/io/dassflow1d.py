import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd
from shapely import simplify
from tqdm.autonotebook import tqdm


class OutputDassFlow1D:
    
    def __init__(self, output_fname, xs_shp=None, segments_shp=None, time_subset=None, spatial_subset=None):
        """Load a output file produced by DassFlow-1D Shallow Water model
        
        Parameters
        ----------
        fname : str
            Output file
        """
        
        self._nc_dataset = nc.Dataset(output_fname, "r")
        if xs_shp is not None:
            self._xs_dataset = gpd.read_file(xs_shp)
        if segments_shp is not None:
            self._segments_dataset = gpd.read_file(segments_shp)

        self._valid = True
        
        # Retrieve results
        self._Q = self._nc_dataset.variables["Q"][:, :]
        if isinstance(self._Q, np.ma.core.MaskedArray):
            self._Q = self._Q.filled(fill_value=np.nan)

        # Retrieve dates
        if "time" in self._nc_dataset.variables:
            time = self._nc_dataset.variables["time"][:]
            self._dates = np.array([np.datetime64("2000-01-01") + np.timedelta64(int(x), "s") for x in time])
        else:
            self._dates = None

        if time_subset is not None:
            self._dates = self._dates[time_subset[0]:time_subset[1]]
            self._Q = self._Q[time_subset[0]:time_subset[1], :]
        if spatial_subset is not None:
            self._Q = self._Q[:, spatial_subset[0]:spatial_subset[1]]


        self._results_variables = {"Q": {"min": np.min(np.ravel(self._Q)), "max": np.max(np.ravel(self._Q))}}
        self._results_variables = {"discharge": {"min": np.min(np.ravel(self._Q)), "max": np.max(np.ravel(self._Q))}}

            
    def status(self, which="global"):
        if which == "vda":
            return self._vda_status
        else:
            return self._status
        
    def get_temporal_means(self, varname, temporal_freq):

        variables = self.variables
        if varname not in variables.keys():
            raise ValueError("Variable not found: %s" % varname)

        min_date = self._dates[0]
        max_date = self._dates[-1]
        df = pd.DataFrame(data={"date": self._dates, "var": variables[varname]})
        df.dropna()
        month_df = df.groupby(pd.PeriodIndex(df['date'], freq=temporal_freq))['var'].mean().reset_index()
        month_df['date'] = month_df['date'].astype(str)
        month_df['date'] = pd.to_datetime(month_df['date'])
        return month_df["date"].values, month_df["var"].values
            
    @property
    def valid(self):
        return self._valid
            
    @property
    def t(self):
        return self._t
            
    @property
    def dates(self):
        return self._dates
            
    @property
    def Q(self):
        return self._Q
            
    @property
    def discharge(self):
        return self._Q
            
    @property
    def variables(self):
        return {"Q": self._Q,
                "discharge": self._Q}

    def getGeometryBounds(self):
        return self._xs_dataset.geometry.total_bounds.tolist()

    def getStaticGeoJson(self, style_function):

        raise NotImplementedError("'getStaticGeoJson' is not implemented yet")


    def getTimelineGeoJson(self, style_function, varname, temporal_mean=None):

        raise NotImplementedError("'getTimelineGeoJson' is not implemented yet")

    
    def getTimestampedGeoJson(self, style_function, varname):

        raise NotImplementedError("'getTimestampedGeoJson' is not implemented yet")


    def getVarMin(self, varname):
        if varname in self._xs_dataset.columns:
            # print("getVarMin[0](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._xs_dataset[varname].min()
        elif varname in self.variables:
            # print("getVarMin[1](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._results_variables[varname]["min"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

    def getVarMax(self, varname):
        if varname in self._xs_dataset.columns:
            return self._xs_dataset[varname].max()
        elif varname in self._results_variables:
            # print("getVarMax[1](%s)=%f" % (varname, self._results_variables[varname]["max"]))
            return self._results_variables[varname]["max"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

