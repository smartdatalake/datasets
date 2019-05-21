

import pandas as pd
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen


class Downloader():

    def __init__(self, links=None):
        self.links = links
        self.df = pd.DataFrame()
        self.names = ['GKGRECORDID', 'DATE', 'SOURCECOLLECTIONIDENTIFIER',
                      'SOURCECOMMONNAME', 'DOCUMENTIDENTIFIER', 'COUNTS',
                      'COUNTS_2', 'THEMES', 'ENHANCEDTHEMES', 'LOCATIONS',
                      'ENHANCEDLOCATIONS', 'PERSONS', 'ENHANCEDPERSONS',
                      'ORGANIZATIONS', 'ENHANCEDORGANIZATIONS', '5TONE',
                      'ENHANCEDDATES', 'GCAM', 'SHARINGIMAGE', 'RELATEDIMAGES',
                      'SOCIALIMAGEEMBEDS', 'SOCIALVIDEOEMBEDS', 'QUOTATIONS',
                      'ALLNAMES', 'AMOUNTS', 'TRANSLATIONINFO', 'EXTRASXML']

        self.sel_names = ['GKGRECORDID', 'DATE', 'SOURCECOLLECTIONIDENTIFIER',
                          'SOURCECOMMONNAME', 'DOCUMENTIDENTIFIER', 'COUNTS',
                          'ENHANCEDTHEMES', 'ENHANCEDLOCATIONS',
                          'ENHANCEDPERSONS', 'ENHANCEDORGANIZATIONS', '5TONE']

    def read_data(self, path, chunksize):
        self.df = pd.read_csv(path, sep='\t', names=self.names,
                              usecols=self.sel_names, chunksize=chunksize,
                              encoding="ISO-8859-1")
        return self.df

    def download_data(self):

        for i, url in enumerate(self.links):
            zipfile = ZipFile(BytesIO(urlopen(url).read()))
            try:
                df = pd.read_csv(zipfile.open(zipfile.namelist()[0]),
                                 sep='\t', names=self.names,
                                 usecols=self.sel_names, encoding='ISO-8859-1')
            except UnicodeDecodeError:
                continue

            df = df[self.sel_names]
            self.df = self.df.append(df)
            print("Link {} out of {}.\n\t{} new records,"
                  "total {} records.".format(i+1, self.links.shape[0],
                                             df.shape[0], self.df.shape[0]))
        return self.df

    def write_data(self, path):
        self.df.to_csv(path, header=True, index=False)
