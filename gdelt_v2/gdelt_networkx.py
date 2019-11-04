import pandas as pd
import networkx as nx
from collections import Counter

def isNaN(s):
    return s != s


class GDELT_NetworkxImporter():
    def __init__(self):
        self.graph = nx.MultiDiGraph()
    
    def create_graph(self, df):
        for no, (index, row) in enumerate(df.iterrows()):
            if df.shape[0] > 1000:
                if no % 1000 == 0:
                    print("\tArticle {} of {}".format(no, df.shape[0]))
            if not isNaN(row['5TONE']):
                tone = row['5TONE'].split(',')
            else:
                tone = [0 for i in range(7)]
            self.graph.add_node("A_{}".format(row["GKGRECORDID"]),
                                nlabel='ART',
                                aid=row['GKGRECORDID'],
                                url=row['DOCUMENTIDENTIFIER'],
                                pos=tone[1],
                                neg=tone[2])
            
            sels = [('SOURCECOMMONNAME', 'SRC', "ART_SRC"),
                    ('PERSONS', 'PER', "ART_PER"),
                    ('ORGANIZATIONS', 'ORG', "ART_ORG"),
                    ('THEMES', 'THM', "ART_THM")]

            for (sel, label, edge) in sels:
                if not isNaN(row[sel]):
                    temp = row[sel].split(";")
                    for key in temp:
                        if key == '':
                            continue
                        self.graph.add_node("{}_{}".format(label[0], key),
                                            nlabel=label, name=key)
                        self.graph.add_edge("A_{}".format(row["GKGRECORDID"]),
                                    "{}_{}".format(label[0], key),
                                    elabel=edge)
            
            sel = "LOCATIONS"
            if not isNaN(row[sel]):
                temp = pd.DataFrame.from_dict(
                                dict(pd.Series(row[sel].split(";")).apply(
                                            lambda x: x.split("#"))),"index")

                if temp.shape[1] != 7:
                    continue
                temp.columns = ['Type', 'FullName', 'CountryCode', 'ADM1Code',
                                'Latitude', 'Longitude', 'FeatureID']

                for index2, row2 in temp.iterrows():
                    self.graph.add_node("L_{}".format(row2['FeatureID']),
                                        nlabel='LOC',
                                        lid=row2['FeatureID'],
                                        type=row2['Type'],
                                        name=row2['FullName'],
                                        cc=row2['CountryCode'],
                                        lat=row2['Latitude'],
                                        lon=row2['Longitude'])
                    self.graph.add_edge("A_{}".format(row["GKGRECORDID"]),
                                        "L_{}".format(row2['FeatureID']),
                                        elabel='ART_LOC')

    def print_statistics(self):
        print("Nodes:")
        t, nodes = zip(*self.graph.nodes(data='nlabel'))
        nodes = Counter(nodes)
        for node in nodes:
            print("\t{}: {:,}".format(node,nodes[node]))
        print("Total: {:,}".format(len(self.graph.nodes)))
        print("Edges:")
        s, t, edges = zip(*self.graph.edges(data='elabel'))
        edges = Counter(edges)
        for edge in edges:
            print("\t{}: {:,}".format(edge,edges[edge]))
        print("Total: {:,}".format(len(self.graph.edges)))
    
    def export_filtered_csv(self, file):
        x = pd.DataFrame()
        cols = ['aid', 'url', 'pos', 'neg', 'nlabel']
        for col in cols:
            y = pd.Series(dict(self.graph.nodes(data=col)))
            x[col] = y
        x = x[x.nlabel=='ART']
        x.drop('nlabel', axis=1, inplace=True)
        
        x['Organizations'] = pd.Series({i: ';'.join(map(lambda y: y[2:],(filter(lambda z: z.startswith('O'), self.graph.neighbors(i))))) for i in x.index})
        x['Persons'] = pd.Series({i: ';'.join(map(lambda y: y[2:],(filter(lambda z: z.startswith('P'), self.graph.neighbors(i))))) for i in x.index})
        x['Source'] = pd.Series({i: ';'.join(map(lambda y: y[2:],(filter(lambda z: z.startswith('S'), self.graph.neighbors(i))))) for i in x.index})
        x['Themes'] = pd.Series({i: ';'.join(map(lambda y: y[2:],(filter(lambda z: z.startswith('T'), self.graph.neighbors(i))))) for i in x.index})

        temp = pd.Series(dict(self.graph.nodes(data=True)))
        temp = temp[temp.index.map(lambda y: y.startswith("L_"))]
        x['Locations'] = pd.Series({i: list(filter(lambda z: z.startswith('L'), self.graph.neighbors(i))) for i in x.index})
        x['Locations']= x.Locations.apply(lambda y: ';'.join((temp[y].apply(lambda y: '#'.join(y.values()).replace('LOC#',''))).values))
        x.to_csv(file, index=None, header=None)
    
    
    def export_gpickle(self, file):
        nx.write_gpickle(self.graph, file)
