from flask import jsonify, request
import requests, time
from pymongo import ReturnDocument
from bson import ObjectId

class LocalAPI:
  def __init__(self, db, food_api):
    self.db = db
    self.food_api = food_api

  def _atlas_search(self, collection, index_name, weight, query, page, limit):
    search_conditions = {
      "index": index_name,
      "compound": {
        "should": [
          {
            "phrase": { 
              "query": query,
              "path": "Description",
              "slop": 0,
            }
          },
          {
            "text": {  
              "query": query,
              "path": "Description",
              "score": {"boost": {"value": 20}}  
            }
          },
          {
            "text": { 
              "query": query,
              "path": "Description",
              "fuzzy": {"maxEdits": 1, "prefixLength": 2},
              "score": {"boost": {"value": 5}}
            }
          }
        ]
      }
    }

    pipeline = [
      {
        "$search": search_conditions
      },
      {
        "$addFields": {
          "searchScore": {"$meta": "searchScore"},
          "adjustedScore": {"$multiply": [{"$meta": "searchScore"}, weight]}  
        }
      },
      {"$sort": {"adjustedScore": -1}},  
      {"$skip": (page - 1) * limit},
      {"$limit": limit}
    ]

    return list(self.db[collection].aggregate(pipeline))
  
  def search_database(self):
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    if not query:
      return jsonify([])

    start_time = time.time()

    branded_count = self.db["branded-foods"].count_documents({})
    survey_count = self.db["survey-foods"].count_documents({})
    custom_count = self.db["custom-foods"].count_documents({})

    total_docs = branded_count + survey_count + custom_count
    branded_weight = total_docs / branded_count if branded_count else 1
    survey_weight = total_docs / survey_count if survey_count else 1
    custom_weight = total_docs / custom_count if custom_count else 1


    branded_results = self._atlas_search("branded-foods", "FoodDesc_BF", branded_weight, query, page, limit)
    survey_results = self._atlas_search("survey-foods", "FoodDesc_SF", survey_weight, query, page, limit)
    custom_results = self._atlas_search("custom-foods", "FoodDesc_CF", custom_weight, query, page, limit)

    all_results = branded_results + survey_results + custom_results
    all_results.sort(key=lambda x: x["adjustedScore"], reverse=True)

    search_time = time.time() - start_time
    print(f"\nSearch execution time: {search_time:.4f} seconds")

    return jsonify({
        "results": self._format_db_search_results(all_results),
        "has_more": len(all_results) >= limit
    })

  def food_details(self, fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={self.food_api}"

    try:
      response = requests.get(url)
      response.raise_for_status()
      return jsonify(self._format_usda_food_details(response.json()))
    except requests.exceptions.HTTPError as e:
      return jsonify({'error': f'HTTP error: {e}'}), response.status_code
    except requests.exceptions.RequestException as e:
      return jsonify({'error': f'API request failed: {e}'}), 500

  def _format_db_search_results(self, *results):
    return [
      {
        'id': str(result['_id']),
        'name': result.get('Description', '').title(),
        'calories': result.get('Calories', 'N/A'),
        'serving_size': result.get('Serving Size', 'N/A'),
        'brand': result.get('Brand Owner', 'N/A').title() if 'Brand Owner' in result else None,
        'fdcId': result.get('FDC ID', None)
      }
      for result_set in results for result in result_set
    ]

  def _format_usda_food_details(self, data):
    food_type = data.get('dataType', 'N/A')

    nutrients = {
      nutrient.get('nutrient', {}).get('name'): nutrient.get('amount')
      for nutrient in data.get('foodNutrients', [])
      if nutrient.get('nutrient', {}).get('name') and nutrient.get('amount') is not None
    }

    serving_size = f"{data.get('servingSize', 'N/A')} {data.get('servingSizeUnit', 'N/A')}"

    attributes = {attr.get('name', 'Unknown'): attr.get('value', 'N/A') for attr in data.get('foodAttributes', [])}

    return {
      'name': data.get('description', 'N/A'),
      'calories': nutrients.get('Energy', 'N/A'),
      'protein': nutrients.get('Protein', 'N/A'),
      'carbs': nutrients.get('Carbohydrate, by difference', 'N/A'),
      'fats': nutrients.get('Total lipid (fat)', 'N/A'),
      'serving_size': serving_size,
      'attributes': attributes,
      'publication_date': data.get('publicationDate', 'N/A')
    }

  def add_custom_food(self, food_name, calories, serving_size=None, brand_owner=None, custom_food_category=None, ingredients=None):
    # TODO: To provide UI feedback
    if not food_name or not calories:
      return {"error": 'Missing required fields'}, 400

    existing_food = self.db["custom-foods"].find_one({
      "Description": food_name,
      "Brand Owner": brand_owner or "N/A",
      "Custom Food Category": custom_food_category or "N/A",
      "Calories": calories,
      "Ingredients": ingredients or "N/A",
      "Serving Size": serving_size or 100
    })
    if existing_food:
      return {"error": "Food item with the same data already exists"}, 400

    counter = self.db["counter"].find_one_and_update(
      {"_id": "fdc_id"},
      {"$inc": {"sequence_value": 1}},  
      return_document=ReturnDocument.AFTER,
      upsert=True  
    )

    fdc_id = counter["sequence_value"]

    new_food = {
      "_id": ObjectId(),
      "Food Class": "Custom",
      "FDC ID": fdc_id,
      "Description": food_name,
      "Brand Owner": brand_owner or "N/A",\
      "Custom Food Category": custom_food_category or "N/A",
      "Calories": calories,
      "Ingredients": ingredients or "N/A",
      "Serving Size": serving_size or 100,
    }

    self.db["custom-foods"].insert_one(new_food)
    return {"message": "Food item added successfully!"}, 200