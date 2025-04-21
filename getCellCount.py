import pandas as pd, numpy as np
import os, pathlib

''' Function to read CSV that contains cell counts from neuroinfo output
    Args:
        - csv (str) -> path of single CSV to read
    Output:
        - count_df (Dataframe) -> pandas df with name, acronym, hemisphere, and counts 
'''
def read_counts_csv(csv, hemisphere=True):
    points_df = pd.read_csv(csv, header=None)
    columns = points_df.iloc[1]
    # remove header rows and use first column as new header
    points_df.drop([0, 1], inplace=True)
    points_df.columns = columns
    # reset indices 
    points_df.reset_index(drop=True, inplace=True)
    #check the format of the csv: there are usually 2 types
    # one has total counts and markers with 'name' as first col, count by reading counts col
    # other format has 'Marker' as first col, count by reading number of times region name appears
    # other format does not include major structures, for example does not contain 'VIS' but contains 'VISl1','VISrl2/3'... 
    # to account for this, use allen sdk reference space to append counts for parent structures
    if points_df.columns[0] == 'name':
        # get total count from last instance of 'count' column 
        points_df['total count'] = points_df['count'].iloc[:,-1].astype(int)
        # get new data frane with region.hemisphere and new count info
        count_df = points_df.loc[:, ['name', 'acronym', 'hemisphere', 'total count']]
    else: # case: 'marker' is first col
        # Count how many times each 'name' appears with value_counts
        if hemisphere:
            count_df = points_df.loc[:, ['name', 'acronym', 'hemisphere']]
        else:
            count_df = points_df.loc[:, ['name', 'acronym']]
        name_counts = count_df['name'].value_counts().rename('total count')
        count_df = count_df.copy()
        count_df['total count'] = count_df['name'].map(name_counts)
        count_df.drop_duplicates(keep='first', inplace=True)
    return count_df.reset_index(drop=True)

''' Function to combine results of cell counts dataframe for each brain
    Args:
        -csv_folder (str) -> path to folder containing neuroinfo output CSVs
        -hemisphere (bool;default:True) -> if true, include 'hemisphere' column and keep 2 rows with same region, 
                                           if false, exclude 'hemisphere' column, combining counts for both hemispheres in region
    Output:
        -counts_combined (Dataframe) -> dataframe containing combined results from counts csvs
'''
def combined_counts_df(csv_folder, hemisphere=True):
    counts_combined = pd.DataFrame()
    # iterate through csvs and create individual counts df to concatenate into 1
    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith('.csv'):
            csv_file = os.path.join(csv_folder, csv_file)
            count_df = read_counts_csv(csv_file, hemisphere=hemisphere)
            counts_combined = pd.concat([counts_combined, count_df], axis=0)
    # sum counts of rows with duplicate values in name,acronym,hemisphere cols
    if hemisphere:
        counts_combined = counts_combined.groupby(['name', 'acronym', 'hemisphere'], as_index=False)['total count'].sum()
    else:
        # if excluding hemisphere, perform group by with only other rows
        counts_combined = counts_combined.groupby(['name', 'acronym'], as_index=False)['total count'].sum()
    return counts_combined

'''Function to take in possible different inputs for 'count' argument and output a count dataframe
   Args:
        - count_inputs (Dataframe OR str) -> input to dataframe output. Take in either outputs of read_counts_csv or combined_counts_df  
                                          if string, specify either a path to a single CSV file OR to a folder containing multiple count CSVS
                                          if dataframe, ensure it is a counts dataframe with name,acronym,counts columns
        - hemisphere (bool;default:True) -> whether to include hemisphere information in count df output
    Output:
        - counts (Dataframe) -> structred count df for plot use 
'''
def get_count_df(count_inputs, hemisphere=True):
    if isinstance(count_inputs, str):
        if os.path.isdir(count_inputs):
            counts = combined_counts_df(count_inputs,hemisphere=hemisphere)
        elif count_inputs.endswith('.csv'):
            counts = read_counts_csv(count_inputs,hemisphere=hemisphere)
    elif isinstance(count_inputs,pd.DataFrame):
        if ((list(count_inputs.columns) == ['name', 'acronym', 'hemisphere', 'total count']) or (
            list(count_inputs.columns) == ['name', 'acronym', 'total count'])):
            counts = count_inputs
        else:
            raise ValueError('Provided dataframe does not contain expected structure of a count Dataframe input.')
    else:
        raise TypeError('Provided input is not a file, folder name, or count dataframe')
    return counts

'''Function to get dictionaries with regions as keys, and counts in region as values
    Args: 
        -counts_df (Dataframe) -> output of read_counts_csv or combined_counts_csv
        -hemisphere (bool;default:False) -> whether to include hemispheres in key, if true, dictionary will have region and hemispheres as 2 seperate keys
                                        otherwise, both hemisphere counts will be included 
        -norm (bool;default:False) -> whether to normalize data to total cell counts on a scale of 0 to 1
    Output:
        -acronym_counts,name_counts (tuple of 2 dictionaries)
''' 
def get_count_dicts(counts_df, hemisphere=False, norm=False):
    if not hemisphere:
        acronym_counts = dict(zip(counts_df['acronym'], counts_df['total count']))
        name_counts = dict(zip(counts_df['name'], counts_df['total count']))
    else:
        if 'hemisphere' in list(counts_df.columns):
            acronym_counts = dict(zip(counts_df['acronym'] + ',' + counts_df['hemisphere'], counts_df['total count']))
            name_counts = dict(zip(counts_df['name'] + ',' + counts_df['hemisphere'], counts_df['total count']))
    if norm:
        cells_total = sum(acronym_counts.values())
        acronym_counts = {acronym:(count / cells_total) for acronym,count in acronym_counts.items()}
        name_counts = {name:(count / cells_total) for name,count in name_counts.items()}
    return acronym_counts, name_counts

'''Function to get a filtered dictionary with filtered areas as keys and counts as values
    Args: 
        -counts_df (Dataframe) -> output of read_counts_csv or combined_counts_csv
        -type (str; valid inputs: 'acronym' or 'name') -> type of dictionary to return and filter; if 'acronym' return filtered acronym counts,
                                                          else if 'name', return filtered names
        -area_contains (str) -> string to filter dictionary with, will check if this is contained in the keys 
        -hemisphere (bool; default:False) -> whether to include hemispheres in key, if true, dictionary will have region and hemispheres as 2 seperate keys
                                        otherwise, both hemisphere counts will be combined 
        -norm (bool; default:False) -> whether to normalize data to total cell counts on a scale of 0 to 1
        -layers_only (bool; default:False) -> whether data includes only layers NOT entire area, ex. 'VISrl1', 'VISp2/3' NOT 'VIS' if layers_only=True
                                             if false, include all filtered counts
        -major_areas_only (bool; default:False) -> whether data includes only entire area NOT layers, ex. if true,'VIS' included but
                                                'VISrl1', 'VISp2/3' excluded. if false, include all filtered counts
                                                -if both layers_only and major_areas_only is true, then include both major areas AND layers 
                                                
    Output:
        - filtered counts (dict) -> filtered area counts dictionary
'''
def get_filtered_counts(counts_df, type_filter='acronym', area_contains='', hemisphere=False, norm=False, layers_only=False, major_areas_only=False):
    if type_filter != 'acronym' and type_filter != 'name':
        raise ValueError('Please provide either "acronym" or "name" as type argument. Please specify which dictionary to filter and return.')
    if layers_only and major_areas_only:
        raise ValueError('Please filter ONLY by layers or ONLY by major areas. Cannot filter with both true.')
    acronyms, names = get_count_dicts(counts_df, hemisphere=hemisphere, norm=norm)
    if type_filter == 'acronym':
        if layers_only:
            acronym_counts = {acronym:count for acronym,count in acronyms.items() if area_contains.lower()
                               in acronym.lower() and not acronym.replace(',','').replace('/','').replace(' ', '').isalpha()}
        elif major_areas_only:
            acronym_counts = {acronym:count for acronym,count in acronyms.items() 
                              if area_contains.lower() in acronym.lower()
                                and acronym.replace(',','').replace('/','').replace(' ', '').isalpha() and acronym != area_contains}
        else:
            acronym_counts = {acronym:count for acronym,count in acronyms.items() if area_contains.lower() in acronym.lower()}
        if norm:
            totals = sum(acronym_counts.values())
            acronym_counts = {acronym:((count / totals) if totals != 0 else count) for acronym,count in acronym_counts.items()}
        return acronym_counts
    elif type_filter == 'name':
        if layers_only:
            name_counts = {name:count for name,count in names.items() if area_contains.lower() in name.lower()
                            and not name.replace(',','').replace('/','').replace(' ', '').isalpha()}
        elif major_areas_only:
            name_counts = {name:count for name,count in names.items() if area_contains.lower() in name.lower()
                            and name.replace(',','').replace('/','').replace(' ', '').isalpha() and name!=area_contains}
        else:
            name_counts = {name:count for name,count in names.items() if area_contains.lower() in name.lower()}
        if norm:
            totals = sum(name_counts.values())
            name_counts = {name:((count / totals) if totals != 0 else count) for name,count in name_counts.items()}
        return name_counts


