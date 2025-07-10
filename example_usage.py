#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timedelta

# Example: How to use the Multi-Patient OpenAPS API

SERVER_URL = "http://localhost:3000"


def pretty_print(title, data):
    print(f"\n{title}:")
    print("=" * 50)
    print(json.dumps(data, indent=2))
    print()


def main():
    print("🩺 OpenAPS Multi-Patient API Usage Example")
    print(f"Server: {SERVER_URL}")

    # Step 1: Create a patient profile
    print("\n📝 Step 1: Creating a patient profile...")

    patient_id = "example-patient"

    patient_data = {
        "profile": {
            "carb_ratio": 10,  # 1 unit insulin per 10g carbs
            "sens": 50,  # 1 unit insulin drops BG by 50 mg/dL
            "dia": 6,  # Duration of insulin action: 6 hours
            "max_bg": 120,  # Target upper bound
            "min_bg": 80,  # Target lower bound
            "max_basal": 4.0,  # Maximum basal rate
            "current_basal": 1.0,  # Current basal rate
            "max_iob": 6.0,  # Maximum insulin on board
            "curve": "rapid-acting",
            "insulinPeakTime": 75,  # Peak effect at 75 minutes
            "enableSMB_with_bolus": True,
            "enableSMB_with_COB": True,
            "maxCOB": 120,
            "max_iob": 6,
            "basalprofile": [
                {"minutes": 0, "rate": 0.8, "start": "00:00:00", "i": 0},  # Midnight
                {"minutes": 360, "rate": 1.2, "start": "06:00:00", "i": 1},  # 6 AM
                {"minutes": 720, "rate": 1.0, "start": "12:00:00", "i": 2},  # Noon
                {"minutes": 1080, "rate": 0.9, "start": "18:00:00", "i": 3},  # 6 PM
            ],
        },
        "initialData": {
            "glucoseHistory": [
                {
                    "date": int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000),
                    "glucose": 110,
                    "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat() + "Z",
                },
                {
                    "date": int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000),
                    "glucose": 115,
                    "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat() + "Z",
                },
            ],
            "pumpHistory": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat() + "Z",
                    "_type": "Bolus",
                    "amount": 1.5,
                    "duration": 0,
                }
            ],
        },
        "settings": {"timezone": "America/New_York", "historyRetentionHours": 24},
    }

    # Initialize patient
    response = requests.post(
        f"{SERVER_URL}/patients/{patient_id}/initialize",
        json=patient_data,
        headers={"Content-Type": "application/json"},
    )
    if response.status_code == 201:
        pretty_print("✅ Patient created successfully", response.json())
    else:
        print(f"❌ Failed to create patient: {response.status_code}")
        print(response.text)
        return
    # Step 2: Check patient status
    print("\n📊 Step 2: Checking patient status...")

    response = requests.get(f"{SERVER_URL}/patients/{patient_id}/status")
    if response.status_code == 200:
        pretty_print("Patient Status", response.json())

    # Step 3: Add new glucose reading and calculate
    print("\n🩸 Step 3: Adding new glucose reading and calculating basal...")

    current_time = datetime.now().isoformat() + "Z"

    calculation_data = {
        "currentTime": current_time,
        "newData": {
            "glucoseReadings": [
                {
                    "date": int(datetime.now().timestamp() * 1000),
                    "glucose": 125,  # Slightly elevated
                    "timestamp": current_time,
                }
            ]
        },
        "options": {"microbolus": True, "autosens": {"ratio": 1.0}},  # Normal sensitivity
    }

    response = requests.post(
        f"{SERVER_URL}/patients/{patient_id}/calculate",
        json=calculation_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        result = response.json()
        pretty_print("Calculation Result", result)

        # Extract key information
        suggestion = result["suggestion"]
        print(f"🎯 Recommendation: {suggestion['rate']} U/h for {suggestion['duration']} minutes")
        print(f"📈 Predicted BG: {suggestion['eventualBG']} mg/dL")
        print(f"💭 Reason: {suggestion['reason']}")
    else:
        print(f"❌ Calculation failed: {response.status_code}")
        print(response.text)
        return
    return
    # Step 4: Simulate meal scenario
    print("\n🍽️  Step 4: Simulating meal scenario...")

    # Add carbs
    meal_time = datetime.now().isoformat() + "Z"

    meal_data = {
        "currentTime": meal_time,
        "newData": {"carbEntries": [{"timestamp": meal_time, "carbs": 45, "enteredBy": "patient"}]},  # 45g carbs
        "options": {"microbolus": True},
    }

    response = requests.post(
        f"{SERVER_URL}/patients/{patient_id}/calculate", json=meal_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        result = response.json()
        pretty_print("Meal Calculation Result", result)

        suggestion = result["suggestion"]
        print(f"🎯 Post-meal recommendation: {suggestion['rate']} U/h")
        print(f"🍞 Carbs on board: {result['context']['meal']['carbs']}g")
    # Step 5: Update patient profile
    print("\n⚙️  Step 5: Updating patient sensitivity...")

    profile_update = {"sens": 45, "carb_ratio": 12}  # Slightly less sensitive  # Need more insulin per carb

    response = requests.patch(
        f"{SERVER_URL}/patients/{patient_id}/profile", json=profile_update, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        pretty_print("Profile Updated", response.json())

    # Step 6: Get patient history
    print("\n📜 Step 6: Retrieving patient history...")

    response = requests.get(f"{SERVER_URL}/patients/{patient_id}/history?type=glucose&hours=1&limit=10")

    if response.status_code == 200:
        history = response.json()
        print(f"Glucose readings in last hour: {len(history['result']['glucose'])}")
        for reading in history["result"]["glucose"][:3]:  # Show first 3
            bg_time = datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
            print(f"  {bg_time.strftime('%H:%M:%S')}: {reading['glucose']} mg/dL")

    # Step 7: Run a test scenario
    print("\n🧪 Step 7: Running test scenario...")

    scenario_data = {"scenario": "basic"}

    response = requests.post(
        f"{SERVER_URL}/test/scenario/{patient_id}", json=scenario_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        scenario_result = response.json()
        print(f"Scenario completed: {scenario_result['summary']['steps']} steps")
        print(f"Final glucose: {scenario_result['summary']['finalGlucose']} mg/dL")
        print(f"Final basal rate: {scenario_result['summary']['finalBasalRate']} U/h")
    # Step 8: List all patients (demo only)
    print("\n👥 Step 8: Listing all patients...")

    response = requests.get(f"{SERVER_URL}/patients")
    if response.status_code == 200:
        patients_list = response.json()
        print(f"Total patients: {patients_list['count']}")
        for patient in patients_list["patients"]:
            print(f"  - {patient['patientId']}: Last calculation at {patient['lastCalculation']}")

    # Step 9: Performance test
    print("\n⚡ Step 9: Quick performance test...")

    start_time = time.time()

    # Rapid-fire calculations
    for i in range(5):
        calc_time = (datetime.now() + timedelta(seconds=i)).isoformat() + "Z"
        glucose_value = 120 + (i * 2)  # Slowly rising

        quick_calc = {
            "currentTime": calc_time,
            "newData": {
                "glucoseReadings": [
                    {
                        "date": int((datetime.now().timestamp() + i) * 1000),
                        "glucose": glucose_value,
                        "timestamp": calc_time,
                    }
                ]
            },
        }

        response = requests.post(
            f"{SERVER_URL}/patients/{patient_id}/calculate",
            json=quick_calc,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  Calc {i+1}: BG {glucose_value} → Rate {result['suggestion']['rate']} U/h")

    end_time = time.time()
    print(f"⏱️  5 calculations completed in {end_time - start_time:.3f} seconds")

    # Cleanup (optional)
    print("\n🧹 Cleanup: Deleting test patient...")

    response = requests.delete(f"{SERVER_URL}/patients/{patient_id}")
    if response.status_code == 200:
        print("✅ Patient deleted successfully")

    print("\n🎉 Example completed successfully!")
    print("\nThis demonstrates:")
    print("  ✓ Patient profile creation with pump settings")
    print("  ✓ Real-time glucose data processing")
    print("  ✓ OpenAPS algorithm calculations")
    print("  ✓ Meal and carb handling")
    print("  ✓ Profile updates and history management")
    print("  ✓ Multi-patient support")
    print("  ✓ Test scenarios and performance testing")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:3000")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
