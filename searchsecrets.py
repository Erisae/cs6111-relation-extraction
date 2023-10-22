import sys

extraction_method = sys.argv[1]
google_api_key = sys.argv[2]
google_engine_id = sys.argv[3]
openai_key = sys.argv[4]
relation_to_extract = int(sys.argv[5])
extraction_confidence_threshold = float(sys.argv[6])
seed_query = sys.argv[7]
tuples_requested = int(sys.argv[8])


