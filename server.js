const express = require('express');
const app = express();

// Library imports - same as the CLI tools use
const generateIOB = require('./lib/iob');
const getLastGlucose = require('./lib/glucose-get-last');
const determine_basal = require('./lib/determine-basal/determine-basal');
const generateMeal = require('./lib/meal');
const tempBasalFunctions = require('./lib/basal-set-temp');

// Embedded JSON data
const data = {
  pumphistory: [
    {
      "timestamp": "2018-06-02T00:05:00-07:00",
      "_type": "Bolus",
      "amount": 0.4,
      "duration": 0
    },
    {
      "timestamp": "2018-06-02T00:00:00-07:00",
      "_type": "TempBasalDuration",
      "duration (min)": 14400
    },
    {
      "timestamp": "2018-06-02T00:00:00-07:00",
      "_type": "TempBasal",
      "temp": "absolute",
      "rate": 0
    }
  ],
  
  profile: {
    "carb_ratios": {
      "schedule": [
        {
          "x": 0,
          "i": 0,
          "offset": 0,
          "ratio": 10,
          "r": 10,
          "start": "00:00:00"
        }
      ],
      "units": "grams"
    },
    "carb_ratio": 10,
    "isfProfile": {
      "first": 1,
      "sensitivities": [
        {
          "endOffset": 1440,
          "offset": 0,
          "x": 0,
          "sensitivity": 50,
          "start": "00:00:00",
          "i": 0
        }
      ],
      "user_preferred_units": "mg/dL",
      "units": "mg/dL"
    },
    "sens": 50,
    "bg_targets": {
      "first": 1,
      "targets": [
        {
          "max_bg": 100,
          "min_bg": 100,
          "x": 0,
          "offset": 0,
          "low": 100,
          "start": "00:00:00",
          "high": 100,
          "i": 0
        }
      ],
      "user_preferred_units": "mg/dL",
      "units": "mg/dL"
    },
    "max_bg": 100,
    "min_bg": 100,
    "out_units": "mg/dL",
    "max_basal": 4,
    "min_5m_carbimpact": 8,
    "maxCOB": 120,
    "max_iob": 6,
    "max_daily_safety_multiplier": 4,
    "current_basal_safety_multiplier": 5,
    "autosens_max": 2,
    "autosens_min": 0.5,
    "remainingCarbsCap": 90,
    "enableUAM": true,
    "enableSMB_with_bolus": true,
    "enableSMB_with_COB": true,
    "enableSMB_with_temptarget": false,
    "enableSMB_after_carbs": true,
    "prime_indicates_pump_site_change": false,
    "rewind_indicates_cartridge_change": false,
    "battery_indicates_battery_change": false,
    "maxSMBBasalMinutes": 75,
    "curve": "rapid-acting",
    "useCustomPeakTime": false,
    "insulinPeakTime": 75,
    "dia": 6,
    "current_basal": 1.0,
    "basalprofile": [
      {
        "minutes": 0,
        "rate": 1.0,
        "start": "00:00:00",
        "i": 0
      }
    ],
    "max_daily_basal": 1.0
  },
  
  clock: "2018-06-02T00:30:00-07:00",
  
  autosens: {"ratio": 1.0},
  
  glucose: [
    {
      "date": 1527924300000,
      "dateString": "2018-06-02T00:25:00-0700",
      "sgv": 101,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 101
    },
    {
      "date": 1527924000000,
      "dateString": "2018-06-02T00:20:00-0700",
      "sgv": 102,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 102
    },
    {
      "date": 1527923700000,
      "dateString": "2018-06-02T00:15:00-0700",
      "sgv": 105,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 105
    },
    {
      "date": 1527923400000,
      "dateString": "2018-06-02T00:10:00-0700",
      "sgv": 105,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 105
    },
    {
      "date": 1527923100000,
      "dateString": "2018-06-02T00:05:00-0700",
      "sgv": 102,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 102
    },
    {
      "date": 1527922800000,
      "dateString": "2018-06-02T00:00:00-0700",
      "sgv": 100,
      "device": "fakecgm",
      "type": "sgv",
      "glucose": 100
    }
  ],
  
  basalProfile: [
    {
      "minutes": 0,
      "rate": 1,
      "start": "00:00:00",
      "i": 0
    }
  ],
  
  carbhistory: [
    {
      "enteredBy": "fakecarbs",
      "carbs": 5,
      "created_at": "2018-06-02T07:00:00.000Z",
      "insulin": null
    },
    {
      "enteredBy": "fakecarbs",
      "carbs": 15,
      "created_at": "2018-06-02T07:05:00.000Z",
      "insulin": null
    }
  ],
  
  tempBasal: {
    "duration": 30,
    "temp": "absolute",
    "rate": 0
  }
};

// oref0-calculate-iob function (like the CLI tool)
function oref0_calculate_iob(pumphistory_data, profile_data, clock_data, autosens_data, pumphistory_24_data) {
  const inputs = {
    history: pumphistory_data,
    history24: pumphistory_24_data,
    profile: profile_data,
    clock: clock_data
  };
  
  if (autosens_data) {
    inputs.autosens = autosens_data;
  }
  
  const iob = generateIOB(inputs);
  return iob;
}

// oref0-meal function (like the CLI tool)
function oref0_meal(pumphistory_data, profile_data, clock_data, glucose_data, basalprofile_data, carb_data) {
  // Input validation - same as CLI tool
  if (typeof(profile_data.carb_ratio) === 'undefined' || profile_data.carb_ratio < 3) {
    return {
      carbs: 0,
      mealCOB: 0,
      reason: `carb_ratio ${profile_data.carb_ratio} out of bounds`
    };
  }
  
  if (typeof basalprofile_data[0] === 'undefined') {
    throw new Error("Error: bad basalprofile_data:" + basalprofile_data);
  }
  
  // Check for argument order (from CLI tool)
  if (typeof basalprofile_data[0].glucose !== 'undefined') {
    console.error("Warning: Argument order has changed: please update your oref0-meal device and meal.json report to place carbhistory.json after basalprofile.json");
    const temp = carb_data;
    carb_data = glucose_data;
    glucose_data = basalprofile_data;
    basalprofile_data = temp;
  }
  
  const inputs = {
    history: pumphistory_data,
    profile: profile_data,
    basalprofile: basalprofile_data,
    clock: clock_data,
    carbs: carb_data || {},
    glucose: glucose_data
  };
  
  const recentCarbs = generateMeal(inputs);
  
  if (glucose_data.length < 36) {
    console.error("Not enough glucose data to calculate carb absorption; found:", glucose_data.length);
    recentCarbs.mealCOB = 0;
    recentCarbs.reason = "not enough glucose data to calculate carb absorption";
  }
  
  return recentCarbs;
}

// oref0-determine-basal function (like the CLI tool)
function oref0_determine_basal(iob_data, currenttemp, glucose_data, profile, autosens_data, meal_data, microbolus, reservoir_data, currentTime) {
  try {
    const glucose_status = getLastGlucose(glucose_data);
    
    if (typeof iob_data.length !== 'undefined' && iob_data.length > 1) {
      console.error(JSON.stringify(iob_data[0]));
    } else {
      console.error(JSON.stringify(iob_data));
    }
    
    console.error(JSON.stringify(glucose_status));
    
    const rT = determine_basal(
      glucose_status, 
      currenttemp, 
      iob_data, 
      profile, 
      autosens_data, 
      meal_data, 
      tempBasalFunctions, 
      microbolus, 
      reservoir_data, 
      currentTime
    );
    
    if (typeof rT.error === 'undefined') {
      return rT;
    } else {
      throw new Error(rT.error);
    }
  } catch (e) {
    throw new Error("Could not parse input data: " + e.message);
  }
}

// Main route - equivalent to example.sh
app.get('/start', (req, res) => {
  try {
    // Step 1: oref0-calculate-iob pumphistory.json profile.json clock.json autosens.json > iob.json
    const iobData = oref0_calculate_iob(
      data.pumphistory,
      data.profile,
      data.clock,
      data.autosens,
      null // pumphistory_24_data
    );
    
    // Step 2: oref0-meal pumphistory.json profile.json clock.json glucose.json basal_profile.json carbhistory.json > meal.json
    const mealData = oref0_meal(
      data.pumphistory,
      data.profile,
      data.clock,
      data.glucose,
      data.basalProfile,
      data.carbhistory
    );
    
    // Step 3: oref0-determine-basal iob.json temp_basal.json glucose.json profile.json --auto-sens autosens.json --meal meal.json --microbolus --currentTime 1527924300000 > suggested.json
    const suggested = oref0_determine_basal(
      iobData,
      data.tempBasal,
      data.glucose,
      data.profile,
      data.autosens,
      mealData,
      true, // microbolus
      null, // reservoir_data
      1527924300000 // currentTime
    );
    
    // Return the suggested result (equivalent to suggested.json)
    res.json(suggested);
    
  } catch (error) {
    res.status(500).json({ error: error.message, stack: error.stack });
  }
});

// Additional routes for individual components (for debugging)
app.get('/iob', (req, res) => {
  try {
    const iobData = oref0_calculate_iob(
      data.pumphistory,
      data.profile,
      data.clock,
      data.autosens,
      null
    );
    res.json(iobData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/meal', (req, res) => {
  try {
    const mealData = oref0_meal(
      data.pumphistory,
      data.profile,
      data.clock,
      data.glucose,
      data.basalProfile,
      data.carbhistory
    );
    res.json(mealData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'OpenAPS server is running' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`OpenAPS server running on port ${PORT}`);
  console.log(`Call GET /start to run the complete OpenAPS algorithm`);
  console.log(`Call GET /iob to get IOB data only`);
  console.log(`Call GET /meal to get meal data only`);
  console.log(`Call GET /health for health check`);
});

module.exports = app;