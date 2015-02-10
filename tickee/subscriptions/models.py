from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Date, Boolean, String
from tickee.core.db.types import MutationDict, JSONEncodedDict
from tickee.exceptions import SubscriptionError
from tickee.subscriptions.plans import FREE, PREMIUM, PREMIUMPRO
import datetime
import plans
import sqlahelper
import sqlalchemy.orm as orm

Base = sqlahelper.get_base()

# -- mapping database to python -----------------------------------------------

subscriptions = {
    FREE: plans.FreeSubscriptionPlan(),
    PREMIUM: plans.PremiumSubscriptionPlan(),
    PREMIUMPRO: plans.PremiumProSubscriptionPlan()
}

# -- database model -----------------------------------------------------------

class Subscription(Base):
    """
    The general ``Account`` used to register organizers and visitors of events
    """
    
    __tablename__ = 'tickee_subscriptions'
    
    # Columns
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('tickee_accounts.id'))
    subscription_reference = Column(String, index=True)
    subscription_type = Column(Integer)
    end_date = Column(Date)
    meta = Column(MutationDict.as_mutable(JSONEncodedDict))
    
    # Relations
    
    account = orm.relationship('Account', backref=orm.backref('subscription', uselist=False))
    
    # Construction
    
    def __init__(self, subscription_type):
        self.subscription_type = subscription_type
        self.meta = {}
    
    # Methods
    
    def get_subscription(self):
        """ Returns the ``SubscriptionPlan`` associated with the subscription."""
        sub = subscriptions.get(self.subscription_type)
        if sub is None:
            raise SubscriptionError('unknown subscription type found.')
        return sub
    
    def get_feature(self, feature):
        """ Returns the value of a feature corresponding to the plan """
        sub = self.get_subscription()
        return getattr(sub, feature, None)
        
    
    def is_active(self):
        """ Returns True if subscription is still active """
        if self.subscription_type == FREE:
            return True
        else:
            return datetime.date.today() <= self.end_date
        