
from numpy import nan
import pandas as pd
import networkx as nx
from collections import Counter
import re

def isNaN(s):
    return s != s


class NetworkxImporter():

    def __init__(self, source):
        self.graph = nx.MultiDiGraph()
        self.source = source

    def __get_nodes_ids(self, attribute, value):
        return [key for key in self.graph.nodes()
                if attribute in self.graph.nodes[key].keys()
                and self.graph.nodes[key][attribute] == value
                and 'source' in self.graph.nodes[key].keys()
                and self.graph.nodes[key]['source'] == self.source]

    def __get_edges_ids(self, attribute, value):
        return [key for key in self.graph.edges()
                if self.graph.edge[key][attribute] == value
                and self.graph.edges[key]['source'] == self.source]

    def __get_nodes_statistics(self, val, choice=0):
        if choice == 0:
            self.no_nodes = Counter([self.graph.nodes[key]['nlabel']
                                    for key in self.graph.nodes()
                                    if 'nlabel' in self.graph.nodes[key].keys()
                                    and 'source' in self.graph.nodes[key].keys()
                                    and self.graph.nodes[key]['source'] == self.source                                        
                                     ])
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
                                and self.graph.edges[edge]['source'] == self.source])
        return self.no_edges["{}_{}_{}".format(val, _from, _to)]

    def __get_nodes_values(self, attr):
        return set([self.graph.nodes[node][attr]
                    for node in self.graph.nodes()
                    if attr in self.graph.node[node].keys()])

    def __get_edges_values(self, attr):
        return set([(self.graph.edges[edge][attr],
                     self.graph.nodes[edge[0]]['nlabel'],
                     self.graph.nodes[edge[1]]['nlabel'])
                    for edge in self.graph.edges.keys()])

    def print_statistics(self):
        print("Statistics:")
        print("\tTotal {} Nodes: {:,}".format(self.source,
                                              self.graph.number_of_nodes()))

        nodes = self.__get_nodes_values('nlabel')
        for i, node in enumerate(nodes):
            print("\t\t{} {} Nodes: {:,}".format(self.source, node,
                                                 self.__get_nodes_statistics(
                                                         node, i)))

        print("\tTotal {} Edges: {:,}".format(self.source,
                                              self.graph.number_of_edges()))

        edges = self.__get_edges_values('elabel')
        for i, (elabel, nlabel1, nlabel2) in enumerate(edges):
            print("\t\t{} {}({},{}) Edges: {:,}".format(self.source, elabel,
                              nlabel1, nlabel2, self.__get_edges_statistics(
                              elabel, nlabel1, nlabel2, i)))
        return nodes

    def __clean(self):
        for node in self.graph.nodes:
            del_keys = []
            for key in self.graph.nodes[node].keys():
                if isinstance(self.graph.nodes[node][key], list):
                    self.graph.nodes[node][key] = ' '.join(
                            self.graph.nodes[node][key])
                elif isinstance(self.graph.nodes[node][key], set):
                    self.graph.nodes[node][key] = ' '.join(
                            self.graph.nodes[node][key])
                if isinstance(self.graph.nodes[node][key], str):
                    self.graph.nodes[node][key] = re.sub(r'[^w]', '_',
                                                   self.graph.nodes[node][key])
                if isNaN(self.graph.nodes[node][key]):
                    del_keys += [key]
            for key in del_keys:
                del(self.graph.nodes[node][key])

    def __write_graphml(self, file, nlab='nlabel', elab='elabel'):
        with open('./graphml/{}.graphml'.format(file.split('.')[0]), 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                    'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns'
                    ' http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')

            for key in set.union(*[set(attr.keys()) for (node, attr)
                                   in self.graph.nodes.data()]):
                f.write('<key id="{}" for="node" attr.name="{}"/>\n'.format(
                        key, key))
            f.write('<key id="label" for="node" attr.name="label"/>\n')

            for key in set.union(*[set(attr.keys()) for (s, t, attr)
                                   in self.graph.edges.data()]):
                f.write('<key id="{}" for="edge" attr.name="{}"/>\n'.format(
                        key, key))

            f.write('<key id="label" for="edge" attr.name="label"/>\n')
            f.write('<graph id="G" edgedefault="directed">\n')

            nodes = {}
            for no, (node, attr) in enumerate(self.graph.nodes.data()):
                temp = node.split("_")
                nodes[node] = '{}_{}_{}'.format(temp[0], temp[1], no)

                f.write('<node id="{}" labels=":{}">'
                        '<data key="labels">:{}</data>\n'.format(
                                nodes[node], attr[nlab], attr[nlab]))
                for key in attr:
                    if key == 'labels':
                        f.write('  <data key="wdlabels">{}</data>\n'.format(
                                attr['labels']))
                    elif key == nlab:
                        continue
                    else:
                        f.write('  <data key="{}">{}</data>\n'.format(key,
                                attr[key]))
                f.write('</node>\n')

            for i, (s, t, attr) in enumerate(self.graph.edges.data()):
                f.write('<edge id="e{}" source="{}" target="{}" label="{}">'
                        '<data key="label">{}</data>\n'.format(i, nodes[s],
                                                               nodes[t],
                                                               attr[elab],
                                                               attr[elab]))
                for key in attr:
                    if key == elab:
                        continue
                    else:
                        f.write('  <data key="{}">{}</data>\n'.format(key,
                                attr[key]))
                f.write('</edge>\n')
            f.write('</graph>\n</graphml>\n')

    def export(self, path, format='gpickle'):
        if format == 'gpickle':
            nx.write_gpickle(self.graph, path)
        elif format == 'graphml':
            self.__clean()
            self.__write_graphml(path)
