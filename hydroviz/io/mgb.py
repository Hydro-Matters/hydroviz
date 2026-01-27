import geopandas as gpd
import netCDF4 as nc
import numpy as np
import pandas as pd
from shapely import simplify
from tqdm.autonotebook import tqdm


class OutputMGB:
    
    def __init__(self, output_fname, catchments_shp=None, reaches_shp=None, time_subset=None, spatial_subset=None):
        """Load a output file produced by MGB Hydrological model
        
        Parameters
        ----------
        fname : str
            Output file
        """
        
        self._nc_dataset = nc.Dataset(output_fname, "r")
        if catchments_shp is not None:
            self._catchments_dataset = gpd.read_file(catchments_shp)
        if reaches_shp is not None:
            self._reaches_dataset = gpd.read_file(reaches_shp)
        
        # # Retrieve status attributes
        # self._status = self._nc_dataset.status
        # self._error_code = self._nc_dataset.error_code

        # if self._error_code == 1:
        #     self._valid = False
        #     return
        # else:
        #     self._valid = True
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
        dates = None
        freq_var = None
        for index in range(variables[varname].shape[0]):
            df = pd.DataFrame(data={"date": self._dates, "var": variables[varname][:, index]})
            df.dropna()
            freq_df = df.groupby(pd.PeriodIndex(df['date'], freq=temporal_freq))['var'].mean().reset_index()
            if dates is None:
                dates = np.array([freq_df.loc[i, "date"].start_time for i in freq_df.index])
                freq_var = np.zeros((dates.size, variables[varname].shape[1]))
            freq_var[:, index] = freq_df["var"].values
                
        return dates, freq_var
            
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
        return self._catchments_dataset.geometry.total_bounds.tolist()

    def getStaticGeoJson(self, style_function):

        features = []
        variable = self._Q
        for i in tqdm(range(variable.shape[1])):
                      
            catchment_row = self._catchments_dataset[self._catchments_dataset["Mini"] == i+1]
            if catchment_row.index.size != 1:
                continue

            index = catchment_row.index[0]

            mini = int(self._catchments_dataset.loc[index, "Mini"])

            geometry = {
                "type": "Polygon",
                "coordinates": [[list(xy) for xy in self._catchments_dataset.loc[index, "geometry"].simplify(tolerance=0.001).exterior.coords]],
            }
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "tooltip": "mini=%i" % mini,
                },
            }
            if style_function is not None:
                feature["properties"]["style"] = style_function(feature)
            else:
                feature["properties"]["style"] = {"stroke": True, "color": "#000000", "fill": False}
            features.append(feature)

        jsonData = {"type": "FeatureCollection",
                    "features": features}

        return jsonData

    def getTimelineGeoJson(self, style_function, varname, temporal_mean=None):

        features = []
        variable = self.variables[varname]
        unix_epoch = np.datetime64(0, 's')

        if temporal_mean is not None:
            if temporal_mean not in ["M", "W"]:
                raise ValueError("temporal_mean must be 'M'")
            dates, values = self.get_temporal_means(varname, temporal_mean)
        else:
            dates = self._dates
            values = self.variables[varname]

        min_start_date = int((dates[0] - unix_epoch) / np.timedelta64(1, 's'))
        max_end_date = int((dates[-1] - unix_epoch) / np.timedelta64(1, 's'))

        ordering_data = {"index": [], "reach_index": [], "stream_order": []}
        for i in tqdm(range(variable.shape[1])):

            catchment_row = self._catchments_dataset[self._catchments_dataset["Mini"].astype(int) == i+1]

            # catchment_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == i+1]
            if catchment_row.index.size != 1:
                continue
            if catchment_row.loc[catchment_row.index[0], "Ordem"] < 3:
                continue

            ID = int(catchment_row["ID"].values[0])
            mini = int(catchment_row["Mini"].values[0])
            stream_order = int(catchment_row["Ordem"].values[0])

            reach_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == ID]
            if reach_row.index.size != 1:
                continue

            ordering_data["index"].append(i)
            ordering_data["reach_index"].append(reach_row.index[0])
            ordering_data["stream_order"].append(stream_order)

        ordering_df = pd.DataFrame(data=ordering_data)
        ordering_df = ordering_df.sort_values(by="stream_order", ascending=True)
        # print(ordering_df)

        # for i in tqdm(range(variable.shape[1])):

        #     catchment_row = self._catchments_dataset[self._catchments_dataset["Mini"].astype(int) == i+1]

        #     # catchment_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == i+1]
        #     if catchment_row.index.size != 1:
        #         continue

        #     ID = int(catchment_row["ID"].values[0])
        #     mini = int(catchment_row["Mini"].values[0])

        #     reach_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == ID]
        #     if reach_row.index.size != 1:
        #         continue

        #     if catchment_row.loc[catchment_row.index[0], "Ordem"] < 3:
        #         continue

        #     index = reach_row.index[0]

        for i in tqdm(range(ordering_df.index.size)):

            index = ordering_df.loc[i, "index"]
            reach_index = ordering_df.loc[i, "reach_index"]

            geometry = {
                "type": "LineString",
                "coordinates": [list(xy) for xy in self._reaches_dataset.loc[reach_index, "geometry"].simplify(tolerance=0.001).coords],
            }
            

            for it in range(len(dates)):

                start_date = int((dates[it] - unix_epoch) / np.timedelta64(1, 's'))
                if it < len(dates) - 1:
                    # end_date = str(self._results[reach_id]._dates[it+1])
                    if temporal_mean == "M":
                        end_date = int((dates[it+1] - unix_epoch - np.timedelta64(1, "h")) / np.timedelta64(1, 's'))
                    else:
                        end_date = int((dates[it+1] - unix_epoch - np.timedelta64(1, "s")) / np.timedelta64(1, 's'))
                else:
                    # end_date = str(self._results[reach_id]._dates[it])
                    end_date = start_date

                varvalue = float(self.variables[varname][it, index])

                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "start": start_date * 1000,
                        "end": end_date * 1000,
                        varname: varvalue,
                        # "tooltip": "mini=%i, date=%s, %s=%.3f SI" % (mini, str(self._dates[it]), varname, varvalue),
                    },
                }
                if style_function is not None:
                    feature["properties"]["style"] = style_function(feature)
                    # print("style=", feature["properties"]["style"])

                features.append(feature)

        jsonData = {"type": "FeatureCollection",
                    "features": features,
                    "date_range": [min_start_date, max_end_date]}

        return jsonData
    
    def getTimestampedGeoJson(self, style_function, varname):

        features = []
        variable = self.variables[varname]

        for i in tqdm(range(variable.shape[1])):

            catchment_row = self._catchments_dataset[self._catchments_dataset["Mini"].astype(int) == i+1]

            # catchment_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == i+1]
            if catchment_row.index.size != 1:
                continue

            ID = int(catchment_row["ID"].values[0])
            mini = int(catchment_row["Mini"].values[0])

            reach_row = self._reaches_dataset[self._reaches_dataset["ID"].astype(int) == ID]
            if reach_row.index.size != 1:
                continue

            if catchment_row.loc[catchment_row.index[0], "Ordem"] < 3:
                continue

            index = reach_row.index[0]

            # mini = int(self._reaches_dataset.loc[index, "ID"])

            geometry = {
                "type": "LineString",
                "coordinates": [list(xy) for xy in self._reaches_dataset.loc[index, "geometry"].simplify(tolerance=0.001).coords],
                # "coordinates": [list(xy) for xy in self._reaches_dataset.loc[index, "geometry"].coords],
            }
            

            for it in range(len(self._dates)):

                varvalue = float(self.variables[varname][it, i])

                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "times": [str(self._dates[it])] * len(geometry["coordinates"]),
                        # "times": [str(self._dates[it]), str(self._dates[it])],
                        # "times": [str(self._dates[it])],
                        varname: varvalue,
                        "tooltip": "mini=%i, date=%s, %s=%.3f SI" % (mini, str(self._dates[it]), varname, varvalue),
                    },
                }
                if style_function is not None:
                    feature["properties"]["style"] = style_function(feature)
                    # print("style=", feature["properties"]["style"])

                features.append(feature)

        jsonData = {"type": "FeatureCollection",
                    "features": features}

        return jsonData

    def getVarMin(self, varname):
        if varname in self._catchments_dataset.columns:
            # print("getVarMin[0](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._dataset[varname].min()
        elif varname in self.variables:
            # print("getVarMin[1](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._results_variables[varname]["min"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

    def getVarMax(self, varname):
        if varname in self._catchments_dataset.columns:
            return self._dataset[varname].max()
        elif varname in self._results_variables:
            # print("getVarMax[1](%s)=%f" % (varname, self._results_variables[varname]["max"]))
            return self._results_variables[varname]["max"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

    
    # def varMin(self, varname):
    #     variables = self.variables
    #     if varname not in variables.keys():
    #         raise ValueError("Variable not found: %s" % varname)
    #     if np.all(np.isnan(variables[varname])):
    #         return np.nan
    #     return float(np.nanmin(variables[varname]))

    # def varMax(self, varname):
    #     variables = self.variables
    #     if varname not in variables.keys():
    #         raise ValueError("Variable not found: %s" % varname)
    #     if np.all(np.isnan(variables[varname])):
    #         return np.nan
    #     return float(np.nanmax(variables[varname]))
