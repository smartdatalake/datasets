import pandas as pd
import networkx as nx
from util.networkx_importer import NetworkxImporter
import yaml
from neo4j import GraphDatabase, exceptions
import py_stringmatching as sm
import py_stringsimjoin as ssj
from scipy.spatial import distance
from sklearn.cluster import KMeans
import re


def isNaN(s):
    return s != s


class GDELT_NetworkxImporter(NetworkxImporter):

    def __init__(self):
        NetworkxImporter.__init__(self, 'GDELT')
        with open("../util/neo4j_creds.yaml", 'r') as stream:
            try:
                creds = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
            self._driver = GraphDatabase.driver(creds["uri"],
                                                auth=(creds["user"],
                                                      creds["password"]))
            self.session = self._driver.session()

    def close(self):
        self._driver.close()

    # locations

    def fetch_locations(self):
        return pd.DataFrame(self.session.run(
                "MATCH (n:Location {source:'Corpwatch'}) "
                "WHERE EXISTS(n.latitude) "
                "RETURN n.id as id, n.latitude as lat, n.longitude as lng"
                ).data()).set_index('id')

    def filter_similar_locations(self, A, B, lim, opt):
        C = []
        if opt:
            n_clusters = int(B.shape[0] * 0.1)
            km = KMeans(n_clusters=n_clusters, random_state=1924)
            X = km.fit_predict(B)
            for index, a in A.iteritems():
                keep = False
                Y = pd.Series(km.predict(a))
                for index1, row1 in enumerate(a):
                    for index2, row2 in B[X == Y[index1]].iterrows():
                        if distance.euclidean(row1, row2) < lim:
                            C += [index]
                            keep = True
                            break
                    if keep:
                        break
        else:
            for index, a in A.iteritems():
                keep = False
                for index1, row1 in enumerate(a):
                    for index2, row2 in B.iterrows():
                        if distance.euclidean(row1, row2) < lim:
                            C += [index]
                            keep = True
                            break
                    if keep:
                        break
        return set(C)

    def filter_locations(self, df, lim, opt):
        A = df.ENHANCEDLOCATIONS.dropna().apply(lambda x: [
                y.split('#')[5:7] for y in x.split(';')])
        A = A.apply(lambda x: [[float(z) for z in y] for y in x])

        B = self.fetch_locations()

        return self.filter_similar_locations(A, B, lim, opt)

    # Person

    def fetch_person(self):
        return pd.DataFrame(self.session.run(
                "MATCH (n:Person {source:'Wikidata'}) WHERE EXISTS(n.label) "
                "RETURN n.id as id, n.label as name").data()
                )

    def filter_person(self, df, lim):
        A = df.ENHANCEDPERSONS.dropna().apply(lambda x: list(set([
                y.split(',')[0].lower() for y in x.split(';')])))
        A = A.apply(pd.Series).stack()
        A.index = A.index.map(lambda i: "{}_{}".format(i[0], i[1]))
        A = A.reset_index()
        A.columns = ['id', 'name']

        B = self.fetch_person()
        B.name = B.name.str.replace(r'_+', ' ').str.lower()

        qg3_tok = sm.QgramTokenizer(qval=3)
        C = ssj.jaccard_join(A, B, 'id', 'id', 'name', 'name', qg3_tok, lim,
                             l_out_attrs=['name'], r_out_attrs=['name'],
                             show_progress=False)

        return set(C.l_id.apply(lambda x: int(x.split("_")[0])))

    # Organization

    def fetch_organization(self):
        A = pd.DataFrame(self.session.run(
                "MATCH (n:Company {source:'Corpwatch'}) "
                "RETURN n.id as id, n.company_name as name").data()
                )

        B = pd.DataFrame(self.session.run(
                "MATCH (n:Organization {source:'Wikidata'}) "
                "WHERE EXISTS(n.label) "
                "RETURN n.id as id, n.label as name").data()
                )
        return pd.concat([A, B]).reset_index(drop=True)

    def filter_organization(self, df, lim):
        A = df.ENHANCEDORGANIZATIONS.dropna().apply(lambda x: list(set([
                y.split(',')[0].lower() for y in x.split(';')])))
        A = A.apply(pd.Series).stack()
        A.index = A.index.map(lambda i: "{}_{}".format(i[0], i[1]))
        A = A.reset_index()
        A.columns = ['id', 'name']

        B = self.fetch_organization()
        B.name = B.name.str.replace(r'_+', ' ').str.lower()

        qg3_tok = sm.QgramTokenizer(qval=3)
        C = ssj.jaccard_join(A, B, 'id', 'id', 'name', 'name', qg3_tok, lim,
                             l_out_attrs=['name'], r_out_attrs=['name'],
                             show_progress=False)

        return set(C.l_id.apply(lambda x: int(x.split("_")[0])))

    def filter_df(self, df, filter_lim):
        (lim, filters, opt) = filter_lim
        C1 = set()
        C2 = set()
        C3 = set()
        if re.search('1..', filters):
            print('\t\tFiltering Locations')
            C1 = self.filter_locations(df, lim, opt)
        if re.search('.1.', filters):
            print('\t\tFiltering Person')
            C2 = self.filter_person(df, lim)
        if re.search('..1', filters):
            print('\t\tFiltering Organization')
            C3 = self.filter_organization(df, lim)
        return list(C1 | C2 | C3)

    def create_graph(self, df, filter_lim=None):
        if filter_lim is not None:
            print('\tFiltering DataFrame')
            ind = self.filter_df(df, filter_lim)
            print("{} rows passed out of {}".format(len(ind), df.shape[0]))
            df = df.loc[ind, :]

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

