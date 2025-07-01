try:
    import folium
    import folium.plugins
except:
    folium = None
try:
    import mapwidget.openlayers as ol
except:
    ol = None
try:
    import keplergl as kgl
except:
    kgl = None

class FoliumBackend:

    def Map(self, location, zoom_start, tiles="cartodbpositron", attr=None):

        if tiles == "GoogleHybrid":
            tiles = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            attr = "Map tiles by Google"

        new_map = folium.Map(location, tiles=tiles, zoom_start=zoom_start, attr=attr)

        svg_style = '<style>svg#legend {background-color: white;}</style>'
        new_map.get_root().header.add_child(folium.Element(svg_style))


        return new_map

    def Circle(self, *args, **kwargs):
        return folium.Circle(*args, **kwargs)

    def GeoJson(self, *args, **kwargs):
        return folium.GeoJson(*args, **kwargs)

    def GeoJsonTooltip(self, *args, **kwargs):
        return folium.GeoJsonTooltip(*args, **kwargs)

    def Marker(self, *args, **kwargs):
        return folium.Marker(*args, **kwargs)

    def TimeStampedGeoJson(self, *args, **kwargs):
        return folium.plugins.TimestampedGeoJson(*args, **kwargs)

    
    def add_to_map(self, map, layerID, data):
        data.add_to(map)


class OpenLayersBackend:

    def Map(self, location, zoom_start, tiles="cartodbpositron"):
        raise NotImplementedError("Not implemented yet !")
        # return ol.Map(location, tiles=tiles, zoom_start=zoom_start)

    def GeoJson(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet !")
        # return ol.GeoJson(*args, **kwargs)

    def GeoJsonTooltip(self, *args, **kwargs):
        return None


class KeplerGlBackend:

    def Map(self, location, zoom_start, tiles="cartodbpositron"):
        config = {
            'version': 'v1',
            'config': {
                'mapState': {
                    'latitude': location[1],
                    'longitude': location[0],
                    'zoom': zoom_start
                }
            }
        }
        return kgl.KeplerGl(config=config)

    def GeoJson(self, *args, **kwargs):
        return args[0]
        # raise NotImplementedError("Not implemented yet !")
        # # return ol.GeoJson(*args, **kwargs)

    def GeoJsonTooltip(self, *args, **kwargs):
        return None

    def TimeStampedGeoJson(self, *args, **kwargs):
        geojson = args[0]
        for feature in geojson["features"]:
            feature["properties"]["time"] = feature["properties"]["times"][0]

        return geojson
    
    def add_to_map(self, map, layerID, data):
        print("data=", data)
        map.add_data(data=data, name=layerID)
