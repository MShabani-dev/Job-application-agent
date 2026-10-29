# Job Application Agent

An automated job-application agent built with Python and [browser-use](https://github.com/browser-use/browser-use). It searches Iranian job boards for matching positions, applies to them using a resume PDF, and returns a JSON report of what was applied to and what was skipped.

## Features

- Searches **jobinja.ir**, **jobvision.ir**, and **e-estekhdam.com** for:
  - Python, Backend Python, Full Stack Developer, Frontend React
- Applies to up to a configurable number of jobs per site (`MAX_APPS_PER_SITE`)
- Uploads the resume from a local PDF
- Uses only facts from the profile and resume. It does not invent experience or skills.
- Skips a job and records the reason when:
  - a required question cannot be answered from the profile
  - login is required and the agent is not logged in
  - a CAPTCHA or 2FA cannot be passed
- Avoids applying to the same job twice
- Returns a final JSON report with `applied` (title, company, url) and `skipped` (title, reason)
- Cost controls: step limit (`max_steps`), vision disabled (`use_vision=False`), and a per-site application cap

## Tech Stack

- Python 3
- browser-use (browser automation agent)
- DeepSeek language model, accessed through an OpenAI-compatible API (GapGPT gateway)
- python-dotenv for configuration

## Project Structure

```
job-agent/
├── agent.py          # Main agent script
├── resume.pdf        # Your resume (not committed)
├── .env              # API key (not committed)
├── requirements.txt  # Python dependencies
└── README.md
```

## Setup

### 1. Create and activate a virtual environment (Windows CMD)

```
cd C:\job-agent
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Configure the API key

Create a file named `.env` in the project folder:

```
GAPGPT_API_KEY=sk-your_full_key_here
```

No spaces and no quotes around the key. Never commit this file.

### 4. Add your resume

Place your resume at `resume.pdf` in the project folder.

### 5. Check your account balance

The GapGPT account must have a positive balance. A negative balance returns `403 insufficient_user_quota`.

## Usage

Run the agent:

```
python agent.py
```

For the first run, use a low-cost setup:
- `MAX_APPS_PER_SITE = 1`
- `max_steps = 30`
- one site enabled at a time
- `use_vision = False`

## Output

The agent prints a JSON report at the end:

```json
{
  "applied": [
    {"title": "...", "company": "...", "url": "..."}
  ],
  "skipped": [
    {"title": "...", "reason": "..."}
  ]
}
```

## Configuration Notes

| Setting | Purpose | Recommended first run |
|---|---|---|
| `MAX_APPS_PER_SITE` | Maximum applications per site | `1` |
| `max_steps` | Maximum agent steps per task | `30` |
| `use_vision` | Send screenshots to the model | `False` (DeepSeek limitation) |

## Security

- Keep `.env` out of version control.
- If an API key was ever shared or committed, delete it in the provider dashboard and create a new one.
- The resume PDF contains personal data. Do not publish it.

## Limitations

- Job sites may change their layout, which can break the browser steps.
- Sites that require login or CAPTCHA will be skipped.
- Each run consumes API credit.

## Status

Under development. The first end-to-end runs were blocked by account balance issues, which are being resolved.
