import pandas as pd
import networkx as nx
from collections import Counter
import re


def isNaN(s):
    return s != s


class NetworkxImporter():

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def __get_nodes_ids(self, attribute, value):
        return [key for key in self.graph.nodes()
                if attribute in self.graph.nodes[key].keys()
                and self.graph.nodes[key][attribute] == value
                and 'source' in self.graph.nodes[key].keys()
                and self.graph.nodes[key]['source'] == 'GDELT']

    def __get_edges_ids(self, attribute, value):
        return [key for key in self.graph.edges()
                if self.graph.edge[key][attribute] == value
                and self.graph.edges[key]['source'] == 'GDELT']

    def __get_nodes_statistics(self, val, choice=0):
        if choice == 0:
            self.no_nodes = Counter([self.graph.nodes[key]['nlabel']
                                    for key in self.graph.nodes.keys()
                                    if 'nlabel' in self.graph.nodes[key].keys()
                                    and 'source' in self.graph.nodes[key].keys()
                                    and self.graph.nodes[key]['source'] ==
                                    'GDELT'])
        return self.no_nodes[val]

    def __get_edges_statistics(self, val, _from=None, _to=None, choice=0):
        if choice == 0:
            self.no_edges = Counter(["{}_{}_{}".format(
                                self.graph.edges[edge]['elabel'],
                                self.graph.nodes[edge[0]]['nlabel'],
                                self.graph.nodes[edge[1]]['nlabel'])
                                for edge in self.graph.edges
                                if 'elabel' in self.graph.edges[edge].keys()
                                and 'source' in self.graph.edges[edge].keys()
                                and self.graph.edges[edge]['source'] == 'GDELT'
                                ])
        return self.no_edges["{}_{}_{}".format(val, _from, _to)]

    def __get_nodes_values(self, attr):
        return set([self.graph.nodes[node][attr]
                    for node in self.graph.nodes()])

    def __get_edges_values(self, attr):
        return set([(self.graph.edges[edge][attr],
                     self.graph.nodes[edge[0]]['nlabel'],
                     self.graph.nodes[edge[1]]['nlabel'])
                    for edge in self.graph.edges.keys()])

    def create_graph(self, df):

        for no, (index, row) in enumerate(df.iterrows()):
            if df.shape[0] > 1000:
                if no % 1000 == 0:
                    print("\tArticle {} of {}".format(no, df.shape[0]))
            if not isNaN(row['5TONE']):
                tone = row['5TONE'].split(',')
            else:
                tone = [0 for i in range(7)]
            self.graph.add_node("GD_A_{}".format(row["GKGRECORDID"]),
                                nlabel='Article',
                                gkg_record_id=row['GKGRECORDID'],
                                date=row['DATE'],
                                source_id=row['SOURCECOLLECTIONIDENTIFIER'],
                                source_name=row['SOURCECOMMONNAME'],
                                document_id=row['DOCUMENTIDENTIFIER'],
                                tone=tone[0],
                                positive_score=tone[1],
                                negative_score=tone[2],
                                polarity=tone[3],
                                activity_reference_density=tone[4],
                                self_group_reference_density=tone[5],
                                word_count=tone[6],
                                counts=row['COUNTS'],
                                source='GDELT')

            sels = [('ENHANCEDPERSONS', 'Person', "MENTIONS"),
                    ('ENHANCEDORGANIZATIONS', 'Organization', "MENTIONS")]

            for (sel, label, edge) in sels:
                if not isNaN(row[sel]):

                    temp = pd.Series(row[sel].split(";")).apply(
                                                lambda x: x.split(","))
                    for (key, pos) in temp[:1]:
                        if key != '':
                            self.graph.add_node("GD_{}_{}".format(label[0],
                                                                  key),
                                                nlabel=label, name=key,
                                                source='GDELT')
                            self.graph.add_edge("GD_A_{}".format(
                                                        row["GKGRECORDID"]),
                                                "GD_{}_{}".format(
                                                            label[0], key),
                                                elabel=edge, source='GDELT',
                                                position=pos)

            sel = 'ENHANCEDTHEMES'

            if not isNaN(row[sel]):

                temp = pd.Series(row[sel].split(";")).apply(
                                            lambda x: x.split(","))
                for (key, pos) in temp[:1]:
                    if key != '':
                        for r_theme, theme in enumerate(key.split("_")):
                            self.graph.add_node("GD_T_{}".format(theme),
                                                nlabel='Theme', name=theme,
                                                rank=r_theme, source='GDELT')
                            self.graph.add_edge("GD_A_{}".format(
                                                row["GKGRECORDID"]),
                                                "GD_T_{}".format(theme),
                                                elabel="IS_ABOUT",
                                                source='GDELT', position=pos)

            sel = "ENHANCEDLOCATIONS"
            if not isNaN(row[sel]):
                temp = pd.DataFrame.from_dict(
                                dict(pd.Series(
                                        row[sel].split(";")).apply(
                                            lambda x: x.split("#"))),
                                "index")
                if temp.shape[1] != 9:
                    continue

                temp.columns = ['Type', 'FullName', 'CountryCode',
                                'ADM1Code', 'ADM2Code', 'Latitude',
                                'Longitude', 'FeatureID', 'Position']

                for index2, row2 in temp.iterrows():

                    self.graph.add_node("GD_L_{}".format(row2['FeatureID']),
                                        nlabel='Location',
                                        feature_id=row2['FeatureID'],
                                        type=row2['Type'],
                                        full_name=row2['FullName'],
                                        country_code=row2['CountryCode'],
                                        adm1_code=row2['ADM1Code'],
                                        adm2_code=row2['ADM2Code'],
                                        latitude=row2['Latitude'],
                                        longitude=row2['Longitude'],
                                        source='GDELT')
                    self.graph.add_edge("GD_A_{}".format(row["GKGRECORDID"]),
                                        "GD_L_{}".format(row2['FeatureID']),
                                        elabel='MENTIONS', source='GDELT',
                                        position=row2['Position'])

    def print_statistics(self):
        print("Statistics:")

        print("\tTotal GDELT Nodes: {:,}".format(
                self.graph.number_of_nodes()))

        nodes = self.__get_nodes_values('nlabel')
        for i, node in enumerate(nodes):
            print("\t\tGDELT {} Nodes: {:,}".format(node,
                                        self.__get_nodes_statistics(node, i)))

        print("\tTotal GDELT Edges: {:,}".format(
                self.graph.number_of_edges()))

        edges = self.__get_edges_values('elabel')
        for i, (elabel, nlabel1, nlabel2) in enumerate(edges):
            print("\t\tGDELT {}({},{}) Edges: {:,}".format(elabel,
                      nlabel1, nlabel2, self.__get_edges_statistics(
                              elabel, nlabel1, nlabel2, i)))

    def export(self, path, format='gpickle'):
        if format == 'gpickle':
            nx.write_gpickle(self.graph, path)
        elif format == 'graphml':
            # necessary cleaning
            for node in self.graph.nodes:
                for key in self.graph.nodes[node].keys():
                    if isinstance(self.graph.nodes[node][key], list):
                        self.graph.nodes[node][key] = '<<;>>'.join(
                                self.graph.nodes[node][key])
                    elif isinstance(self.graph.nodes[node][key], set):
                        self.graph.nodes[node][key] = '<<;>>'.join(
                                self.graph.nodes[node][key])
                    if isinstance(self.graph.nodes[node][key], str):
                        self.graph.nodes[node][key] = re.sub(
                                b'[\x00-\x10]', b'',
                                self.graph.nodes[node][key].encode(
                                        'utf-8')).decode('utf-8')

            nx.write_graphml(self.graph, path, 'utf-8')
