import networkx as nx
import os
from time import time
import re
import pandas as pd
from collections import Counter

def isNaN(s):
    return s != s


def clean(graph):
    for node in graph.nodes:
        del_keys = []
        for key in graph.nodes[node].keys():
            if isinstance(graph.nodes[node][key], list):
                graph.nodes[node][key] = ' '.join(graph.nodes[node][key])
            elif isinstance(graph.nodes[node][key], set):
                graph.nodes[node][key] = ' '.join(graph.nodes[node][key])
            if isinstance(graph.nodes[node][key], str):

                graph.nodes[node][key] = re.sub(r'[^\w]', '_',
                                                graph.nodes[node][key])
            if isNaN(graph.nodes[node][key]):
                del_keys += [key]
        for key in del_keys:
            del(graph.nodes[node][key])
    return graph


def write_xml(graph, file, nlab='nlabel', elab='elabel'):
    with open('./graphml/{}.graphml'.format(file.split('.')[0]), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
                'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')

        for key in set.union(*[set(attr.keys()) for (node, attr)
                               in graph.nodes.data()]):
            f.write('<key id="{}" for="node" attr.name="{}"/>\n'.format(key,
                    key))
        f.write('<key id="label" for="node" attr.name="label"/>\n')

        for key in set.union(*[set(attr.keys()) for (s, t, attr)
                               in graph.edges.data()]):
            f.write('<key id="{}" for="edge" attr.name="{}"/>\n'.format(key,
                    key))

        f.write('<key id="label" for="edge" attr.name="label"/>\n')
        f.write('<graph id="G" edgedefault="directed">\n')

        nodes = {}
        for no, (node, attr) in enumerate(graph.nodes.data()):
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

        for i, (s, t, attr) in enumerate(graph.edges.data()):
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


for file in os.listdir('./gpickle/'):
    if not file.endswith('.gpickle'):
        continue

    print('\n{}'.format(file))
    t0 = time()
    t1 = time()
    graph = nx.read_gpickle('./gpickle/'+file)
    t2 = time()
    print("\tTime elapsed for reading: {:.2f} sec".format(t2-t1))

    t1 = time()
    graph = clean(graph)
    t2 = time()
    print("\tTime elapsed for cleaning: {:.2f} sec".format(t2-t1))

    t1 = time()
    write_xml(graph, file)
    t2 = time()
    print("\tTime elapsed for writing: {:.2f} sec".format(t2-t1))

    print("Edges are {:,} and Nodes are {:,}".format(graph.number_of_edges(),
                                                     graph.number_of_nodes()))
    t2 = time()
    print("Total time elapsed: {:.2f} sec".format(t2-t0))
    del(graph)
