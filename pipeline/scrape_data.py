import os
from argparse import ArgumentParser
from datetime import date, timedelta

import pandas as pd
import statsapi


OPENING_DAY = date(2022, 4, 7)

COL_NAMES = {
    "game_id": "id",
    "home_name": "home_team",
    "away_name": "away_team",
    "game_date": "date",
    "doubleheader": "dh",
}
SCHED_COLS = [
    "id",
    "home_team",
    "away_team",
    "date",
    "season",
    "week",
    "dh",
    "date_changed",
]
DATA_DIR = os.environ.get("UECKER_DATA_DIR", "output")


def _week_of_season(date_):
    # Opening day is a Thursday, let's call that week 0 and increment on Mondays
    od_week_no = date.isocalendar(OPENING_DAY)[1]
    date_week_no = date.isocalendar(date_)[1]
    return date_week_no - od_week_no


def _determine_result(row, selection):
    status = row["status"]
    if "Final" not in status and "Completed" not in status:
        return -1  # not complete
    # spring training ties not always indicated in status,
    # so check equivalence of scores
    if row["home_score"] == row["away_score"]:
        return 2  # tie
    # otherwise compare winning team to selection team
    # 1 = selection won, 0 = selection lost
    return 1 if row["winning_team"] == selection else 0


def get_outcomes(games):
    items = list()
    for _, row in games.iterrows():
        for i, team in enumerate(("home_team", "away_team")):
            item = {
                "id": f"{row['id']}-{i}",
                "selection_name": row[team],
                "game_id": row["id"],
                "result": _determine_result(row, row[team]),
                "outcome_date": date.today(),
                "runs": row[team.split("_")[0] + "_score"],
            }
            items.append(item)
    out = pd.DataFrame.from_records(items)
    out.result = out.result.astype("Int64")
    out.outcome_date = pd.to_datetime(out.outcome_date).dt.date
    return out.set_index("id")


def get_schedule(games):
    games["date_changed"] = games.status.isin(("Postponed", "Suspended", "Cancelled"))
    return games[SCHED_COLS].set_index("id")


def clean_data(data):
    games = pd.DataFrame.from_records(data)
    games = games.rename(COL_NAMES, axis=1)
    games["date"] = pd.to_datetime(games["date"]).dt.date
    games["dh"] = games["dh"].replace(dict(Y=1, S=1, N=0))
    games["season"] = OPENING_DAY.year
    games["week"] = games["date"].apply(_week_of_season)
    return games


def write_data(schedule, outcomes, date_str, s3=False):
    if s3:
        bucket = os.environ["S3_BUCKET"]
        prefix = f"s3://{bucket}"
    else:
        prefix = DATA_DIR
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
    schedule.to_csv(os.path.join(prefix, f"schedule_{date_str}.csv"))
    outcomes.to_csv(os.path.join(prefix, f"outcomes_{date_str}.csv"))


def main(date_str=None, s3=False):
    if date_str is None:
        today = date.today()
        date_str = today.isoformat()
    else:
        today = date.fromisoformat(date_str)
    yesterday = today - timedelta(days=1)
    end_day = today + timedelta(days=6)
    data = statsapi.schedule(start_date=yesterday, end_date=end_day)
    games = clean_data(data)
    outcomes = get_outcomes(games)
    schedule = get_schedule(games)
    write_data(schedule, outcomes, date_str, s3)


# Entrypoint when run as Lambda function
def lambda_handler(event, context):
    date_str = None
    if "date" in event:
        date_str = event["date"]
    main(date_str, s3=True)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Scrape schedule and outcome data for uecker-bot."
    )
    parser.add_argument(
        "--date",
        help="Date to scrape schedules around in YYYY-MM-DD format",
        default=None,
        required=False,
    )
    parser.add_argument(
        "--s3", help="Write to S3 bucket instead of filesystem", action="store_true"
    )
    args = parser.parse_args()
    main(args.date, args.s3)
