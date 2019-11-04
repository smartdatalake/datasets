import pandas as pd
import networkx as nx

def isNaN(s):
    return s != s

def export_all_csv(graph, file):
    temp = {}
    for node in graph.nodes:
        if node.startswith('A_'):
            t = []
            for neighbor in graph.neighbors(node):
                if neighbor.startswith("S_"):
                    continue
                elif neighbor.startswith("L_"):
                    t.append(graph.nodes[neighbor]['full_name'].lower())
                else:
                    t.append(neighbor[2:].lower())
            temp[node[2:]] = (' '.join(t)).replace(',','')
    temp = pd.Series(temp)
    temp.to_csv(file, sep=';', header=False)


def export_vertex_csv(graph, file, cols, label):
    x = pd.DataFrame()
    for col in cols:
        y = pd.Series(dict(graph.nodes(data=col)))
        x[col] = y
    x = x[x.nlabel==label]
    x.drop('nlabel', axis=1, inplace=True)
    x.to_csv(file, index=None)


def export_edge_csv(graph, path):
    x = pd.DataFrame(list(graph.edges(data='elabel')),
                     columns=['Source','Target','Edge'])
    x.Source = x.Source.apply(lambda x: x[2:])
    x.Target = x.Target.apply(lambda x: x[2:])
    for label in x.Edge.unique():
        x.loc[x.Edge==label, ['Source','Target']].to_csv("{}{}.csv".format(
                path,label.lower()), header=True, index=None)


def write_graphml(graph, file, nlab='nlabel', elab='elabel'):
    with open('./graphml/{}.graphml'.format(file.split('.')[0]), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns'
                ' http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')

        for key in set.union(*[set(attr.keys()) for (node, attr)
                               in graph.nodes.data()]):
            f.write('<key id="{}" for="node" attr.name="{}"/>\n'.format(
                    key, key))
        f.write('<key id="label" for="node" attr.name="label"/>\n')

        for key in set.union(*[set(attr.keys()) for (s, t, attr)
                               in graph.edges.data()]):
            f.write('<key id="{}" for="edge" attr.name="{}"/>\n'.format(
                    key, key))

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
                if key == 'document_id':
                    f.write('  <data key="{}">"{}"</data>\n'.format(key,
                            attr[key]))
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
