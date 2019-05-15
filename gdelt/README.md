# GDELT Articles Graph

## Overview

This page provides instructions and source code for producing a graph of news articles and associated information about mentioned organizations and persons from data obtained from the [GDELT](https://www.gdeltproject.org/) project.

## Instructions

There are two ways to import data from GDELT:

**A)** Run the script `import_data_from_url.py`, which downloads the list of all available files and the user can then select which ones to fetch. Indicatively, we have downloaded data from the 3rd week (15.Jan - 21.Jan) of 2018. Then, the data is imported into a [NetworkX](https://networkx.github.io/) graph via the NetworkxImporter class, found in the `gdelt_networkx.py` module.

**B)** Run the script `import_data_from_file.py`, where all the data has been already fetched and stored locally. This is done by using a bash script, `fetch_data.sh`. Afterwards, the data is imported into a [NetworkX](https://networkx.github.io/) graph as in the previous case, via the NetworkxImporter.


## Data description

The figure below depicts the schema of the produced graph.

![alt text](GDELT_Schema.png)

The following table shows the number of graph nodes and edges for each type:
(*NOTE* We took a sample of 1,553,626 Articles that were stored during the 15.Jan-21.Jan 2018)

| Node | Number |
| --- | --- |
| Article | 1,426,386 |
| Person | 260,843 |
| Organization | 174,042 |
| Theme | 5,297 |
| Location | 91,172 |
| **Total** | **1,957,740** |

| Edge | Number |
| --- | --- |
| mentions(Article, Person) | 1,247,059 |
| mentions(Article, Organization) | 1,183,760 |
| is_about(Article, Theme) | 1,394,215 |
| mentions(Article, Location) | 13,753,271 |
| **Total** | **17,578,305** |

More information about the GDELT data can be found [here](http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf).




