import xml.etree.ElementTree as ET
import pandas as pd, traceback, os

'''transform aligned neuroinfo coordinates to be consistent with allen ccfv3 for usage, uses 528 slices for x and z and 320 slices for y
# 0,0,0 is center, ventral surface= 13175, at origin point, x=left, y=posterior, z=dorsal
# for 25 um -> x (left->right) = 456 * 25um = 114000 um, y(posterior->anterior)= 320 * 25 um = 8000 um, z(dorsal->ventral) = 13200 um (same as x)
# x and z should be flipped and absolute values should be used

'''
''' Function to transform coords for allen tools usage to get_coords_df output
    Args:
        - coord_data (Dataframe) -> output of get_coords_df or get_combined_coord_data, OR any other dataframe with x, y, z coords
        - inplace (bool;default:False) -> specify whether to modify coord dataframe in place or as a copy
    Output:
        - (if not inplace) -> modified copy of coord data
'''
def apply_allen_transform(coord_data, inplace=False):
    if not inplace:
        coord_data = coord_data.copy(deep=True)
    # save x coords before modification
    x_coords = coord_data['x']
    # get absolute values
    coord_data['x'] = coord_data['z'].apply(lambda z: abs(z))
    coord_data['y'] = coord_data['y'].apply(lambda y: abs(y))
    coord_data['z'] = x_coords
    if not inplace:
        return coord_data

''' Function to read XML file from neuroinfo output 
    Args:
        - xml_file (str) -> path to neuroinfo output, aligned to allen mouse 25um atlas 
        - allen_transform (bool) -> if True, realign coordinates for use with brain render and other allen tools,
          else dont alter and read straight from XML
    Output:
        - positions_df (dataframe) -> info containing regions, cell coords, and IDs
        - markers_df (dataframe) -> info containing marker coordinates and IDs
'''
def get_coords_df(xml_file, allen_transform=True):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    markers_data, region_cells_data = [], []
    for child in root:
        # iterate through children to get region, normalize to lower case, no commas
        # add points to list of dictionaries, then convert to data frame
        if 'name' in child.attrib.keys():
            region_name = child.attrib.get('name').replace(",", "").lower()
            subchildren = child.findall('{https://www.mbfbioscience.com/filespecification}point')
            if 'marker' in region_name.lower():
                for point in subchildren:
                    markers_data.append({'Marker': region_name,'x': float(point.attrib.get('x')),
                                           'y': float(point.attrib.get('y')),
                                             'z':float(point.attrib.get('z'))})
            else:
                for point in subchildren:
                    region_cells_data.append({'Region Name': region_name,'x': float(point.attrib.get('x')),
                                           'y': float(point.attrib.get('y')),
                                             'z':float(point.attrib.get('z'))})
    markers_df,positions_df = pd.DataFrame(markers_data), pd.DataFrame(region_cells_data)
    # use allen CCF tree and read as dataframe to add acronym and ID column from region name in XML
    allen_csv = pd.read_csv("structure_tree_safe_2017.csv")
    # normalize names to lower for merge on region name
    allen_csv['name'] = allen_csv['name'].apply(lambda x: x.lower())
    allen_csv = allen_csv.loc[:, ['name', 'acronym', 'id']]
    # rename name col to match coord df, and cast IDs for region to integers
    allen_csv.rename(columns={'name': 'Region Name'}, inplace=True)
    # merge allen csv on region name to get all info
    positions_df = pd.merge(positions_df, allen_csv, on=['Region Name'])
    positions_df['id'] = positions_df['id'].astype('Int64')
    if allen_transform:
        apply_allen_transform(positions_df, inplace=True)
        apply_allen_transform(markers_df, inplace=True)
    return positions_df, markers_df

''' Function to read multiple XML file from neuroinfo output, merge individual coord_data outputs into one df 
    Args:
        - xml_file (str) -> path to neuroinfo output DIRECTORY, aligned to allen mouse 25um atlas 
        - allen_transform (bool) -> if True, realign coordinates for use with brain render and other allen tools,
          else dont alter and read straight from XML
    Output:
        - positions_df (dataframe) -> info containing regions, cell coords, and IDs for ALL data in folder
        - markers_df (dataframe) -> info containing marker coordinates and IDs for ALL data in folder 
'''
def get_combined_coord_data(xml_folder, allen_transform=True):
    combined_positions_df = pd.DataFrame({'Region Name':[], 'x':[],'y':[], 'z':[], 'acronym':[], 'id':[]})
    combined_markers_df = pd.DataFrame({'Marker':[], 'x':[],'y':[], 'z':[]})
    for xml_file in os.listdir(xml_folder):
        try:
            xml_file = os.path.join(xml_folder, xml_file)
            # ensure it is xml file, if so get individual coord df, then merge with current combined
            if xml_file.endswith('.xml'):
                new_positions_df, new_markers_df = get_coords_df(xml_file, allen_transform=allen_transform)
                combined_positions_df = pd.concat([combined_positions_df, new_positions_df], axis=0)
                combined_markers_df = pd.concat([combined_markers_df, new_markers_df], axis=0)
        except Exception as e:
            traceback.print_exc()
    combined_positions_df.to_csv('combined_coords_test.csv')
    return combined_positions_df, combined_markers_df


def get_coords(xml_data, allen_transform=True):
    if os.path.isdir(xml_data):
        return get_combined_coord_data(xml_data,allen_transform=allen_transform)
    else:
        return get_coords_df(xml_data, allen_transform=allen_transform)