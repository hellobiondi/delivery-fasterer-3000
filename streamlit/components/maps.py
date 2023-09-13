from folium import Map
from folium.plugins import HeatMap


def get_map(map_data):
    '''
        map_data: List of [lat, long, weight]
    '''
    fig = Map(location = [1.357, 103.826], zoom_start = 11.4)

    heatmap_gradient = {
        0.2 : 'blue',
        0.4 : 'orange',
        0.6 : 'red',
        0.8 : 'maroon',
        1.0 : 'maroon',
    }

    HeatMap(map_data, radius = 10, gradient = heatmap_gradient).add_to(fig)

    return fig