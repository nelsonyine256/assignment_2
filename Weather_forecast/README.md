# OOP with Python, Assignment 2 (Advent 2026)

**Name:** [YOUR NAME]  
**Course:** MSCS & MSDS, OOP with Python  
**Mini-Project 1:** Fetching and Displaying a Weather Forecast with Python Web APIs

This repository has one Jupyter notebook per mini-project. This README covers Mini-Project 1. Mini-Project 2 will be added as its own notebook (see the layout below).

## What the project does

The notebook takes a place name (default: Dresden), finds its coordinates with the Open-Meteo Geocoding API, gets a daily forecast from the Open-Meteo Forecast API, and shows it as a text summary, a formatted table and a chart. It then adds MET Norway as a second source and compares the two. All HTTP calls are made by hand with `urllib` and `requests`, with no weather wrapper library.

## Repository layout

```
.
├── README.md
├── requirements.txt
├── pytest.ini
├── project1_weather.ipynb      <- the notebook (Parts A to D)
├── src/
│   ├── __init__.py
│   └── weather_api.py          <- reusable functions (docstrings + type hints)
├── tests/
│   └── test_weather_parsing.py <- offline pytest checks
├── sample_json/                <- saved API responses used by the tests
│   ├── forecast_sample.json
│   ├── met_sample.json
│   ├── geocode_sample.json
│   └── geocode_no_results.json
└── project2_<name>.ipynb       <- Mini-Project 2 (to be added)
```

## How to set it up

You need Python 3.9 or newer (the code uses the standard library `zoneinfo`).

```bash
git clone <REPO LINK>
cd <repo folder>

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac / Linux

pip install -r requirements.txt
```

What each command does: `git clone` downloads the repository, `python -m venv venv` creates a private environment so the packages do not mix with other projects, `activate` switches it on, and `pip install -r requirements.txt` installs the libraries listed in `requirements.txt`.

**Contact email.** MET Norway requires a real contact address in the User-Agent. Never type a personal email into shared code. Set your own university email in an environment variable before starting Jupyter:

```bash
set WEATHER_CONTACT_EMAIL=you@your-university.edu        # Windows (cmd)
# export WEATHER_CONTACT_EMAIL=you@your-university.edu   # Mac / Linux
```

If the variable is not set, the notebook uses a fake placeholder address.

## How to run

```bash
jupyter notebook
```

Open `project1_weather.ipynb` and choose **Kernel > Restart & Run All**. Start Jupyter from the repository root, otherwise `from src.weather_api import ...` and the `sample_json/` folder will not be found.

The only cell I edit is the configuration cell near the top:

| Variable | Meaning |
|---|---|
| `LOCATION_NAME` | place to look up, e.g. `"Dresden"` |
| `PICK_CANDIDATE` | which match to use if the name is ambiguous (0 = first) |
| `FORECAST_DAYS` | number of days, 1 to 16 |
| `CONTACT_EMAIL` | read from `WEATHER_CONTACT_EMAIL` |

The notebook needs internet. A different location, for example `"Kampala"`, only needs a change in the first line.

## How to run the tests

```bash
pytest
```

The tests read the files in `sample_json/`, so they run offline. They cover geocode parsing (several candidates, and the missing `results` key), the forecast DataFrame, weather-code decoding, the MET daily aggregation, a malformed payload, latitude validation, and the retry logic (recovery after two 503 errors, and no retry on a 400). The notebook also runs 7 assert checks on the same samples.

To refresh the samples with new real responses, set `SAVE_SAMPLES = True` in the notebook once (with internet), run it, and set it back to `False`.

## Summary of findings

[EDIT THIS with what you saw when you ran it.]

* The two services agreed on the general pattern (warmer and cooler days, rainy days) but not on exact numbers. Daily maximum temperatures differed by roughly 1 to 3 °C. They use different weather models, and my MET daily values come from readings at time steps, so they can miss the true peak.
* MET Norway's first and last days can be partial, so their rain and temperature numbers are less reliable than the middle days.
* The errors I met while building it were `gaierror` (a weak connection, and later a typo in the URL), an HTTP 400 from MET Norway because I used `latitude`/`longitude` instead of `lat`/`lon`, a missing `results` key for unknown cities, and `NameError` from using a variable name that did not exist.
* The retry logic recovered correctly from a simulated server that failed twice with 503, and gave up cleanly with a custom `WeatherAPIError` when the network was simulated as down.

The full written report (data flow, licensing, reliability, privacy) is in Part D of the notebook.

## Design decisions

* **Network code and parsing code are separate.** `geocode`, `get_forecast` and `fetch_met` talk to the network. `parse_geocode`, `forecast_to_dataframe` and `met_to_daily` only read JSON, so they can be tested offline.
* **One safe request function.** Every call goes through `request_json`: timeout, `raise_for_status()`, retries with exponential backoff and a retry cap, and a custom `WeatherAPIError` on final failure. A 4xx error is not retried because it is my mistake.
* **A configuration variable instead of `input()`**, so the notebook runs top to bottom with Restart & Run All.
* **No secrets in code.** The contact email comes from an environment variable.

## Data sources and licences

* Open-Meteo Forecast and Geocoding APIs: free for non-commercial use, data under CC BY 4.0 (geocoding data from GeoNames). Credit is printed in the notebook output and on the chart.
* MET Norway Locationforecast 2.0: data under NLOD 2.0 / CC BY 4.0. Requires an identifying User-Agent with contact details.

The licence terms should be checked on the providers' own websites before any real use.

## What I borrowed, and AI use declaration

**AI assistance.** I used Claude (Anthropic's AI assistant) while working on this assignment. It was used to:

* explain concepts (HTTP, status codes, JSON, exceptions, classes, docstrings, functions and parameters, retries and backoff);
* draft and explain most of the code, which I then typed or pasted into my notebook, ran, debugged and reorganised;
* help me find errors (for example the `gaierror` and the MET Norway HTTP 400);
* review my notebook, suggest the `src/` and `tests/` layout, draft the README, and draft and shorten the report text in Part D.
* debugging


I ran all the code myself and tested it on real API responses, and I can explain every part of it. [EDIT: change this wording if it does not describe exactly what you did.]

**Other sources used:**

* Weather code descriptions: WMO Weather interpretation codes (WW), from the Open-Meteo documentation (https://open-meteo.com/en/docs).
* API behaviour and parameters: the Open-Meteo and MET Norway documentation.
* Libraries: `requests`, `pandas`, `matplotlib`, `pytest` and `jupyter`, plus the standard library (`urllib`, `json`, `time`, `os`, `datetime`, `zoneinfo`, `typing`). `zoneinfo` is used only to convert MET's UTC times to local time.

I did not copy another student's work, and no code comes from a weather wrapper library.
