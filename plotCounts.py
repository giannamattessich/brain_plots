from getCellCount import *
import matplotlib.pyplot as plt
import pandas as pd, os

'''Function to plot areas on a horizontal bar plot with their counts as dependent variable. Generalized to include a variety of 
   parameters for plots. Can specify whether plot only shows major areas, only layers, or both. Type_filer specifies whether
   plots use area acronyms or area names. Area_contains filter should be consistent with the type for type filter if filtering on area. 
   Ex. type_filter='name',area_contains='visual'; type_filter='acronym', area_contains='VIS'

   Args:
        -counts(pd.DataFrame OR csv folder OR csv file path) -> provide either a count dataframe produced from getCellCount.read_counts_csv
        or combined_counts_df, a path to a csv folder with multiple counts csv files, OR a path to a single count csv file
        -norm(bool;default:True) -> whether to normalize counts
        -area_contains (str;default:visual) -> area to filter on. provide proper 'type_filter' to work
        -figsize(tuple of len=2;default(6.4,4.8)) -> size for figure
        -title(str) -> title of figure
        -xlab(str), ylab(str) -> specify either or both with x/y labels of fig
        -bar_color(str) -> color of bars
        -type_filter(str;either 'acronym' or 'name') -> what type of area label to use
        -major_areas_only(bool;default:False) -> whether to include only major areas of provided acronym/name on figure;excluding layers
        -layers_only(bool;default:False) -> whether to include only layers of provided acronym/name on figure;excluding major areas
        -tick_sizes(float/int;default:10) -> fontsize of y labels(areas)
        -destination(str of path;default:None) -> specify path to save created figure; if None don't save and only show result 
'''
'''EXAMPLE USAGE
csv_file = '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files/6989_points.csv'
csv_folder = '/run/user/1000/gvfs/smb-share:server=data.einsteinmed.edu,share=users/Gianna Mattessich/2P_desktop_data/SliceData/nelson_brains/coord_files'
counts_df = get_count_df(csv_folder)
'''

def area_counts_bar(counts, norm=True, hemisphere=False, area_contains='visual',figsize=(6.4, 4.8),
                     title='Visual Areas: Cell Counts', xlab='Cell Counts', ylab='Area',
                            bar_color='skyblue', type_filter='name', major_areas_only= False,
                              layers_only = False, tick_sizes= 10 ,destination=None):
    counts = get_count_df(counts,hemisphere=hemisphere)
    if major_areas_only and layers_only:
        raise ValueError('Major areas only or layers only cannot both be true. Please make only one variable true to properly filter.')
    filtered_dict = get_filtered_counts(counts,area_contains=area_contains,norm=norm, type_filter=type_filter,
                                         hemisphere=hemisphere,major_areas_only=major_areas_only, layers_only=layers_only)
    print(filtered_dict)
    filtered_dict = {area.capitalize():count for area,count in filtered_dict.items()}
    plt.figure(figsize=figsize)
    plt.barh(filtered_dict.keys(), filtered_dict.values(), capsize=5, color=bar_color, edgecolor='black')
    if title is not None:
        plt.title(title)
    if xlab is not None:
        plt.xlabel(xlab)
    if ylab is not None:
        plt.ylabel(ylab)
    plt.tick_params('y',labelsize=tick_sizes)
    plt.tight_layout()
    #### if wanting to modify this function for plot settings, can do so here; ex. adjust horizontal/vertical plotting, etc
    if destination is not None:
        plt.savefig(destination)
    plt.show()

