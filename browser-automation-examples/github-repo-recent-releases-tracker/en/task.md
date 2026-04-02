# Translate the Following Task into Python Code

## Task Objective  
Fetch the release information of a specified GitHub repository over the past N days, and use `claude -p` to perform summarization and analysis.

## Task Steps  
1. Construct the releases page URL based on the specified repository (`repo_name`):  
   https://github.com/<repo_name>/releases  
   For example, if repo_name="openclaw/openclaw", the URL becomes:  
   https://github.com/openclaw/openclaw/releases  

2. Use a browser to visit the constructed releases page URL.

3. Read each release entry in reverse chronological order. Extract the following information: release name, release date, and release description (this is the main content and may be lengthy). Stop reading once the release date exceeds the specified time range. If there are many releases within the time range, make sure to paginate and continue reading.

4. Store all collected information in order into the file `./outputs/releases_data.md` in Markdown format. Ensure the file is successfully saved before proceeding to the next step.

5. Change directory to `./outputs/`. If this fails, exit with an error.

6. Use `claude -p` to summarize the release records stored in the directory, and output the summary in Markdown format to `./outputs/report.md`.  
   The summary should be concise and must not exceed 400 words.  
   **It is required** to first provide an overall summary describing where the main maintenance effort of the repository was focused during the specified time range. Then, provide brief summaries of key releases, with special emphasis on major feature launches, architectural changes, and significant bug fixes.  
   Please incorporate all these requirements into a well-crafted prompt for `claude -p`.

## Parameter Requirements  
- The repository name `repo_name` should be a parameter of the generated program.  
- The specified time range (in days) should be a parameter of the generated program, with a default of 7 days.  
- Whether to use a headed browser should also be a parameter of the generated program.

## Additional Requirements  
- Generate a README file that clearly explains how to use the generated program.

## Verification Strategy
 - After generating the program, verify it with at least the following cases: repo_name="openclaw/openclaw" and repo_name="bitsky-tech/bridgic-browser".