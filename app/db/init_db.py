from app.db.session import Base, engine

# Import all models here
from app.models.user import User  # Import all models here
from app.models.otp import OTP
from app.models.books import Books

# from app.models.validator import SingleValidation, FileValidation
# from app.models.subscription_stripe import SubscriptionsStripe, Invoices


def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    print("Creating initial database tables...")
    init_db()
    print("Database tables created successfully!")
