from time import time
import yaml
from neo4j import GraphDatabase, exceptions


def isNaN(s):
    return s != s


class Neo4jImporter(object):

    def __init__(self, creds):
        self._driver = GraphDatabase.driver(creds["uri"], auth=(creds["user"],
                                            creds["password"]))
        self.session = self._driver.session()

    def close(self):
        self._driver.close()

    def add_constraints(self):
        constraints = ["SectorGroup", "Sector", "Industry", "Company", "Filer",
                       "Location", "Subdivision", "Country", "Organization",
                       "Article", "Person", "Theme", "Group", "Product",
                       "StockExchange", "Grant"]
        constraints = ["CREATE CONSTRAINT ON (n:{}) ASSERT n.id IS "
                       "UNIQUE".format(c) for c in constraints]

        added = 0
        for constraint in constraints:
            added += self.session.run(constraint
                                      ).summary().counters.constraints_added
        print('\tConstraints added {}'.format(added))

    def drop_constraints(self):
        constraints = self.session.run('CALL db.constraints').values()
        constraints = ['DROP {}'.format(c[0]) for c in constraints]

        rem = 0
        for constraint in constraints:
            rem += self.session.run(constraint
                                    ).summary().counters.constraints_removed
        print('\tConstraints removed {}'.format(rem))

    def import_files(self, files, path):
        queries = ["CALL apoc.import.graphml('{}{}', {{batchSize:10000, "
                   "storeNodeIds: true, readLabels: true}})".format(path, file)
                   for file in files]

        for file, query in zip(files, queries):
            print("\tImporting {}".format(file))
            res = self.session.run(query).data()[0]
            for key in res:
                print("\t\t{}: {}".format(key, res[key]))

    def merge_nodes(self, label=None, source=None):
        label = self.__san_label(label)
        source = self.__san_source(source)
        query = "MATCH (n{} {}), (m{} {}) WHERE n.id=m.id and id(n)<>id(m) "\
                "CALL apoc.refactor.mergeNodes([n,m]) YIELD node "\
                "RETURN COUNT(node)".format(label, source, label, source)

        merged = self.session.run(query).values()[0][0]
        print('\tNodes merged {}'.format(merged))

    def __san_label(self, label):
        return ':{}'.format(label) if label is not None else ''

    def __san_source(self, source):
        return '{{source:"{}"}}'.format(source) if source is not None else ''

    def delete_graph(self, label=None, source=None, batch=1000):
        label = self.__san_label(label)
        source = self.__san_source(source)
        query = 'CALL apoc.periodic.iterate("MATCH (n{} {}) RETURN n", '\
                '"DETACH DELETE n", {{batchSize:{}}}) YIELD batches, total '\
                'RETURN batches, total'.format(label, source, batch)
        deleted = self.session.run(query).data()[0]['total']
        print("\tNodes Deleted: {:,}".format(deleted))


if __name__ == '__main__':
    with open("neo4j_creds.yaml", 'r') as stream:
        try:
            creds = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    # files = ['wd_graph.graphml', 'cw_graph.graphml', 'gdelt_graph.graphml']
    files = ['cw_graph.graphml', 'wd_graph.graphml']
    path = '/var/local/data-1/datasets/graphml/'

    nim = Neo4jImporter(creds)
    print("Adding constraints")
    nim.add_constraints()
    print("Importing files")
    nim.import_files(files, path)
