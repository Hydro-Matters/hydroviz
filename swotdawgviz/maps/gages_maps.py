import branca
import folium
import numpy as np

from .style_functions import *


class GagesMap():
    
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
            
    def get_map(self, varname_id=None, add_to_map=None):

        if add_to_map is None:
            
            # Retrieve bounding box and center
            bounds = self._dataset.geometry.total_bounds.tolist()
            center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))
            
            # Create map
            new_map = folium.Map(location=center, tiles=self._tiles, zoom_start=6)
            parent_map = new_map
            
        else:
            
            parent_map = add_to_map

        # Add layer of circles
        for index in self._dataset.index:
            
            coords = self._dataset.geometry.loc[index].coords[0]
            coords = (coords[1], coords[0])
            
            if varname_id is not None:
                popup = "%s" % str(self._dataset.loc[index, varname_id].values[0])
            else:
                popup = None
                
            folium.Marker(location=coords,
                          popup=popup).add_to(parent_map)
            #folium.Circle(radius=50,
                          #location=coords,
                          #color="#048B9A",
                          #popup=popup,
                          #fill_color="#048B9A",
                          #fill=True).add_to(parent_map)
        
        if add_to_map is None:
            return new_map
