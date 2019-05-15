import pandas as pd
from urllib.request import urlopen
from gdelt_networkx import NetworkxImporter
from gdelt_downloader import Downloader

url_prefix = 'http://data.gdeltproject.org/gdeltv2/'
url = url_prefix+'masterfilelist.txt'
links = pd.read_csv(urlopen(url), sep=' ', names=['Col1', 'Col2', 'Link']).Link
links = links[links.str.contains("gkg").fillna(False)]

# keep only files in the 3rd week of 2018
links = links[(links >= url_prefix+'20180115') &
              (links < url_prefix+'20180122')]

d = Downloader(links)
df = d._download_data()

nim = NetworkxImporter()
nim._create_graph(df)
nim._print_statistics()
nim._export('gdelt_graph.xml')
