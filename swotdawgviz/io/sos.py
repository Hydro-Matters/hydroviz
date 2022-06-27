import netCDF4 as nc
import numpy as np
import pandas as pd
from shapely.geometry import LineString


class SosNetCDF:
    
    def __init__(self, fname, level="reaches", reaches_list=None, verbose=True):
        """Load Sos (SWORD of Science) data in the netCDF format
        
        Parameters
        ----------
        fname : str
            SoS netCDF file
        level : str
            Data level, must be 'reaches' or 'nodes'
        reaches_lists : list or None
            List of reaches to keep. Default is None (keep all the reaches in the file)
        verbose : bool
            True to enable verbose output (info about variables imported)
        """

        # Store fname and level
        self._fname = fname
        self._level = level
        
        # Open dataset
        self._nc_dataset = nc.Dataset(fname, "r")
        
        # Select group
        group = self._nc_dataset.groups[level]
        
        if reaches_list is not None:
            # Retrieve reach_id
            reach_id = group.variables["reach_id"][:]
            mask = np.isin(reach_id, reaches_list)
            #print(indices)
        else:
            mask = None

        # Set dimension associated to level
        if level == "reaches":
            level_dimension = "num_reaches"
        elif level == "nodes":
            level_dimension = "num_nodes"
        else:
            raise ValueError("'level' must be reaches or nodes")
        
        # Initialised unextracted variables
        self._unextracted_variables = {}
        self._unextracted_variables["dataset"] = []

        # Load one dimensional variables in level group
        variables_dict = {}
        hidden_variables = ["x", "y"]
        for variable in group.variables:
            if variable not in hidden_variables:
                #print("dimensions:", group.variables[variable].dimensions)
                if group.variables[variable].dimensions == (level_dimension,):
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    variables_dict[variable] = variable_data
                else:
                    self._unextracted_variables["dataset"].append(variable)

        # Load one dimensional variables in model group (GRADES)
        group = self._nc_dataset.groups["model"]
        self._unextracted_variables["model"] = []
        extracted_variable_count = 0
        for variable in group.variables:
            if variable not in hidden_variables:
                if group.variables[variable].dimensions == (level_dimension,):
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    extracted_variable_count += 1
                    variables_dict["model_%s" % variable] = variable_data
                else:
                    self._unextracted_variables["model"].append(variable)
        if verbose:
            print("%i variables extracted in model (GRADES) group" % extracted_variable_count)

        # Load one dimensional variables in gbpriors/level group
        if level == "reaches":
            sublevel = "reach"
        elif level == "nodes":
            sublevel = "node"
        group = self._nc_dataset.groups["gbpriors"].groups[sublevel]
        self._unextracted_variables["gbpriors"] = []
        extracted_variable_count = 0
        for variable in group.variables:
            if variable not in hidden_variables:
                if group.variables[variable].dimensions == (level_dimension,):
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    extracted_variable_count += 1
                    variables_dict["gbpriors_%s" % variable] = variable_data
                else:
                    self._unextracted_variables["gbpriors"].append(variable)
        if verbose:
            print("%i variables extracted in gbpriors/%s group" % (extracted_variable_count, sublevel))
                    
        self._dataset = pd.DataFrame(data=variables_dict)
        
        # Load model data
        model_group = self._nc_dataset.groups["model"]
        
        # Load GRDC data
        if "grdc" in model_group.groups.keys():
            self.__load_grdc_dataset__(reaches_list, verbose)
        else:
            self._grdc_dataset = None
        
        # Load usgs data
        if "usgs" in model_group.groups.keys():
            self.__load_usgs_dataset__(reaches_list, verbose)
        else:
            self._usgs_dataset = None
            
    def get_reach(self, reach_id):
        
        if self._level != "reaches":
            raise RuntimeError("Cannot extract data for a reach because level is nodes")
        
        reach_dataset = self._dataset[self._dataset["reach_id"] == reach_id]
        if reach_dataset.shape[0] == 0:
            raise RuntimeError("Reach %i not found" % reach_id)
        
        return reach_dataset
            
    @property
    def dataset(self):
        return self._dataset
            
    @property
    def unextracted_variables(self):
        return self._unextracted_variables

    def get_nc_variable(self, varname, group=None):
        """Direct access to a variable in the NetCDF dataset (may be useful for variable not extracted in the pandas dataframes)
        
        Parameters
        ----------
        varname : str
            Name of the variable
        group : str or list
            Name of the group that contain the variable or a list that defines the groups tree
            
        Return
        ------
        netCDF4.Variable
            Extracted variable
        """
        
        if group is not None:
            root = self._nc_dataset
            if isinstance(group, list):
                for i in range(0, len(group)):
                    root = root.groups[group[i]]
            elif isinstance(group, str):
                root = root.groups[group]
            else:
                raise ValueError("'group' must be a string or a list of string")
            
            return root.variables[varname]
    
    def __load_grdc_dataset__(self, reaches_list, verbose=True):
        """Load variables with dimension (num_reaches,) in the grdc group, put it in a dedicated dataset 
        (pandas.DataFrame) and merge it in the global dataset
        
        Parameters
        ----------
        reaches_lists : list or None
            List of reaches to keep. Default is None (keep all the reaches in the file)
        """
        
        group = self._nc_dataset.groups["model"].groups["grdc"]
        
        if reaches_list is not None:
            # Retrieve reach_id
            reach_id = group.variables["reach_id"][:]
            mask = np.isin(reach_id, reaches_list)
        else:
            mask = None
        
        variables_dict = {}
        hidden_variables = []
        self._unextracted_variables["grdc"] = []
        for variable in group.variables:
            if variable not in hidden_variables:
                if group.variables[variable].dimensions == ("num_grdc_reaches",):
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    if "grdc" in variable:
                        variables_dict[variable] = variable_data
                    else:
                        variables_dict["grdc_%s" % variable] = variable_data
                else:
                    self._unextracted_variables["grdc"].append(variable)
        if verbose:
            print("%i variables extracted in grdc group" % len(variables_dict))

        # Create dedicated dataset
        self._grdc_dataset = pd.DataFrame(data=variables_dict)
            
        # Merge GRDC data in global dataset
        self._dataset = self._dataset.merge(self._grdc_dataset, left_on="reach_id", 
                                            right_on="grdc_reach_id", how="left")
    
    def __load_usgs_dataset__(self, reaches_list, verbose=True):
        """Load variables with dimension (num_reaches,) in the usgs group, put it in a dedicated dataset 
        (pandas.DataFrame) and merge it in the global dataset
        
        Parameters
        ----------
        reaches_lists : list or None
            List of reaches to keep. Default is None (keep all the reaches in the file)
        """
        
        group = self._nc_dataset.groups["model"].groups["usgs"]
        
        if reaches_list is not None:
            # Retrieve reach_id
            reach_id = group.variables["reach_id"][:]
            mask = np.isin(reach_id, reaches_list)
        else:
            mask = None
        
        variables_dict = {}
        hidden_variables = []
        self._unextracted_variables["usgs"] = []
        for variable in group.variables:
            if variable not in hidden_variables:
                if group.variables[variable].dimensions == ("num_usgs_reaches",):
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    if "usgs" in variable:
                        variables_dict[variable] = variable_data
                    else:
                        variables_dict["usgs_%s" % variable] = variable_data
                else:
                    self._unextracted_variables["usgs"].append(variable)
        if verbose:
            print("%i variables extracted in usgs group" % len(variables_dict))

        # Create dedicated dataset
        self._grdc_dataset = pd.DataFrame(data=variables_dict)
            
        # Merge GRDC data in global dataset
        self._dataset = self._dataset.merge(self._grdc_dataset, left_on="reach_id", 
                                            right_on="usgs_reach_id", how="left")
        
