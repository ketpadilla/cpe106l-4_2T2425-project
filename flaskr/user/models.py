from flask import jsonify, request, session
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from ..app import db
from ..utils import debug_border

class User:
    """Class for managing user-related operations.

    This class handles user authentication, profile management, and interactions with the database.
    """

    def start_session(self, user):
        """Start a session for the user.

        Args:
            user (dict): The user data to store in the session.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        debug_border()
        print("🔑 Starting session for user:", user["email"])
        debug_border()

        user_copy = user.copy()
        user_copy.pop("password", None)
        session['logged_in'] = True
        session['user'] = user_copy

        return jsonify(user_copy), 200

    def sign_up(self):
        """Register a new user.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        valid_object_id = str(ObjectId())
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))

        debug_border()
        print("📝 User Sign-Up Attempt")
        print(f"Name: {request.form.get('name')}")
        print(f"Email: {request.form.get('email')}")
        debug_border()

        user = {
            "_id": valid_object_id,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": pbkdf2_sha256.hash(request.form.get('password')),
            "weight": weight,
            "height": height,
            "activity_level": request.form.get('activity_level'),
            "dob": request.form.get('dob'),
            "sex": request.form.get('sex'),
            "bmi": self._calculate_bmi(weight, height)
        }

        if db.users.find_one({"email": user['email']}):
            print("❌ Email already in use")
            return {"error": "Email address already in use"}, 400

        if db.users.insert_one(user):
            print("✅ User successfully registered")
            return self.start_session(user)

        print("❌ Signup failed")
        return {"error": "Signup failed"}, 400

    def sign_in(self):
        """Authenticate a user.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        debug_border()
        print("🔑 User Sign-In Attempt")
        print(f"Email: {request.form.get('email')}")
        debug_border()

        user = db.users.find_one({"email": request.form.get('email')})

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            print("✅ Login successful")
            return self.start_session(user)

        print("❌ Invalid email or password")
        return {"error": "Invalid email or password"}, 401

    def sign_out(self):
        """End the user's session."""
        debug_border()
        print("🚪 User signed out")
        debug_border()

        session.clear()

    def find_by_email(self, email):
        """Find a user by their email.

        Args:
            email (str): The email of the user to find.

        Returns:
            dict: The user data if found, otherwise None.
        """
        debug_border()
        print(f"🔍 Searching for user by email: {email}")
        debug_border()

        return db.users.find_one({"email": email})

    def update_password(self, email, new_password):
        """Update the user's password.

        Args:
            email (str): The email of the user.
            new_password (str): The new password to set.

        Returns:
            bool: True if the password was updated, otherwise False.
        """
        debug_border()
        print(f"🔑 Updating password for: {email}")
        debug_border()

        hashed_password = pbkdf2_sha256.hash(new_password)
        result = db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})

        if result.modified_count > 0:
            print("✅ Password updated successfully")
        else:
            print("❌ No changes made")

        return result.modified_count > 0

    def update_calorie_intake(self, email, recommended_calorie_intake):
        """Update the user's recommended calorie intake.

        Args:
            email (str): The email of the user.
            recommended_calorie_intake (float): The recommended calorie intake.

        Returns:
            bool: True if the calorie intake was updated, otherwise False.
        """
        try:
            recommended_calorie_intake = float(recommended_calorie_intake)

            debug_border()
            print(f"📊 Updating calorie intake for {email} to {recommended_calorie_intake}")
            debug_border()

            result = db.users.update_one(
                {"email": email},
                {"$set": {"recommended_calorie_intake": recommended_calorie_intake}}
            )

            if result.modified_count > 0:
                session["user"]["recommended_calorie_intake"] = recommended_calorie_intake
                session.modified = True
                print("✅ Calorie intake updated")
                return True

            print("❌ No changes detected in calorie intake")
            return False
        except Exception as e:
            print(f"❌ Error updating calorie intake: {e}")
            return False

    def update_profile(self):
        """Update the user's profile information.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        user = session.get("user", {})
        email = user["email"]

        debug_border()
        print(f"📝 Updating profile for: {email}")
        debug_border()

        updated_data = {
            key: request.form.get(key, "").strip() for key in ["name", "email", "sex", "dob", "activity_level"]
        }

        updated_data["weight"] = float(request.form.get("weight", 0) or 0)
        updated_data["height"] = float(request.form.get("height", 0) or 0)

        if "weight" in updated_data or "height" in updated_data:
            updated_data["bmi"] = self._calculate_bmi(updated_data["weight"], updated_data["height"])

        result = db.users.update_one({"email": email}, {"$set": updated_data})

        if result.modified_count > 0:
            session["user"].update(updated_data)
            session.modified = True
            print("✅ Profile updated successfully")
            return jsonify({"message": "Profile updated successfully", "bmi": session["user"].get("bmi")}), 200

        print("❌ No profile changes detected")
        return jsonify({"message": "No changes detected."}), 200

    def _calculate_bmi(self, weight, height):
        """Calculate the BMI based on weight and height.

        Args:
            weight (float): The weight of the user.
            height (float): The height of the user.

        Returns:
            float: The calculated BMI.
        """
        bmi = weight / ((height / 100) ** 2) if weight > 0 and height > 0 else None
        debug_border()
        print(f"⚖️ Calculating BMI: {bmi}")
        debug_border()
        return bmi

    def add_to_favorites(self, email, fdc_id):
        """Add a food item to the user's favorites.

        Args:
            email (str): The email of the user.
            fdc_id (str): The FDC ID of the food item.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        debug_border()
        print(f"⭐ Adding {fdc_id} to favorites for {email}")
        debug_border()

        user = db.users.find_one({"email": email})
        if not user:
            print("❌ User not found")
            return jsonify({"error": "User not found"}), 404

        if fdc_id not in user.get("favorites", []):
            db.users.update_one(
                {"email": email},
                {"$push": {"favorites": fdc_id}}
            )
            print("✅ Added to favorites")

        return jsonify({"message": "Added to favorites successfully"}), 200

    def get_favorites(self, email):
        """Retrieve the user's favorite food items.

        Args:
            email (str): The email of the user.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        debug_border()
        print(f"📌 Retrieving favorites for {email}")
        debug_border()

        user = db.users.find_one({"email": email}, {"favorites": 1})
        if not user or "favorites" not in user:
            print("❌ No favorites found")
            return jsonify({"favorites": []}), 200

        favorites_details = []
        for fdc_id in user["favorites"]:
            food = db.foods.find_one({"FDC ID": fdc_id})
            if food:
                favorites_details.append({
                    "name": food.get("Description", "Unknown"),
                    "calories": food.get("Calories", "N/A"),
                    "serving_size": food.get("Serving Size", "N/A"),
                    "brand": food.get("Brand Owner", None),
                    "fdcId": fdc_id
                })

        print(f"✅ Found {len(favorites_details)} favorite items")
        return jsonify({"favorites": favorites_details}), 200

    def remove_from_favorites(self, email, fdc_id):
        """Remove a food item from the user's favorites.

        Args:
            email (str): The email of the user.
            fdc_id (str): The FDC ID of the food item.

        Returns:
            tuple: A tuple containing the JSON response and status code.
        """
        debug_border()
        print(f"🗑️ Removing {fdc_id} from favorites for {email}")
        debug_border()

        result = db.users.update_one(
            {"email": email},
            {"$pull": {"favorites": fdc_id}}
        )

        if result.modified_count > 0:
            print("✅ Removed from favorites successfully")
            return jsonify({"message": "Removed from favorites successfully"}), 200

        print("❌ Failed to remove from favorites")
        return jsonify({"error": "Failed to remove from favorites or item not found"}), 400
