import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    apikey = kwargs.get("apikey")
    try:
        if apikey:
            params = dict()
            params["text"] = kwargs["text"]
            params["version"] = kwargs["version"]
            params["features"] = kwargs["features"]
            params["return_analyzed_text"] = kwargs["return_analyzed_text"]
            
            response = requests.get(url, data=params, auth=HTTPBasicAuth('apikey', apikey), headers={'Content-Type': 'application/json'},)
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    try:
        # Call get method of requests library with URL and parameters
        response = requests.post(url, json=json_payload, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data
    

# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    state = kwargs.get("state")
    if state:
        json_result = get_request(url, state=state)
    else:
        json_result = get_request(url)

    # print('json_result from line 31', json_result)    

    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            # print(dealer_doc)
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"], full_name=dealer_doc["full_name"],
                                
                                   st=dealer_doc["st"], zip=dealer_doc["zip"], short_name=dealer_doc["short_name"])
            results.append(dealer_obj)

    return results

def get_dealer_by_id_from_cf(url, **kwargs):
    # Call get_request with a URL parameter
    json_result = get_request(url, **kwargs)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["row"]
        for dealer in dealers:
            dealer_doc = dealer["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                         id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                         short_name=dealer_doc["short_name"], state=dealer_doc["state"],
                         st=dealer_doc["st"], zip=dealer_doc["zip"])
            results = dealer_obj
    return results

def get_dealers_by_state_from_cf(url, state, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, state=state)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["rows"]
        # For each dealer object
        for dealer in dealers:
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                   id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                   short_name=dealer["short_name"],
                                   st=dealer["st"], zip=dealer["zip"])
            results.append(dealer_obj)
    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    json_result = get_request(url, **kwargs)
    print(json_result)
    if json_result:
        reviews = json_result["docs"]
        for review in reviews:
            review_obj = DealerReview(dealership=review["dealership"],
                                   name=review["name"],
                                   purchase=review["purchase"],
                                   review=review["review"])
            if "id" in review:
                review_obj.id = review["id"]
            if "purchase_date" in review:
                review_obj.purchase_date = review["purchase_date"]
            if "car_make" in review:
                review_obj.car_make = review["car_make"]
            if "car_model" in review:
                review_obj.car_model = review["car_model"]
            if "car_year" in review:
                review_obj.car_year = review["car_year"]
            
            sentiment = analyze_review_sentiments(review_obj.review)
            print(sentiment)
            review_obj.sentiment = sentiment
            results.append(review_obj)
    return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(dealer_review):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
    apikey = "zIHLg9w_7g8Ryf-Yulmuci5kicgTWl7dI9vtSUXhWztT"
    url = "https://api.us-east.natural-language-understanding.watson.cloud.ibm.com/instances/e19fe775-15a7-4db7-9dd9-e352d4c6b466"
    
    authenticator = IAMAuthenticator(apikey)
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        version='2022-04-07',
        authenticator=authenticator
    )

    natural_language_understanding.set_service_url(url)

    response = natural_language_understanding.analyze(
        text=dealer_review,
        language='en',
        features=Features(sentiment=SentimentOptions(targets=[dealer_review]))
    ).get_result()

    print(json.dumps(response, indent=2))
    
    return response["sentiment"]["document"]["label"]