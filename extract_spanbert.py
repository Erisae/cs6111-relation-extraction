import spacy
from spanbert import SpanBERT
from spacy_help_functions import get_entities, create_entity_pairs

entities_in_relation = [
                        [["PERSON"], ["ORGANIZATION"]],                                     # Schools_Attended
                        [["PERSON"], ["ORGANIZATION"]],                                     # Work_For
                        [["PERSON"], ["LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]], # Live_In
                        [["ORGANIZATION"], ["PERSON"]]                                      # Top_Member_Employees
]

relations = ["per:schools_attended", "per:employee_of", "per:cities_of_residence", "org:top_members/employees"]

# Load spacy model
nlp = spacy.load("en_core_web_lg")  

# Load pre-trained SpanBERT model
spanbert = SpanBERT("./pretrained_spanbert") 

def info_extract_spanbert(raw_text, r, t, target_relations): 
    # Apply spacy model to raw text (to split to sentences, tokenize, extract entities etc.)
    doc = nlp(raw_text)  

    # filter entities of interest based on target relation
    entities_of_interest = entities_in_relation[r - 1][0] + entities_in_relation[r - 1][1]

    sent_num = 0
    useful_sents = 0
    all_matching_relations = 0
    useful_relations = 0
    total_sents = len(list(doc.sents))
    print("        Extracted", total_sents, "sentences. Processing each sentence one by one to check for presence of right pair of named entity types; if so, will run the second pipeline ...")
    for sentence in doc.sents:  
        sent_num += 1
        if sent_num % 5 == 0:
            print("        Processed",  sent_num, "/", total_sents, "sentences")
        ents = get_entities(sentence, entities_of_interest)
        
        # create entity pairs
        candidate_pairs = []
        sentence_entity_pairs = create_entity_pairs(sentence, entities_of_interest)
        for ep in sentence_entity_pairs:
            # keep subject-object pairs of the right type for the target relation (e.g., Person:Organization for the "Work_For" relation)
            if ep[1][1] in entities_in_relation[r-1][0] and ep[2][1] in entities_in_relation[r-1][1]:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  # e1=Subject, e2=Object
            elif ep[2][1] in entities_in_relation[r-1][0] and ep[1][1] in entities_in_relation[r-1][1]:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  # e1=Object, e2=Subject    

        # Classify Relations for all Candidate Entity Pairs using SpanBERT
        # candidate_pairs = [p for p in candidate_pairs if not p["subj"][1] in ["DATE", "LOCATION"]]  # ignore subject entities with date/location type

        if len(candidate_pairs) == 0:
            continue

        relation_preds = spanbert.predict(candidate_pairs)  # get predictions: list of (relation, confidence) pairs

        useful = False
        for ex, pred in list(zip(candidate_pairs, relation_preds)):
            # focus on target relations
            # '1':"per:schools_attended"
            # '2':"per:employee_of"
            # '3':"per:cities_of_residence"
            # '4':"org:top_members/employees"
            if pred[0]==relations[r-1] and pred[1] >= t:
                all_matching_relations += 1
                print("                === Extracted Relation ===")
                print("                Input tokens: {}".format([token.text for token in sentence]))
                print("                Output Confidence:", pred[1], "; Subject:", ex["subj"][0], "; Object:",ex["obj"][0], ";")
                if (ex["subj"][0], ex["obj"][0]) in target_relations and target_relations[(ex["subj"][0], ex["obj"][0])] > pred[1]:
                    print("                Duplicate with lower confidence than existing record. Ignoring this.")
                else:
                    print("                Adding to set of extracted relations")
                    useful = True
                    useful_relations += 1
                print("                ==========")

                if (ex["subj"][0], ex["obj"][0]) in target_relations:
                    target_relations[(ex["subj"][0], ex["obj"][0])] = max(target_relations[(ex["subj"][0], ex["obj"][0])], pred[1])
                else: # first time to appear
                    target_relations[(ex["subj"][0], ex["obj"][0])] =  pred[1]

        if useful:
            useful_sents += 1
            print("")

    print("        Extracted annotations for ", useful_sents, " out of total ", total_sents, " sentences")
    print("        Relations extracted from this website:" , useful_relations , "(Overall:", all_matching_relations, ")\n")
    return target_relations

