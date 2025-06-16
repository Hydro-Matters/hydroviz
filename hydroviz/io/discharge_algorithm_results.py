import geopandas as gpd
import json
# import netCDF4 as nc
import numpy as np
import os
import pandas as pd
from shapely import simplify
from tqdm import tqdm


from .sos import SosNetCDF
from .sword import SwordNetCDF

from .h2ivdi import OutputH2iVDI
from .sic4dvar import OutputSIC4DVar
from .hivdi import OutputHiVDI
from .sword import SwordShapefile, sword_continent_from_id


class DischargeAlgorithmResults:
    
    def __init__(self, algorithm, input_dir, output_dir, sets_file, set_index=None, sword_shp_dir=None, sword_version=16, basinID=None, simplify_tolerance=2.0):

        # Load sets file
        with open(os.path.join(input_dir, sets_file), "r") as jsonfile:
            sets_list = json.load(jsonfile)

        # Retrieve set(s)
        if set_index is not None:
            sets_list = [sets_list[set_index]]

        # Retrieve total list reach IDs and SWORDS shapefiles IDs
        reach_ids = []
        sword_ids = []
        print("Retrieve reaches")
        for index in tqdm(range(len(sets_list))):
            if isinstance(sets_list[index], dict):
                reaches_def = [sets_list[index]]
            else:
                reaches_def = sets_list[index]
            for reach in reaches_def:
                reach_id = reach["reach_id"]
                print("--Reach ID: %s" % str(reach_id))
                if reach_id not in reach_ids:
                    fname = os.path.join(output_dir, "%s_%s.nc" % (str(reach_id), algorithm))
                    if algorithm == "h2ivdi":
                        if not os.path.isfile(fname):
                            fname = os.path.join(output_dir, "%s_%s.nc" % (str(reach_id), "hivdi"))
                    print("--fname: %s" % str(reach_id))
                    if os.path.isfile(fname):
                        if basinID is not None:
                            basinIDstr = str(basinID)
                            if str(reach_id)[0:len(basinIDstr)] == basinIDstr:
                                reach_ids.append(reach_id)
                                sword_id = str(reach_id)[0:2]
                                if sword_id not in sword_ids:
                                    sword_ids.append(sword_id)
                        else:
                            reach_ids.append(reach_id)
                            sword_id = str(reach_id)[0:2]
                            if sword_id not in sword_ids:
                                sword_ids.append(sword_id)
        if len(sword_ids) == 0:
            raise RuntimeError("Zero results found for algorithm %s in basin with ID %s" % (algorithm, str(basinID)))

        # Load SWORD geometry
        self._sword_dataset = None
        print("Load SWORD data")
        for index in tqdm(range(len(sword_ids))):
            sword_id = sword_ids[index]
            continent = sword_continent_from_id[int(sword_id[0:1])]
            sword_file = os.path.join(sword_shp_dir, continent, "%s_sword_reaches_hb%s_v16.shp" % (continent.lower(), sword_id))
            sword = SwordShapefile(sword_file, reaches_list=[int(reach_id) for reach_id in reach_ids])
            if self._sword_dataset is None:
                self._sword_dataset = sword.dataset.loc[:, ["reach_id", "geometry"]]
            else:
                self._sword_dataset = pd.concat((self._sword_dataset, sword.dataset.loc[:, ["reach_id", "geometry"]]), ignore_index=True)
            # print(self._sword_dataset)

        # Simplify SWORD geometry
        initial_vertices_count = 0.0
        final_vertices_count = 0.0
        print("Simplify SWORD geometry")
        for i in tqdm(range(len(self._sword_dataset.index))):
            index = self._sword_dataset.index.values[i]
            geometry = self._sword_dataset.loc[index, "geometry"]
            initial_vertices_count += len(geometry.coords)
            self._sword_dataset.loc[index, "geometry"] = simplify(geometry, tolerance=simplify_tolerance)
            final_vertices_count += len(self._sword_dataset.loc[index, "geometry"].coords)
        print("- Initial vertices count: %i" % initial_vertices_count)
        print("- Final vertices count  : %i" % final_vertices_count)

        # Load results
        self._results = {}
        self._results_variables = {}
        sword_ids = []
        nodata_index = []
        print("Load %s results" % algorithm)
        for i in tqdm(range(len(self._sword_dataset.index))):
            index = self._sword_dataset.index.values[i]
            # print("INDEX=", index)
            reach_id = self._sword_dataset.loc[index, "reach_id"]
            # print("reach_id=", reach_id)
            fname = os.path.join(output_dir, "%s_%s.nc" % (str(reach_id), algorithm))
            if algorithm == "hivdi":
                results = OutputHiVDI(fname)
            elif algorithm == "h2ivdi":
                if not os.path.isfile(fname):
                    fname = os.path.join(output_dir, "%s_%s.nc" % (str(reach_id), "hivdi"))
                results = OutputH2iVDI(fname)
            elif algorithm == "sic4dvar":
                results = OutputSIC4DVar(fname)
            else:
                raise ValueError("Unknown (or unimplemented) algorithm: %s" % algorithm)
            if not results.valid:
                nodata_index.append(index)
                continue
            if len(self._results_variables.keys()) == 0:
                for varname in results.variables.keys():
                    self._results_variables[varname] = {"min": np.nan,
                                                        "max": np.nan}
                    # if np.isnan(varmin):

                    # self._results_variables[varname] = {"min": results.varMin(varname),
                    #                                     "max": results.varMax(varname)}
            for varname in results.variables.keys():
                varmin = results.varMin(varname)
                varmax = results.varMax(varname)
                if np.isfinite(varmin):
                    # print("%s: min=%f (%f)" % (reach_id, varmin, self._results_variables[varname]["min"]))
                    self._results_variables[varname]["min"] = np.nanmin([self._results_variables[varname]["min"], varmin])
                if np.isfinite(varmax):
                    # print("%s: max=%f (%f)" % (reach_id, varmax, self._results_variables[varname]["max"]))
                    self._results_variables[varname]["max"] = np.nanmax([self._results_variables[varname]["max"], varmax])
            self._results[int(reach_id)] = results

        if len(nodata_index) > 0:
            self._sword_dataset = self._sword_dataset.drop(index=nodata_index)

        # self._sets = 
        # self._sos = Sos

    def getVarMin(self, varname):
        if varname in self._sword_dataset.columns:
            print("getVarMin[0](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._dataset[varname].min()
        elif varname in self._results_variables:
            print("getVarMin[1](%s)=%f" % (varname, self._results_variables[varname]["min"]))
            return self._results_variables[varname]["min"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

    def getVarMax(self, varname):
        if varname in self._sword_dataset.columns:
            return self._dataset[varname].max()
        elif varname in self._results_variables:
            return self._results_variables[varname]["max"]
        else:
            raise RuntimeError("Variable not found in dataset: %s" % varname)

    def getGeometryBounds(self):
        return self._sword_dataset.geometry.total_bounds.tolist()

    def getTimestampedGeoJson(self, style_function, varname):

        features = []
        for i in tqdm(range(len(self._sword_dataset.index))):

            index = self._sword_dataset.index[i]

            reach_id = int(self._sword_dataset.loc[index, "reach_id"])

            for it in range(len(self._results[reach_id]._dates)):

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [list(xy) for xy in self._sword_dataset.loc[index, "geometry"].coords],
                    },
                    "properties": {
                        "times": [str(self._results[reach_id]._dates[it])] * len(self._sword_dataset.loc[index, "geometry"].coords),
                        varname: float(self._results[reach_id].variables[varname][it]),
                        "tooltip": "%i, %s=%.3f m3/s" % (reach_id, varname, float(self._results[reach_id]._Q[it])),
                    },
                }
                if style_function is not None:
                    feature["properties"]["style"] = style_function(feature)
                features.append(feature)

        jsonData = {"type": "FeatureCollection",
                    "features": features}

        return jsonData
    
    def load(self):

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
        else:
            self._inference_status = self._nc_dataset.inference_status
        
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
