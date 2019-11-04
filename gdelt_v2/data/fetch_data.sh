wget -nv http://data.gdeltproject.org/gdeltv2/masterfilelist.txt

for File in $(cat masterfilelist.txt | grep '/'$1 | grep 'gkg' |  awk '{ print $3 }')
do
wget -nv $File
sleep 2
done

for File in $(ls *.zip)
do
unzip $File
rm $File
done

cat *.csv >> $1"_raw.txt"

rm masterfilelist.txt
rm *.csv
