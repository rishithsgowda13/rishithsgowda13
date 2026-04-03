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
        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            return []
            
        if 'data' not in data or not data['data'] or not data['data']['user']:
            print("Error: Invalid response structure")
            return []

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
        
    # GitHub contributions are in UTC
    current_date = datetime.utcnow().date()
    yesterday_date = current_date - timedelta(days=1)
    
    # Today or yesterday must have a contribution to keep the streak alive
    has_activity_today = next((d for d in days if d['date'] == str(current_date) and d['contributionCount'] > 0), None)
    has_activity_yesterday = next((d for d in days if d['date'] == str(yesterday_date) and d['contributionCount'] > 0), None)

    if not has_activity_today and not has_activity_yesterday:
        return 0

    streak = 0
    # Start checking from the most recent day with activity
    start_date = current_date if has_activity_today else yesterday_date
    
    for day in days:
        d = datetime.strptime(day['date'], '%Y-%m-%d').date()
        if d > start_date:
            continue
        if day['contributionCount'] > 0:
            streak += 1
        else:
            # If we were at start_date and found 0, the streak is over if it's before start_date
            if d < start_date:
                break
    return streak

def generate_mermaid_graph(days, limit=14):
    if not days:
        return "```mermaid\ngitGraph\n    commit id: \"No data\"\n```"

    # Take the last 'limit' days
    graph_days = sorted(days[:limit], key=lambda x: x['date'])
    mermaid = "```mermaid\ngitGraph\n"
    
    # Always start with a baseline commit to ensure the graph renders
    # Use the first date in our window or a generic "Start" node
    first_date = graph_days[0]['date']
    mermaid += f'    commit id: "streak_start" tag: "{first_date}"\n'
    
    # Then add activity
    for day in graph_days:
        date_str = day['date']
        count = day['contributionCount']
        if count > 0:
            # We skip the very first day if we already used it for baseline, but multiple commits on same day are fine
            mermaid += f'    commit id: "{date_str}"\n'
        else:
            # Visualizing breaks as branches or just skipping?
            # Creating branches for every break might look messy if there are many.
            # Let's just use a special commit for "no activity" or just skip.
            # Actually, the user liked the branch idea, but let's make it cleaner.
            pass
    
    mermaid += "```"
    return mermaid

def main():
    username = "rishithsgowda13"
    token = os.getenv("GH_TOKEN")
    
    if not token:
        print("GH_TOKEN not found. If this is local, set the environment variable. Skipping.")
        return

    print("Fetching contributions...")
    days = get_contributions(username, token)
    if not days:
        print("Failed to fetch contributions or no data found.")
        return

    streak = calculate_streak(days)
    mermaid = generate_mermaid_graph(days)
    print(f"Current streak: {streak} days")

    if not os.path.exists("README.md"):
        print("README.md not found!")
        return

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Update Streak Count
    new_streak_text = f"<!-- STREAK_COUNT -->🔥 {streak} days<!-- STREAK_COUNT_END -->"
    content = re.sub(
        r"<!-- STREAK_COUNT -->.*?<!-- STREAK_COUNT_END -->",
        new_streak_text,
        content,
        flags=re.DOTALL
    )

    # Update Mermaid Graph
    new_graph_text = f"<!-- START_STREAK_GRAPH -->\n{mermaid}\n<!-- END_STREAK_GRAPH -->"
    content = re.sub(
        r"<!-- START_STREAK_GRAPH -->.*?<!-- END_STREAK_GRAPH -->",
        new_graph_text,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
