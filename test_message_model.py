""" Message model tests """

import os
from unittest import TestCase

from models import db, Message, User, Follows
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

os.environ['DATABASE_URL'] = "postgresql://postgres:17273185@localhost/warbler_test"

from app import app, CURR_USER_KEY

db.create_all()

# For tests to work, need to disable CSRF checking in tests
app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


# Access to different testing methods by inheriting from the base TestCase 
class MessageModelTestCase(TestCase):
    """ Test views for messages """

    def setUp(self):
        """Create test client, add sample data."""

        # deletes all rows (records) while keeping the table structure intact.
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # Sets up a test client to simulate requests to the app
        self.client = app.test_client()

        self.user = User.signup(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            image_url="/static/images/default-pic.png"
        )

        # finalizes all the changes made to the database
        db.session.commit()


    def tearDown(self):
        """ Clean up database after each test"""

        # Clear the current session
        db.session.remove()


    # 1. Does the message model work as expected?
    def test_message_model(self):
        """ test basic message model """

        # Create a valid user for testing (owner of messages)
        u = self.user

        # Create a message and associate it with the user
        msg = Message(text="testing message model")

        # Associate the message with the user
        u.messages.append(msg)

        # finalizes all the changes made to the database
        db.session.commit()

        # Check the message text is correct
        self.assertEqual(msg.text, "testing message model")

        # Check the message is associated with the user
        self.assertEqual(u.id, msg.user_id)

        # Check the message is in the user's message list
        self.assertIn(msg, u.messages)

        # Check the message has a timestamp
        self.assertIsNotNone(msg.timestamp)

        # Check the message is assigned a primary key
        self.assertIsNotNone(msg.id)

    
    def test_user_message_relationships(self):
        """ test the one-to-many relationship between User and Message models """

        # Create a valid user for testing (owner of messages)
        u = self.user

        # Create two messages
        msg_one = Message(text="first testing message")
        msg_two = Message(text="second testing message")

        # Associate messages with the user
        u.messages.append(msg_one)
        u.messages.append(msg_two)

        # finalizes all the changes made to the database
        db.session.commit()

        # User should have two messages
        self.assertEqual(len(u.messages), 2)

        # The messages should have the correct user id
        self.assertEqual(msg_one.user_id, u.id)
        self.assertEqual(msg_two.user_id, u.id)

        # The user's message should match the messages' text
        self.assertEqual(u.messages[0].text, "first testing message")
        self.assertEqual(u.messages[1].text, "second testing message")


    # 7. Does Message fail to create a new message if non-nullable fields fail?
    def test_message_without_text(self):
        """ test new message failed due to missing text field """

        # Create a valid user for testing (owner of messages)
        u = self.user

        # Create a message object without text field
        invalid_text = Message(text=None)

        # Associate message with the user
        u.messages.append(invalid_text)

        
        # Assert that an IntegrityError is raised when trying to commit a message with a missing non-nullable field
        with self.assertRaises(IntegrityError):
            # finalizes all the changes made to the database
            db.session.commit()
        
        # Undoes uncommitted changes 
        # clean up the session and reset it for future use
        db.session.rollback()

        # The length of users' messages should be 0
        self.assertEqual(len(u.messages), 0)


    def test_message_without_timestamp(self):
        """ test a new message gets a timestamp by default """

        # Create a valid user for testing (owner of messages)
        u = self.user

        msg = Message(text="testing message", timestamp=None)

        # Associate message with the user
        u.messages.append(msg)

        # finalizes all the changes made to the database
        db.session.commit()

        # Ensure the timestamp is not None
        self.assertIsNotNone(msg.timestamp)

    
    def test_message_without_user_id(self):
        """ test a message without a user """

        # Create a message without a user
        msg_without_user = Message(text="Testing a message without user")

        db.session.add(msg_without_user)

        # Assert that an IntegrityError is raised when trying to commit a message with a missing non-nullable field
        with self.assertRaises(IntegrityError):
            # finalizes all the changes made to the database
            db.session.commit()


    # 8. Does ***Message*** successfully return a user when given a message?
    def test_message_associate_with_user(self):
        """ test a message is successfully associated with and returns a user """

        # Create a valid user for testing (owner of messages)
        u = self.user

        # Create a message and associate it with the user
        msg = Message(text="testing message model")

        # Associate the message with user
        u.messages.append(msg)

        # finalizes all the changes made to the database
        db.session.commit()

        # Verify that the message is correctly associated with the user 
        # by checking the user object, user ID, username, 
        # and confirming the message is in the user's messages list.
        self.assertEqual(msg.user, u)
        self.assertEqual(msg.user_id, u.id)
        self.assertEqual(msg.user.username, "testuser")
        self.assertIn(msg, u.messages)


        