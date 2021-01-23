import requests             #https://requests.readthedocs.io/en/master/
import os
import re

import sys
import os
import argparse             #parsing command line arguments
from datetime import datetime    




##################################################
################### FUNCTIONS   ##################
###################################################


def download(parameters, address):
    ##send requests to the API until getting a result
    connect = 0
    while True:
        try:
            result = requests.get(address, params = parameters, timeout = 60)
            break
        except requests.exceptions.HTTPError as errh:
            print("Http Error:",errh)
            return(1)

        except requests.exceptions.Timeout as to:
            print(f'Connection Timed out\n{to}')
            continue

        except requests.exceptions.ConnectionError as errc:
            if connect == 1:
                continue
            elif connect == 0:
                connect = 1
                print(f'Connection error (please reconnect)\n ')
                continue

        except requests.exceptions.RequestException as e:
            print(f'An exception occured:\n{e}')
            continue

    return result


def esearchquery(QUERY):
    ##unpack QUERY:
    (query, apikey) = QUERY

    ##build api address
    esearchaddress = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    #parameters
    parameters = {}
    if apikey:
        parameters["api_key"] = str(apikey)
    parameters["db"] = "nucleotide"
    parameters["idtype"] = "acc"
    parameters["retmode"] = "json"
    parameters["retmax"] = "0"
    parameters["usehistory"] = "y"    
    #user's query
    parameters["term"] = query
    
    ###send request to the API
    y = download(parameters, esearchaddress)  

    return (y.json())


def fasta(path, QUERY, params, verb):
    
    ##unpack parameters
    (_, apikey) = QUERY
    (querykey, webenv, count) = params

    if verb and verb > 0:
        print("Downloading fasta files...")

    numberofsequences = 0
    retmax = 100
    for x in range((count//retmax) + 1):
        ##build API address
        efetchaddress = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        parameters = {}
        #parameters 
        parameters['db'] = "nuccore"
        parameters['query_key'] = querykey
        parameters['WebEnv'] = webenv
        parameters['retstart'] = str(x * retmax)
        parameters['retmax'] = str(retmax)
        if apikey:
            parameters["api_key"] = apikey
        parameters['rettype'] = "fasta"
        parameters['retmode'] = "text"


        ##send requests to the API until getting a result
        result = download(parameters, efetchaddress)
        result = result.text
        numberofsequences  += len(result.split('>'))
        with open(path + "/fastafiles.fasta", "a") as f:
            f.write(result)

        if verb > 1:
            start = (x*retmax) + retmax
            print(f'{round((start/count)*100, 1)} %  of the fasta files downloaded')

    return numberofsequences
    
############################################
###### CHECK COMMAND LINE ARGUMENTS ########
############################################

parser = argparse.ArgumentParser()

##POSITIONAL ARGUMENTS
parser.add_argument("-r", "--request", required=True, help="The request to the NCBI database")

##OPTIONAL ARGUMENTS
#api key
parser.add_argument("-a", "--apikey", default=None, help="API key (register to NCBI to get an API key)")
#verbose
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", help="Diplays downloads progress and actions", action="store_true")
group.add_argument("-q", "--quiet", help="No verbose output", action="store_true")

args = parser.parse_args()
#################################################
#############   GLOBAL VARIABLES    #############
#################################################

#verbose
if args.verbose:
    verb = 2
elif args.quiet:
    verb = 0
else:
    verb = 1 

##foldername and path
name = str(datetime.now())
name = '_'.join(name.split())
path = "./results/" + name

#create the directory to store the results
if not os.path.exists(path):
    os.makedirs(path)

QUERY = (args.request, args.apikey)

###############################################################
################### RUN ! #####################################
###############################################################

####query to ncbi
##esearchquery

y = esearchquery(QUERY)
##check errors (if bad API key etc) errors returned by the Entrez API
if "error" in y.keys():
    errors = y["error"]
    sys.exit(errors)

count = int(y["esearchresult"]["count"])
if count < 1: 
    sys.exit("No results found")
webenv =  str(y["esearchresult"]["webenv"])
querykey = str(y["esearchresult"]["querykey"])
params = (querykey, webenv, count)

if verb and verb > 0:
    print(f'number of results returned by NCBI: {count}')

##dl fasta files
found = fasta(path, QUERY, params, verb)

print(f'downloaded {found} number of fasta sequences')
