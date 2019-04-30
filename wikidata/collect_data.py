from wikidata_filter import WikidataFilter

wf = WikidataFilter("type", files=['../data/1_ids/country.txt',
                                  '../data/1_ids/grant.txt',
                                  '../data/1_ids/group.txt',
                                  '../data/1_ids/industry.txt',
                                  '../data/1_ids/market.txt',
                                  '../data/1_ids/organizations.txt',
                                  '../data/1_ids/person.txt',
                                  '../data/1_ids/product.txt',
                                  '../data/1_ids/trading_venue.txt'])
wf.filter(10000)
