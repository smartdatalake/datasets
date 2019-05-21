from gdelt_networkx import NetworkxImporter
from gdelt_downloader import Downloader


d = Downloader()
nim = NetworkxImporter()

df = d.read_data('./data/total2.txt', chunksize=10000)

for i, chunk in enumerate(df):
    print("Chunk {}".format(i))
    nim.create_graph(chunk)

nim.print_statistics()
nim.export('gdelt_graph.gpickle')
