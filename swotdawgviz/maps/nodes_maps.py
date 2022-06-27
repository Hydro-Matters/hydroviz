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
            
    def get_map(self, varname=None, cmap=None, tooltip_attributes=None, add_to_map=None, varlimits=[None, None]):

        
        if cmap is None and varname is not None:
            if varlimits[0] is None:
                varlimits[0]= self._dataset[varname].min()
            if varlimits[1] is None:
                varlimits[1]= self._dataset[varname].max()
            
            cmap = branca.colormap.linear.YlOrRd_09.scale(varlimits[0],
                                                          varlimits[1])
        elif isinstance(cmap, list):
            if varlimits[0] is None:
                varlimits[0]= self._dataset[varname].min()
            if varlimits[1] is None:
                varlimits[1]= self._dataset[varname].max()

            cmap = branca.colormap.LinearColormap(cmap).scale(varlimits[0],
                                                              varlimits[1])
        

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
            if varname is not None:
                color = cmap(self._dataset.loc[index, varname])
                popup = "%s = %s" % (varname, repr(self._dataset.loc[index, varname]))
            else:
                color = "#"+''.join([random.choice('0123456789ABCDEF') for i in range(6) ])
                popup = "%i" % index
                
            folium.Circle(radius=50,
                          location=coords,
                          popup=popup,
                          color=color,
                          fill_color=color,
                          fill=True).add_to(parent_map)

        if varname is not None:
            
            # Add colorbar
            colormap = cmap.to_step(n=8)
            colormap.caption = varname
            colormap.add_to(parent_map)

        #if add_to_map is None:
            #parent_map.fit_bounds(self._dataset.total_bounds.tolist())
        
        if add_to_map is None:
            return new_map
