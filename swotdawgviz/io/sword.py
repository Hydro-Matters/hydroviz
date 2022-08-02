import geopandas as gpd
import netCDF4 as nc
import numpy as np
from shapely.geometry import LineString


class SwordShapefile:
    """Object to handle SWORD data in shapefile format
    """
    
    def __init__(self, fname, reaches_list=None):
        """Load a SWORD shapefile
        
        Parameters
        ----------
        fname : str
            Sword file
        reaches_lists : list or None
            List of reaches to keep. Default is None (keep all the reaches in the file)
        """
        
        self._dataset = gpd.read_file(fname)
        
        if reaches_list is not None:
            self._dataset = self._dataset[self._dataset["reach_id"].isin(reaches_list)]
            
    @property
    def dataset(self):
        return self._dataset
            

class SwordNetCDF:
    """Object to handle SWORD data in netCDF4 format
    """
    
    def __init__(self, fname, level="reaches", reaches_list=None, load_geometry=False):
        """Load SWORD data in the netCDF format
        
        Parameters
        ----------
        fname : str
            Sword netCDF file
        level : str
            Data level, must be 'reaches' or 'nodes'
        load_geometry : bool
            True to load geometry
        reaches_lists : list or None
            List of reaches to keep. Default is None (keep all the reaches in the file)
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
        

        # Load one dimensional variables
        variables_dict = {}
        hidden_variables = ["x", "y"]
        for variable in group.variables:
            if variable not in hidden_variables:
                #print("dimensions:", group.variables[variable].dimensions)
                if group.variables[variable].dimensions == ("num_reaches",):
                    print("adding_variable:", variable)
                    if mask is None:
                        variable_data = group.variables[variable][:]
                    else:
                        variable_data = group.variables[variable][mask]
                    variables_dict[variable] = variable_data
                    
        if load_geometry:
            
            # Load centerline points
            cl_group = self._nc_dataset.groups["centerlines"]
            cl_x = cl_group.variables["x"][:]
            cl_y = cl_group.variables["y"][:]
            cl_id = cl_group.variables["cl_id"][:]
            
            # Compute association dict
            cl_id2idx = {}
            for i in range(0, cl_id.size):
                cl_id2idx[cl_id[i]] = i
            
            geometries = []
            cl_ids = group.variables["cl_ids"][:, mask]
            #print(cl_ids)
            
            for index in range(0, cl_ids.shape[1]):
                min_cl_id = cl_ids[0, index]
                max_cl_id = cl_ids[1, index]
                #print("reach %i: %i->%i" % (index, min_cl_id, max_cl_id))
                coords = [(cl_x[cl_id2idx[i]], cl_y[cl_id2idx[i]]) for i in range(min_cl_id, max_cl_id+1)]
                geometry = LineString(coords)
                geometries.append(geometry)
                
        else:
            geometry = None
                    
        self._dataset = gpd.GeoDataFrame(data=variables_dict, geometry=geometries)
                #if group.variables[variable].dimensions 
                #variable_data =  group.variables[variable][:]
        #self.wse = self.load_xt_variable(group, "wse")
        #self.width = self.load_xt_variable(group, "width")
        #self.d_x_area = self.load_xt_variable(group, "d_x_area")
        #if level == "reach":
            #self.slope2 = self.load_xt_variable(group, "slope2")
            #self.slope = self.slope2
            
    @property
    def dataset(self):
        """Return a reference to the internal (netCDF) dataset
        
        Return
        ------
        netCDF4.Dataset
            Reference to the internal dataset
        """
        return self._dataset
    
    def close(self):
        """Close the dataset
        """
        self._dataset.close()
