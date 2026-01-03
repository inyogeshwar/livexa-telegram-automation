import schedule
import time
import json
import os
from datetime import datetime
from dispatcher import dispatcher

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILE = os.path.join(CODE_DIR, '../config/schedule.json')

def load_jobs():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, 'r') as f:
        return json.load(f)

def run_job(job):
    print(f"[{datetime.now()}] Running scheduled job: {job['name']}")
    dispatcher.start_stream(job['stream_key'], job['playlist'])

def scheduler_loop():
    print("Scheduler started...")
    jobs = load_jobs()
    for job in jobs:
        # Example format: {"time": "18:00", "days": "daily", ...}
        if job['frequency'] == 'daily':
            schedule.every().day.at(job['time']).do(run_job, job)
        elif job['frequency'] == 'hourly':
            schedule.every().hour.do(run_job, job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    scheduler_loop()
