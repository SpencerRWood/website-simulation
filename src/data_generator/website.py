import random
from datetime import timedelta, datetime

class Website:
    """Represents a website with pages and interactions."""
    
    def __init__(self, env, website_structure, current_date, dropoff_probability=None):
        dropoff_probability = {page:data['dropoff_probability'] for page, data in website_structure.items()}
        self.env = env
        self.pages = website_structure  
        self.dropoff_probability = dropoff_probability or {}
        self.current_date = current_date

    def dropoff(self, page):
        """Check if a visitor drops off at a given page."""
        prob = self.dropoff_probability.get(page,0)
        drop = random.random() < prob
        # print(f"Checking drop-off at {page}: Probability={prob}, Result={drop}")
        return drop

    def get_current_time(self):
        """Convert simulation time (in minutes) to a timestamp."""
        current_time = datetime.combine(self.current_date, datetime.min.time()) + timedelta(minutes=self.env.now)
        return current_time.strftime('%Y-%m-%d %H:%M:%S')

class Session:
    """Handles a single visitor's interactions on the website."""
    
    def __init__(self, env, website, visitor, channel='Direct'):
        self.env = env
        self.website = website
        self.visitor = visitor
        self.channel = channel
        self.data = []  

    def interaction(self, page, interaction, element=None):
        """Log a visitor's interaction."""
        self.data.append({
            'visitor_id': self.visitor.visitor_id,
            'channel': self.channel,
            'page': page,
            'interaction': interaction,
            'element': element,
            'timestamp': self.website.get_current_time()
        })

    def visit_page(self, page):
        
        """Handles visiting a page and interacting with elements."""
        self.interaction(page, 'Pageview')

        if self.website.pages.get(page, {}).get("account_creation", False):
            # print(f'Visitor {self.visitor.visitor_id} signed up on {page}')
            self.visitor.complete_signup(session=self.visitor.session)  # Ensure update is committed

        if self.website.dropoff(page):  
            yield self.env.timeout(1)
            return  

        yield self.env.timeout(1)

        if page in self.website.pages and 'clickable_elements' in self.website.pages[page]:
            interactive_elements = self.website.pages[page]['clickable_elements']
            if interactive_elements:
                for element in random.sample(interactive_elements, random.randint(0, len(interactive_elements))):
                    yield self.env.timeout(0.2)
                    self.interaction(page, 'Click', element)

        next_page = None
        if page in self.website.pages and 'navigation_elements' in self.website.pages[page]:
            navigation_elements = self.website.pages[page]['navigation_elements']
            if navigation_elements:  
                next_page = random.choice(navigation_elements)
                yield self.env.timeout(0.2)
                self.interaction(page, 'Click', next_page)
                return next_page
    
        return None  

    def simulate_site_interactions(self):
        """Simulate the visitor's session on the website."""
        current_page = 'Homepage'  
        while current_page:
            # print(f"Visitor {self.visitor.visitor_id} is at {current_page}")
            next_page = yield from self.visit_page(current_page)
            if not next_page:
                # print(f"Visitor {self.visitor.visitor_id} dropped off at {current_page}")
                break  
            current_page = next_page

