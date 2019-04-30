# CorpWatch Dataset

## Overview

This page contains instructions and code for producing a company graph from [CorpWatch](https://corpwatch.org/) data.

## Instructions

**Step 1.** Download the "Dump of entire API database" in CSV format from [here](http://api.corpwatch.org/).

**Step 2.** Run the script `cw_import.py` to create the graph and import it into a Neo4j database.

## Data description

The figure below depicts the schema of the produced graph.

![alt text](https://github.com/smartdatalake/datasets/blob/master/corpwatch/Corpwatch_Schema.png "Corpwatch Schema")

The following table shows the number of graph nodes and edges for each type:

| Node | Number |
| --- | --- |
| Company | 1,089,047 |
| Industry | 484 |
| Sector | 83 |
| Sector Group | 8 |
| Filer | 1,431,398 |
| Location | 9,454,302 |
| Subdivision | 967 |
| Country | 244 |
| **Total** | 11,976,533 |

| Edge | Number |
| --- | --- |
| part_of(Company, Industry) | 44,522 |
| part_of(Industry, Sector) | 484 |
| part_of(Sector, Sector Group) | 83 |
| parent(Company, Company) | 2,867,135 |
| filed(Filer, Company) | |
| located_at(Company, Location) | |
| located_at(Filer, Location) | 5,727,592 |
| is_in(Location, Subdivision) | 3,032,015 |
| is_in(Subdivision, Country) | 967 |
| **Total** | 11,672,798 |

For more information about the CorpWatch data please visit [this page](http://api.corpwatch.org/documentation/faq.html).




