import pandas as pd
import re
import yaml
from neo4j import GraphDatabase

limit = 2000
chunksize = 10000


def isNaN(s):
    return s != s


class Neo4jImporter(object):

    def __init__(self, creds):
        self._driver = GraphDatabase.driver(creds["uri"], auth=(creds["user"],
                                            creds["password"]))

    def close(self):
        self._driver.close()

    def exec_query(self, choice, df=None):
        with self._driver.session() as session:
            if choice == 0:
                session.write_transaction(self._constraint_graph)
            elif choice == 1:
                session.write_transaction(self._create_companies, df)
            elif choice == 2:
                session.write_transaction(self._create_industries, df)
            elif choice == 3:
                session.write_transaction(self._create_sectors, df)
            elif choice == 4:
                session.write_transaction(self._create_countries, df)
            elif choice == 5:
                session.write_transaction(self._create_subdivisions, df)
            elif choice == 6:
                session.write_transaction(self._create_countries_aliases, df)
            elif choice == 7:
                session.write_transaction(self._create_locations, df)
            elif choice == 8:
                session.write_transaction(self._create_filers, df)
            elif choice == 9:
                session.write_transaction(self._create_relationships, df)
            elif choice == 10:
                session.write_transaction(self._print_statistics)

    @staticmethod
    def _constraint_graph(tx):
        tx.run("CREATE CONSTRAINT ON (c:Company) ASSERT c.cw_id IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (sg:SectorGroup) "
               "ASSERT sg.sector_group IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (se:Sector) "
               "ASSERT se.sic_sector IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (ind:Industry)"
               "ASSERT ind.sic_code IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (ct:Country)"
               "ASSERT ct.country_code IS UNIQUE")
        tx.run("CREATE CONSTRAINT ON (sd:Subdivision)"
               "ASSERT sd.subdivision_code IS UNIQUE")
        tx.run("CREATE INDEX ON :Location(type)")
        tx.run("CREATE CONSTRAINT ON (f:Filer) ASSERT f.cik IS UNIQUE")

    @staticmethod
    def _create_companies(tx, df):
        for index, row in df.iterrows():
            query = "MERGE (c:Company {{cw_id: {}, latest_year: {},"\
                "cik: {}, irs_number: {}, no_parents: {}, no_children: {}, "\
                "top_parent: {}, company_name: '{}', source: 'Corpwatch'"\
                "}})".format(row["cw_id"], row["year"],
                             row["cik"], row["irs_number"], row["num_parents"],
                             row["num_children"], row["top_parent_id"],
                             row["company_name"])
            if not(isNaN(row["sic_code"]) and isNaN(row["industry_name"])):
                query += " MERGE (ind:Industry {{sic_code: {} }})".format(
                                                            row["sic_code"])
                query += " MERGE (c) - [:PART_OF] -> (ind)"
            tx.run(query)

    @staticmethod
    def _create_industries(tx, df):
        for index, row in df.iterrows():
            row["industry_name"] = re.sub("'", "\\'", row["industry_name"])
            query = "MERGE (ind:Industry {{sic_code: {}, name:'{}', "\
                "source: 'Corpwatch'}})".format(
                    row["sic_code"], row["industry_name"])
            query += " MERGE (se:Sector {{sic_sector: {}}}) ".format(
                     row["sic_sector"])
            query += " MERGE (ind) - [:PART_OF] -> (se)"
            tx.run(query)

    @staticmethod
    def _create_sectors(tx, df):
        for index, row in df.iterrows():
            row["sector_name"] = re.sub("'", "\\'", row["sector_name"])
            row["sector_group_name"] = re.sub("'", "\\'",
                                              row["sector_group_name"])
            query = "MERGE (se:Sector {{sic_sector: {}}}) SET se.name='{}', "\
                "se.source='Corpwatch'".format(
                    row["sic_sector"], row["sector_name"])
            query += "MERGE (sg:SectorGroup {{ "\
                "name:'{}', sector_group:{}, "\
                "source: 'Corpwatch'}})".format(
                    row["sector_group_name"], row["sector_group"])
            query += " MERGE (se) - [:PART_OF] -> (sg)"
            tx.run(query)

    @staticmethod
    def _create_countries(tx, df):
        for index, row in df.iterrows():
            row["country_name"] = re.sub("'", "\\'", row["country_name"])
            query = "MERGE (ct:Country {{country_code:'{}', "\
                "name:'{}', latitude:{}, longitude:{}, source: "\
                "'Corpwatch'}})".format(
                    row["country_code"], row["country_name"],
                    row["latitude"], row["longitude"])
            tx.run(query)

    @staticmethod
    def _create_subdivisions(tx, df):
        for index, row in df.iterrows():
            row["subdivision_name"] = re.sub("'", "\\'",
                                             row["subdivision_name"])
            query = "MERGE (sd:Subdivision {{subdivision_code:'{}', "\
                "name:'{}', latitude:{}, longitude:{}, "\
                "source: 'Corpwatch'}})".format(
                    row["country_code"]+"_"+row["subdivision_code"],
                    row["subdivision_name"], row["latitude"], row["longitude"])
            query += " MERGE (ct:Country {{country_code:'{}'}})".format(
                    row["country_code"])
            query += " MERGE (sd) - [:IS_IN] -> (ct)"
            tx.run(query)

    @staticmethod
    def _create_countries_aliases(tx, df):
        df = pd.DataFrame(df.groupby('country_code').country_name.agg(
                lambda x: ';'.join(x))).reset_index(level=0)
        for index, row in df.iterrows():
            row["country_name"] = re.sub("'", "\\'", row["country_name"])
            query = " MERGE (ct:Country {{country_code:'{}'}}) ON MATCH SET "\
                "ct.alias=split('{}',';')".format(
                    row["country_code"], row["country_name"])
            tx.run(query)

    @staticmethod
    def _create_locations(tx, df):
        for index, row in df.iterrows():
            row["street_1"] = re.sub("'", "\\'", row["street_1"])
            row["street_2"] = re.sub("'", "\\'", row["street_2"])
            row["city"] = re.sub("'", "\\'", row["city"])
            query = "MERGE (c:Company {{cw_id:{}}})".format(row["cw_id"])
            query += " CREATE (l:Location {{type:'{}', street_1:'{}', "\
                "street_2:'{}', city:'{}', state:'{}', postal_code:'{}', "\
                "source: 'Corpwatch'}})".format(
                    row["type"], row["street_1"], row["street_2"],
                    row["city"], row["state"], row["postal_code"])
            query += " MERGE (c) - [:LOCATED_AT] -> (l)"
            if not(isNaN(row["country_code"]) and isNaN(row["subdiv_code"])):
                query += " MERGE (sd:Subdivision {{subdivision_code:'{}'"\
                    "}})".format(
                        row["country_code"] + "_" + row["subdiv_code"])
                query += " MERGE (l) - [:IS_IN] -> (sd)"
            tx.run(query)

    @staticmethod
    def _create_filers(tx, df):
        for index, row in df.iterrows():
            for key in row.keys():
                if type(row[key]) is str:
                    row[key] = re.sub("'", "\\'", row[key])
            query = "MERGE (f:Filer {{cw_id:'{}', "\
                "business_phone:'{}', match_name: '{}', conformed_name:"\
                "'{}', irs_number: '{}', cik: '{}' , "\
                "source: 'Corpwatch'}})".format(
                    row["cw_id"],
                    row["business_phone"],
                    row["match_name"], row["conformed_name"],
                    row["irs_number"], row["cik"])
            query += " CREATE (l1:Location {{type:'business', street_1:'{}', "\
                "street_2:'{}', city:'{}', state:'{}', postal_code:'{}', "\
                "source: 'Corpwatch'}})".format(
                    row["business_street_1"], row["business_street_2"],
                    row["business_city"], row["business_state"],
                    row["business_zip"])
            query += " MERGE (f) - [:LOCATED_AT] -> (l1)"
            query += " CREATE (l2:Location {{type:'mail', street_1:'{}', "\
                "street_2:'{}', city:'{}', state:'{}', postal_code:'{}', "\
                "source: 'Corpwatch'}})".format(
                    row["mail_street_1"], row["mail_street_2"],
                    row["mail_city"], row["mail_state"], row["mail_zip"])
            query += " MERGE (f) - [:LOCATED_AT] -> (l2)"
            tx.run(query)

    @staticmethod
    def _create_relationships(tx, df):
        for index, row in df.iterrows():
            query = "MERGE (f:Filer {{cik:{}}})".format(row["filer_cik"])
            query += " MERGE (c1:Company {{cw_id:{}}})".format(row["cw_id"])
            query += " MERGE (f) - [:FILED {{id: {}}}] -> (c1)".format(
                    row["filing_id"])
            if not isNaN(row["parent_cw_id"]):
                query += " MERGE (c2:Company {{cw_id:{}}})".format(
                        row["parent_cw_id"])
                query += " MERGE (c2) - [:PARENT {{filing_id: {}}}] -> "\
                    "(c1)".format(
                        row["filing_id"])
            tx.run(query)
            
    @staticmethod
    def _print_statistics(tx):
        print("Statistics:")
        print("\tTotal Corpwatch Nodes: {:,}".format(
                tx.run("MATCH (n {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Company Nodes: {:,}".format(
                tx.run("MATCH (n:Company {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Industry Nodes: {:,}".format(
                tx.run("MATCH (n:Industry {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Sector Nodes: {:,}".format(
                tx.run("MATCH (n:Sector {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Sector Group Nodes: {:,}".format(
                tx.run("MATCH (n:SectorGroup  {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Filer Nodes: {:,}".format(
                tx.run("MATCH (n:Filer {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Location Nodes: {:,}".format(
                tx.run("MATCH (n:Location {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Subdivision Nodes: {:,}".format(
                tx.run("MATCH (n:Subdivision {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch Country Nodes: {:,}".format(
                tx.run("MATCH (n:Country {source:'Corpwatch'}) RETURN COUNT(n)"
                       ).values()[0][0]))

        print("\tTotal Corpwatch Edges: {:,}".format(
                tx.run("MATCH (n1 {source:'Corpwatch'}) - [r] -> "
                       "(n2 {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch part_of(Company, Industry) Edges: {:,}".format(
                tx.run("MATCH (n1:Company {source:'Corpwatch'}) - [r:PART_OF] -> "
                       "(n2:Industry {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch part_of(Industry, Sector) Edges: {:,}".format(
                tx.run("MATCH (n1:Industry {source:'Corpwatch'}) - [r:PART_OF] -> "
                       "(n2:Sector {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch part_of(Sector, Sector Group) Edges: {:,}".format(
                tx.run("MATCH (n1:Sector {source:'Corpwatch'}) - [r:PART_OF] -> "
                       "(n2:SectorGroup {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch parent(Company, Company) Edges: {:,}".format(
                tx.run("MATCH (n1:Company {source:'Corpwatch'}) - [r:PARENT] -> "
                       "(n2:Company {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch filed(Filer, Company) Edges: {:,}".format(
                tx.run("MATCH (n1:Filer {source:'Corpwatch'}) - [r:FILED] -> "
                       "(n2:Company {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch located_at(Company, Location) Edges: {:,}".format(
                tx.run("MATCH (n1:Company {source:'Corpwatch'}) - [r:LOCATED_AT] -> "
                       "(n2:Location {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch located_at(Filer, Location) Edges: {:,}".format(
                tx.run("MATCH (n1:Filer {source:'Corpwatch'}) - [r:LOCATED_AT] -> "
                       "(n2:Location {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch is_in(Location, Subdivision) Edges: {:,}".format(
                tx.run("MATCH (n1:Location {source:'Corpwatch'}) - [r:IS_IN] -> "
                       "(n2:Subdivision {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))
        print("\t\tTotal Corpwatch is_in(Subdivision, Country) Edges: {:,}".format(
                tx.run("MATCH (n1:Subdivision {source:'Corpwatch'}) - [r:IS_IN] -> "
                       "(n2:Country {source:'Corpwatch'}) RETURN COUNT(r)"
                       ).values()[0][0]))  


with open("neo4j_creds.yaml", 'r') as stream:
    try:
        creds = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

print("Creating Constraints")
nim = Neo4jImporter(creds)
nim.exec_query(0)

print("Creating Industries")
chunks = pd.read_csv('./data/sic_codes.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(2, df)

print("Creating Sectors")
chunks = pd.read_csv('./data/sic_sectors.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(3, df.fillna(""))

print("Creating Countries")
chunks = pd.read_csv('./data/un_countries.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(4, df.fillna(0))

print("Creating Subdivisions")
chunks = pd.read_csv('./data/un_country_subdivisions.csv', sep='\t',
                     chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(5, df.fillna(0))

print("Creating Countries Aliases")
df = pd.read_csv('./data/un_country_aliases.csv', sep='\t')
nim.exec_query(6, df)

print("Creating Companies")
chunks = pd.read_csv('./data/company_info.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    df = df[df.most_recent == 1].fillna(0).reset_index(drop=True)
    nim.exec_query(1, df)

print("Creating Locations")
chunks = pd.read_csv('./data/company_locations.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    df = df[df.most_recent == 1].reset_index(drop=True)
    nim.exec_query(7, df.fillna(""))

print("Creating Filers")
chunks = pd.read_csv('./data/filers.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(8, df.fillna(""))

print("Creating Relationships")
chunks = pd.read_csv('./data/relationships.csv', sep='\t', chunksize=1000)
for i, df in enumerate(chunks):
    print("\tChunk {}".format(i))
    nim.exec_query(9, df)

nim.exec_query(10)    
