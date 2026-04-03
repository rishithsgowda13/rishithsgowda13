import os
import requests
import re
from datetime import datetime, timedelta

def get_contributions_from_heatmap(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch heatmap, status code {response.status_code}")
            return []
        
        # Parse the HTML to find all td elements with data-date and id containing "contribution-day"
        # The new GitHub UI uses tooltips, but the table cells still exist in the timeline.
        html = response.text
        
        # Look for data-date="YYYY-MM-DD" and data-level="X"
        days = []
        matches = re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"', html)
        for match in matches:
            date_str = match.group(1)
            level = int(match.group(2))
            days.append({"date": date_str, "contributionCount": level})
        
        if not days:
            # Alternate parsing if GitHub changed their UI classes
            # Let's try capturing from the raw tool-tips or rx-data
            matches = re.finditer(r'<tool-tip.*?>(\d+|No) contributions? on (\w+ \d+, \d+)</tool-tip>', html)
            for match in matches:
                count_str = match.group(1)
                date_text = match.group(2)
                
                # Convert "No" to 0
                count = 0 if count_str == "No" else int(count_str)
                
                # Convert "March 28, 2026" to "2026-03-28"
                date_obj = datetime.strptime(date_text, "%B %d, %Y")
                date_str = date_obj.strftime("%Y-%m-%d")
                
                days.append({"date": date_str, "contributionCount": count})
                
        # Sort chronologically descending
        return sorted(days, key=lambda x: x['date'], reverse=True)
    except Exception as e:
        print(f"Exception fetching heatmap: {e}")
        return []

def calculate_streak(days):
    # Calculate IST time (UTC + 5:30)
    current_time_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date = current_time_ist.date()
    yesterday_date = current_date - timedelta(days=1)

    if not days:
        return 0, current_date, current_date
        
    # Convert list to a lookup dictionary for fast exact-date checking
    days_dict = {d['date']: d['contributionCount'] for d in days}
    
    # Forcefully ignore automated bot commit days
    ignore_dates = ['2026-03-28']
    for d in ignore_dates:
        if d in days_dict:
            days_dict[d] = 0
            
    # Check if there is activity today or yesterday (relative to IST) to keep streak alive
    count_today = days_dict.get(str(current_date), 0)
    count_yesterday = days_dict.get(str(yesterday_date), 0)

    if count_today == 0 and count_yesterday == 0:
        return 0, current_date, current_date

    streak = 0
    # Start iterating backwards from today or yesterday
    check_date = current_date if count_today > 0 else yesterday_date
    
    # Step backwards exactly 1 day at a time, ensuring continuous calendar dates
    while True:
        date_str = str(check_date)
        count = days_dict.get(date_str, 0)
        
        if count > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # We hit a day with exactly 0 contributions (or ignored bot-only day)
            break
            
    return streak, check_date + timedelta(days=1), current_date

def main():
    username = "rishithsgowda13"
    
    print("Fetching contributions from GitHub heatmap...")
    days = get_contributions_from_heatmap(username)
    if not days:
        print("Failed to fetch contributions or no data found.")
        return

    streak, start_date, end_date = calculate_streak(days)
    print(f"Actual verified streak from visual HTML graph: {streak} days")

    # Fetch the original Demolab SVG to keep the rich aesthetics
    print("Fetching Demolab SVG for rich aesthetics...")
    demolab_url = "https://streak-stats.demolab.com?user=rishithsgowda13&hide_border=true&background=0d1117&ring=a78bfa&fire=6a00ff&currStreakLabel=a78bfa&currStreakNum=ffffff&sideLabels=c9d1d9&sideNums=ffffff&dates=6b7280&stroke=0d1117&border_radius=10&date_format=j%20M%5B%20Y%5D"
    
    try:
        svg_resp = requests.get(demolab_url)
        svg_content = svg_resp.text
        
        # Patch the Current Streak Number
        svg_content = re.sub(
            r"(<!-- Current Streak big number -->.*?<text.*?>)\s*\d+\s*(</text>)",
            rf"\g<1>{streak}\g<2>",
            svg_content,
            flags=re.DOTALL
        )
        
        # Patch the Current Streak Date Range
        if streak > 0:
            date_range = f"{start_date.strftime('%b %d').lstrip('0').replace(' 0', ' ')} - {end_date.strftime('%b %d').lstrip('0').replace(' 0', ' ')}"
        else:
            date_range = "No Active Streak"
            
        svg_content = re.sub(
            r"(<!-- Current Streak range -->.*?<text.*?>)\s*.*?(</text>)",
            rf"\g<1>{date_range}\g<2>",
            svg_content,
            flags=re.DOTALL
        )

        with open("github-streak-stats.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        print("Saved accurate streak SVG to github-streak-stats.svg")
    except Exception as e:
        print(f"Failed to fetch/patch SVG: {e}")

    if not os.path.exists("README.md"):
        print("README.md not found!")
        return

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # We will now assume README.md points to github-streak-stats.svg directly instead of STREAK_BADGE.
    print("README process finished.")

if __name__ == "__main__":
    main()
