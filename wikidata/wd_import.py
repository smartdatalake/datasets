import pandas as pd
import re
import yaml
from neo4j import GraphDatabase


def isNaN(s):
    return s != s


class Neo4jImporter(object):

    organization_nodes = {"Person": {"labels": ['Person'], "links": [
            'Founded_by', 'Chief_executive_officer', 'Director',
            'Chairperson', 'Board_member'], "files": ['human.csv']},
             "Organization": {"labels": ['Organization'],
                         "links": ['Owner_of', 'Parent_organization',
                                   'Subsidiary', 'Member_of', 'Different_from',
                                   'Replaced_by', 'Replaces'],
                         "files": ['']},
             "Owner": {"labels": ['Person', 'Organization'],
                       "links": ['Owned_by'], "files": ['']},
             "StockExchange": {"labels": ['StockExchange'],
                               "links": ['In_stock_exchange'],
                               "files": ['trading_venue.csv', 'market.csv']},
             "Group": {"labels": ['Group'], "links": ['Part_of'],
                       "files": ['group.csv']},
             "Industry": {"labels": ['Industry'], "links": ['In_industry'],
                          "files": ['industry.csv']},
             "Grant": {"labels": ['Grant'], "links": ['Received_grant'],
                       "files": ['grant.csv']},
             "Location": {"labels": ['Location'],
                          "links": ['Location_of_formation'], "files": ['']},
             "Country": {"labels": ['Country'], "links": ['Country'],
                         "files": ['country.csv']},
             "Product": {"labels": ['Product'], "links": ['Produces'],
                         "files": ['products.csv ']}
     }

    person_nodes = {"Organization": {"labels": ['Organization'],
                                "links": ['Member_of'], "files": ['']},
                    "Grant": {"labels": ['Grant'], "links": ['Received_grant'],
                              "files": ['grant.csv']},
                    "Location": {"labels": ['Location'],
                                 "links": ['Place_of_Birth'], "files": ['']},
                    "Country": {"labels": ['Country'],
                                "links": ['Citizenship'],
                                "files": ['country.csv']}
                    }

    def __init__(self, creds):
        self._driver = GraphDatabase.driver(creds["uri"], auth=(creds["user"],
                                            creds["password"]))

    def close(self):
        self._driver.close()

    def exec_query(self, choice, df=None, node=None):
        with self._driver.session() as session:
            if choice == 0:
                session.write_transaction(self._constraint_graph)
            elif choice == 1:
                session.write_transaction(self._print_statistics)
            elif choice == 2:
                session.write_transaction(self._create_companies, df)
            elif choice == 3:
                ids = set([val for [val] in session.write_transaction(
                        self._find_ids, node)])
                print("\t\t{} nodes will be expanded out of {}".format(
                        len(ids & set(df.index)), len(ids)))
                session.write_transaction(
                        self._expand_node, df.loc[ids & set(df.index)], node)
            elif choice == 4:
                session.write_transaction(self._clean_companies_onwer)
            elif choice == 5:
                ids = set([val for [val] in session.write_transaction(
                        self._find_ids, "Person")])
                print("\t\t{} nodes will be expanded out of {}".format(
                        len(ids & set(df.index)), len(ids)))
                session.write_transaction(
                        self._create_person, df.loc[ids & set(df.index)])
            elif choice == 6:
                ids = set([val for [val] in session.write_transaction(
                        self._find_ids, "Product")])
                print("\t\t{} nodes will be expanded out of {}".format(
                        len(ids & set(df.index)), len(ids)))
                session.write_transaction(
                        self._create_product, df.loc[ids & set(df.index)])

    @staticmethod
    def _constraint_graph(tx):
        tx.run("CREATE CONSTRAINT ON (c:Organization) ASSERT c.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (p:Person) ASSERT p.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (g:Group) ASSERT g.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (se:StockExchange) "
               "ASSERT se.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (a:Grant) ASSERT a.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (pr:Product) ASSERT pr.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (ct:Country) ASSERT ct.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (l:Location) ASSERT l.ID IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (i:Industry) ASSERT i.ID IS UNIQUE")

    @staticmethod
    def _create_companies(tx, df):
        print("\t\tCreating nodes for Organizations")
        for index, row in df.iterrows():
            query = "MERGE (c:Organization {{ ID:'{}' }}) "\
                    "SET c.source='Wikidata'".format(index)
            for key in ['Label', 'Inception', 'Official_website',
                        'Phone_number', 'E_mail', 'Address', 'Postal_code']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= "{}"'.format(key, row[key])
            for key in ['Aliases', 'Descriptions', 'Labels', 'Official_name',
                        'Employees', 'Total_revenue', 'Total_assets',
                        'Net_profit', 'Operating_income']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= SPLIT("{}",";")'.format(key, row[key])
            for key in ['Latitude', 'Longitude']:
                if not isNaN(row[key]) and isinstance(row[key], float):
                    query += ',c.{}= {}'.format(key, row[key])
            tx.run(query)

        for node in Neo4jImporter.organization_nodes.keys():
            Neo4jImporter._create_node(tx, df, "Organization", node)

    @staticmethod
    def _create_node(tx, df, source, target):
        print("\t\tCreating Nodes & Relationships for {}-{}".format(
                source, target))
        if source == "Organization":
            temp = Neo4jImporter.organization_nodes
        elif source == "Person":
            temp = Neo4jImporter.person_nodes

        for index, row in df.iterrows():
            for key in temp[target]["links"]:
                for label in temp[target]["labels"]:
                    if not isNaN(row[key]):
                        for item in row[key].split(';'):
                            query = "MERGE (c:{} {{ ID: '{}'}})".format(source,
                                                                        index)
                            query += " MERGE (n:{} {{ ID: '{}' }}) SET "\
                                     "n.source='Wikidata'".format(label, item)
                            query += " MERGE (c) - [:{}] -> (n)".format(
                                    key.upper())
                            tx.run(query)

    @staticmethod
    def _clean_companies_onwer(tx):
        print("\t\tCleaning after relationships for Organizations-Owner")
        tx.run("MATCH (c:Organization), (p:Person) WHERE c.ID = p.ID AND NOT "
               "EXISTS(c.Label) DETACH DELETE(c)")
        tx.run("MATCH (c:Organization), (p:Person) WHERE c.ID = p.ID AND NOT "
               "EXISTS(p.Label) DETACH DELETE(p)")

    @staticmethod
    def _expand_node(tx, df, node):
        print("\t\tExpanding Nodes for ", node)
        for index, row in df.iterrows():
            query = "MERGE (n:{} {{ ID:'{}' }}) SET "\
                    "n.source='Wikidata'".format(node, index)
            for key in ['Label']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',n.{}= "{}"'.format(key, row[key])
            for key in ['Aliases', 'Descriptions', 'Labels']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',n.{}= SPLIT("{}",";")'.format(key, row[key])
            tx.run(query)

    @staticmethod
    def _find_ids(tx, node):
        print("\t\tCollecting ids for {}".format(node))
        return tx.run("MATCH (n:{} {{source: 'Wikidata'}}) WHERE NOT "
                      "EXISTS(n.Label) RETURN DISTINCT n.ID".format(node)
                      ).values()

    @staticmethod
    def _create_person(tx, df):
        for index, row in df.iterrows():
            query = "MERGE (c:Person {{ ID:'{}' }}) SET "\
                    "c.source='Wikidata'".format(index)
            for key in ['Label', 'Gender', 'Name',
                        'Date_of_Birth', 'Erdos_Number']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= "{}"'.format(key, row[key])
            for key in ['Aliases', 'Descriptions', 'Labels', 'Occupation']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= SPLIT("{}",";")'.format(key, row[key])
            tx.run(query)

        for node in Neo4jImporter.person_nodes.keys():
            Neo4jImporter._create_node(tx, df, "Person", node)

    @staticmethod
    def _create_product(tx, df):
        for index, row in df.iterrows():
            query = "MERGE (c:Product {{ ID:'{}' }}) "\
                    "SET c.source='Wikidata'".format(index)
            for key in ['Label', 'Inception', 'License']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= "{}"'.format(key, row[key])
            for key in ['Aliases', 'Descriptions', 'Labels']:
                if not isNaN(row[key]):
                    row[key] = re.sub("\\\\", "/", str(row[key]))
                    row[key] = re.sub('"', "\'", str(row[key]))
                    query += ',c.{}= SPLIT("{}",";")'.format(key, row[key])
            tx.run(query)

    @staticmethod
    def _print_statistics(tx):
        print("Statistics:")
        print("\tTotal Wikidata Records: {:,}".format(
                tx.run("MATCH (n {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Organization Records: {:,}".format(
                tx.run("MATCH (n:Organization {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Person Records: {:,}".format(
                tx.run("MATCH (n:Person {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t StockExchange Records: {:,}".format(
                tx.run(
                  "MATCH (n:StockExchange {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Group Records: {:,}".format(
                tx.run("MATCH (n:Group {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Industry Records: {:,}".format(
                tx.run("MATCH (n:Industry {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Grant Records: {:,}".format(
                tx.run("MATCH (n:Grant {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Location Records: {:,}".format(
                tx.run("MATCH (n:Location {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Country Records: {:,}".format(
                tx.run("MATCH (n:Country {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\t Product Records: {:,}".format(
                tx.run("MATCH (n:Product {source:'Wikidata'}) RETURN COUNT(n)"
                       ).values()[0][0]))

        print("\n\tTotal Unlabeled Wikidata Records: {:,}".format(
                tx.run("MATCH (n {source:'Wikidata'}) WHERE NOT EXISTS"
                       "(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Organization Records: {:,}".format(
                tx.run("MATCH (n:Organization {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Person Records: {:,}".format(
                tx.run("MATCH (n:Person {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t StockExchange Records: {:,}".format(
                tx.run("MATCH (n:StockExchange {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Group Records: {:,}".format(
                tx.run("MATCH (n:Group {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Industry Records: {:,}".format(
                tx.run("MATCH (n:Industry {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Grant Records: {:,}".format(
                tx.run("MATCH (n:Grant {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Location Records: {:,}".format(
                tx.run("MATCH (n:Location {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Country Records: {:,}".format(
                tx.run("MATCH (n:Country {source:'Wikidata'}) WHERE NOT "
                       "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))
        print("\t\t Product Records: {:,}".format
              (tx.run("MATCH (n:Product {source:'Wikidata'}) WHERE NOT "
                      "EXISTS(n.Label) RETURN COUNT(n)").values()[0][0]))


with open("neo4j_creds.yaml", 'r') as stream:
    try:
        creds = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

print("Creating Constraints")
nim = Neo4jImporter(creds)
nim.exec_query(0)

print("Creating Organizations")
chunks = pd.read_csv('../data/4_clean_data/organizations.csv',
                     quotechar='"', escapechar='\\', chunksize=1000,
                     index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(2, df)

nim.exec_query(1)

for node in ['Country', 'Grant', 'Stock_Exchange', 'Industry', 'Group']:
    for file in Neo4jImporter.organization_nodes[node]["files"]:
        print("Expanding for {}-{}".format(node, file))
        chunks = pd.read_csv('../data/4_clean_data/'+file, quotechar='"',
                             escapechar='\\', chunksize=10000, index_col="ID")
        for i, df in enumerate(chunks):
            print("\tChunk {}".format(i))
            nim.exec_query(3, df, node)

nim.exec_query(1)
nim.exec_query(4)
nim.exec_query(1)

print("Creating Person")
chunks = pd.read_csv('../data/4_clean_data/human.csv', quotechar='"',
                     escapechar='\\', chunksize=10000, index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(5, df)


nim.exec_query(1)

print("Creating Product")
chunks = pd.read_csv('../data/4_clean_data/product.csv', quotechar='"',
                     escapechar='\\', chunksize=10000, index_col="ID")
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(6, df)

nim.exec_query(1)
