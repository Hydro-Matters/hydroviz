import netCDF4 as nc
import numpy as np
import pandas as pd


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
        self._error_code = self._nc_dataset.error_code

        if self._error_code == 1:
            self._valid = False
            return
        else:
            self._valid = True
        
        # Retrieve results
        self._t = self._nc_dataset.variables["nt"][:]
        group = self._nc_dataset.groups["reach"]
        self._A0 = group.variables["A0"][:]
        if isinstance(self._A0, np.ma.core.MaskedArray):
            self._A0 = self._A0.filled(fill_value=np.nan)
        self._A0 = float(self._A0)
        self._n = group.variables["n"][:]
        if isinstance(self._n, np.ma.core.MaskedArray):
            self._n = self._n.filled(fill_value=np.nan)
        self._n = float(self._n)
        self._Q = group.variables["Q"][:]
        if isinstance(self._Q, np.ma.core.MaskedArray):
            self._Q = self._Q.filled(fill_value=np.nan)
        self._Q_ci = group.variables["Q_ci"][:]
        if isinstance(self._Q_ci, np.ma.core.MaskedArray):
            self._Q_ci = self._Q_ci.filled(fill_value=np.nan)

        # Retrieve dates
        if "time" in self._nc_dataset.variables:
            time = self._nc_dataset.variables["time"][:]
            self._dates = np.array([np.datetime64("2000-01-01") + np.timedelta64(int(x), "s") for x in time])
        else:
            self._dates = None

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
        # print(df)
        month_df = df.groupby(pd.PeriodIndex(df['date'], freq=temporal_freq))['var'].mean().reset_index()
        # print(month_df, type(month_df))
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
    def A0(self):
        return self._A0
            
    @property
    def n(self):
        return self._n
            
    @property
    def manning(self):
        return self._n
            
    @property
    def Q(self):
        return self._Q
            
    @property
    def discharge(self):
        return self._Q
            
    @property
    def variables(self):
        return {"A0": self._A0,
                "n": self._n,
                "discharge": self._Q}

    def varMin(self, varname):
        variables = self.variables
        if varname not in variables.keys():
            raise ValueError("Variable not found: %s" % varname)
        if np.all(np.isnan(variables[varname])):
            return np.nan
        return float(np.nanmin(variables[varname]))

    def varMax(self, varname):
        variables = self.variables
        if varname not in variables.keys():
            raise ValueError("Variable not found: %s" % varname)
        if np.all(np.isnan(variables[varname])):
            return np.nan
        return float(np.nanmax(variables[varname]))
