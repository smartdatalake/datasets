from time import time
import yaml
from neo4j import GraphDatabase, exceptions
import networkx as nx
import os
import re


def isNaN(s):
    return s != s


class Neo4jImporter(object):

    def __init__(self, creds):
        self._driver = GraphDatabase.driver(creds["uri"], auth=(creds["user"],
                                            creds["password"]))
        self.session = self._driver.session()

    def close(self):
        self._driver.close()

    def constraints(self):
        constraints = [
                "CREATE CONSTRAINT ON (n:SectorGroup) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Sector) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Industry) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Company) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Filer) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Location) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Subdivision) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Country) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Organization) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Article) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Person) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Theme) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Group) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Product) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:StockExchange) ASSERT n.id IS UNIQUE",
                "CREATE CONSTRAINT ON (n:Grant) ASSERT n.id IS UNIQUE"]

        for constraint in constraints:
            self.session.run(constraint)

    def delete_graph(self):
        results = self.session.run(
                "MATCH (n) DETACH DELETE(n)").summary().counters
        print("Nodes Deleted: {:,}".format(results.nodes_deleted))
        print("Edges Deleted: {:,}".format(results.relationships_deleted))

    def import_nodes(self, graph, nlab):
        error = []
        for (node, attr) in graph.nodes.data():
            query = "MERGE (n:{} {{id:'{}'".format(attr[nlab], node)
            for key in attr.keys():
                if isNaN(attr[key]):
                    continue

                if isinstance(attr[key], str):
                    attr[key] = re.sub('"', '\\"', attr[key])

                    query += ', {}: "{}"'.format(key, attr[key])
                else:
                    query += ", {}: {}".format(key, attr[key])
            query += "})"
            #query = re.sub(b'\xa0', b'', query.encode('utf-8'))
            try:
                self.session.run(query)
            except exceptions.CypherSyntaxError:
                error += [node]
        return error

    def import_edges(self, graph, nlab, elab):
        for (n0, n1, attr) in graph.edges.data():
            query = "MATCH (a:{} {{id: '{}'}})".format(
                    graph.nodes[n0][nlab], n0)
            query += " MATCH (b:{} {{id: '{}'}})".format(
                     graph.nodes[n1][nlab], n1)
            query += " MERGE (a) - [:{} {{elabel: '{}'".format(
                     attr[elab], attr[elab])

            for key in attr.keys():
                if isNaN(attr[key]):
                    continue

                if isinstance(attr[key], str):
                    query += ', {}: "{}"'.format(key, attr[key])
                else:
                    query += ", {}: {}".format(key, attr[key])

            query += "}] -> (b)"
            self.session.run(query)


if __name__ == '__main__':
    with open("neo4j_creds.yaml", 'r') as stream:
        try:
            creds = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    nim = Neo4jImporter(creds)
    nim.constraints()
    nim.delete_graph()

    for file in os.listdir('./gpickle/'):
        if not file.endswith('.gpickle'):
            continue
        print('\n{}'.format(file))

        t1 = time()
        print('\tReading gpickle')
        graph = nx.read_gpickle('./gpickle/'+file)
        t2 = time()
        print("\t\tTime elapsed for reading gpickle: {:.2f} sec".format(t2-t1))
        t1 = time()
        print('\tImporting nodes')
        error = nim.import_nodes(graph, 'nlabel')
        t2 = time()
        print("\t\tTime elapsed for importing nodes: {:.2f} sec".format(t2-t1))
        t1 = time()
        print('\tImporting edges')
        nim.import_edges(graph, 'nlabel', 'elabel')
        t2 = time()
        print("\t\tTime elapsed for importing edges: {:.2f} sec".format(t2-t1))
        t1 = time()
        del(graph)
