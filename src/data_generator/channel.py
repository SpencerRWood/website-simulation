
import numpy as np

def logistic_saturation(max_users, spend, sat_threshold, scaling_factor):
    return max_users / (1 + np.exp(- (spend - sat_threshold) / (scaling_factor * sat_threshold)))

class Display:
    ##TODO: Simulate user universe so that we can add carry-over effects
    ##Store campaign data per day in database table
    def __init__(self, campaign_name, spend, sat_threshold, scaling_factor=.2, max_users=10000, click_probability = .02):
        """
        Initialize a Display Ad simulation with saturation effects.

        Parameters:
        - spend (float): The ad spend amount.
        - sat_threshold (float): The spend level where diminishing returns start.
        - max_users (int): Maximum potential users that could be reached.
        """
        self.campaign_name = campaign_name
        self.spend = spend
        self.sat_threshold = sat_threshold
        self.max_users = max_users
        self.scaling_factor = scaling_factor
        self.click_probability = click_probability

    def impressions_served(self):
        """
        Calculate the number of users reached based on spend, using a logistic function
        to model saturation effects.

        Returns:
        - int: The number of users reached.
        """

        users_reached = logistic_saturation(self.max_users, self.spend, self.sat_threshold, self.scaling_factor)
        return int(users_reached)
    
    def ad_clicks(self, users_reached):
        clicks = np.random.binomial(users_reached, self.click_probability)
        return int(clicks)
    
class Email:
    def __init__(self):
        ##Email after signup
        ##Email every Tuesday
        ##Email post-signup
        ...

class PaidSearch:
    def __init__(self):
        ...

class PaidSocial:
    def __init__(self):
        ...