import google.generativeai as genai
import os
import time
from collections import deque
from dotenv import load_dotenv
import google.api_core.exceptions # For specific API error handling
import threading
import queue
from flask import Flask, render_template_string, jsonify
import logging
from datetime import datetime, timezone
# import socket # No longer needed for random port
# import random # No longer needed for random port

# --- Configuration ---
# Load environment variables from .env file if it exists in the current directory
load_dotenv()

# Fetch API key from environment variable
API_KEY ="AIzaSyBjGpN5O8oirIKaXb6aZWTSrQA3Rhy_tWk"

# Gemini API Rate Limit (Requests Per Minute - RPM)
# Adjust this based on your specific Gemini model and plan.
# - Gemini 1.0 Pro: Typically 60 RPM
# - Gemini 1.5 Pro / Flash Preview: Can be much lower (e.g., 2-15 RPM or less).
#   **IMPORTANT: Verify the RPM limit for your specific model (gemini-2.5-flash-preview-04-17)
#   in the Google Cloud documentation.
#   DEFAULT_RPM_LIMIT is a safeguard for THIS SCRIPT's *overall* requests, not per model.
DEFAULT_SCRIPT_OVERALL_RPM_LIMIT = 60 # Max requests this script will make in total per minute

# Tier 1 Published RPM Limits (Requests Per Minute)
MODEL_PUBLISHED_RPM_LIMITS = {
    "gemini-1.5-pro": 1000,
    "gemini-2.5-flash-preview-04-17": 1000,
    "gemini-2.5-pro-preview-05-06": 150,
    "gemini-2.0-flash": 2000,
    "gemini-2.0-flash-lite": 4000,
}

# Models this script will check
MODELS_TO_CHECK = [
    "gemini-1.5-pro",                 # General purpose, good to check
    "gemini-2.5-flash-preview-04-17", # Original model from your script
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash",               # Note: Verify these 2.0 models are active/correct for your project
    "gemini-2.0-flash-lite",          # if you encounter 'MODEL_ERROR'
]

FIXED_PROMPT = "Tell me a very short, famous quote." # Simple query for testing

REFRESH_INTERVAL_SECONDS = 10 # How often to make a test request

# --- Rate Limiter State ---
# Stores timestamps of requests made by THIS SCRIPT, per model
request_timestamps_per_model = {model_name: deque() for model_name in MODELS_TO_CHECK}
# Stores timestamps for the script's overall request rate
script_overall_request_timestamps = deque()

# --- Web App State ---
latest_results_lock = threading.Lock()
latest_results_for_cycle = []
last_refresh_time_str = "N/A"
current_script_rpm_info = {"current": 0, "limit": DEFAULT_SCRIPT_OVERALL_RPM_LIMIT}

app = Flask(__name__)

def _prune_old_timestamps_for_deque(timestamp_deque: deque):
    """Removes timestamps older than 60 seconds from the given deque."""
    now = time.time()
    while timestamp_deque and timestamp_deque[0] < now - 60:
        timestamp_deque.popleft()

def get_current_rpm_for_model(model_name: str) -> int:
    """Calculates the current RPM for a specific model based on this script's requests."""
    if model_name in request_timestamps_per_model:
        _prune_old_timestamps_for_deque(request_timestamps_per_model[model_name])
        return len(request_timestamps_per_model[model_name])
    return 0

def get_current_script_overall_rpm() -> int:
    """Calculates the current overall RPM for this script."""
    _prune_old_timestamps_for_deque(script_overall_request_timestamps)
    return len(script_overall_request_timestamps)

def _check_and_wait_if_script_too_fast(script_rpm_cap: int):
    """
    Checks if THIS SCRIPT's overall request rate is too high and waits if necessary.
    If so, it calculates the necessary wait time and sleeps.
    """
    current_script_rpm = get_current_script_overall_rpm()

    if current_script_rpm >= script_rpm_cap:
        wait_time = 0
        if script_overall_request_timestamps:
            # Wait until the oldest request in the window expires, plus a small buffer
            wait_time = (script_overall_request_timestamps[0] + 60.5) - time.time()

        if wait_time <= 0: # Fallback if calculation is off or clock sync issues
            wait_time = 1 # pragma: no cover

        print(f"Script's overall RPM limit ({script_rpm_cap} RPM) met. Pausing script for {wait_time:.2f}s...")
        time.sleep(wait_time)
        # No need to re-evaluate here, next call will do it.

def make_gemini_request(prompt_text, model_name_to_check, script_rpm_limit):
    """Makes a request to the Gemini API, respecting rate limits."""
    _check_and_wait_if_script_too_fast(script_rpm_limit) # Script's own overall throttle

    # API call attempts are now silent as per request; errors will still print.
    try:
        model = genai.GenerativeModel(model_name_to_check)
        response = model.generate_content(prompt_text)
        # Record successful request timestamp *after* the call
        if model_name_to_check in request_timestamps_per_model:
            request_timestamps_per_model[model_name_to_check].append(time.time())
        script_overall_request_timestamps.append(time.time())

        message_excerpt = response.text.strip().replace('\n', ' ')
        # No need to print "Gemini Response Received." here, table will show status
        return {"model_name": model_name_to_check, "status_code": "OK", "message": message_excerpt}

    except google.api_core.exceptions.ResourceExhausted as e:
        print(f"API Rate Limit for {model_name_to_check}: {e}")
        return {"model_name": model_name_to_check, "status_code": "API_RATE_LIMIT", "message": str(e)}
    except google.api_core.exceptions.InvalidArgument as e:
        print(f"Invalid Argument/Model Error for {model_name_to_check}: {e}")
        return {"model_name": model_name_to_check, "status_code": "MODEL_ERROR", "message": str(e)}
    except google.api_core.exceptions.PermissionDenied as e:
        print(f"Permission Denied for {model_name_to_check} (API Key issue?): {e}")
        return {"model_name": model_name_to_check, "status_code": "AUTH_ERROR", "message": str(e)}
    except google.api_core.exceptions.NotFound as e: # e.g. model not found
        print(f"Model Not Found or other NotFound error for {model_name_to_check}: {e}")
        return {"model_name": model_name_to_check, "status_code": "NOT_FOUND", "message": str(e)}
    except Exception as e:
        print(f"Generic Error for {model_name_to_check}: {e}")
        return {"model_name": model_name_to_check, "status_code": "OTHER_ERROR", "message": str(e)}

def worker_thread_function(model_to_check, prompt, script_rpm_limit, results_queue):
    """
    Worker function executed by each thread to make an API request.
    Puts the result dictionary into the results_queue.
    """
    # print(f"Thread for {model_to_check} starting...") # Optional: for debugging threads
    status_dict = make_gemini_request(prompt, model_to_check, script_rpm_limit)
    results_queue.put(status_dict)
    # print(f"Thread for {model_to_check} finished.") # Optional: for debugging threads

def background_data_fetcher():
    """
    Runs in a background thread to periodically fetch data from Gemini API
    and update the global state.
    """
    global latest_results_for_cycle, last_refresh_time_str, current_script_rpm_info

    if not API_KEY:
        print("Error: API_KEY is not set in the script. Please ensure it's hardcoded correctly.")
        return

    try:
        genai.configure(api_key=API_KEY)
        print("Gemini API configured successfully with the hardcoded key.")
    except Exception as e:
        print(f"Fatal Error: Could not configure Gemini API: {e}")
        print("Please check your hardcoded API_KEY and network connection.")
        return

    print("Background data fetcher started...")
    time.sleep(1) # Brief pause to see initial messages

    try:
        while True:
            results_queue = queue.Queue()
            threads = []
            current_cycle_results = []

            for model_to_check in MODELS_TO_CHECK:
                thread = threading.Thread(
                    target=worker_thread_function,
                    args=(model_to_check, FIXED_PROMPT, DEFAULT_SCRIPT_OVERALL_RPM_LIMIT, results_queue)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join() # Wait for all threads to complete

            while not results_queue.empty():
                current_cycle_results.append(results_queue.get())

            with latest_results_lock:
                latest_results_for_cycle = current_cycle_results
                last_refresh_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
                current_script_rpm_info = {
                    "current": get_current_script_overall_rpm(),
                    "limit": DEFAULT_SCRIPT_OVERALL_RPM_LIMIT
                }

            # Log to console that a cycle completed
            print(f"Data fetch cycle complete at {last_refresh_time_str}. Script RPM: {current_script_rpm_info['current']}/{current_script_rpm_info['limit']}. Waiting {REFRESH_INTERVAL_SECONDS}s...")

            # Wait for the next refresh cycle
            time.sleep(REFRESH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\nBackground data fetcher stopped by user.")
    except Exception as e:
        print(f"\n\nAn unexpected error occurred in the background data fetcher: {e}")
        import traceback
        traceback.print_exc()

@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemini API Quota Monitor</title>
        <style>
            body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
            h1 { text-align: center; color: #2c3e50; }
            .info { margin-bottom: 20px; padding: 10px; background-color: #eaf2f8; border-left: 5px solid #3498db; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            .status-ok { color: green; font-weight: bold; }
            .status-api_rate_limit { color: red; font-weight: bold; }
            .status-model_error { color: orange; font-weight: bold; }
            .status-auth_error { color: darkred; font-weight: bold; }
            .status-not_found { color: purple; font-weight: bold; }
            .status-other_error { color: sienna; font-weight: bold; }
            .footer { text-align: center; margin-top: 20px; font-size: 0.9em; color: #777; }
        </style>
    </head>
    <body>
        <h1>Gemini API Live Quota Tracker</h1>
        <div class="info">
            Last Refresh: <span id="lastRefresh">Loading...</span><br>
            Script's Overall RPM (this script's total calls): <span id="scriptRpm">Loading...</span><br>
            Checking {{ num_models }} models. Refreshing data every {{ refresh_interval }} seconds.<br>
            Note: 'Usage' is requests by THIS SCRIPT in the last 60s vs Published Model RPM.
        </div>
        <table>
            <thead>
                <tr>
                    <th>Model Name</th>
                    <th>Status</th>
                    <th>Usage (RPM)</th>
                    <th>Message/Quote (Excerpt)</th>
                </tr>
            </thead>
            <tbody id="statusTableBody">
                <tr><td colspan="4" style="text-align:center;">Loading data...</td></tr>
            </tbody>
        </table>
        <div class="footer">Powered by Flask & Gemini</div>

        <script>
            const REFRESH_INTERVAL_MS = {{ refresh_interval * 1000 }};

            async function fetchData() {
                try {
                    const response = await fetch('/data');
                    const data = await response.json();

                    document.getElementById('lastRefresh').textContent = data.last_refresh_time;
                    document.getElementById('scriptRpm').textContent = `${data.script_rpm.current}/${data.script_rpm.limit}`;

                    const tableBody = document.getElementById('statusTableBody');
                    tableBody.innerHTML = ''; // Clear existing rows

                    if (data.results.length === 0) {
                        tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No data available yet. Waiting for first fetch...</td></tr>';
                        return;
                    }

                    data.results.forEach(res => {
                        const row = tableBody.insertRow();
                        row.insertCell().textContent = res.model_name;
                        const statusCell = row.insertCell();
                        statusCell.textContent = res.status_code;
                        statusCell.className = 'status-' + res.status_code.toLowerCase().replace(/_/g, ''); // e.g. status-apiratelimit
                        row.insertCell().textContent = `${res.current_model_rpm} / ${res.published_model_rpm}`;
                        row.insertCell().textContent = res.message_excerpt;
                    });
                } catch (error) {
                    console.error('Error fetching data:', error);
                    document.getElementById('statusTableBody').innerHTML = '<tr><td colspan="4" style="text-align:center; color:red;">Error fetching data. Check console.</td></tr>';
                }
            }

            document.addEventListener('DOMContentLoaded', () => {
                fetchData(); // Initial fetch
                setInterval(fetchData, REFRESH_INTERVAL_MS);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, num_models=len(MODELS_TO_CHECK), refresh_interval=REFRESH_INTERVAL_SECONDS)

@app.route('/data')
def get_data():
    with latest_results_lock:
        # Augment results with current RPM for each model for the table
        results_with_rpm = []
        for res_item in latest_results_for_cycle:
            model_name = res_item.get("model_name")
            augmented_res = res_item.copy()
            augmented_res["current_model_rpm"] = get_current_rpm_for_model(model_name)
            augmented_res["published_model_rpm"] = MODEL_PUBLISHED_RPM_LIMITS.get(model_name, "N/A")
            augmented_res["message_excerpt"] = (res_item.get("message", "")[:37] + "...") if len(res_item.get("message", "")) > 40 else res_item.get("message", "")
            results_with_rpm.append(augmented_res)

        return jsonify({
            "results": results_with_rpm,
            "last_refresh_time": last_refresh_time_str,
            "script_rpm": current_script_rpm_info
        })

@app.route('/v1/context/<path:model_identifier>', methods=['GET'])
def get_mcp_context(model_identifier: str):
    """
    MCP endpoint to provide context (quota status) for a given model_identifier.
    """
    with latest_results_lock:
        # Find the data for the requested model_identifier
        model_data = None
        for item in latest_results_for_cycle:
            if item.get("model_name") == model_identifier:
                model_data = item
                break

        if not model_data:
            return jsonify({
                "error": "Model identifier not found or not monitored.",
                "model_identifier": model_identifier
            }), 404

        current_model_rpm_usage = get_current_rpm_for_model(model_identifier)
        published_rpm = MODEL_PUBLISHED_RPM_LIMITS.get(model_identifier, "N/A")

        # Attempt to parse last_refresh_time_str to ISO format
        try:
            # Assuming last_refresh_time_str is in local time 'YYYY-MM-DD HH:MM:SS'
            dt_object = datetime.strptime(last_refresh_time_str, '%Y-%m-%d %H:%M:%S')
            # Make it timezone-aware (assuming local timezone, then convert to UTC)
            # For simplicity, if your server runs in UTC, this is easier.
            # Otherwise, proper timezone handling with pytz might be needed.
            # Here, we'll just format it as if it were UTC for ISO 8601.
            context_source_updated_at_iso = dt_object.replace(tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            context_source_updated_at_iso = "N/A" # Fallback if parsing fails

        mcp_response = {
            "model_identifier": model_identifier,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "context_source_updated_at": context_source_updated_at_iso,
            "context": {
                "type": "api_quota_status",
                "published_rpm_limit": published_rpm,
                "current_script_rpm_usage": current_model_rpm_usage, # Usage by this monitor script
                "last_api_call_status": model_data.get("status_code", "N/A"),
                "last_api_call_message": model_data.get("message", "N/A")
            },
            "metadata": {
                "provider": "Gemini API Quota Monitor (Self-Hosted)",
                "data_fetch_interval_seconds": REFRESH_INTERVAL_SECONDS
            }
        }
        return jsonify(mcp_response), 200


if __name__ == "__main__":
    # Configure basic logging for Flask and our app
    logging.basicConfig(level=logging.INFO)

    FIXED_PORT = 39400

    # Start the background thread for data fetching
    print("Starting background data fetcher thread...")
    fetcher_thread = threading.Thread(target=background_data_fetcher, daemon=True)
    fetcher_thread.start()

    # Start the Flask web server
    print(f"Starting Flask web server. Open http://127.0.0.1:{FIXED_PORT} in your browser.")
    print(f"MCP endpoint available at http://127.0.0.1:{FIXED_PORT}/v1/context/<model_identifier>")
    app.run(debug=False, host='0.0.0.0', port=FIXED_PORT) # debug=False for production-like background thread behavior