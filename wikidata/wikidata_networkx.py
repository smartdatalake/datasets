import pandas as pd
import networkx as nx
from collections import Counter
import re
from util.networkx_importer import NetworkxImporter
import pickle

def isNaN(s):
    return s != s


class WD_NetworkxImporter(NetworkxImporter):

    def __init__(self):
        NetworkxImporter.__init__(self, 'Wikidata')

        with open('maps/organization_nodes.pkl', 'rb') as f:
            self.o_nodes = pickle.load(f)

        with open('maps/person_nodes.pkl', 'rb') as f:
            self.p_nodes = pickle.load(f)

    def __get_unlabeled_nodes_ids(self, node):
        return set([self.graph.nodes[key]['id'] for key in self.graph.nodes()
                    if self.graph.nodes[key]['nlabel'] == node
                    and 'label' not in self.graph.nodes[key].keys()
                    and 'source' in self.graph.nodes[key].keys()
                    and self.graph.nodes[key]['source'] == 'Wikidata'])

    def __get_unlabeled_nodes_statistics(self, val, choice=0):
        if choice == 0:
            self.no_nodes = Counter([self.graph.nodes[key]['nlabel']
                                    for key in self.graph.nodes.keys()
                                    if 'nlabel' in self.graph.nodes[key].keys()
                                    and 'label' not in
                                    self.graph.nodes[key].keys()
                                    and 'source' in
                                    self.graph.nodes[key].keys()
                                    and self.graph.nodes[key]['source'] ==
                                    'Wikidata'])
        return self.no_nodes[val]

    def create_companies(self, df):
        print("\t\tCreating nodes for Organizations")
        for index, row in df.iterrows():
            self.graph.add_node("WD_Org_{}".format(index),
                                id=index, nlabel='Organization',
                                label=row['label'],
                                inception=row['inception'],
                                official_website=row['official_website'],
                                phone_number=row['phone_number'],
                                e_mail=row['e_mail'],
                                address=row['address'],
                                postal_code=row['postal_code'],
                                latitude=row['latitude'],
                                longitude=row['longitude'],
                                source='Wikidata')

            keys = ['aliases', 'descriptions', 'labels', 'official_name',
                    'employees', 'total_revenue', 'total_assets', 'net_profit',
                    'operating_income']

            self.graph.add_nodes_from([("WD_Org_{}".format(index),
                                       {key.lower(): row[key].split(';')
                                       for key in keys
                                       if not isinstance(row[key], float)
                                        })])
            self.graph.add_nodes_from([("WD_Org_{}".format(index),
                                       {key.lower(): row[key] for key in keys
                                       if isinstance(row[key], float)
                                        })])

        for node in self.o_nodes.keys():
            self.__create_node(df, "Organization", node)

    def __create_node(self, df, source, target):
        print("\t\tCreating Nodes & Relationships for {}-{}".format(
                source, target))
        if source == "Organization":
            temp = self.o_nodes
        elif source == "Person":
            temp = self.p_nodes

        for index, row in df.iterrows():
            for key in temp[target]["links"]:
                for label in temp[target]["labels"]:
                    if not isNaN(row[key]) and len(row[key]) > 1:
                        for item in row[key].split(';'):
                            self.graph.add_node("WD_{}_{}".format(label[:3],
                                                item),
                                                nlabel=label, id=item,
                                                source='Wikidata')
                            self.graph.add_edge("WD_{}_{}".format(source[:3],
                                                index),
                                                "WD_{}_{}".format(label[:3],
                                                item),
                                                elabel=key.upper(),
                                                source='Wikidata')

    def clean_companies_onwer(self):
        print("Cleaning after relationships for Organizations-Owner")

        o_ids = set([x[7:] for x in self._NetworkxImporter__get_nodes_ids(
                'nlabel', 'Organization')])
        o_u_ids = set([x[7:] for x in self.__get_unlabeled_nodes_ids(
                'Organization')])
        o_l_ids = o_ids - o_u_ids
        p_ids = set([x[7:] for x in self._NetworkxImporter__get_nodes_ids(
                'nlabel', 'Person')])
        p_u_ids = set([x[7:] for x in self.__get_unlabeled_nodes_ids('Person')])
        p_l_ids = p_ids - p_u_ids

        common_ids = o_ids & p_ids

        i = 0
        for key in common_ids:
            if key in p_l_ids:
                i += 1
                self.graph.remove_node("WD_Org_{}".format(key))
            if key in o_l_ids:
                i += 1
                self.graph.remove_node("WD_Per_{}".format(key))
        print("\tCleaned totally {} nodes".format(i))

    def __find_ids(self, node):
        print("\t\tCollecting ids for {}".format(node))
        return set([self.graph.nodes[key]['id'] for key in self.graph.nodes()
                    if 'label' not in self.graph.nodes[key].keys()
                    and 'nlabel' in self.graph.nodes[key].keys()
                    and self.graph.nodes[key]['nlabel'] == node])

    def __expand_node(self, df, node):
        print("\t\tExpanding Nodes for ", node)
        for index, row in df.iterrows():
            self.graph.add_node("WD_{}_{}".format(node[:3], index),
                                id=index, nlabel=node, label=row['label'],
                                source='Wikidata')

            keys = ['aliases', 'descriptions', 'labels']
            self.graph.add_nodes_from([("WD_{}_{}".format(node[:3], index),
                                       {key.lower(): row[key].split(';')
                                       for key in keys if not isNaN(row[key])
                                   })])

    def __expand_person(self, df):
        print("\t\tExpanding Nodes for Person")
        for index, row in df.iterrows():
            self.graph.add_node("WD_Per_{}".format(index),
                                id=index, nlabel='Person', label=row['label'],
                                gender=row['gender'], name=row['name'],
                                date_of_birth=row['date_of_birth'],
                                erdos_number=row['erdos_number'],
                                source='Wikidata')

            keys = ['aliases', 'descriptions', 'labels', 'occupation']

            self.graph.add_nodes_from([("WD_Per_{}".format(index),
                                       {key.lower(): row[key].split(';')
                                       for key in keys
                                       if not isinstance(row[key], float)
                                        })])
            self.graph.add_nodes_from([("WD_Per_{}".format(index),
                                       {key.lower(): row[key] for key in keys
                                       if isinstance(row[key], float)
                                        })])

        for node in self.p_nodes.keys():
            self.__create_node(df, "Person", node)

    def __expand_product(self, df):
        print("\t\tExpanding Nodes for Product")
        for index, row in df.iterrows():
            self.graph.add_node("WD_Pro_{}".format(index),
                                id=index, nlabel='Product', label=row['label'],
                                inception=row['inception'],
                                license=row['license'], source='Wikidata')

            keys = ['aliases', 'descriptions', 'labels']

            self.graph.add_nodes_from([("WD_Pro_{}".format(index),
                                       {key.lower(): row[key].split(';')
                                       for key in keys
                                       if not isinstance(row[key], float)
                                        })])
            self.graph.add_nodes_from([("WD_Pro_{}".format(index),
                                       {key.lower(): row[key] for key in keys
                                       if isinstance(row[key], float)
                                        })])

    def expand_nodes(self, df, node):
        ids = self.__find_ids(node)
        print("\t\t{} nodes will be expanded out of {}".format(
                len(ids & set(df.index)), len(ids)))
        if node == 'Person':
            self.__expand_person(df.loc[ids & set(df.index)])
        elif node == 'Product':
            self.__expand_product(df.loc[ids & set(df.index)])
        else:
            self.__expand_node(df.loc[ids & set(df.index)], node)

    def export_unlabeled_ids(self):
        nodes = self._NetworkxImporter__get_nodes_values('nlabel')
        for i, node in enumerate(nodes):
            print("\tExporting {}".format(node))
            pd.Series(list(self.__get_unlabeled_nodes_ids(node))).to_csv(
                    "./data/{}_collected.csv".format(node),
                    header=False, index=None)

    def print_statistics(self):
        nodes = super(WD_NetworkxImporter, self).print_statistics()
        print('\n\tUnlabeled Nodes:')
        for i, node in enumerate(nodes):
            print("\t\tUnlabeled Wikidata {} Nodes: {:,}".format(node,
                            self.__get_unlabeled_nodes_statistics(node, i)))
