"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
# Import `TestCase` base class that contains different testnig methods
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database)

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
# Isolating the test database
os.environ['DATABASE_URL'] = "postgresql://postgres:17273185@localhost/warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data)

db.create_all()

# TODO: Do I need CSRF key in models testing?

# For tests to work, need to disable CSRF checking in tests
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Access to different testing methods by inheriting from the base TestCase 
class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # Sets up a test client to simulate requests to the app
        self.client = app.test_client()

    
    def tearDown(self):
        """ Clean up database after each test"""

        db.session.rollback()
        

    # Test methods
    # Access to testing methods by passing in self
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # 1. Does the repr method work as expected?
        self.assertEqual(repr(u), f"<User #{u.id}: {u.username}, {u.email}>")


    def test_following_followers_relationships(self):
        """ test the relationships followers and following between users"""


        # Create two users for testing relationships
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u_two = User(
            email="test_two@test.com",
            username="testuser_two",
            password="HASHED_PASSWORD_two"
        )

        u.following.append(u_two)

        db.session.add_all([u, u_two])
        db.session.commit()

        # 2. Does is_following successfully detect when user1 is following user2?
        self.assertTrue(u.is_following(u_two))

        # 3. Does is_following successfully detect when user1 is not following user2?
        self.assertFalse(u_two.is_following(u))

        # 4. Does is_followed_by successfully detect when user1 is followed by user2?
        self.assertTrue(u_two.is_followed_by(u))

        # 5. Does is_followed_by successfully detect when user1 is not followed by user2?
        self.assertFalse(u.is_followed_by(u_two))


    # 6. Does User.create successfully create a new user given valid credentials?
    def test_successful_signup(self):
        """ test a successful user signup """

        # Call the `signup` method with valid data
        valid_user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        db.session.commit()

        found_user = User.query.filter_by(username="testuser").first()

        # Verify the user is an `User` instance
        self.assertIsInstance(found_user, User)

        # Verify the user exists in database
        self.assertIsNotNone(found_user)

        # Verify the password is hashed
        self.assertNotEqual("HASHED_PASSWORD", found_user.password)

        
    # 7. Does User.create fail to create a new user if non-nullable fields fail?
    def test_failed_non_nullable_signup(self):
        """ test a failed user signup due to missing fields"""

        # Attempt to signup without email
        invalid_user = User.signup(
            email=None,
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        # `self.assertRaises()` a method provided by `TestCase`
        # to assert that a specific exception is raised during 
        # the execution of a block code. 
        # It's used when you expect a block of code to fail in 
        # a certain way and want to ensure that failure happens
        # as expected.
        with self.assertRaises(IntegrityError):
            # Code that is expected to raise `SomeException`
            # if the specified exception (`SomeException`) is
            # raised, the test passes. 
            # If no exception or a different exception is 
            # raised, the test fails.
            db.session.commit()


    # 7. Does User.create fail to create a new user if uniqueness fail?
    def test_failed_uniqueness_signup(self):
        """ test a fail user signup due to duplicate username"""


        existing_user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        db.session.commit()

        duplicate_user = User.signup(
            email="testduplicate@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        # `self.assertRaises()` a method provided by `TestCase`
        # to assert that a specific exception is raised during 
        # the execution of a block code. 
        # It's used when you expect a block of code to fail in 
        # a certain way and want to ensure that failure happens
        # as expected.
        with self.assertRaises(IntegrityError):
            # Code that is expected to raise `SomeException`
            # if the specified exception (`SomeException`) is
            # raised, the test passes. 
            # If no exception or a different exception is 
            # raised, the test fails.
            db.session.commit()
    

    # 8. Does ***User.authenticate*** successfully return a user when given a valid username and password?
    def test_successful_authenticate(self):
        """ test a successful user authentication """

        # Create a valid user for testing
        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        db.session.commit()

        auth_user = User.authenticate("testuser", "HASHED_PASSWORD")

        # Check that the `auth_user` is the same as user created
        self.assertIsInstance(auth_user, User)
        self.assertEqual(u, auth_user)


    def test_failed_authenticate(self):
        """ test an invalid username/password authentication """

        # Create a valid user for testing
        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="image_url",
        )

        db.session.commit()

        invalid_username = User.authenticate("invalid username", "HASHED_PASSWORD")
        invalid_pw = User.authenticate("testuser", "invalid password")

        # 9. Does ***User.authenticate*** fail to return a user when the username is invalid?
        self.assertFalse(invalid_username)

        # 10. Does ***User.authenticate*** fail to return a user when the password is invalid?
        self.assertFalse(invalid_pw)