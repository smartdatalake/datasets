echo 'Collecting organization ids'
wdtaxonomy Q43229 | grep -oh 'Q[0-9]\+' > ./data/organizations.txt
echo 'Collecting industry ids'
wdtaxonomy Q8148  | grep -oh 'Q[0-9]\+' > ./data/industry.txt
echo 'Collecting market ids'
wdtaxonomy Q37654 | grep -oh 'Q[0-9]\+' > ./data/market.txt
echo 'Collecting trading_venue ids'
wdtaxonomy Q43371537 | grep -oh 'Q[0-9]\+' > ./data/tradingvenue.txt
echo 'Collecting product ids'
wdtaxonomy Q2424752 | grep -oh 'Q[0-9]\+' > ./data/product.txt
echo 'Collecting grant ids'
wdtaxonomy Q230788 | grep -oh 'Q[0-9]\+' > ./data/grant.txt

