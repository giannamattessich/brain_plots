import pandas as pd
import os
import vedo
vedo.settings.default_backend= 'vtk'
import matplotlib.cm as cm
import numpy as np
from brainrender.actors import Points, PointsDensity
from vedo import Plotter
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from brainrender import Scene,settings,Animation
from getCellCount import *
from getCoordData import *
from pathlib import Path

'''Function to map a list of integers to a matplotlib colormap based on value/intensity
   Args:
        -int_list (list[int] or list[float]) -> list of ints/floats to map
        -cmap (str;default:'Reds') -> matplotlib cmap type 

   Output:
        -colors (list[str]) -> list of hex colors with intensities based on int values
'''
# # Normalize integers to range [0, 1] and map them to colors using a colormap
def integer_to_color_with_cmap(int_list, cmap_name='Reds'):
    # Normalize the integer values to the range [0, 1]
    min_val = min(int_list)
    max_val = max(int_list)
    # Avoid division by zero
    if max_val == min_val:
        return ['#000000' for _ in int_list]  # return black for all if all values are the same
    # Normalize values to the range [0, 1]
    normalized_values = [(i - min_val) / (max_val - min_val) for i in int_list]
    # Get colormap
    cmap = cm.get_cmap(cmap_name)  # You can choose other colormaps like 'inferno', 'plasma', etc.
    # Generate hex colors based on the colormap
    colors = []
    for value in normalized_values:
        rgba = cmap(value)  # Get RGBA tuple from the colormap
        hex_color = f'#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}'
        colors.append(hex_color)
    return colors

'''Function to map a count dictionary (with areas) as keys, counts as values to an area-colormap for heatmap plots
   Args:
        -count_dict(dict) -> dict produced from calling getCellCount.get_count_dicts on dataframe produced from
          get_count_OR getCellCount.read_counts_csv OR getCellCount.combined_counts_df 
        -cmap_name(str;default:'Reds') -> name of matplotlib colormap to map
   Output:
        -cmap_dict(dict) -> dict with areas as keys and their values as a mapped color from counts/intensity
'''

def areas_colormap_dict(count_dict,cmap_name='Reds'):
    return {area:color for area, color in zip(list(count_dict.keys()),
                                               integer_to_color_with_cmap(count_dict.values(), cmap_name=cmap_name))}

''' Function to plot 3D brain scene heatmap
    Args:
        - counts_data (Dataframe, str) -> either countdf from getCellCount functions OR CSV file name OR CSV folder containing csvs
        - cmap_name (str) -> matplotlib color map to use
        - markers (bool;default:False) -> whether to plot markers as points (starter cells)
        - xml_data (str;default:None) -> path to xml data
        - hemisphere (bool;default:True) -> whether to plot a mirrored version of hemispheres with total counts, specify True to seperate left/right regions
        - title (str;default:'') -> title label of plot
        - marker_colors (list[str] of len==2) -> specify colors for markers, first color in list is start somas and second is astrocytes marker
        - marker_radius (float) -> size of start marker points
        - regions_alpha (float[0 to 1];default:0.7) -> alpha/opacity of brain region colors
        - markers_alpha (float[0 to 1];default:1) ->  alpha/opacity value of marker points
'''
def plot_brain_heatmap(counts_data, cmap_name='Reds', markers=False, xml_data=None, hemisphere=True, title='',
                        marker_colors=['blue', 'green'], marker_radius=100, regions_alpha=0.7, markers_alpha=1):
    if isinstance(counts_data, pd.DataFrame):
        acronym_counts, name_counts = get_count_dicts(count_df,hemisphere=hemisphere)
    elif isinstance(counts_data, dict):
        acronym_counts = counts_data
    else:
        raise TypeError('Provided input data is not an acronym count dictionary or a count ')
    if len(marker_colors) != 2:
        raise ValueError('Please only set marker_colors argument as a list of length 2 with valid colors.')
    try:
        acronym_color_map = areas_colormap_dict(acronym_counts,cmap_name=cmap_name)
        scene = Scene(atlas_name='allen_mouse_25um',title=title)
        if hemisphere:
            # if hemisphere argument set to true, seperate out left and right areas to prevent from rerendering sides iteratively  
            right_acronym_colors = {acronym:color for acronym,color in acronym_color_map.items() if 'right' in acronym}
            left_acronym_colors = {acronym:color for acronym,color in acronym_color_map.items() if 'left' in acronym}
            # seperately loop through regions for both sides
            for acronym,hex_color in right_acronym_colors.items():
                areaname, hemisphere = tuple(acronym.split(','))
                scene.add_brain_region(areaname,alpha=regions_alpha,hemisphere='right',color=hex_color,silhouette=True,force=True)
            for acronym,hex_color in left_acronym_colors.items():
                areaname, hemisphere = tuple(acronym.split(','))
                scene.add_brain_region(areaname,alpha=regions_alpha,hemisphere='left',color=hex_color,silhouette=True,force=True)
        else:
            for acronym,hex_color in acronym_color_map.items():    
                scene.add_brain_region(acronym,alpha=regions_alpha,hemisphere='both',color=hex_color,force=True)
        if markers:
            if xml_data is None:
                raise ValueError('Markers argument was set to True but no XML data was provided. Please provide either a folder containing' \
                'properly constructed XML file, or folder containing XML files')
            positions, markers = get_coords(xml_data)
            marker_19_coords = markers[markers['Marker'] == 'marker 19'].loc[:,['x','y','z']].to_numpy()
            marker_20_coords = markers[markers['Marker'] == 'marker 20'].loc[:,['x','y','z']].to_numpy()
            scene.add(Points(marker_19_coords, radius=marker_radius, alpha=markers_alpha, colors=marker_colors[0]))
            scene.add(Points(marker_20_coords, radius=marker_radius, alpha=markers_alpha, colors=marker_colors[1]))
        # render
        scene.render()
        plt = Plotter()
        plt.show(*scene.renderables)
    except Exception as e:
        print(e)
        traceback.print_exc()


# count_df = get_count_df(
#     '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files/7000_points.csv',
#     hemisphere=True)
# #acronym_counts, name_counts = get_count_dicts(count_df,hemisphere=True)
# counts_data = get_filtered_counts(count_df,hemisphere=True)
# hemisphere=True
# cmap_name = 'Reds'
# regions_alpha = 0.8
# title= 'title'
# markers=True
# xml_data='/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/xml_files/7000_output.xml'
# positions,markers = get_coords(xml_data)
# marker_radius=100
# markers_alpha=1
# marker_colors=['blue','green']
# if isinstance(counts_data, pd.DataFrame):
#     acronym_counts, name_counts = get_count_dicts(count_df,hemisphere=hemisphere)
# elif isinstance(counts_data, dict):
#     acronym_counts = counts_data
# else:
#     raise TypeError('Provided input data is not an acronym count dictionary or a count ')
# acronym_color_map = areas_colormap_dict(acronym_counts,cmap_name=cmap_name)
# scene = Scene(atlas_name='allen_mouse_25um',title=title)
# if hemisphere:
#     right_acronym_colors = {acronym:color for acronym,color in acronym_color_map.items() if 'right' in acronym}
#     left_acronym_colors = {acronym:color for acronym,color in acronym_color_map.items() if 'left' in acronym}
#     for acronym,hex_color in right_acronym_colors.items():
#         areaname, hemisphere = tuple(acronym.split(','))
#         scene.add_brain_region(areaname,alpha=regions_alpha,hemisphere='right',color=hex_color,silhouette=True,force=True)
#     for acronym,hex_color in left_acronym_colors.items():
#         areaname, hemisphere = tuple(acronym.split(','))
#         scene.add_brain_region(areaname,alpha=regions_alpha,hemisphere='left',color=hex_color,silhouette=True,force=True)
# else:
#     for acronym,hex_color in acronym_color_map.items():    
#         scene.add_brain_region(acronym,alpha=regions_alpha,hemisphere='both',color=hex_color,force=True)
# if markers is not None:
#     if xml_data is None:
#         raise ValueError('Markers argument was set to True but no XML data was provided. Please provide either a folder containing' \
#         'properly constructed XML file, or folder containing XML files')
#     marker_19_coords = markers[markers['Marker'] == 'marker 19'].loc[:,['x','y','z']].to_numpy()
#     marker_20_coords = markers[markers['Marker'] == 'marker 20'].loc[:,['x','y','z']].to_numpy()
#     scene.add(Points(marker_19_coords, radius=marker_radius, alpha=markers_alpha, colors=marker_colors[0]))
#     scene.add(Points(marker_20_coords, radius=marker_radius, alpha=markers_alpha, colors=marker_colors[1]))
# # render
# scene.render()
# plt = Plotter()
# plt.show(*scene.renderables)

# anim = Animation(scene, Path.cwd(), "brainrender_animation")

# # Specify camera position and zoom at some key frames
# # each key frame defines the scene's state after n seconds have passed
# anim.add_keyframe(0, camera="top", zoom=1)
# anim.add_keyframe(1.5, camera="sagittal", zoom=0.95)
# anim.add_keyframe(3, camera="sagittal", zoom=0.8)
# anim.add_keyframe(4, camera="sagittal", zoom=0.9)
# anim.add_keyframe(5, camera="frontal", zoom=1)
# anim.add_keyframe(6, camera="frontal", zoom=1.2)
# anim.add_keyframe(7, camera="top", zoom=1)

# # Make videos
# anim.make_video(duration=7, fps=15, resetcam=True)

count_df = get_count_df(
    '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files',
    hemisphere=True)
xml_data = '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/xml_files'
acronym_counts, name_counts = get_count_dicts(count_df,hemisphere=True)
count_df = get_filtered_counts(count_df, area_contains='VIS',hemisphere=True, major_areas_only=True, norm=True)
plot_brain_heatmap(count_df, xml_data=xml_data, cmap_name='Blues', regions_alpha=0.9, marker_radius= 25,markers=True, marker_colors=['purple','green'])
# csv_file = '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files/6989_points.csv'
# csv_folder = '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files'
# counts_df = get_count_df(csv_file)
#acronym_counts,name_counts = get_count_dicts(counts_df,hemisphere=True)


