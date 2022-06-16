import branca
import folium
import numpy as np

from .style_functions import *


class ReachesMap():
    
    def __init__(self, dataset, tiles="cartodbpositron"):
        """Instanciate a ReachesMap object to create maps that display reaches
        
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
            
    def get_centerlines_map(self, varname=None, cmap=None, tooltip_attributes=None):
        """Build a map width reaches as centerlines colored with values of a variable
        
        Parameters
        ----------
        varname : str
            Name of the variable used for coloring
        width_attribute : str
            Name of the variable for the width
        cmap : branca.Colormap
            Colormap used for coloring
        tooltip_attributes : list or None
            List of variables to display using ToolTip
        """
        
        # Set default values for unset parameters
        if cmap is None and varname is not None:
            cmap = branca.colormap.linear.YlOrRd_09.scale(self._dataset[varname].min(),
                                                          self._dataset[varname].max())
        if tooltip_attributes is None:
            if varname is None:
                tooltip_attributes = ["reach_id"]
            else:
                tooltip_attributes = ["reach_id", varname]
        
        # Retrieve bounding box and center
        bounds = self._dataset.geometry.total_bounds.tolist()
        center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))

        # Create map
        new_map = folium.Map(location=center,
                                  tiles=self._tiles, zoom_start=6)
                       
        # Add layer
        tooltip = folium.GeoJsonTooltip(fields=tooltip_attributes)

        if varname is None:
            style_function = ColormapStyleFunction(cmap, varname,randomcolors=True)
        else:
            style_function = ColormapStyleFunction(cmap, varname)

        folium.GeoJson(self._json_dataset,
                       style_function=style_function,
                       tooltip=tooltip,
                       name="Test").add_to(new_map)

        if varname is not None:
            # Add colorbar
            colormap = cmap.to_step(n=8)
            colormap.caption = varname
            colormap.add_to(new_map)

        new_map.fit_bounds(self._dataset.total_bounds.tolist())
        
        return new_map

            
    def get_polygons_map(self, varname, width_attribute, cmap=None, tooltip_attributes=None):
        """Build a map width reaches as polygons computed using the width, colored with values of a variable
        
        Parameters
        ----------
        varname : str
            Name of the variable used for coloring
        width_attribute : str
            Name of the variable for the width
        cmap : branca.Colormap
            Colormap used for coloring
        tooltip_attributes : list or None
            List of variables to display using ToolTip
        """
        
        # Set default values for unset parameters
        if cmap is None:
            cmap = branca.colormap.linear.YlOrRd_09.scale(self._dataset[varname].min(),
                                                          self._dataset[varname].max())
        if tooltip_attributes is None:
            tooltip_attributes = ["reach_id", varname]
        
        # Project dataset to EPSG:3857 to get distance in meters (for buffers)
        dataset = self._dataset.to_crs('epsg:3857')
        
        # Add buffers
        polygons = []
        for index in dataset.index:
            
            # Retrieve centerline
            centerline = dataset.loc[index, "geometry"]
            
            # Add buffer
            polygon = centerline.buffer(dataset.loc[index, width_attribute], cap_style=2)
            dataset.loc[index, "geometry"] = polygon
            
        # Project dataset back to EPSG:4326
        dataset = dataset.to_crs('epsg:4326')
        
        # Retrieve bounding box and center
        bounds = dataset.geometry.total_bounds.tolist()
        center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))
        
        # Create map
        new_map = folium.Map(location=center,
                                  tiles=self._tiles, zoom_start=6)

        # Add layer
        style_function = ColormapStyleFunction(cmap, varname)
        tooltip = folium.GeoJsonTooltip(fields=tooltip_attributes)
        folium.GeoJson(dataset.to_json(),
                       style_function=style_function,
                       tooltip=tooltip,
                       name="Reach map of variable %s" % varname).add_to(new_map)

        # Add colorbar
        colormap = cmap.to_step(n=8)
        colormap.caption = varname
        colormap.add_to(new_map)

        new_map.fit_bounds(self._dataset.total_bounds.tolist())
        
        return new_map


    # DEPRECATED
    def get_polygons_map2(self, varname, width_attribute, cmap=cm.jet, tooltip_attributes=None):
        
        # Project dataset to EPSG:3857
        dataset = self._dataset.to_crs("epsg:3857")
        
        # Add buffer
        #dataset = cpr_gdf['geometry'] = cpr_gdf.geometry.buffer(buffer_length_in_meters)
        polygons = []
        for index in dataset.index:
            
            # Retrieve centerline
            centerline = dataset.loc[index, "geometry"]
            
            # Add buffer
            polygon = centerline.buffer(dataset.loc[index, width_attribute], cap_style=2)
            dataset.loc[index, "geometry"] = polygon
            
        # Project dataset back to EPSG:4326
        dataset = dataset.to_crs("epsg:4326")
        
        bounds = dataset.geometry.total_bounds.tolist()
        center = (0.5 * (bounds[1] + bounds[3]), 0.5 * (bounds[0] + bounds[2]))
        coloured_map = folium.Map(location=center,
                                  tiles=self._tiles, zoom_start=6)
        style_function = ColormapStyleFunction(cmap, varname, 
                                               minval=self._dataset[varname].min(),
                                               maxval=self._dataset[varname].max())
        if tooltip_attributes is None:
            tooltip_attributes = ["reach_id", varname]
        tooltip = folium.GeoJsonTooltip(fields=tooltip_attributes)
        folium.Choropleth(geo_data=dataset,
                          data=dataset,
                          key_on="feature.properties.reach_id",
                          columns=["reach_id", varname],
                          fill_color="GnBu",
                          fill_opacity=0.9,
                          line_opacity=0.2,
                          legend_name=varname,
                          tooltip=tooltip,
                          name="Test").add_to(coloured_map)
        coloured_map.fit_bounds(self._dataset.total_bounds.tolist())
        
        return coloured_map
