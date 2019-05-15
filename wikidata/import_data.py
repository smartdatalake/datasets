import pandas as pd
from wikidata_networkx import NetworkxImporter

chunksize = 10000

nim = NetworkxImporter()

print("Creating Organizations")
chunks = pd.read_csv('./data/organizations_cleaned.txt',
                     quotechar='"', escapechar='\\', chunksize=chunksize,
                     index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._create_companies(df)

for node in ['Country', 'Grant', 'StockExchange', 'Industry', 'Group']:
    for file in nim.o_nodes[node]["files"]:
        print("Expanding for {}-{}".format(node, file))
        chunks = pd.read_csv('./data/'+file, quotechar='"',
                             escapechar='\\', chunksize=chunksize,
                             index_col="ID")
        for i, df in enumerate(chunks):
            print("\tChunk {}".format(i))
            nim._expand_nodes(df, node)

print("Creating Person")
chunks = pd.read_csv('./data/person_cleaned.txt', quotechar='"',
                     escapechar='\\', chunksize=chunksize, index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._expand_nodes(df, "Person")


print("Creating Product")
chunks = pd.read_csv('./data/product_cleaned.txt', quotechar='"',
                     escapechar='\\', chunksize=chunksize, index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim._expand_nodes(df, "Product")

nim._clean_companies_onwer()
nim._print_statistics()
nim._export_unlabeled_ids()
nim._export('wd_graph.gpickle')
