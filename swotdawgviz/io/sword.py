import geopandas as gpd
import netCDF4 as nc
import numpy as np


class SwordShapefile:
    
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
            

#class SwordNetCDF:
    
    #def __init__(self, fname, level="reach", load_geometry, extra_variables=[]):
        #"""Load SWORD data in the netCDF format
        
        #Parameters
        #----------
        #fname : str
            #Sword file
        #level : str
            #Data level, must be 'reach', 'node' or 'both'
        #load_geometry : bool
            #True to load geometry
        #extra_variables : list
            #List of supplementary variables to load in the file. Default is empty
        #"""

        ## Retrieve logger and append debug messages
        #logger = logging.getLogger("swotviz")
        #logger.debug("Instanciate SwordNetCDF object <%s>" % id(self))
        #logger.debug("- fname: %s" % fname)
        #logger.debug("- level: %s" % level)
        #logger.debug("- load_geometry: %s" % str(load_geometry))
        #logger.debug("- extra_variables: %s" % str(extra_variables))
        #self._logger = logger
        
        ## Store fname and level
        #self._fname = fname
        #self._level = level
        
        ## Open dataset
        #self._dataset = nc.Open(fname, "r")
        
        ## Select group
        #group = self._dataset.groups[level]

        ## Load default variables
        #self.wse = self.load_xt_variable(group, "wse")
        #self.width = self.load_xt_variable(group, "width")
        #self.d_x_area = self.load_xt_variable(group, "d_x_area")
        #if level == "reach":
            #self.slope2 = self.load_xt_variable(group, "slope2")
            #self.slope = self.slope2


    #def get_reaches_from_extent(self, lonmin, lonmax, latmin, latmax):
        #"""Retrieve reaches inside a custom  extent (bounding box)
        
        #Parameters
        #----------
        #lonmin : float
            #Minimum longitude
        #lonmax : float
            #Maximum longitude
        #latmin : float
            #Minimum latitude
        #latmax : float
            #Maximum latitude
            
        #Return
        #------
        #numpy.ndarray
            #Array of the variable values
        #"""
           
        #var = group.variables[varname]
        #if var.dimensions = ():
            #return var[0]
        #elif var.dimensions = (u'nt',):
            #array = var[:]
        #else:
            #raise RuntimeError("Wrong dimensions: %s" % repr(var.dimensions))
            
        ## Fill masked values with NaN
        #if isinstance(array, np.ma.core.MaskedArray):
            #array = array.filled(fill_value=np.nan)
            
        #return array
