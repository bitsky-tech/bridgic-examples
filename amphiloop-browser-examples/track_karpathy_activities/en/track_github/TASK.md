# Browser Automation Task

## Task Description
Track recent activity on Andrej Karpathy's GitHub profile and save the results to a file.

1. Open https://github.com/karpathy.
2. Read each activity in the "Contribution activity" section in reverse chronological order, limited to the specified time range.
3. If needed, click the "Show more activity" button at the bottom of the page to load more activities within the specified time range.
4. Save all retrieved activities to the file `github_activities.json` in JSON format.

## Expected Output
`github_activities.json`: Andrej Karpathy's GitHub contribution activities within the specified time range, in reverse chronological order and JSON format.

## Notes
- Parameters:
  - The time range (in days) should be a parameter of the generated program, with a default of 7 days.
  - Whether to use a headed browser should also be a parameter of the generated program.
- Output a README file explaining how to use the generated program.
