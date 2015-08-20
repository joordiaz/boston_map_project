# Module for Boston OpenStreet Map Project
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import codecs
import json

"""
Create a dictionary with the tags in the xml file, where keys are tags and values
are the number of times each tag appears.
"""
def count_tags(filename):
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag not in d:
            d[elem.tag] = 1
        else:
            d[elem.tag] = d[elem.tag] + 1
    return d


"""
Count the type of keys.
There are 3 types of keys described by the regex below
"""
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        if re.search(lower,element.attrib['k']):
            keys["lower"] = keys["lower"] + 1
        elif re.search(lower_colon,element.attrib['k']):
            keys["lower_colon"] = keys["lower_colon"] + 1
        elif re.search(problemchars,element.attrib['k']):
            keys["problemchars"] = keys["problemchars"] + 1
        else:
            keys["other"] = keys["other"] + 1
        
    return keys

def process_tag_keys(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

def audit_lowerkey(filename):
    d = {}
    capital = {}
    for _, element in ET.iterparse(filename):
        if element.tag == "tag":
            k = element.attrib['k']
            if re.search(lower,k):
                if k not in d:
                    d[k] = 1
            elif k.lower() in d:
                if k not in capital:
                    capital[k] = 1
                else:
                    capital[k] += 1

    return capital


def count_tag_attributes(filename, tag):
    """ Count the all the attributes that appear for a given tag """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == tag:
            for key in elem.attrib.keys():
                if key not in d:
                    d[key] = 1
                else:
                    d[key] = d[key] + 1
    return d


def count_tag_keys(filename):
    """ count all keys that appear for tag "tag" """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == "tag":
            key = elem.attrib['k']
            if key not in d:
                    d[key] = 1
            else:
                d[key] = d[key] + 1
    return d


# Regular expression of valid zipcodes
five_digit_zipcode = re.compile(r'^\d{5}$')
complete_zipcode = re.compile(r'^\d{5}(?:[-\s]\d{4})?$')

def get_invalid_zipcodes(filename):
    """ Get a dictionary with counts of invalid zipcodes  """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == "tag":
            key = elem.attrib['k']
            if key == 'addr:postcode':
                zipcode = elem.attrib['v']
                if not five_digit_zipcode.match(zipcode) and not complete_zipcode.match(zipcode):
                    if zipcode not in d:
                        d[zipcode] = 1
                    else:
                        d[zipcode] = d[zipcode] + 1
    return d

#get all zipcodes
def get_zipcodes(filename):
    """ Get a dictionary of counts for all zipcodes  """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == "tag":
            key = elem.attrib['k']
            if key == 'addr:postcode':
                zipcode = elem.attrib['v']
                if zipcode not in d:
                    d[zipcode] = 1
                else:
                    d[zipcode] = d[zipcode] + 1
    return d

def count_child_tags(filename,tag):
    """  Count the tags of childs of a given tag  """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == tag:
            for child in elem:
                if child.tag not in d:
                    d[child.tag] = 1
                else:
                    d[child.tag] = d[child.tag] + 1
    return d

def count_nd_in_way(filename):
    """ Count how many nd tags appear in way """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == "way":
            count = 0
            for child in elem:
                if child.tag == "nd":
                    count += 1
            if count not in d:
                d[count] = 1
            else:
                d[count] = d[count] + 1
    return d


# street names
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Highway", "Way"]

mapping = { "Ave": "Avenue",
            "Ave.": "Avenue",
            "ct": "Court",
            "Hwy": "Highway",
            "Pkwy": "Parkway",
            "Pl": "Place",
            "Rd": "Road",
            "ST": "Street",
            "Sq": "Square",
            "St": "Street",
            "St,": "Street",
            "St.": "Street",
            "Street.": "Street",
            "ave": "Avenue",
            "avenue": "Avenue",
            "place": "Place",
            "rd.": "Road",
            "st": "Street",
            "street": "Street"
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected_street_types:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def process_street_type(osmfile):
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

    return street_types


# cound addr: tags
def count_addr_tags(filename):
    """  Count the different types of addr: tags """
    d = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag == "tag":
            if "k" in elem.attrib:
                k = elem.attrib["k"]
                if k.startswith("addr:"):
                    if k not in d:
                        d[k] = 1
                    else:
                        d[k] += 1
    return d

# process street name
def process_street_name(name):
    new_name = name
    match = street_type_re.search(name)
    if match:
        street_type = match.group()
        if street_type in mapping:
            new_name = re.sub(street_type,mapping[street_type],name)
    return new_name

# Process the map and write to a JSON file
def audit_addr_key(k):
    """
    input:
        k is strings
    function:
        check if k starts with "addr:" and, if so, only contains one colon.
    returns:
        valid_addr if k is a valid address
        field is the string following "addr:" 
    """
    valid_addr = False
    field = ''

    match = re.match(r'addr:(\w+)$',k)
    if match:
        valid_addr = True
        field = match.group(1)

    return valid_addr, field 

# See process_map for fixes implemented in this function.
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :

        node["id"] = element.attrib["id"]
        node["type"] = element.tag
        if "visible" in element.attrib.keys():
            node["visible"] = element.attrib["visible"]

        # add a "created" dictionary
        created = {}
        created["version"] = element.attrib["version"]
        created["changeset"] = element.attrib["changeset"]
        created["timestamp"] =element.attrib["timestamp"]
        created["user"] = element.attrib["user"]
        created["uid"] = element.attrib["uid"]
        node["created"] = created

        # add latitud and longitud to a a position array of floats.
        if "lat" in element.attrib.keys():
            pos = [float(element.attrib["lat"]),float(element.attrib["lon"])]
            node["pos"] = pos

        # process "tag" tags
        address = {}
        for tag in element.iter("tag"):
            k = tag.attrib["k"]
            # Drop problematic keys
            if problemchars.search(k):
                continue
            # if k matches addr: and the rest has no extra ":""
            # then we add a new element to the address dictionary
            if k.startswith("addr:"):
                valid_addr, field = audit_addr_key(k)
                if valid_addr:
                    # if k is addr:street, convert to proper street types
                    if field == "street":
                        street_name = process_street_name(tag.attrib["v"])
                        address["street"] = street_name
                    else:
                        address[field] = tag.attrib["v"]
                else:
                    continue
            else:
                node[k] = tag.attrib["v"]

        if address:
            node["address"] = address
            
        # proces "nd" tags
        node_refs = []
        for nd in element.iter("nd"):
            node_refs.append(nd.attrib["ref"])

        if node_refs:
            node["node_refs"] =  node_refs
            
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    """
    Process_map takes in an xml file a produces a json file with a clean dataset.
    Fixes performed are:
    - Convert location information (longitud and latitud) into an array of floats with 2 elements. This is used for geospacial indexing.
    - Create an address record that is nested inside the the overall record. The address record contains fields like: city, street, state, etc...
    - Create a "created" record (dictionary) that contains information about the record creation such as "time" and "user"
    - If second level tag "k" value contains problematic characters, it is be ignored
    - If second level tag "k" value starts with "addr:", it is added to a dictionary "address"
    - If second level tag "k" value does not start with "addr:", but contains ":", we process it the same as any other tag.
    - If there is a second ":" that separates the type/direction of a street, the tag is ignored.
    - All "nd" in "way" are turned into an array of nds.
    - Correct street types. For instance: "St.", "street", "ST." are converted to "Street"
    """
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

