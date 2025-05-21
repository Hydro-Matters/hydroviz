try:
    import folium
except:
    folium = None
try:
    import mapwidget.openlayers as ol
except:
    ol = None

from .backends import FoliumBackend, OpenLayersBackend

class Map:

    def __init__(self, backend="folium"):
        if backend == "folium":
            if folium == None:
                raise RuntimeError("'folium' library is not installed.")
            self._backend = FoliumBackend()
        elif backend == "openlayers":
            if ol == None:
                raise RuntimeError("'mapwidget' library is not installed.")
            self._backend = OpenLayersBackend()


        

