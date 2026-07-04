import os
import requests

def main():
    print("Fetching Demolab SVG for rich aesthetics...")
    demolab_url = "https://streak-stats.demolab.com?user=rishithsgowda13&hide_border=true&background=0d1117&ring=a78bfa&fire=6a00ff&currStreakLabel=a78bfa&currStreakNum=ffffff&sideLabels=c9d1d9&sideNums=ffffff&dates=6b7280&stroke=0d1117&border_radius=10&date_format=j%20M%5B%20Y%5D"
    
    try:
        svg_resp = requests.get(demolab_url)
        svg_content = svg_resp.text
        
        # The user's streak started on Feb 27th IST, but Demolab (UTC) counts it from Feb 26th.
        # Patch the date range text.
        svg_content = svg_content.replace("26 Feb -", "27 Feb -")
        
        with open("github-streak-stats.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        print("Saved accurate streak SVG to github-streak-stats.svg")
    except Exception as e:
        print(f"Failed to fetch/patch SVG: {e}")

if __name__ == "__main__":
    main()
