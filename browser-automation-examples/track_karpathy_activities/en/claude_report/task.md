## Task Objective
Write a Shell script. This script should call the `claude -p` command to analyze local file data in a specified directory and produce an analysis report.

## Task Description
1. First, change directory (`cd`) to `../tracking_results/`. If changing directory fails, exit with an error and do not continue.
2. After entering `../tracking_results/`, run `claude -p` to analyze the three files in this directory: `github_activities.json`, `x_posts.json`, and `google_search_results.json`. Then organize the output into a Markdown analysis report and write it to `../tracking_results/karpathy_report.md`. Below are specific requirements; construct the `claude -p` instruction arguments accordingly.
    - Based on the GitHub information, summarize Andrej Karpathy’s major research directions in recent months, his primary areas of focus, and any major findings or theoretical breakthroughs.
    - Based on the X information, summarize Andrej Karpathy’s latest updates in recent days: what thoughts he has shared, how they relate to his major research directions, who he interacts with most frequently, etc.
    - Use the Google Search information as supplementary context.

## Other Requirements
 - Output a README file explaining how to use the generated script.