import json
import pandas as pd
import re
import os


class WikidataCleaner():

    def __init__(self,  files={}):

        self.claims = {'P1559': 'text', 'P1448': 'text', 'P6375': 'text',
                       'P569': 'time',  'P571': 'time',
                       'P2021': 'amount', 'P1128': 'amount',
                       'P2139': 'amount', 'P2295': 'amount',
                       'P2403': 'amount', 'P3362': 'amount',
                       'P571':  'time'}

        self.datasets = {"country": {"claims":  [],  "header":  ""},
                         "person": {"claims": ['P21', 'P106', 'P1559', 'P569',
                                               'P2021', 'P27', 'P19', 'P463',
                                               'P166'],
                                    "header":  ",gender,occupation,name,"
                                               "date_of_birth,erdos_number,"
                                               "CITIZENSHIP,PLACE_OF_BIRTH,"
                                               "MEMBER_OF,RECEIVED_GRANT"},
                         "grant": {"claims":  [],  "header":  ""},
                         "market": {"claims":  [],  "header":  ""},
                         "tradingvenue": {"claims":  [],  "header":  ""},
                         "industry": {"claims":  [],  "header":  ""},
                         "group": {"claims":  [],  "header":  ""},
                         "organizations": {"claims": ['P571', 'P856', 'P1448',
                                                      'P1128', 'P2139',
                                                      'P2295', 'P2403',
                                                      'P3362', 'P1329',
                                                      'P968', 'P625', 'P6375',
                                                      'P112', 'P169', 'P1037',
                                                      'P488', 'P3320', 'P414',
                                                      'P361', 'P452', 'P1830',
                                                      'P127', 'P749', 'P355',
                                                      'P463', 'P1889', 'P1366',
                                                      'P1365', 'P166', 'P17',
                                                      'P740', 'P281', 'P1056'],
                                           "header": ",inception,"
                                                     "official_website,"
                                                     "official_name,employees,"
                                                     "total_revenue,"
                                                     "net_profit,"
                                                     "total_assets,"
                                                     "operating_income,"
                                                     "phone_number,e_mail,"
                                                     "latitude,longitude,"
                                                     "address,FOUNDED_BY,"
                                                     "CHIEF_EXECUTIVE_OFFICER,"
                                                     "DIRECTOR,CHAIRPERSON,"
                                                     "BOARD_MEMBER,"
                                                     "IN_STOCK_EXCHANGE,"
                                                     "PART_OF,"
                                                     "IN_INDUSTRY,OWNER_OF,"
                                                     "OWNED_BY,"
                                                     "PARENT_ORGANIZATION,"
                                                     "SUBSIDIARY,MEMBER_OF,"
                                                     "DIFFERENT_FROM,"
                                                     "REPLACED_BY,REPLACES,"
                                                     "RECEIVED_GRANT,COUNTRY,"
                                                     "LOCATION_OF_FORMATION,"
                                                     "postal_code,PRODUCES"},
                         "product": {"claims":  ['P571', 'P275'],
                                      "header":  ",inception,license"},
                         }

        if not isinstance(files,  dict):
            raise ValueError("Please pass a dictionary as an argument for "
                             "files")
        for key in files.keys():
            if key not in self.datasets.keys():
                raise ValueError(key + " is not a valid Entity. "
                                 " Please choose one of the"
                                 " following: \n -country\n -person\n -grant\n"
                                 " -market\n -tradingvenue\n -industry\n"
                                 " -group\n -organizations\n -product\n")

        self.files = files

    def clean(self):
        for dataset in self.files.keys():
            no_lines = 0

            print("Cleaning ", dataset)

            with open(self.files[dataset],  'r') as f:
                dest_file = self.files[dataset].replace('filtered', 'cleaned')
                if self.files[dataset] == dest_file:
                    dest_file = self.files[dataset].replace('.', '_cleaned.')
                with open(dest_file,  'w') as f2:
                    f2.write(
                            "id,label,aliases,descriptions,labels{}\n".format(
                                    self.datasets[dataset]["header"]))
                    j_line = f.readline()
                    while j_line != "":
                        no_lines += 1
                        if no_lines % 10000 == 0:
                            print("\tLine {:,}".format(no_lines))
                        line = json.loads(j_line[: -2])

                        label = ""
                        if "en" in [pair["language"]
                                    for pair in line["labels"].values()]:

                            label = [pair["value"]
                                     for pair in line["labels"].values()
                                     if pair["language"] == "en"][0]
                        else:
                            labels = pd.Series(
                                    [pair["value"]
                                        for pair in line["labels"].values()])
                            if not labels.empty:
                                label = labels.groupby(labels).count().idxmax()

                        aliases = ';'.join([
                                pair["value"]
                                for l in line["aliases"].values()
                                for pair in l if pair["language"] == "en"])
                        descriptions = ';'.join([
                                pair["value"]
                                for pair in line["descriptions"].values()
                                if pair["language"] == "en"])
                        labels = ';'.join([pair["value"]
                                           for pair in line["labels"].values()
                                           if pair["language"] == "en"])

                        label = re.sub('\\\\"',  '"',  label)
                        label = re.sub('"',  '\\"',  label)
                        aliases = re.sub('"',  '\\"',  aliases)
                        descriptions = re.sub('"',  '\\"',  descriptions)
                        labels = re.sub('"',  '\\"',  labels)
                        f2.write('\"{}\",\"{}\",\"{}\",\"{}\",\"{}\"'.format(
                                line["id"], label, aliases, descriptions,
                                labels))

                        for claim_code in self.datasets[dataset]["claims"]:
                            f2.write(",")
                            if claim_code in line["claims"].keys():
                                if claim_code in ['P856', 'P281', 'P1329',
                                                  'P968']:
                                    output = '\"'+';'.join(
                                      [claim['mainsnak']['datavalue']['value']
                                       for claim in line["claims"][claim_code]
                                       if 'datavalue' in (
                                            claim['mainsnak']).keys()])+'\"'
                                elif claim_code in ['P625']:
                                    if 'datavalue' in (line["claims"]
                                                       [claim_code][0]
                                                       ['mainsnak']).keys():
                                        output = '\"'+str(
                                                line["claims"][claim_code]
                                                [0]['mainsnak']
                                                ['datavalue']['value']
                                                ['latitude'])+'\",\"'+str(
                                                line["claims"][claim_code][0]
                                                ['mainsnak']['datavalue']
                                                ['value']['longitude'])+'\"'
                                elif claim_code in self.claims.keys():
                                    output = ';'.join([claim['mainsnak']
                                                      ['datavalue']['value']
                                                      [self.claims[claim_code]]
                                                      for claim in
                                                      line["claims"]
                                                      [claim_code]
                                                      if 'datavalue' in (
                                                      claim['mainsnak']
                                                      ).keys()])
                                    output = '\"'+re.sub('"',  '\\"',
                                                         output)+'\"'
                                else:
                                    output = '\"'+';'.join([claim['mainsnak']
                                                            ['datavalue']
                                                            ['value']["id"]
                                                            for claim
                                                            in line["claims"]
                                                            [claim_code]
                                                            if 'datavalue' in (
                                                        claim['mainsnak']
                                                        ).keys()])+'\"'
                                f2.write(output)
                            else:
                                if claim_code in ['P625']:
                                    f2.write(",")
                        f2.write("\n")
                        j_line = f.readline()
