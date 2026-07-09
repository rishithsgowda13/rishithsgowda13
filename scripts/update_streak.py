import os
import requests
import re
from datetime import datetime, timedelta

def get_contributions(username):
    token = os.environ.get("GH_TOKEN")
    days = []
    total_contributions = 0
    
    if not token:
        print("Warning: GH_TOKEN not found! The GraphQL query requires a token to see private contributions.")
        return [], 0

    query = """
    query($userName:String!) {
      user(login: $userName){
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    variables = {"userName": username}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            calendar = data.get("data", {}).get("user", {}).get("contributionsCollection", {}).get("contributionCalendar", {})
            total_contributions = calendar.get("totalContributions", 0)
            
            for week in calendar.get("weeks", []):
                for day in week.get("contributionDays", []):
                    days.append({"date": day["date"], "contributionCount": day["contributionCount"]})
                    
            days = sorted(days, key=lambda x: x['date'], reverse=True)
            return days, total_contributions
        else:
            print(f"GraphQL API failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Exception fetching GraphQL: {e}")
        
    return [], 0

def calculate_streaks(days):
    # Calculate IST time (UTC + 5:30)
    current_time_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date = current_time_ist.date()
    yesterday_date = current_date - timedelta(days=1)

    if not days:
        return 0, current_date, current_date, 0, current_date, current_date, current_date
        
    days_dict = {d['date']: d['contributionCount'] for d in days}
    
    # Forcefully ignore automated bot commit days
    ignore_dates = ['2026-03-28']
    for d in ignore_dates:
        if d in days_dict:
            days_dict[d] = 0
            
    # 1. Calculate Current Streak
    count_today = days_dict.get(str(current_date), 0)
    count_yesterday = days_dict.get(str(yesterday_date), 0)

    current_streak = 0
    curr_start_date = current_date
    curr_end_date = current_date

    if count_today > 0 or count_yesterday > 0:
        check_date = current_date if count_today > 0 else yesterday_date
        curr_end_date = check_date
        while True:
            date_str = str(check_date)
            if days_dict.get(date_str, 0) > 0:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        curr_start_date = check_date + timedelta(days=1)

    # 2. Calculate Longest Streak
    longest_streak = 0
    longest_start_date = current_date
    longest_end_date = current_date
    
    temp_streak = 0
    temp_start_date = None
    
    earliest_date_str = min(days_dict.keys())
    earliest_date = datetime.strptime(earliest_date_str, "%Y-%m-%d").date()
    
    iter_date = earliest_date
    while iter_date <= current_date:
        date_str = str(iter_date)
        count = days_dict.get(date_str, 0)
        
        if count > 0:
            if temp_streak == 0:
                temp_start_date = iter_date
            temp_streak += 1
            
            if temp_streak >= longest_streak:
                longest_streak = temp_streak
                longest_start_date = temp_start_date
                longest_end_date = iter_date
        else:
            temp_streak = 0
            
        iter_date += timedelta(days=1)
        
    return current_streak, curr_start_date, curr_end_date, longest_streak, longest_start_date, longest_end_date, earliest_date

def main():
    username = "rishithsgowda13"
    
    print("Fetching contributions from GitHub GraphQL API...")
    days, total_contributions = get_contributions(username)
    if not days:
        print("Failed to fetch contributions or no data found.")
        # We continue anyway to potentially reset Demolab's broken values to 0 properly, or we can just return.
        # But wait, if they just set it up locally, GH_TOKEN might not be set.
    
    curr_streak, curr_start, curr_end, longest_streak, longest_start, longest_end, earliest_date = calculate_streaks(days)
    print(f"Total: {total_contributions}, Current: {curr_streak}, Longest: {longest_streak}")

    print("Fetching Demolab SVG for rich aesthetics...")
    demolab_url = f"https://streak-stats.demolab.com?user={username}&hide_border=true&background=0d1117&ring=a78bfa&fire=6a00ff&currStreakLabel=a78bfa&currStreakNum=ffffff&sideLabels=c9d1d9&sideNums=ffffff&dates=6b7280&stroke=0d1117&border_radius=10&date_format=j%20M%5B%20Y%5D"
    
    try:
        svg_resp = requests.get(demolab_url)
        svg_content = svg_resp.text
        
        # Helper to patch SVG segments
        def patch_svg(content, marker, new_value):
            return re.sub(
                rf"(<!-- {marker} -->.*?<text.*?>)\s*.*?(</text>)",
                rf"\g<1>{new_value}\g<2>",
                content,
                flags=re.DOTALL
            )
            
        # Format dates
        def fmt_date(d):
            return d.strftime('%b %d').lstrip('0').replace(' 0', ' ')
            
        def fmt_year(d):
            return d.strftime('%b %d, %Y').lstrip('0').replace(' 0', ' ')

        # 1. Total Contributions
        svg_content = patch_svg(svg_content, "Total Contributions big number", f"{total_contributions:,}")
        if total_contributions > 0:
            total_range = f"{fmt_year(earliest_date)} - Present"
        else:
            total_range = "No Contributions"
        svg_content = patch_svg(svg_content, "Total Contributions range", total_range)
        
        # 2. Current Streak
        svg_content = patch_svg(svg_content, "Current Streak big number", str(curr_streak))
        if curr_streak > 0:
            curr_range = f"{fmt_date(curr_start)} - {fmt_date(curr_end)}"
        else:
            curr_range = "No Active Streak"
        svg_content = patch_svg(svg_content, "Current Streak range", curr_range)
        
        # 3. Longest Streak
        svg_content = patch_svg(svg_content, "Longest Streak big number", str(longest_streak))
        if longest_streak > 0:
            long_range = f"{fmt_date(longest_start)} - {fmt_date(longest_end)}"
        else:
            long_range = "No Active Streak"
        svg_content = patch_svg(svg_content, "Longest Streak range", long_range)

        with open("github-streak-stats.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        print("Saved accurate streak SVG to github-streak-stats.svg")
    except Exception as e:
        print(f"Failed to fetch/patch SVG: {e}")

if __name__ == "__main__":
    main()
