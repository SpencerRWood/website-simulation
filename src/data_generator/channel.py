import numpy as np
import pandas as pd
from datetime import datetime
from .visitor import Visitor

class Display:
    def __init__(self, campaign_row):
        self.name = campaign_row['campaign_name']
        self.daily_spend = campaign_row['daily_spend']
        self.channel = campaign_row['channel']

    def generate_visitors(self, current_date, db_session, cpm=2):
        impressions = self.daily_spend / cpm
        click_through_rate = 0.02
        num_visitors = int(impressions * click_through_rate)
        return [
            Visitor(db_session=db_session, created_at=current_date, channel='Display')
            for _ in range(num_visitors)
        ]

class Email:
    def __init__(self, campaign_row):
        self.name = campaign_row['campaign_name']
        self.schedule = campaign_row.get('schedule')
        self.channel = campaign_row['channel']

    def is_scheduled_today(self, current_date):
        return self.schedule == 'weekly_tuesday' and current_date.weekday() == 1

    def generate_visitors(self, current_date, db_session, email_users):
        if not self.is_scheduled_today(current_date):
            return []

        open_rate = 0.3
        click_rate = 0.02  # 2% of sends

        num_sends = len(email_users)
        num_opens = int(num_sends * open_rate)
        num_clicks = int(num_sends * click_rate)

        if num_clicks == 0 or num_opens == 0:
            return []

        opened_users = np.random.choice(email_users, num_opens, replace=False)
        clicked_users = np.random.choice(opened_users, num_clicks, replace=False)
        for visitor in clicked_users:
            visitor.return_visitor = True  # Optional update
            visitor.channel = 'Email'     # Optional update
        return list(clicked_users)
    
def generate_normalized_spend(total_spend, active_days, pct_std_dev=0.1):
    base_spend = total_spend / active_days
    std_dev = base_spend * pct_std_dev
    daily_spends = np.random.normal(loc=base_spend, scale=std_dev, size=active_days)
    daily_spends = daily_spends / daily_spends.sum() * total_spend
    return np.round(daily_spends, 2)

def build_campaign_activity_lookup(df):
    activity_by_day = {}

    for idx, row in df.iterrows():
        campaign_id = idx
        campaign_name = row["campaign_name"]
        channel = row["channel"]
        total_spend = row["spend"]

        start = pd.to_datetime(row["start_date"]).date()
        end = pd.to_datetime(row["end_date"]).date()
        active_days = (end - start).days + 1

        daily_spend = generate_normalized_spend(total_spend, active_days)
        date_range = pd.date_range(start, end)

        for i, date in enumerate(date_range):
            date_key = date.date()
            activity_by_day.setdefault(date_key, []).append({
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "channel": channel,
                "daily_spend": daily_spend[i],
                "schedule": row.get("schedule", None),
                "event_trigger": row.get("event_trigger", None),
                "trigger_type": row.get("trigger_type", None),
            })

    return activity_by_day