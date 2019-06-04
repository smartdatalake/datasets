import pandas as pd
import yaml
from neo4j import GraphDatabase, exceptions
import geocoder
from time import time, sleep


def print_stats(session):
    c_nodes = session.run("MATCH (n:Location {source:'Corpwatch'}) "
                          "WHERE EXISTS(n.street_1) AND EXISTS(n.latitude)"
                          " RETURN COUNT(n)").values()[0][0]
    u_nodes = session.run("MATCH (n:Location {source:'Corpwatch'}) "
                          "WHERE EXISTS(n.street_1) AND NOT EXISTS(n.latitude)"
                          " RETURN COUNT(n)").values()[0][0]
    print("Nodes of Corpwatch with coordinates: {:,} "
          "and without coordinates {:,}".format(c_nodes, u_nodes))


with open("../util/neo4j_creds.yaml", 'r') as stream:
    try:
        creds = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
    driver = GraphDatabase.driver(creds["uri"], auth=(creds["user"],
                                  creds["password"]))
    session = driver.session()
    print_stats(session)

    step = 100
    limit = 20000

    df = pd.DataFrame(
            session.run("MATCH (n:Location {source:'Corpwatch'})  "
                        "WHERE EXISTS(n.street_1) AND NOT EXISTS(n.latitude) "
                        "RETURN n.id as id, n.street_1 as street, "
                        "n.city as city, n.postal_code as pcode "
                        "LIMIT {}".format(limit)).data()).set_index('id')

    df.fillna("", inplace=True)
    df['address'] = df.street + ' ' + df.city + ' ' + df.pcode
    df.address = df.address.str.replace('_', ' ')
    df = df.address

    total = 0
    p_set = 0
    no_null = 0
    for i, (index, row) in enumerate(df.iteritems()):
        if i % step == 0:
            total += int(p_set/2)
            print("\tRow {:,} ({:,}): Set coords for total {:,} nodes. "
                  "True: {} Null: {}".format(i, df.shape[0], total,
                                             int(p_set/2)-no_null, no_null))
            p_set = 0
            no_null = 0

        j = geocoder.osm(row).json
        if j is None:
            j = {'lat': 0.0, 'lng': 0.0}
            no_null += 1

        q = "MERGE (n:Location {{id:'{}', source:'Corpwatch'}}) SET "\
            "n.latitude={}, n.longitude={}".format(index, j['lat'], j['lng'])
        p_set += session.run(q).summary().counters.properties_set
        sleep(1)

    print_stats(session)
    driver.close()
