# Wikidata Dataset

## Overview

This page contains instructions and code for producing a company graph from [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page).

## Instructions

**Step 1.** Download a JSON dump from [here](https://www.wikidata.org/wiki/Wikidata:Database_download).

**Step 2.** Use the [wdtaxonomy](https://wdtaxonomy.readthedocs.io/en/latest/) tool to identify relevant types of entities (i.e., taxonomy classes). The selected ones are shown in the following table:

Entity Type | Wikidata Taxonomy ID | Include Descendants
| --- | --- | --- | --- |
| Country | Q6256 (Country) | No |
| Grant | Q230788 (Grant) | Yes |
| Group | Q16887380 (Group) | No |
| Industry | Q8148 (Industry) | Yes |
| Stock Exchange | Q37654 (Market) & Q43371537 (Trading Venue) | Yes |
| Organization | Q43229 (Organization) | Yes |
| Person | Q5 (Human) | No |
| Product | Q2424752 (Product) | Yes |

**Step 3.** Run the script `collect_ids.sh` to create lists of IDs for the relevant classes to be used for filtering.

**Step 4.** Use the `WikidataFilter` class in the script `wikidata_filter.py` to filter the lines of the original dump into separate files for each entity type. Specify that filtering is done by `type` and provide the files that contain the Ids of the relevant classes, produced in the previous step. Separate files, corresponding to each entity type, will be created, containg the filtered records from the original dump. This procedure is executed by calling the `filter` method, as indicated below:

```
from wikidata_filter import WikidataFilter

wf = WikidataFilter("type", files=['country.txt','grant.txt','group.txt','industry.txt','market.txt','organizations.txt','person.txt','product.txt','trading_venue.txt'])
temp = wf.filter(10000)
```

**Step 5.** Use the `WikidataCleaner` class in the `wikidata_cleaner.py` to extract all the necessary information from the original JSON dump and export it in CSV format to facilitate further processing. This is done by passing a dictionary indicating the entity types to be extracted and the corresponding files, as shown below:

```
from wikidata_cleaner import WikidataCleaner

wc = WikidataCleaner({"market": "market.txt"})
wc.clean()
```

**Step 6.** This step imports the data into a Neo4j database, by executing the script `wd_import.py`. This first creates entities of type *Organization* with all their links (just nodes with ids and edges). Following that, all the files concerning those nodes are imported to add their information. Finally, the file concerning entities of type *Person* is read to create its links, while parsing those files as well. In each step, the statistics of the graph are printed, thus allowing to find which nodes do not have their information integrated, in order to feed the subsequent step.

**Step 7.** TODO

## Data description

The figure below depicts the schema of the produced graph.

![alt text](https://github.com/smartdatalake/datasets/blob/master/wikidata/Wikidata_Schema.png "Wikidata Schema")

The following table shows the number of graph nodes and edges for each type:

| Node | Number |
| --- | --- |
| Organization |  |
| Person |  |
| StockExchange |  |
| Group | |
| Industry | |
| Location | |
| Grant | |
| Country | |
| Product | |
| **Total** | ** **|

| Edge | Number |
| --- | --- |
| founded_by(Organization,Person) | |
| chief_executive_officer(Organization,Person) | |
| director(Organization,Person) | |
| chairperson(Organization,Person) | |
| board_member(Organization,Person) | |
| owner_of(Organization,Organization) | |
| parent_organization(Organization,Organization) | |
| subsidiary(Organization,Organization) | |
| member_of(Organization,Organization) | |
| different_from(Organization,Organization) | |
| replaced_by(Organization,Organization) | |
| replaces(Organization,Organization) | |
| owned_by(Organization,Owner) | |
| in_stock_exchange(Organization,StockExchange) | |
| part_of(Organization,Group) | |
| in_industry(Organization,Industry) | |
| received_grant(Organization,Grant) | |
| location_of_formation(Organization,Location) | |
| country(Organization,Country) | |
| produces(Organization,Product) | |
| member_of(Person,Organization) | |
| received_grant(Person,Grant) | |
| place_of_birth(Person,Location) | |
| citizenship(Person,Country) | |
| **Total** | ** **|
