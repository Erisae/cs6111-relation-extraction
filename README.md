## Name and Uni
Yuhan Xia yx2729

Jenny Liu jl6093
## Files submitting
```shell
pytorch_pretrained_bert
download_finetuned.sh
example_relations.py
extract_gpt3.py
extract_spanbert.py
project2.py
relations.txt
requirements.txt
searchsecrets.py
spacy_help_functions.py
spanbert.py
```

## How to Run Program:
```shell
# this assumes you are using python3, otherwise use pip and python respectively
sudo apt update
sudo apt install python3-pip
pip3 install beautifulsoup4
sudo apt-get update
pip3 install -U pip setuptools wheel
pip3 install -U spacy
python3 -m spacy download en_core_web_lg

# the project files are in the same directory as spanbert
# for your convenience we've added all them to the zip folder
# so there's no need to do `git clone https://github.com/zackhuiiiii/SpanBERT`
pip3 install -r requirements.txt
bash download_finetuned.sh

# run program
python3 project2.py [-spanbert|-gpt3] <google api key>  <google engine id> <openai secret key>  <r> <t> <q> <k>
```
- `<r>`: extraction relationship
  - 1 is for Schools_Attended
  - 2 is for Work_For
  - 3 is for Live_In
  - 4 is for Top_Member_Employees
- `<t>`: real number between 0 and 1, indicating the "extraction confidence threshold," which is the minimum extraction confidence that we request for the tuples in the output; t is ignored if we are using -gpt3 **but should not be missed**
- `<q>`: seed query, list of words in double quotes 
- `<k>`: indicating the number of tuples that we request in the output

## Project design

#### general structure
- `searchsecrets.py` takes in the system inputs from the command line. It also imports the sys library. 
- Performs a Google search using the seed query
- Iteratively extracts relations from the web pages obtained from the search until k tuples are extracted or no new relation is found. 
  - Store urls in searched to skip already-seen URLs.
  - Use `BeautifulSoup` to parse the HTML content. The text is purified by removing unwanted characters like tabs, newlines, spaces, and non-breaking spaces. Finally, the code truncates the text to its first 10,000 characters. 
  - With every url, call `info_extract_spanbert` or `info_extract_gpt3` to update `X` with wanted relations organized in dict `{(subject, object) : confidence}` without duplication.
- After each iteration (10 google search), Sort X by confidence. If X's size is bigger than k, print it and exit iteration. If not, use `queried` to store queried strings, and update the query to be the combination of the tuple generated with highest confidence.

#### structure
- extract_gpt3.py:
- extract_spanbert.py:
- project2.py:

#### info_extract_spanbert
- input
  - finalText: purifed text from `BeautifulSoup`
  - r: target relation
  - t: confidence threshhold
  - X: tuples of target relation
- output
  - X: dict in structure `{(subject, object) : confidence}`, updated X
- `entities_in_relation`: defines a list of entity types that are relevant for each of the target relations. Specifically they are partitioned between object and subject.
- `relations`: defines the string representation of each of the target relations. 
- Within the `info_extract_spanbert function`:
  - The spacy model is applied to the raw text to split it into sentences, tokenize it, and extract entities.
  - The relevant entity types for the target relation are filtered.
  - For each sentence in the input text, `candidate_pairs` are composed where the token of object and subject matches the relation.
  - The SpanBERT model is used to predict the relation for each candidate entity pair. The resulting relation predictions are filtered based on whether they match the target relation and meet the threshold confidence level.

#### info_extract_gpt3
- input
  - raw_text: purified text from `BeautifulSoup`
  - r: target relation
  - k: number of tuples requested
  - X: tuples of target relation
- output
  - X: dict in structure `{(subject, object) : confidence}`, updated X
- `get_openai_completion`: submits a prompt with the desired parameters to OpenAI GPT3 to generate a response text.
- within the `info_extract_gpt3 function`:
  - The spacy model is applied to the raw text to split it into sentences, tokenize it, and extract entities.
  - The entities of interest are identified.
  - Each sentence is analyzed to determine if it has all of the entites of interest. If so, it is added to a list of sentence to ask GPT3.
  - A prompt is created based the on the relation type asked for, the entities that a relation would require, and then instructions on what relations and format the response should have.
  - Each sentence is prompted to gpt3, which then responds with the desired format. 
  - Given the response, it is cleaned, and transformed into a tuple. If the tuple is of length 2, doesn't have any blank elements and has not appeared in X, it is added to X as a dictionary element (the tuple is the key, and the confidence value is 1).
  - The resulting relations are returned as a dictionary. All confidence values are 1. 