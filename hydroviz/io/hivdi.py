import netCDF4 as nc
import numpy as np
import pandas as pd


class OutputHiVDI:
    
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
        if hasattr(self._nc_dataset, "VDA_status"):
            self._inference_status = self._nc_dataset.VDA_status
        elif hasattr(self._nc_dataset, "inference_status"):
            self._inference_status = self._nc_dataset.inference_status
        else:
            self._inference_status = None
        
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
        return self._status == 1
            
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
            
    @property
    def variables(self):
        return {"A0": self._A0,
                "alpha": self._alpha,
                "beta": self._beta,
                "discharge": self._Q}

    def varMin(self, varname):
        variables = self.variables
        if varname not in variables.keys():
            raise ValueError("Variable not found: %s" % varname)
        return float(np.min(variables[varname]))

    def varMax(self, varname):
        variables = self.variables
        if varname not in variables.keys():
            raise ValueError("Variable not found: %s" % varname)
        return float(np.max(variables[varname]))
        
