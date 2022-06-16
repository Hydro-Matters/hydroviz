from matplotlib import cm
import numpy as np


class ColormapStyleFunction:
    
    def __init__(self, cmap, attribute):
        self._cmap = cmap
        self._attribute = attribute
        
    def __call__(self, x):
        hexcolor = self._cmap(x["properties"][self._attribute])
        return {'color': hexcolor, 'weight' : 3}
