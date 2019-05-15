from wikidata_filter import WikidataFilter

wf = WikidataFilter("type", files=['./data/country.txt',
                                   './data/grant.txt',
                                   './data/group.txt',
                                   './data/industry.txt',
                                   './data/market.txt',
                                   './data/organizations.txt',
                                   './data/person.txt',
                                   './data/product.txt',
                                   './data/tradingvenue.txt'])
wf.filter(10000)
