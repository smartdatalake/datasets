import json
import os
import pandas as pd
from time import time


class WikidataFilter():

    def __init__(self, choice="id", files=[],
                 source='../data/latest-all.json.gz'):
        self.choice = choice
        self.source = source

        if choice != "type" and choice != "id":
            raise ValueError('Not a valid choice for filtering. '
                             'Choose either "type" or "id".')

        if not isinstance(files, list):
            files = [files]

        self.files = files
        self.store = pd.DataFrame(columns=["FileDescriptor", "ids", "Found"])

        for file in files:
            base = os.path.basename(file)
            try:
                self.store.loc[base, "ids"] = set(
                        (pd.read_csv(file, header=None))[0])
            except FileNotFoundError:
                raise FileNotFoundError("This is not a valid filename.")

            try:
                self.store.loc[base, "FileDescriptor"] = open("{}_{}{}".format(
                        os.path.splitext(file)[0], "filtered",
                        os.path.splitext(file)[1]), 'w')
            except FileNotFoundError:
                raise FileNotFoundError("Could not create new file.")

        self.store.Found = 0

    def filter_line(self, line):
        line = json.loads(line)
        if self.choice == "type":
            if "P31" in line["claims"].keys():
                line = set([snak["mainsnak"]["datavalue"]["value"]["id"]
                            for snak in line["claims"]["P31"] if 'datavalue' in
                            snak["mainsnak"].keys()])
                for index, row in self.store.iterrows():
                    if len(line & row.ids) > 0:
                        return index
        elif self.choice == "id":
            for index, row in self.store.iterrows():
                if line["id"] in row.ids:
                    return index
        return False

    def filter(self, chunksize):
        lines = 0

        chunks = pd.read_csv(self.source, chunksize=chunksize,
                             compression='gzip', sep='\n', header=None,
                             skiprows=1, names=["Value"])
        for i, chunk in enumerate(chunks):
            print("\tChunk {}".format(i))
            if chunk.iloc[-1].Value == "]":
                print("\t\tLast Line!")
                chunk = chunk[:-1]

            t1 = time()
            chunk["FileDescriptor"] = chunk.apply(
                    lambda x: self.filter_line(
                            x["Value"][:-1]), axis=1)

            t2 = time()
            print("\t\tTime elapsed: {:,} sec".format(t2-t1))
            t1 = time()

            if self.choice == "id":
                self.store.Found = self.store.Found.add(
                        chunk.FileDescriptor.groupby(
                                chunk.FileDescriptor).count(), fill_value=0)
                lines += chunksize

            chunk[~(chunk.FileDescriptor == False)].apply(
                lambda x: self.store.FileDescriptor[x["FileDescriptor"]].write(
                        x["Value"]+'\n'), axis=1)

            if self.choice == "id" and not self.breaker(lines):
                return
            t2 = time()
            print("\t\tTime elapsed: {:,} sec".format(t2-t1))
            break

    def breaker(self, lines):
        bools = []
        for index, row in self.store.iterrows():
            print("\t\tFor file {}: ".format(index), end=" ")
            if self.choice == "id":
                print("Found {:,} of {:,} ({:0.2f}%) at {:,} lines".format(
                        row.Found, len(row.ids),
                        row.Found/len(row.ids)*100, lines))
                if row.Found == len(row.ids):
                    bools += [True]
                else:
                    bools += [False]
            else:
                print("Found {:,} at {:,} lines".format(row.Found, lines))
                bools += [False]

        self.store = self.store[[not x for x in bools]]
        return self.store.shape[0]
