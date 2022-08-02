import glob
import netCDF4 as nc
import numpy as np
import os


class SwotObservations:
    """Object to handle SWOT observations data in CONFLUENCE netCDF4 format
    """
    
    def __init__(self, fname, level="reach", sword=None, extra_variables=[]):
        """Load SWOT observations in the (netCDF) Confluence format
        
        Parameters
        ----------
        fname : str
            Observation file
        level : str
            Data level, must be 'reach' or 'node'
        extra_variables : list
            List of supplementary variables to load in the file. Default is empty
        """

        # Retrieve logger and append debug messages
        logger = logging.getLogger("swotviz")
        logger.debug("Instanciate ConfluenceSwotObservations object <%s>" % id(self))
        logger.debug("- fname: %s" % fname)
        self._logger = logger
        
        # Store fname and level
        self._fname = fname
        self._level = level
        
        # Open dataset
        self._dataset = nc.Open(fname, "r")
        
        # Select group
        group = self._dataset.groups[level]

        # Load default variables
        self.wse = self.load_xt_variable(group, "wse")
        self.width = self.load_xt_variable(group, "width")
        self.d_x_area = self.load_xt_variable(group, "d_x_area")
        if level == "reach":
            self.slope2 = self.load_xt_variable(group, "slope2")
            self.slope = self.slope2


    def load_variable(self, group, varname):
        """Load variable with name 'varname' in a group of the dataset
        
        Parameters
        ----------
        group : netcdf4.Dataset
            Group containing the variable
        varname : str
            Name of the variable
            
        Return
        ------
        numpy.ndarray
            Array of the variable values
        """
           
        var = group.variables[varname]
        if var.dimensions == ():
            return var[0]
        elif var.dimensions == (u'nt',):
            array = var[:]
        else:
            raise RuntimeError("Wrong dimensions: %s" % repr(var.dimensions))
            
        # Fill masked values with NaN
        if isinstance(array, np.ma.core.MaskedArray):
            array = array.filled(fill_value=np.nan)
            
        return array
    
    
    def close(self):
        """Close the dataset
        """
        self._dataset.close()


class SwotObservationsCollection:
    """Object to handle collections of SWOT observations data in CONFLUENCE netCDF4 format
    """
    
    def __init__(self, dirname):
        """List a collection of SWOT observations files
        
        Parameters
        ----------
        dirname : str
            Path to the directory containing SWOT observations files
        suffix : str
            Suffix of the SWOT observations files
            
        """
        
        # Store directory
        self._dirname = dirname
        
        # List files in directory
        fnames = glob.glob(os.path.join(dirname, "*_SWOT.nc"))
        
        # Sort files and retrieve basenames
        fnames.sort()
        self._swotfnames = [os.path.basename(fname) for fname in fnames]
        
        
    @property
    def files_list(self):
        return self._swotfnames

        
    @property
    def reaches_list(self):
        return [fname.split("_")[0] for fname in self._swotfnames]

