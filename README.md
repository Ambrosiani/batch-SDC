## About This Repository
This repository contains a Pywikibot-based Python3 script used to write structured data on Wikimedia Commons (SDC). 

### Additional Reading:
* The underlying structure is based on this [blog post](https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python) by Albin Larsson.

## Requirements

To run it you will have to install dependencies using:
`pip install -r requirements.txt`

## User Account

The script uses **Pywikibot** and expects to find a username in a `user-config.py` file.

## Features
- Currently supported datatypes are `wikibase-item` (Wikidata item) and `string`.
- If the target file already contains a statement with the same value as provided (regardless of the content of any qualifiers), a duplicate statement will **not** be created.
- Multiple statements are [grouped in one edit](https://commons.wikimedia.org/w/index.php?title=File%3ATest.pdf&type=revision&diff=520547355&oldid=520541181).

## Data

Data is read from a CSV file:

````
python3 app.py --data data.csv
````

The data is to be structured like this:

````
Filename,Caption|sv,Caption|en,P180,P217|P195
Test.pdf,beskrivning på svenska,caption in english,Q147,NMA.0096620-03|Q1142142
````

The file can be prepared using software of your choice, such as OpenRefine or a spreadsheet, for convenient tabular display:

| Filename      |Caption\|sv            |Caption\|en       |P180 |P217\|P195              |
| --------------|-----------------------|------------------|-----|------------------------|
| Test.pdf      | beskrivning på svenska|caption in english|Q147 |NMA.0096620-03\|Q1142142|

This will add the following statements:
- Caption _beskrivning på svenska_ in **Swedish**
- Catpion _caption in english_ in **English**
- [Depicts](https://www.wikidata.org/wiki/Property:P180) → [kitten](https://www.wikidata.org/wiki/Q147)
- [Inventory number](https://www.wikidata.org/wiki/Property:P217) → NMA.0096620-03
  - With qualifier [Collection](https://www.wikidata.org/wiki/Property:P195) → [Nordic Museum](https://www.wikidata.org/wiki/Q1142142)
  