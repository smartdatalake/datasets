wget http://data.gdeltproject.org/gdeltv2/masterfilelist.txt

for File in $(cat masterfilelist.txt | grep '/201801' | grep 'gkg' |  awk '{ print $3 }')
do
wget $File
done

for File in $(ls *.zip)
do
unzip $File
rm $File
done

cat *.csv >> total.txt

rm masterfilelist.txt
rm *.csv
