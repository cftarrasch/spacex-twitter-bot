# SpaceX Launch/Landing Predictor X Bot

Python bot that trains on the public r/SpaceX API and posts a prediction for the next SpaceX launch to X/Twitter.

The bot predicts:

- launch success probability
- booster landing success probability, conditional on a declared landing attempt

It is conservative by default: it runs in dry-run mode unless you explicitly disable it, keeps a local state file to avoid duplicate posts, and refuses to tweet if the API's next launch date is already in the past.

## Data Sources

- API docs: https://docs.spacexdata.com/
- Runtime API base: `https://api.spacexdata.com/v4`
- User reference guide: `/Users/christiantarrasch/Downloads/spacex_twitter_bot_guide.md`

Note: this API is community-run and unaffiliated with SpaceX. During verification in May 2026, the public upcoming-launch data still returned 2022 launches, so the bot includes a stale-data guard.

## Model Caveats

The model is a practical baseline, not a guarantee. SpaceX historical outcomes are highly imbalanced toward success, and the public API does not always contain every operational feature that affects a mission. Treat the output as a transparent estimate based on available public fields.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-build-isolation
cp .env.example .env
```

Fill in `.env` only if you want to post for real.

## Train The Models

```bash
python -m spacex_twitter_bot.train --model-path models/spacex_success.joblib
```

This fetches past launches from the SpaceX API, builds model features, trains launch and landing classifiers, and saves the model bundle.

## Dry Run The Bot

```bash
python -m spacex_twitter_bot.bot --dry-run --force --allow-stale
```

`--force` bypasses the "launch is not close enough" rule. `--allow-stale` is only for local testing against stale API data.

For normal operation:

```bash
python -m spacex_twitter_bot.bot
```

## Real Posting

Set these in `.env`:

```bash
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
DRY_RUN=false
```

Then run:

```bash
python -m spacex_twitter_bot.bot
```

The bot will post only when:

- a model exists
- there is an upcoming launch
- the launch date is not stale
- the launch is within `POST_WINDOW_HOURS`
- the launch has not already been posted in `data/bot_state.json`

## Optional Local Cron

Example: run every 6 hours.

```cron
0 */6 * * * cd /path/to/this/project && . .venv/bin/activate && python -m spacex_twitter_bot.bot >> logs/bot.log 2>&1
```

Create `logs/` first if you use that cron target.
