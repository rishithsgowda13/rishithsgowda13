import os
import requests
import re
from datetime import datetime, timedelta

def get_contributions(username, token):
    query = """
    query($username:String!) {
      user(login:$username) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(url, json={"query": query, "variables": {"username": username}}, headers=headers)
        if response.status_code != 200:
            print(f"Error: API returned status {response.status_code}")
            return []
        
        data = response.json()
        days = []
        for week in data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']:
            for day in week['contributionDays']:
                days.append(day)
        return sorted(days, key=lambda x: x['date'], reverse=True)
    except Exception as e:
        print(f"Exception during fetch: {e}")
        return []

def calculate_streak(days):
    if not days:
        return 0
        
    # Calculate IST time (UTC + 5:30)
    current_time_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date = current_time_ist.date()
    yesterday_date = current_date - timedelta(days=1)
    
    # Check if there is activity today or yesterday (relative to IST) to keep streak alive
    has_activity_today = next((d for d in days if d['date'] == str(current_date) and d['contributionCount'] > 0), None)
    has_activity_yesterday = next((d for d in days if d['date'] == str(yesterday_date) and d['contributionCount'] > 0), None)

    if not has_activity_today and not has_activity_yesterday:
        return 0

    streak = 0
    start_date = current_date if has_activity_today else yesterday_date
    
    for day in days:
        d = datetime.strptime(day['date'], '%Y-%m-%d').date()
        if d > start_date:
            continue
        if day['contributionCount'] > 0:
            streak += 1
        else:
            if d < start_date:
                break
    return streak

def main():
    username = "rishithsgowda13"
    token = os.getenv("GH_TOKEN")
    
    if not token:
        print("GH_TOKEN not found. Skipping.")
        return

    print("Fetching contributions...")
    days = get_contributions(username, token)
    if not days:
        print("Failed to fetch contributions or no data found.")
        return

    streak = calculate_streak(days)
    print(f"Actual verified streak (IST): {streak} days")

    if not os.path.exists("README.md"):
        print("README.md not found!")
        return

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Update Streak Badge
    new_badge_text = f'  <!-- STREAK_BADGE -->\n  <img src="https://img.shields.io/badge/Current_Streak-{streak}_days-a78bfa?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Streak Tracker" />\n  <!-- STREAK_BADGE_END -->'
    content = re.sub(
        r"<!-- STREAK_BADGE -->.*?<!-- STREAK_BADGE_END -->",
        new_badge_text,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
