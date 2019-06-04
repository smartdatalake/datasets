from gdelt_networkx import GDELT_NetworkxImporter
from gdelt_downloader import Downloader
from time import time

d = Downloader()
nim = GDELT_NetworkxImporter()

df = d.read_data('./data/small100.txt', chunksize=10000)
C = []
for i, chunk in enumerate(df):
    print("Chunk {}".format(i))
    nim.create_graph(chunk, (.7, '010', True))

nim.print_statistics()
nim.export('gdelt_graph.gpickle')
