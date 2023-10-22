import searchsecrets
import extract_spanbert
import extract_gpt3
import requests
import re
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

def merge_without_duplicate(dict1, dict2): # (k1, k2): value
    dict3 = {}
    for key, value in dict1.items():
            dict3[key] = value
    
    for key, value in dict2.items():
        if key in dict3:
            dict3[key] = max(dict3[key], value)
        else:
            dict3[key] = value

    return dict3
        
def printTopk(X, k, method, searchIter, type):
    print("================== ALL RELATIONS for", type, "(", len(X), ") =================")
    count = 0
    for key, value in X.items():
        if searchsecrets.extraction_method == "-spanbert":
            print("Confidence: {:.8f}           | Subject: {}           | Object: {}".format(value, key[0], key[1]))
        elif searchsecrets.extraction_method == "-gpt3":
            print("Subject: {}          | Object: {}".format(key[0], key[1]))
        else:
            print("Must input either (-spanbert) or (-gpt3)")
            return
        count += 1
        if count >= k:
            print("Total # of iterations =", searchIter)
            return 

def main():
    service = build(
        "customsearch", "v1", developerKey=searchsecrets.google_api_key
    )

    keepSearching = True
    query = searchsecrets.seed_query
    queryList = searchsecrets.seed_query.split(" ")
    queried = [query]
    searched = []
    r  = searchsecrets.relation_to_extract
    k = searchsecrets.tuples_requested
    t = searchsecrets.extraction_confidence_threshold
    X = {}
    printed = False
    searchIterations = 0
    gptSize = 0
    while (keepSearching):
        # execute Google search
        res = (
            service.cse()
            .list(
                q=query,
                cx=searchsecrets.google_engine_id,
            )
            .execute()
        )

        # print parameters of search
        print("Parameters:")
        print("Client key      = " + searchsecrets.google_api_key)
        print("Engine key      = " +  searchsecrets.google_engine_id)
        print("OpenAI key      = " + searchsecrets.openai_key)
        print("Method  = ", searchsecrets.extraction_method[1:])
        relations_text = ["Schools_Attended", "Work_For", "Live_In", "Top_Member_Employees"]
        print("Relation        = " + relations_text[searchsecrets.relation_to_extract - 1])
        print("Threshold       =" , searchsecrets.extraction_confidence_threshold)
        print("Query           = " + query)
        print("# of Tuples     =" , searchsecrets.tuples_requested)
        print("Loading necessary libraries; This should take a minute or so ...)")
        print("=========== Iteration:", searchIterations , "- Query:" , query , "===========\n\n")
        searchIterations += 1

        # iterate through each result
        i = 1
        for r1 in res['items']:
            print("URL (", i , "/ 10):" , r1['formattedUrl'])
            i += 1

            # skip already-seen URLs
            if r1['link'] in searched:
                continue
            searched.append(r1['link'])

            # soup
            print("        Fetching text from url ...")
            response = requests.get(r1['link'])
            htmlPage = response.text
            soup = BeautifulSoup(htmlPage, 'html.parser')
            finalText = soup.get_text()
            ogLength = len(finalText)
            print("        Trimming webpage content from" , ogLength , "to 10000 characters")
            # regex = r'[\.\?\!,]'
            # finalText = ""
            # for string in soup.strings:
            #     if re.search(regex, string[-1]):
            #         finalText += string
            finalText = re.sub(u'\xa0', ' ', finalText) 
            finalText = re.sub('\t+', ' ', finalText) 
            finalText = re.sub('\n+', ' ', finalText) 
            finalText = re.sub(' +', ' ', finalText) 
            finalText = finalText.replace('\u200b', '')
            #  truncate the text to its first 10,000 characters
            finalText = finalText[:10000]
            finalLength = len(finalText)
            print("        Webpage length (num characters):", finalLength)

            # tuples
            print("        Annotating the webpage using spacy...")
            if searchsecrets.extraction_method == "-spanbert":
                X  = extract_spanbert.info_extract_spanbert(finalText, r, t, X)
            elif searchsecrets.extraction_method == "-gpt3":
                X = extract_gpt3.info_extract_gpt3(finalText, r, k, X)
            else:
                print("Must input either (-spanbert) or (-gpt3)")
                break

            # since it just says relations extracted, we are counting all relations extracted, even if one is a duplicate
            # however, that duplicate will not increase the overall
            
            if len(X) >= k:
                break

        # Sort X by confidence    
        X = dict(sorted(X.items(), key = lambda kv:(kv[1], kv[0]), reverse=True))

        keepSearching = False
        if len(X) >= k:
            printTopk(X, k, searchsecrets.extraction_method, searchIterations, relations_text[searchsecrets.relation_to_extract - 1])  
            printed = True
        else:
            # update query
            for key in X.keys():
                query_new = key[0] + " " + key[1]
                if query_new not in queried:
                    query = query_new
                    queried.append(query_new)
                    keepSearching = True
                    break
    if not printed:
        printTopk(X, len(X), searchsecrets.extraction_method, searchIterations, relations_text[searchsecrets.relation_to_extract - 1])


    
                
        
if __name__ == "__main__":
    main()
