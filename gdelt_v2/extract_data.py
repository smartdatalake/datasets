from gdelt_networkx import GDELT_NetworkxImporter
from time import time
import pandas as pd
import sys

def read_data(path, chunksize):
    names = ['GKGRECORDID', 'DATE', 'SOURCECOLLECTIONIDENTIFIER',
             'SOURCECOMMONNAME', 'DOCUMENTIDENTIFIER', 'COUNTS', 'COUNTS_2',
             'THEMES', 'ENHANCEDTHEMES', 'LOCATIONS', 'ENHANCEDLOCATIONS',
             'PERSONS', 'ENHANCEDPERSONS', 'ORGANIZATIONS',
             'ENHANCEDORGANIZATIONS', '5TONE', 'ENHANCEDDATES', 'GCAM',
             'SHARINGIMAGE', 'RELATEDIMAGES', 'SOCIALIMAGEEMBEDS',
             'SOCIALVIDEOEMBEDS', 'QUOTATIONS', 'ALLNAMES', 'AMOUNTS',
             'TRANSLATIONINFO', 'EXTRASXML']

    sel_names = ['GKGRECORDID', 'DATE', 'SOURCECOMMONNAME', 'DOCUMENTIDENTIFIER',
                 'THEMES', 'LOCATIONS', 'PERSONS', 'ORGANIZATIONS', '5TONE']

    
    df = pd.read_csv(path, sep='\t', names=names, usecols=sel_names,
                     chunksize=chunksize, encoding="ISO-8859-1")
    return df


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Date needed!")

    t1 = time()
    nim = GDELT_NetworkxImporter()
    date = sys.argv[1]
    
    df = read_data('./data/{}_raw.txt'.format( date), chunksize=10000)

    for i, chunk in enumerate(df):
        print("Chunk {}".format(i))
        nim.create_graph(chunk)
    
    t2 = time()
    print('Elapsed {:.2f} sec'.format(t2-t1))

    nim.print_statistics()
    t2 = time()
    nim.export_gpickle('./data/{}_gpickle.gpickle'.format(date))
    t3 = time()
    print('Elapsed {:.2f} sec'.format(t3-t2))
    nim.export_filtered_csv('./data/{}_filtered.csv'.format(date))
    t4 = time()
    print('Elapsed {:.2f} sec'.format(t4-t3))
    