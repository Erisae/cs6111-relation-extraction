import spacy
import os
import openai
import searchsecrets
from spacy_help_functions import get_entities, create_entity_pairs

entities_in_relation = [
                        [["PERSON"], ["ORGANIZATION"]],                                     # Schools_Attended
                        [["PERSON"], ["ORGANIZATION"]],                                     # Work_For
                        [["PERSON"], ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]], # Live_In
                        [["ORGANIZATION"], ["PERSON"]]                                      # Top_Member_Employees
]

#openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = searchsecrets.openai_key

models_li= openai.Model.list()
# print(models_li)

def get_openai_completion(prompt, model, max_tokens, temperature = 0.2, top_p = 1, frequency_penalty = 0, presence_penalty =0):
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    response_text = response['choices'][0]['text']
    return response_text

def info_extract_gpt3(raw_text, r, k, X):
    # Load spacy model
    nlp = spacy.load("en_core_web_lg")  

    # Apply spacy model to raw text (to split to sentences, tokenize, extract entities etc.)
    doc = nlp(raw_text)  

    # entities of interest
    entities_of_interest = entities_in_relation[r - 1][0] + entities_in_relation[r - 1][1]

    # target_sentences = []  # sentences to analyze
    output = {}
    relation_types = ["Schools_Attended", "employee of", "cities of residence", "top members/employees"]
    format_types = ["person1,organization1|person2,organization2.", "person1,organization1|person2,organization2.", "person1,location1|person2,location2.", "organization1,person1|organization2,person2."]
    chat1 = "I have a sentence with the following types of extracted entities: " + ','.join(entities_of_interest) + ". Can you create a relations of type "
    chat2 = "from the following sentence: "
    chat3 = " Can you write the relations a tuple with this format "
    chat4 = " You can have as many pairs seperated by | as you see fit, or you can return nothing (not the word nothing, just a space) at all if there are no relations to extract."
    sent_num = 0
    useful_sents = 0
    useful_relations = 0
    all_relations = 0
    total_sents = len(list(doc.sents))
    print("        Extracted", total_sents, "sentences. Processing each sentence one by one to check for presence of right pair of named entity types; if so, will run the second pipeline ...")
    for sentence in doc.sents:
        sent_num += 1
        if sent_num % 5 == 0:
            print("        Processed",  sent_num, "/", total_sents, "sentences")
        
        ents = get_entities(sentence, entities_of_interest)

        # if all(item in ents for item in entities_of_interest):
        if all(elem in [x[1] for x in ents] for elem in entities_of_interest):
            useful_sents += 1
            # prompt for this sentence to ask gpt3
            prompt = chat1 + relation_types[r-1] + chat2 + sentence.text + chat3 + format_types[r-1] + chat4
            
            # parameters desired for gpt3
            model = 'text-davinci-003'
            max_tokens = 100
            response_text = get_openai_completion(prompt, model, max_tokens)
            response_text = response_text.lstrip(".\n")      #removes the initial unncecessary characters at beginning of response

            # clean, and transform from text into entry in dictionary
            pairs_list = response_text.split("|")
            for pair in pairs_list:
                # create relation tuple
                tup = tuple(pair.split(','))
                if (len(X) < k):
                    if (len(tup) == 2 and tup[0] != '' and tup[1] != ''):
                        

                        # print extracted relation
                        print("                === Extracted Relation ===")
                        print("                Sentence:" , sentence)
                        print("                Subject:", tup[0] , "; Object:" , tup[1] , ";")
                        if (tup in output):
                            print("                Duplicate. Ignoring this.")
                        else:
                            useful_relations += 1
                            print("                Adding to set of extracted relations")
                        print("                ==========") 

                        # if another tuple is wanted, and the tuple is valid, then add to dictionary with confidence value of 1
                        output[tup] = 1
                        all_relations += 1

                else:
                    break
            # stop adding tuples
            print("")
        if len(X) >= k: break

    print("        Extracted annotations for ", useful_sents, " out of total ", total_sents, " sentences")
    print("        Relations extracted from this website:" , useful_relations , "(Overall:", all_relations, ")\n")
    return output
