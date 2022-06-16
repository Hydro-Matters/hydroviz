import branca
import folium
import numpy as np

from .style_functions import *


class NodesMap():
    
    def __init__(self, dataset, tiles="cartodbpositron"):
        """Instanciate a NodesMap object to create maps that display nodes
        
        Parameters
        ----------
        dataset : geopandas.GeoDataSet
            dataset to display
        tiles : str
            Identifier of the tiles for the background map
        """
        
        # Store parameters
        self._dataset = dataset
        self._json_dataset = dataset.to_json()
        self._tiles = tiles
            
    def get_map(self, varname=None, cmap=None, tooltip_attributes=None):

        
        if cmap is None:
            cmap = branca.colormap.linear.YlOrRd_09.scale(self._dataset[varname].min(),
                                                          self._dataset[varname].max())
        
        bounds = self._dataset.geometry.total_bounds.tolist()
        center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))
        new_map = folium.Map(location=center,
                                  tiles=self._tiles, zoom_start=6)
        
        for index in self._dataset.index:
            
            coords = self._dataset.geometry.loc[index].coords[0]
            coords = (coords[1], coords[0])
            folium.Circle(radius=50,
                          location=coords,
                          popup="%s = %s" % (varname, repr(self._dataset.loc[index, varname])),
                          color=cmap(self._dataset.loc[index, varname]),
                          fill_color=cmap(self._dataset.loc[index, varname]),
                          fill=True).add_to(new_map)

        # Add colorbar
        colormap = cmap.to_step(n=8)
        colormap.caption = varname
        colormap.add_to(new_map)

        new_map.fit_bounds(self._dataset.total_bounds.tolist())
        
        
        return new_map
