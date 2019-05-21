
from numpy import nan
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
                and self.graph.nodes[key]['source'] == 'Corpwatch']

    def __get_edges_ids(self, attribute, value):
        return [key for key in self.graph.edges()
                if self.graph.edge[key][attribute] == value
                and self.graph.edges[key]['source'] == 'Corpwatch']

    def __get_nodes_statistics(self, val, choice=0):
        if choice == 0:
            self.no_nodes = Counter([self.graph.nodes[key]['nlabel']
                                    for key in self.graph.nodes()
                                    if 'nlabel' in self.graph.nodes[key].keys()
                                    and 'source' in self.graph.nodes[key].keys()
                                    and self.graph.nodes[key]['source'] == 'Corpwatch'                                        
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
                                and self.graph.edges[edge]['source'] == 'Corpwatch'                                
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

    def create_companies(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_C_{}".format(row["cw_id"]),
                                cw_id=row["cw_id"], nlabel="Company",
                                latest_year=row["year"], cik=row["cik"],
                                irs_number=row["irs_number"],
                                no_parents=row["num_parents"],
                                no_children=row["num_children"],
                                top_parent=row["top_parent_id"],
                                company_name=row["company_name"],
                                source='Corpwatch')

            if not isNaN(row["sic_code"]):
                self.graph.add_node("CW_I_{}".format(int(row["sic_code"])),
                                    nlabel='Industry', source='Corpwatch')
                self.graph.add_edge("CW_C_{}".format(row["cw_id"]),
                                    "CW_I_{}".format(int(row["sic_code"])),
                                    elabel='PART_OF', source='Corpwatch')

    def create_industries(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_I_{}".format(row["sic_code"]),
                                sic_code=row["sic_code"], nlabel='Industry',
                                name=row["industry_name"], source='Corpwatch')
            self.graph.add_node("CW_S_{}".format(row["sic_sector"]),
                                nlabel='Sector', source='Corpwatch')
            self.graph.add_edge("CW_I_{}".format(row["sic_code"]),
                                "CW_S_{}".format(row["sic_sector"]),
                                elabel='PART_OF', source='Corpwatch')

    def create_sectors(self, df):
        for index, row in df.iterrows():

            self.graph.add_node("CW_S_{}".format(row["sic_sector"]),
                                nlabel='Sector', sic_sector=row["sic_sector"],
                                name=row["sector_name"], source='Corpwatch')
            self.graph.add_node("CW_SG_{}".format(row["sector_group"]),
                                nlabel='SectorGroup',
                                name=row["sector_group_name"],
                                sector_group=row["sector_group"],
                                source='Corpwatch')
            self.graph.add_edge("CW_S_{}".format(row["sic_sector"]),
                                "CW_SG_{}".format(row["sector_group"]),
                                elabel='PART_OF', source='Corpwatch')

    def create_countries(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_CT_{}".format(row["country_code"]),
                                nlabel='Country',
                                country_code=row["country_code"],
                                country_name=row["country_name"],
                                latitude=row["latitude"],
                                longitude=row["longitude"], source='Corpwatch')

    def create_subdivisions(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_SD_{}_{}".format(row["country_code"],
                                row["subdivision_code"]),
                                nlabel='Subdivision',
                                subdivision_code="{}_{}".format(
                                        row["country_code"],
                                        row["subdivision_code"]),
                                name=row["subdivision_name"],
                                latitude=row["latitude"],
                                longitude=row["longitude"], source='Corpwatch')

            self.graph.add_node("CW_CT_{}".format(row["country_code"]),
                                nlabel='Country', source='Corpwatch')
            self.graph.add_edge("CW_SD_{}_{}".format(row["country_code"],
                                row["subdivision_code"]),
                                "CW_CT_{}".format(row["country_code"]),
                                elabel='IS_IN', source='Corpwatch')

    def create_countries_aliases(self, df):
        df = pd.DataFrame(df.groupby('country_code').country_name.agg(
                lambda x: set(x))).reset_index(level=0)
        for index, row in df.iterrows():
            if not isNaN(row["country_name"]):
                self.graph.add_node("CW_CT_{}".format(row["country_code"]),
                                    alias=row["country_name"])

    def create_locations(self, df):
        for index, row in df.iterrows():
            lat, long = self.__find_coords(row)
            self.graph.add_node("CW_L_{}".format(row["street_1"]),
                                nlabel='Location', street_1=row["street_1"],
                                street_2=row["street_2"], city=row["city"],
                                state=row["state"],
                                postal_code=row["postal_code"],
                                latitude=lat, longitude=long,
                                source='Corpwatch')
            self.graph.add_node("CW_C_{}".format(row["cw_id"]),
                                nlabel='Company', source='Corpwatch')
            self.graph.add_edge("CW_L_{}".format(row["street_1"]),
                                "CW_C_{}".format(row["cw_id"]),
                                elabel='LOCATED_AT', type=row['type'],
                                source='Corpwatch')

            if not(isNaN(row["country_code"]) and isNaN(row["subdiv_code"])):
                self.graph.add_node("CW_SD_{}_{}".format(row["country_code"],
                                                         row["subdiv_code"]),
                                    nlabel='Subdivision', source='Corpwatch')
                self.graph.add_edge("CW_L_{}".format(row["street_1"]),
                                    "CW_SD_{}_{}".format(row["country_code"],
                                                         row["subdiv_code"]),
                                    elabel='IS_IN', source='Corpwatch')

    def create_filers(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_F_{}".format(row["cik"]), nlabel='Filer',
                                cik=row["cik"], cw_id=row["cw_id"],
                                business_phone=row["business_phone"],
                                match_name=row["match_name"],
                                conformed_name=row["conformed_name"],
                                irs_number=row["irs_number"],
                                source='Corpwatch')
            if not isNaN(row["business_street_1"]):
                lat, long = self.__find_coords(row, "business_")
                self.graph.add_node("CW_L_{}".format(row["business_street_1"]),
                                    nlabel='Location',
                                    street_1=row["business_street_1"],
                                    street_2=row["business_street_2"],
                                    city=row["business_city"],
                                    state=row["business_state"],
                                    postal_code=row["business_zip"],
                                    latitude=lat, longitude=long,
                                    source='Corpwatch')
                self.graph.add_edge("CW_F_{}".format(row["cik"]),
                                    "CW_L_{}".format(row["business_street_1"]),
                                    elabel='LOCATED_AT', type='business',
                                    source='Corpwatch')
            if not isNaN(row["mail_street_1"]):
                lat, long = self.__find_coords(row, "mail_")
                self.graph.add_node("CW_L_{}".format(row["mail_street_1"]),
                                    nlabel='Location',
                                    street_1=row["mail_street_1"],
                                    street_2=row["mail_street_2"],
                                    city=row["mail_city"],
                                    state=row["mail_state"],
                                    postal_code=row["mail_zip"],
                                    latitude=lat, longitude=long,
                                    source='Corpwatch')
                self.graph.add_edge("CW_F_{}".format(row["cik"]),
                                    "CW_L_{}".format(row["mail_street_1"]),
                                    elabel='LOCATED_AT', type='mail',
                                    source='Corpwatch')

    def create_relationships(self, df):
        for index, row in df.iterrows():
            self.graph.add_node("CW_F_{}".format(int(row["filer_cik"])),
                                nlabel='Filer', source='Corpwatch')
            self.graph.add_node("CW_C_{}".format(row["cw_id"]),
                                nlabel="Company", source='Corpwatch')
            self.graph.add_edge("CW_F_{}".format(int(row["filer_cik"])),
                                "CW_C_{}".format(row["cw_id"]),
                                elabel='FILED', filing_id=row["filing_id"],
                                source='Corpwatch')

            if not isNaN(row["parent_cw_id"]):
                self.graph.add_node("CW_C_{}".format(row["parent_cw_id"]),
                                    nlabel="Company", source='Corpwatch')
                self.graph.add_edge("CW_C_{}".format(row["parent_cw_id"]),
                                    "CW_C_{}".format(row["cw_id"]),
                                    elabel='PARENT',
                                    filing_id=row["filing_id"],
                                    source='Corpwatch')

    def __find_coords(self, row, prefix=""):
        if prefix+'latitude' in row.index:
            return (row[prefix+'latitude'], row[prefix+'longitude'])
        return (nan, nan)

    def print_statistics(self):
        print("Statistics:")
        print("\tTotal Corpwatch Nodes: {:,}".format(
                self.graph.number_of_nodes()))

        nodes = self.__get_nodes_values('nlabel')
        for i, node in enumerate(nodes):
            print("\t\tCorpwatch {} Nodes: {:,}".format(node,
                            self.__get_nodes_statistics(node, i)))

        print("\tTotal Corpwatch Edges: {:,}".format(
                self.graph.number_of_edges()))

        edges = self.__get_edges_values('elabel')
        for i, (elabel, nlabel1, nlabel2) in enumerate(edges):
            print("\t\tCorpwatch {}({},{}) Edges: {:,}".format(elabel,
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
