from matplotlib import cm
import numpy as np
import random

class ColormapStyleFunction:
    """Object to handle colormap style functions
    """
    
    def __init__(self, cmap, attribute,randomcolors=False):
        self._cmap = cmap
        self._attribute = attribute
        self._randomcolors = randomcolors
        
    def __call__(self, x):
        # print("__call__:", x["properties"][self._attribute])
        if np.isnan(x["properties"][self._attribute]):
            return {'color': "#999999", 'weight': 3}

        if self._randomcolors:
            #hexcolor = '#ff0000'
            hexcolor="#"+''.join([random.choice('0123456789ABCDEF') for i in range(6) ] )
        else:
            hexcolor = self._cmap(x["properties"][self._attribute])

        return {'color': hexcolor, 'weight' : 5, "dash_array": ""}
