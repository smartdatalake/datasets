from gdelt_networkx import NetworkxImporter
from gdelt_downloader import Downloader


d = Downloader()
nim = NetworkxImporter()

df = d.read_data('./data/total.txt', chunksize=10000)

for i, chunk in enumerate(df):
    print("Chunk {}".format(i))
    cl_chunk = d.clean_chunk(chunk)
    nim._create_graph(cl_chunk)

nim._print_statistics()
nim._export('gdelt_graph.gpickle')
