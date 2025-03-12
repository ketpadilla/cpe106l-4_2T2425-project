from flask import jsonify, request
import requests, time
from pymongo import ReturnDocument
from bson import ObjectId
from tabulate import tabulate
from ..utils import debug_border

class LocalAPI:
    """API for managing local food database operations.

    This class provides methods to search the local food database, fetch food details,
    and add custom food items.

    Args:
        db (Database): The MongoDB database instance.
        food_api (str): The API key for accessing external food data.
    """

    def __init__(self, db, food_api):
        """Initialize the LocalAPI with a database instance and API key.

        Args:
            db (Database): The MongoDB database instance.
            food_api (str): The API key for accessing external food data.
        """
        self.db = db
        self.food_api = food_api

    def _atlas_search(self, collection, index_name, weight, query, page, limit):
        """Perform a search on the specified MongoDB collection using Atlas Search.

        Args:
            collection (str): The name of the MongoDB collection to search.
            index_name (str): The name of the Atlas Search index.
            weight (float): The weight to apply to the search results.
            query (str): The search query.
            page (int): The page number for pagination.
            limit (int): The number of results per page.

        Returns:
            list: A list of search results.
        """
        start_time = time.time()

        search_conditions = {
            "index": index_name,
            "compound": {
                "should": [
                    {
                        "phrase": {"query": query, "path": "Description", "slop": 0}
                    },
                    {
                        "text": {
                            "query": query, "path": "Description",
                            "score": {"boost": {"value": 20}}
                        }
                    },
                    {
                        "text": {
                            "query": query, "path": "Description",
                            "fuzzy": {"maxEdits": 1, "prefixLength": 2},
                            "score": {"boost": {"value": 5}}
                        }
                    }
                ]
            }
        }

        pipeline = [
            {"$search": search_conditions},
            {"$addFields": {"searchScore": {"$meta": "searchScore"},
                            "adjustedScore": {"$multiply": [{"$meta": "searchScore"}, weight]}}},
            {"$sort": {"adjustedScore": -1}},
            {"$skip": (page - 1) * limit},
            {"$limit": limit}
        ]

        results = list(self.db[collection].aggregate(pipeline))

        debug_border()
        print(f"Collection: {collection}")
        print(f"Query: {query}")
        print(f"Results found: {len(results)}")
        print(f"Execution Time: {time.time() - start_time:.4f} sec")
        debug_border()

        return results

    def search_database(self):
        """Search the local food database for matching food items.

        Returns:
            str: JSON response containing the search results.
        """
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

        debug_border()
        print("📊 Database Document Counts:")
        print(f"Branded: {branded_count}, Survey: {survey_count}, Custom: {custom_count}, Total: {total_docs}")
        print("⚖️  Search Weights:")
        print(f"Branded: {branded_weight:.2f}, Survey: {survey_weight:.2f}, Custom: {custom_weight:.2f}")
        debug_border()

        branded_results = self._atlas_search("branded-foods", "FoodDesc_BF", branded_weight, query, page, limit)
        survey_results = self._atlas_search("survey-foods", "FoodDesc_SF", survey_weight, query, page, limit)
        custom_results = self._atlas_search("custom-foods", "FoodDesc_CF", custom_weight, query, page, limit)

        all_results = branded_results + survey_results + custom_results
        all_results.sort(key=lambda x: x["adjustedScore"], reverse=True)

        search_time = time.time() - start_time

        debug_border()
        print(f"🔎 Search Completed in {search_time:.4f} seconds")
        debug_border()

        formatted_results = self._format_db_search_results(all_results)

        if formatted_results:
            print("📝 Top 5 Results Preview:")
            print(tabulate(formatted_results[:5], headers="keys", tablefmt="grid"))

        return jsonify({"results": formatted_results, "has_more": len(all_results) >= limit})

    def food_details(self, fdc_id):
        """Fetch detailed information for a specific food item using its FDC ID.

        Args:
            fdc_id (str): The FDC ID of the food item.

        Returns:
            str: JSON response containing the food details.
        """
        url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={self.food_api}"

        debug_border()
        print(f"Fetching food details for FDC ID: {fdc_id}")
        debug_border()

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            debug_border()
            print(f"✅ API Request Successful: {response.status_code}")
            print(f"Food Name: {data.get('description', 'N/A')}")
            debug_border()

            return jsonify(self._format_usda_food_details(data))
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            return jsonify({'error': f'HTTP error: {e}'}), response.status_code
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Failed: {e}")
            return jsonify({'error': f'API request failed: {e}'}), 500

    def _format_db_search_results(self, results):
        """Format the search results from the local database.

        Args:
            results (list): A list of search results.

        Returns:
            list: A list of formatted search results.
        """
        formatted = [
            {
                'id': str(result['_id']),
                'name': result.get('Description', '').title(),
                'calories': result.get('Calories', 'N/A'),
                'serving_size': result.get('Serving Size', 'N/A'),
                'brand': result.get('Brand Owner', 'N/A').title() if 'Brand Owner' in result else None,
                'fdcId': result.get('FDC ID', None)
            }
            for result in results
        ]
        return formatted

    def _format_usda_food_details(self, data):
        """Format the food details from the USDA API.

        Args:
            data (dict): The raw food details from the USDA API.

        Returns:
            dict: A dictionary containing formatted food details.
        """
        nutrients = {
            nutrient.get('nutrient', {}).get('name'): nutrient.get('amount')
            for nutrient in data.get('foodNutrients', [])
            if nutrient.get('nutrient', {}).get('name') and nutrient.get('amount') is not None
        }

        return {
            'name': data.get('description', 'N/A'),
            'calories': nutrients.get('Energy', 'N/A'),
            'protein': nutrients.get('Protein', 'N/A'),
            'carbs': nutrients.get('Carbohydrate, by difference', 'N/A'),
            'fats': nutrients.get('Total lipid (fat)', 'N/A'),
            'serving_size': f"{data.get('servingSize', 'N/A')} {data.get('servingSizeUnit', 'N/A')}",
            'publication_date': data.get('publicationDate', 'N/A')
        }

    def add_custom_food(self, food_name, calories, serving_size=None, brand_owner=None, custom_food_category=None, ingredients=None):
        """Add a custom food item to the local database.

        Args:
            food_name (str): The name of the food item.
            calories (int): The calorie count of the food item.
            serving_size (str, optional): The serving size of the food item.
            brand_owner (str, optional): The brand owner of the food item.
            custom_food_category (str, optional): The category of the custom food item.
            ingredients (str, optional): The ingredients of the food item.

        Returns:
            tuple: A tuple containing a response message and status code.
        """
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
            "Brand Owner": brand_owner or "N/A",
            "Custom Food Category": custom_food_category or "N/A",
            "Calories": calories,
            "Ingredients": ingredients or "N/A",
            "Serving Size": serving_size or 100
        }

        self.db["custom-foods"].insert_one(new_food)
        return {"message": "Food item added successfully!"}, 200
