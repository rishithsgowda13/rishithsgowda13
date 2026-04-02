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
    response = requests.post(url, json={"query": query, "variables": {"username": username}}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.text}")
    
    data = response.json()
    days = []
    for week in data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']:
        for day in week['contributionDays']:
            days.append(day)
    return sorted(days, key=lambda x: x['date'], reverse=True)

def calculate_streak(days):
    current_date = datetime.now().date()
    yesterday_date = current_date - timedelta(days=1)
    
    streak = 0
    # Today or yesterday must have a contribution to keep the streak alive
    has_activity_today = next((d for d in days if d['date'] == str(current_date) and d['contributionCount'] > 0), None)
    has_activity_yesterday = next((d for d in days if d['date'] == str(yesterday_date) and d['contributionCount'] > 0), None)

    if not has_activity_today and not has_activity_yesterday:
        return 0

    # Start checking from the most recent day with activity
    start_date = current_date if has_activity_today else yesterday_date
    
    for day in days:
        d = datetime.strptime(day['date'], '%Y-%m-%d').date()
        if d > start_date:
            continue
        if day['contributionCount'] > 0:
            streak += 1
        else:
            # Check if this day is before the start_date
            if d < start_date:
                break
    return streak

def generate_mermaid_graph(days, limit=14):
    # Take the last 'limit' days
    graph_days = sorted(days[:limit], key=lambda x: x['date'])
    mermaid = "```mermaid\ngitGraph\n"
    
    # Calculate start of streak in this window
    for day in graph_days:
        date_str = day['date']
        count = day['contributionCount']
        if count > 0:
            mermaid += f'    commit id: "{date_str}"\n'
        else:
            mermaid += f'    branch break_{date_str.replace("-", "")}\n'
            mermaid += f'    checkout main\n'
    
    mermaid += "```"
    return mermaid

def main():
    username = "rishithsgowda13"
    token = os.getenv("GH_TOKEN")
    if not token:
        print("GH_TOKEN not found, skipping streak update.")
        return

    days = get_contributions(username, token)
    streak = calculate_streak(days)
    mermaid = generate_mermaid_graph(days)

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Update Streak Count
    content = re.sub(
        r"<!-- STREAK_COUNT -->.*?<!-- STREAK_COUNT_END -->",
        f"<!-- STREAK_COUNT -->🔥 {streak} days<!-- STREAK_COUNT_END -->",
        content,
        flags=re.DOTALL
    )

    # Update Mermaid Graph
    content = re.sub(
        r"<!-- START_STREAK_GRAPH -->.*?<!-- END_STREAK_GRAPH -->",
        f"<!-- START_STREAK_GRAPH -->\n{mermaid}\n<!-- END_STREAK_GRAPH -->",
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
