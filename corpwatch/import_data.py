

import pandas as pd
from corpwatch_networkx import NetworkxImporter

chunksize = 100000

print("Creating Constraints")

nim = NetworkxImporter()
print("Creating Industries")
chunks = pd.read_csv('./data/sic_codes.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_industries(df)

print("Creating Sectors")
chunks = pd.read_csv('./data/sic_sectors.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_sectors(df.fillna(""))

print("Creating Countries")
chunks = pd.read_csv('./data/un_countries.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_countries(df.fillna(0))

print("Creating Subdivisions")
chunks = pd.read_csv('./data/un_country_subdivisions.csv', sep='\t',
                     chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_subdivisions(df.fillna(0))

print("Creating Countries Aliases")
df = pd.read_csv('./data/un_country_aliases.csv', sep='\t')
nim._create_countries_aliases(df)

print("Creating Companies")
chunks = pd.read_csv('./data/company_info.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    df = df[df.most_recent == 1].fillna(0).reset_index(drop=True)
    nim._create_companies(df)

print("Creating Locations")
chunks = pd.read_csv('./data/company_locations.csv',
                     sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    df = df[df.most_recent == 1].reset_index(drop=True)
    nim._create_locations(df.fillna(""))

print("Creating Filers")
chunks = pd.read_csv('./data/filers.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_filers(df[~df.cik.isna()])

print("Creating Relationships")
chunks = pd.read_csv('./data/relationships.csv', sep='\t', chunksize=chunksize)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_relationships(df)

nim._print_statistics()
nim._export('cw_graph.gpickle')
