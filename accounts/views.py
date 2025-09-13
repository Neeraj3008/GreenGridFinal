import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse

# Firebase + API Keys
FIREBASE_API_KEY = "AIzaSyDYuavLFztniC0ACqSBH7_DyTRAZ_FRhhQ"
DATA_API_KEY = "public-demo-key-2025"
DATA_API_URL = f"https://4224e1bdc986.ngrok-free.app/latest?api_key={DATA_API_KEY}"

# Store historical readings per meter
HISTORICAL_DATA = {}  # { "MH01": [ {timestamp, carbon, consumption}, ... ] }


# ---------------- AUTH VIEWS ----------------
def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        payload = {"email": email, "password": password, "returnSecureToken": True}

        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}",
            json=payload
        )
        data = r.json()

        if "localId" in data:
            messages.success(request, "Account created! Please login.")
            return redirect("login")
        else:
            messages.error(request, data.get("error", {}).get("message", "Signup failed"))
            return redirect("signup")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        payload = {"email": email, "password": password, "returnSecureToken": True}

        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json=payload
        )
        data = r.json()

        if "idToken" in data:
            request.session["firebase_user"] = {
                "email": email,
                "localId": data["localId"],
                "idToken": data["idToken"]
            }
            return redirect("energy_dashboard")
        else:
            messages.error(request, data.get("error", {}).get("message", "Login failed"))
            return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    request.session.flush()  # Clear Firebase session
    return redirect("login")


# ---------------- DASHBOARD VIEWS ----------------
def energy_dashboard_view(request):
    if "firebase_user" not in request.session:
        return redirect("login")

    try:
        r = requests.get(DATA_API_URL, timeout=10)
        data = r.json()  # list of latest readings
    except Exception as e:
        print("Error fetching live data:", e)
        data = []

    # Update historical data
    for entry in data:
        meter_id = entry["meter_id"]
        if meter_id not in HISTORICAL_DATA:
            HISTORICAL_DATA[meter_id] = []
        # Append new timestamped record only if not already present
        if not any(e["timestamp"] == entry["timestamp"] for e in HISTORICAL_DATA[meter_id]):
            HISTORICAL_DATA[meter_id].append(entry)

    # Get the latest unique meter data for dashboard summaries
    households = list({entry["meter_id"]: entry for entry in data}.values())

    # Calculate totals
    total_energy = sum(h["consumption"] for h in households)
    total_carbon = sum(h["carbon"] for h in households)
    total_cost = total_energy * 10  # example cost calculation

    user = request.session["firebase_user"]

    # Pass meter_ids for dropdown or UI elements
    meter_ids = list(HISTORICAL_DATA.keys())

    return render(request, "energy_dashboard.html", {
        "user": user,
        "households": households,
        "total_energy": total_energy,
        "total_carbon": total_carbon,
        "total_cost": total_cost,
        "meter_ids": meter_ids
    })


def meter_data_view(request, meter_id):
    try:
        # Fetch fresh data from external API
        r = requests.get(DATA_API_URL, timeout=10)
        api_data = r.json()
    except Exception as e:
        print("Error fetching API in meter_data_view:", e)
        api_data = []

    # Update HISTORICAL_DATA with any new entries
    for entry in api_data:
        mid = entry["meter_id"]
        if mid not in HISTORICAL_DATA:
            HISTORICAL_DATA[mid] = []
        if not any(e["timestamp"] == entry["timestamp"] for e in HISTORICAL_DATA[mid]):
            HISTORICAL_DATA[mid].append(entry)

    # Return selected meter’s history
    return JsonResponse(HISTORICAL_DATA.get(meter_id, []), safe=False)


def summary_data_view(request):
    """Return JSON for summary cards"""
    households = []
    for meter_id, readings in HISTORICAL_DATA.items():
        if readings:
            households.append(readings[-1])  # latest reading

    total_energy = sum(h["consumption"] for h in households)
    total_carbon = sum(h["carbon"] for h in households)
    total_cost = total_energy * 10  # example cost calculation

    return JsonResponse({
        "total_energy": total_energy,
        "total_carbon": total_carbon,
        "total_cost": total_cost,
        "households": households
    })
