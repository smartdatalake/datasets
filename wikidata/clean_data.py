from wikidata_cleaner import WikidataCleaner
import os

files = {file.split("_")[0]: './data/'+file for file in os.listdir('./data/')
         if file.endswith("filtered.txt")}

wc = WikidataCleaner(files)
wc.clean()
