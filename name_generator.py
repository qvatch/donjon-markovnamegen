##########################################################################
# name_generator.py
# Translated from name_generator.js, https://donjon.bin.sh/code/name/ by Quatch (gmail.com), 2021-07-19
# Released to the public domain: http://creativecommons.org/publicdomain/zero/1.0/

# To use:
#   [opt] Provide 'egyptian_set.js' from https://donjon.bin.sh/code/name/egyptian_set.js
#   [opt] Provide 'wordlist.txt' a utf8 text file containing words, one 'word' per line, though words can contain spaces (multi-part).
#   [opt] Edit this file to provide name_set['pythonlist']=['word1', 'word2',...'wordn'] (on line 25)
#   run main(), or call as name_generator.py


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# // name_generator.js
# // written and released to the public domain by drow <drow@bin.sh>
# // http://creativecommons.org/publicdomain/zero/1.0/


import random
import math
from typing import Union  # for typechecking, which is mildly overdone.

# A quick (and maybe wrong) description of what a markov chain is, and how it's stored.
#   *what: a state machine where the choice of new state is a weighted random selection of all possible exits from the current state.
#   *how: a dictionary of states. Each state is a dictionary of exits. Each exit is the (weighted) count of how often it happened in the input text.


name_set: dict = {'pythonlist': ['replace this with a python style list of words']}  # Global storage for seperate wordlists. Each entry is a list of space-seperated-words.
chain_cache: dict = {}  # Global storage for the markov chains. It is populated by construct_chain() from an input wordlist


# Each chain contained in chain_cache has:
#   *parts: how many space-separated-words comprise a name.
#   *name_len: how long each word in the name can be
#   *initial: outgoing links for each starting letter
#   *[letters]: outgoing links for each given letter
#   *table_len: for each chain in the cache, a 'total' count of the outgoing links


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# // generator function

def generate_name(wordlistName: str) -> str:
    """Generate a name using the named markov chain.
    
    Only really useful if you want to have several different wordlists loaded in at once. For the js example, this is called as   document.write(generate_name('egyptian')); to start the whole generator in action.
    
    @param wordlistName: name of the chain to use.
    """
    
    chain = markov_chain(wordlistName)  # get the chain for the desired wordlist
    if chain != {}:
        return markov_name(chain)
    else:
        return ''


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#   // generate multiple

def name_list(wordlist: str, n_of: int) -> list:
    """Generate multiple names from a wordlist
    
    @param wordlist: name of the wordlist to use
    @param n_of: how many names to generate
    @return: list of names
    """
    namelist = []
    for i in range(0, n_of):
        namelist.append(generate_name(wordlist))
    return namelist


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# // get markov chain by type


def markov_chain(chainName) -> dict:
    """Get a markov chain from the global chain_cache called 'chainName'
    
    If the chain does not exist, build it from the name_set, then get it.
    
    @param chainName: name of the chain we want to get
    @return: the desired markov chain. {} if the chain cannot be found or made.
    """
    try:
        chain: dict = chain_cache[chainName]
        return chain
    except KeyError:
        wordlist = name_set[chainName]
        if wordlist and len(wordlist) > 0:
            chain_cache[chainName] = {}  # initialize empty markov chain
            chain = construct_chain(chainName)
            if chain:
                chain_cache[chainName] = chain
            return chain
        else:
            return {}


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#   // construct markov chain from list of names


def construct_chain(wordlistName: str) -> dict:
    """Build the markov chain from the input wordlist
     
     @param wordlistName: which set of words to use from global name_set.
     @return: built and scaled chain, to be inserted somewhere into chain_cache.
     """
    global name_set
    wordlist: Union[list, str] = name_set[wordlistName]
    chain: dict = {}
    
    for names in wordlist:
        if type(names) is str:
            names: list = [names]
        chain: dict = incr_chain(wordlistName, 'parts', str(len(names)))
        
        for j in range(0, len(names)):
            name: str = names[j]
            chain = incr_chain(chain, 'name_len', str(len(name)))
            
            c: str = name[0]
            chain = incr_chain(chain, 'initial', c)
            
            word: str = name[1:]
            last_c: str = c
            
            while len(word) > 0:
                c = word[0]
                chain = incr_chain(chain, last_c, c)
                word = word[1:]
                last_c = c
    return scale_chain(chain)


def incr_chain(chain: Union[None, str, dict], key: str, token: str) -> dict:
    """Add an occurance of chain[key][token], creating it if it does not exist, incrementing it by one otherwise.
    
    @param chain: which chain to work on (None: global chain_cache, str: chain_cache[chain])
    @param key: which state to increment or create.
    @param token: which outgoing link to increment or create.
    @return: adjusted chain
    """
    global chain_cache
    
    if chain is None:
        chain = chain_cache
    elif type(chain) is str and chain in chain_cache.keys():
        chain = chain_cache[chain]
    else:
        chain: dict = chain
    if key in chain.keys():
        if token in chain[key].keys():
            chain[key][token] = chain[key][token] + 1
            # chain[key]['__SCALEVALUE'] = chain[key]['__SCALEVALUE'] + 1
        else:
            chain[key][token] = 1
    else:
        chain[key] = {}
        chain[key][token] = 1
        # chain[key]['__SCALEVALUE'] = 1
    return chain


def scale_chain(chain: dict) -> dict:
    """Count the number of outgoing links in each node of the chain, apply a scaling factor (why?)
    
    @param chain: the chain to scale
    @return: the scaled chain.
    """
    table_len: dict = {}
    
    for key in chain.keys():
        table_len[key]: int = 0
        for token in chain[key].keys():
            count: int = chain[key][token]
            weighted: int = math.floor(math.pow(count, 1.3))  # ^1.3
            chain[key][token]: int = weighted
            table_len[key]: int = table_len[key] + weighted
    chain['table_len'] = table_len  # Save this weighted list of outgoing links to the node in the chain.
    return chain


# // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#   // construct name from markov chain

def markov_name(chain: dict) -> str:
    """Generate a single name from given chain"""
    
    parts: int = int(select_link(chain, 'parts'))  # parts is how many space-seperated-words comprise the new name.
    names: list = []  # the space-separated-words that make up the new name
    
    for i in range(parts):
        name_len: int = int(select_link(chain, 'name_len'))  # pre-determine the length of this name
        c: str = select_link(chain, 'initial')  # pick starting letter
        name: str = c  # begin building the name
        last_c: str = c  # save the current character so we can look it up in the chain
        
        while len(name) < name_len:  # keep building up name until we hit the desired length
            c = select_link(chain, last_c)
            if len(c) == 0:
                # There are no valid outgoing links from this node in the chain, terminate early.
                break
            name = name + c
            last_c = c
        names.append(name)
    return ' '.join(names)  # collapse the new-name-list into a single space-separated-string.


def select_link(chain: dict, key: str) -> str:
    """Given a position in the chain, randomly* pick an outgoing link.
    *Random: weighted choice based on frequency of occurance in the input wordlist that was used to build the chain.
    
    @param chain: the whole markov chain that contains key.
    @param key: origin from which to select a link from.
    @return: name of the new state, or '' if there are no availiable states.
    """
    chainlen: int = chain['table_len'][key]
    if chainlen is False:
        return ''
    idx: int = random.randrange(0, chainlen)
    tokens = chain[key].keys()
    acc: int = 0
    
    for token in tokens:
        acc = acc + chain[key][token]
        if acc > idx:
            return token
    return ''


#######################################################################
#######################################################################
#######################################################################


def cleanuplist(thelist: list, replacements: dict) -> list:
    """cleanup list entries with repeated str.replace() calls
    
    @param thelist: list to be cleaned
    @param replacements: dict of substitutions, as str.replace(key,value)
    @return: cleaned list
    """
    
    for subst in replacements:
        thelist: list = [x.replace(subst, replacements[subst]) for x in thelist]
    return thelist


def main():
    #######################################################################
    # read the example wordlist: (a local copy of https://donjon.bin.sh/code/name/egyptian_set.js)
    f = open("egyptian_set.js", "r", encoding='utf8')
    
    # we are going to brutally ignore the JSON formatting.
    name_set['egyptian'] = [x.strip() for x in f.readlines()[10:436]]  # skip the first 10 lines, and the last few
    name_set['egyptian'] = cleanuplist(name_set['egyptian'], {'\'': "", ',': ''})
    
    # clean up multiple spaces. Make it all lowercase..replace("  "," ")
    name_set['egyptian'] = '\n'.join(name_set['egyptian']).strip().lower().split()
    
    # Construct the markov chain from the wordlist.
    markov_chain('egyptian')
    
    # generate a new name
    print("\n\n----------------------------------\negyptian_set.js name:")
    print('\t' + markov_name(chain_cache['egyptian']))
    
    #######################################################################
    # Read the custom wordlist from 'wordlist.txt' if it exists.
    try:
        f = open("wordlist.txt", "r", encoding='utf8')
        name_set['wordlist'] = f.read().strip().lower().split()
        
        # clean up multiple spaces, turn all other space elements into newlines, turn comma, semicolon into newlines too. Make it all lowercase.
        name_set['wordlist'] = cleanuplist(name_set['wordlist'], {'\'': "", '\t': '\n', '\r': '\n', ',': '\n', ';': '\n', "  ": " "})
        
        # Construct the markov chain from the wordlist.
        markov_chain('wordlist')
        
        # Generate a bunch of new words and print them
        print("\n\n----------------------------------\nwordlist.txt names:")
        namelist = name_list('wordlist', 10)
        print('\t' + '\n\t'.join(namelist))
    except FileNotFoundError:
        pass
    
    #######################################################################
    # Generate from name_set['pythonlist'] if it exists.
    if name_set['pythonlist'][0] != 'replace this with a python style list of words':
        # clean up multiple spaces, turn all other space elements into newlines, turn comma, semicolon into newlines too. Make it all lowercase.
        name_set['pythonlist'] = cleanuplist(name_set['pythonlist'], {'\'': "", '\t': '\n', '\r': '\n', ',': '\n', ';': '\n', "  ": " "})
        
        # Construct the markov chain from the wordlist.
        markov_chain('pythonlist')
        
        # Generate a bunch of new words and print them
        print("\n\n----------------------------------\npythonlist names:")
        namelist = name_list('pythonlist', 10)
        print('\t' + '\n\t'.join(namelist))
    
    #######################################################################
    # All done.
    print("\n\n------done------")
    return


if __name__ == "__main__":
    main()
