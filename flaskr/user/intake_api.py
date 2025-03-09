from flask import jsonify, request
from ..app import db
from ..utils import debug_border
from tabulate import tabulate
from datetime import datetime
import pytz

LOCAL_TZ = datetime.now().astimezone().tzinfo

class IntakeAPI:
  def __init__(self, db):
    self.db = db

  def _get_food(self, fdc_id):
    debug_border()
    print(f"🔎 Searching for food with FDC ID: {fdc_id}")

    food = db.get_collection("branded-foods").find_one({"FDC ID": fdc_id}) or \
      db.get_collection("survey-foods").find_one({"FDC ID": fdc_id}) or \
      db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})
    
    if food:
      print(f"✅ Food found: {food.get('Description', 'Unknown')}")
    else:
      print("❌ Food not found")
    debug_border()

    return food
  
  def _debug_food_entries(self, food_entries):
    if not food_entries:
      print("ℹ️ No food entries to display.")
      return

    headers = ["FDC ID", "Name", "Calories", "Servings", "Serving Size", "Brand"]
    table = [[f["fdcId"], f["name"], f["calories"], f["servings"], f["serving_size"], f["brand"]] for f in food_entries]

    debug_border()
    print("📋 Food Entries:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    debug_border()

  def get_daily_intake(self, email):
    debug_border()
    print(f"📩 Fetching daily intake for {email}")
    user = db.users.find_one({"email": email}, {"_id": 1})

    if not user:
      print("❌ User not found")
      debug_border()
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record or not daily_record.get("consumed"):
      print("ℹ️ No food records found for today")
      debug_border()
      return jsonify({"foods": []})

    food_entries = []
    for item in daily_record["consumed"]:
      fdc_id = item["fdcId"]
      servings = item["servings"]

      food = self._get_food(fdc_id)

      if food:
        food_entries.append({
          "fdcId": fdc_id,
          "name": food.get("Description", "Unknown").title(),
          "calories": int(food.get("Calories", 0)),
          "servings": servings,
          "serving_size": food.get("Serving Size", "N/A"),
          "brand": food.get("Brand Owner", "").title() if "Brand Owner" in food else None
        })

    self._debug_food_entries(food_entries)
    debug_border()
    return jsonify({"foods": food_entries})

  def user_calories(self, email):
    debug_border()
    print(f"🔥 Fetching calorie intake for {email}")
    
    user = db.users.find_one({"email": email}, {"_id": 1, "recommended_calorie_intake": 1})
    
    if not user:
        print("❌ User not found")
        debug_border()
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    recommended_calories = user.get("recommended_calorie_intake", 2000)

    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
        print("ℹ️ No daily calorie record found")
        debug_border()
        return jsonify({
            "recommended_calories": recommended_calories,
            "consumed": [],
            "total_calories": 0,
        })

    print(f"✅ Total Calories Consumed: {daily_record.get('total_calories', 0)}")
    debug_border()
    return jsonify({
        "recommended_calories": recommended_calories,
        "consumed": daily_record.get("consumed", []),
        "total_calories": daily_record.get("total_calories", 0),
    })
  
  def remove_daily_intake(self, email):
    print("🟢 Entering remove_daily_intake")

    user = db.users.find_one({"email": email}, {"_id": 1, "recommended_calorie_intake": 1})
    
    if not user:
      print("🔴 User not found!")
      return jsonify({"error": "User not found"}), 404
    
    user_id = user["_id"]
    data = request.json
    fdc_id = int(data.get("fdcId"))

    if not fdc_id:
      print("🔴 Invalid food ID!")
      return jsonify({"error": "Invalid food ID"}), 400

    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
      print("🔴 Daily intake record not found!")
      return jsonify({"error": "Daily intake record not found"}), 404

    existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

    if not existing_food:
      print(f"🔴 Food item with FDC ID {fdc_id} not found in daily intake!")
      return jsonify({"error": "Food item not found"}), 404

    print(f"🟡 Removing food item with FDC ID {fdc_id}...")
    db["intake-daily"].update_one(
      {"_id": daily_record["_id"]},
      {"$pull": {"consumed": {"fdcId": fdc_id}}}
    )

    total_calories = sum(
      item["calories"] * item["servings"] 
      for item in daily_record["consumed"] 
      if item["fdcId"] != fdc_id
    )

    print(f"🟡 Updating total calories after removal: {total_calories}")
    db["intake-daily"].update_one(
      {"_id": daily_record["_id"]},
      {"$set": {"total_calories": total_calories}}
    )

    print("🟢 Food item removed successfully!")
    return jsonify({
      "message": "Food item removed successfully!",
      "new_total_calories": total_calories
    })
  
  def update_daily_intake(self, email, data):
    print("🟢 Entering update_daily_intake")

    user = db.users.find_one({"email": email}, {"_id": 1, "recommended_calorie_intake": 1})

    if not user:
      print("🔴 User not found!")
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    fdc_id = int(data.get("fdcId"))
    new_servings = data.get("servings")

    if not fdc_id or not isinstance(new_servings, int) or new_servings < 1:
      print("🔴 Invalid food ID or servings count!")
      return jsonify({"error": "Invalid food ID or servings count"}), 400

    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
      print("🔴 Daily intake record not found!")
      return jsonify({"error": "Daily intake record not found"}), 404

    existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

    if not existing_food:
      print(f"🔴 Food item with FDC ID {fdc_id} not found in daily intake!")
      return jsonify({"error": "Food item not found"}), 404

    print(f"🟡 Updating servings for FDC ID {fdc_id} to {new_servings}")
    existing_food["servings"] = new_servings

    # Recalculate total calories
    total_calories = 0
    for item in daily_record["consumed"]:
      food = self._get_food(item["fdcId"])  # Ensure fetching correct food data per item

      if food and "Calories" in food:
        total_calories += int(food["Calories"]) * item["servings"]

    print(f"🟡 Updating total calories after update: {total_calories}")
    db["intake-daily"].update_one(
      {"_id": daily_record["_id"]},
      {
        "$set": {
          "consumed": daily_record["consumed"],
          "total_calories": total_calories
        }
      }
    )

    updated_record = db["intake-daily"].find_one({"_id": daily_record["_id"]})

    print("🟢 Servings updated successfully!")
    return jsonify({
      "message": "Servings updated successfully!",
      "new_total_calories": updated_record["total_calories"],
      "recommended_calories": user.get("recommended_calorie_intake", 2000),
      "consumed": updated_record.get("consumed", [])
    })

  def add_daily_intake(self, email, data):
    print("🟢 Entering add_daily_intake")

    user = db.users.find_one({"email": email}, {"_id": 1})

    if not user:
      print("🔴 User not found!")
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    fdc_id = data.get("fdcId")

    if not fdc_id:
      print("🔴 Missing food ID!")
      return jsonify({"error": "Missing food ID"}), 400

    food = self._get_food(fdc_id)

    if not food:
      print(f"🔴 Food with FDC ID {fdc_id} not found!")
      return jsonify({"error": "Food not found"}), 404

    # Handle missing calorie information
    if "Calories" not in food or not isinstance(food["Calories"], (int, float)):
      estimated_calories = 100
      print(f"🟡 Assigning estimated calories ({estimated_calories}) to FDC ID {fdc_id}")
      db.get_collection("custom-foods").update_one(
          {"FDC ID": fdc_id}, {"$set": {"Calories": estimated_calories}}, upsert=True
      )
      calories_per_serving = estimated_calories
    else:
      calories_per_serving = int(food["Calories"])

    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if daily_record:
      existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

      if existing_food:
        print(f"🟡 Incrementing servings for FDC ID {fdc_id}")
        db["intake-daily"].update_one(
          {"_id": daily_record["_id"], "consumed.fdcId": fdc_id},
          {
            "$inc": {
              "consumed.$.servings": 1,
              "total_calories": calories_per_serving
            }
          }
        )
      else:
        print(f"🟡 Adding new food entry for FDC ID {fdc_id}")
        db["intake-daily"].update_one(
          {"_id": daily_record["_id"]},
          {
            "$push": {"consumed": {"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}},
            "$inc": {"total_calories": calories_per_serving}
          }
        )
    else:
      print(f"🟡 Creating a new daily intake record with FDC ID {fdc_id}")
      db["intake-daily"].insert_one({
        "user_id": user_id,
        "date": today,
        "consumed": [{"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}],
        "total_calories": calories_per_serving
      })

    print("🟢 Food added successfully!")
    return jsonify({"message": "Food added successfully!", "calories_added": calories_per_serving})
