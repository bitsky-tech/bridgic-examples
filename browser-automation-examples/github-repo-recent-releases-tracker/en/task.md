# Browser Automation Task

## Task Description
Fetch the release information of a specified GitHub repository over the past N days, and perform summarization and analysis.

1. Construct the releases page URL based on the specified repository (`repo_name`): https://github.com/<repo_name>/releases
2. Use a browser to visit the constructed releases page URL.
3. Read each release entry in reverse chronological order. Extract the following information: release name, release date, and release description (this is the main content and may be lengthy). Stop reading once the release date exceeds the specified time range. If there are many releases within the time range, make sure to paginate and continue reading.
4. Store all collected information in order into the file `releases_data.md` in Markdown format. Ensure the file is successfully saved before proceeding to the next step.
5. Summarize the release records stored in the directory, and output the summary in Markdown format to `report.md`. The summary should be concise and must not exceed 400 words. **It is required** to first provide an overall summary describing where the main maintenance effort of the repository was focused during the specified time range. Then, provide brief summaries of key releases, with special emphasis on major feature launches, architectural changes, and significant bug fixes.

## Expected Output
- `releases_data.md`: the release records within the specified time range, in reverse chronological order and Markdown format, containing release name, date, and description.
- `report.md`: a Markdown summary report, no more than 400 words, beginning with an overall summary followed by briefings on key releases.

## Notes (optional)
- Parameter requirements:
  - The repository name `repo_name` should be a parameter of the generated program.
  - The specified time range (in days) should be a parameter of the generated program, with a default of 7 days.
  - Whether to use a headed browser should also be a parameter of the generated program.
- Generate a README file that clearly explains how to use the generated program.
- Verification strategy: after generating the program, verify it with at least the following cases: `repo_name="openclaw/openclaw"` and `repo_name="bitsky-tech/bridgic-browser"`.
