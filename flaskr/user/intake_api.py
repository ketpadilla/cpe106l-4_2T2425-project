from flask import jsonify, request
from ..app import db
from tabulate import tabulate
from datetime import datetime

class IntakeAPI:
  def __init__(self, db):
    self.db = db

  def _get_food(self, fdc_id):
    return db.get_collection("branded-foods").find_one({"FDC ID": fdc_id}) or \
      db.get_collection("survey-foods").find_one({"FDC ID": fdc_id}) or \
      db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})
  
  def _debug_food_entries(self, food_entries):
    headers = ["FDC ID", "Name", "Calories", "Servings", "Serving Size", "Brand"]
    table = [ [f["fdcId"], f["name"], f["calories"], f["servings"], f["serving_size"], f["brand"]] for f in food_entries ]
    print(tabulate(table, headers=headers, tablefmt="grid"))

  def get_daily_intake(self, email):
    user = db.users.find_one({"email": email}, {"_id": 1})

    if not user:
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record or not daily_record.get("consumed"):
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
    return jsonify({"foods": food_entries})

  def user_calories(self, email):
    user = db.users.find_one({"email": email}, {"_id": 1, "recommended_calorie_intake": 1})
    
    if not user:
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    recommended_calories = user.get("recommended_calorie_intake", 2000)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
      return jsonify({
        "recommended_calories": recommended_calories,
        "consumed": [],
        "total_calories": 0,
      })

    return jsonify({
      "recommended_calories": recommended_calories,
      "consumed": daily_record.get("consumed", []),
      "total_calories": daily_record.get("total_calories", 0),
    })
  
  def remove_daily_intake(self, email):
    user = db.users.find_one({"email": email}, {"_id": 1, "recommended_calorie_intake": 1})
    
    if not user:
      return jsonify({"error": "User not found"}), 404
    
    user_id = user["_id"]
    data = request.json
    fdc_id = int(data.get("fdcId"))

    if not fdc_id:
      return jsonify({"error": "Invalid food ID"}), 400

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
      return jsonify({"error": "Daily intake record not found"}), 404

    existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

    if not existing_food:
      return jsonify({"error": "Food item not found"}), 404

    db["intake-daily"].update_one(
      {"_id": daily_record["_id"]},
      {"$pull": {"consumed": {"fdcId": fdc_id}}}
    )

    total_calories = sum(item["calories"] * item["servings"] for item in daily_record["consumed"] if item["fdcId"] != fdc_id)

    db["intake-daily"].update_one(
      {"_id": daily_record["_id"]},
      {"$set": {"total_calories": total_calories}}
    )

    return jsonify({
      "message": "Food item removed successfully!",
      "new_total_calories": total_calories
    })
  
  def update_daily_intake(self, email, data):
    user = db.users.find_one({"email": email}, {"_id": 1})

    if not user:
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    fdc_id = int(data.get("fdcId"))
    new_servings = data.get("servings")

    if not fdc_id or not isinstance(new_servings, int) or new_servings < 1:
      return jsonify({"error": "Invalid food ID or servings count"}), 400

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
      return jsonify({"error": "Daily intake record not found"}), 404

    existing_food = None
    for item in daily_record["consumed"]:
      if item["fdcId"] == fdc_id:
        existing_food = item  # Assign the entire item, not just fdc_id
        break

    if not existing_food:
      return jsonify({"error": "Food item not found"}), 404

    existing_food["servings"] = new_servings
    total_calories = 0
    for item in daily_record["consumed"]:
      food = self._get_food(fdc_id)

      if food and "Calories" in food:
        total_calories += int(food["Calories"]) * item["servings"]

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

    return jsonify({
      "message": "Servings updated successfully!",
      "new_total_calories": updated_record["total_calories"],
      "recommended_calories": user.get("recommended_calorie_intake", 2000),
      "consumed": updated_record.get("consumed", [])
    })
  
  def add_daily_intake(self, email, data):
    user = db.users.find_one({"email": email}, {"_id": 1})

    if not user:
      return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    fdc_id = data.get("fdcId")

    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400

    food = self._get_food(fdc_id)

    if not food:
      return jsonify({"error": "Food not found"}), 404

    if "Calories" not in food or not isinstance(food["Calories"], (int, float)):
      estimated_calories = 100
      db.get_collection("custom-foods").update_one(
        {"FDC ID": fdc_id}, {"$set": {"Calories": estimated_calories}}, upsert=True
      )
      calories_per_serving = estimated_calories
    else:
      calories_per_serving = int(food["Calories"])

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if daily_record:
      existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

      if existing_food:
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
        db["intake-daily"].update_one(
          {"_id": daily_record["_id"]},
          {
            "$push": {"consumed": {"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}},
            "$inc": {"total_calories": calories_per_serving}
          }
        )
    else:
      db["intake-daily"].insert_one({
        "user_id": user_id,
        "date": today,
        "consumed": [{"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}],
        "total_calories": calories_per_serving
      })

    return jsonify({"message": "Food added successfully!", "calories_added": calories_per_serving})