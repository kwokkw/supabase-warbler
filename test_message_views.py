"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
os.environ['DATABASE_URL'] = "postgresql://postgres:17273185@localhost/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    # HELPERS

    def do_login(self, client, user):
        """Helper to log a user in """

        # this statement accesses the Flask sesseion, 
        # allowing us to modify it.
        # Flask sessions are usually stored client-side 
        # (using cookies), but here during the test, 
        # the `session_transaction()` allows us to directly
        # interact with and modify the session server-side 
        # for testing purposes.
        with client.session_transaction() as sess:
            # this simulates logging in by manually setting 
            # the session value to represent the logged-in
            # user's ID.
            # this bypasses the usual authentication flow
            # (e.g., logging in through a form) and directly sets the session so the app will treat the test as if the user is logged in. 
            sess[CURR_USER_KEY] = user.id

    # ############################################

    def setUp(self):
        """Create test client, add sample data."""

        # Deletes existing data in the tables
        # Start with a clean database
        User.query.delete()
        Message.query.delete()

        # Create a test client, simulates requests to the app
        # It will be used to send requests to the app during tests
        self.client = app.test_client()

        # Create a test user 
        # Adds the user to the session 
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        # Commits the new test user to the database.
        db.session.commit()

    def tearDown(self):

        db.session.rollback()
        db.session.remove()
    

    # 3. When you’re logged in, can you add a message as yourself?
    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            self.do_login(c, self.testuser)

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            # Send POST request, simulating a form submission.
            # The form data contains a message with text "Hello".
            # `c.post` sends the request as if the user is logged in.
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Query the database to retrieve the newly added message. 
            msg = Message.query.first()
            user = User.query.get(self.testuser.id)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, html)
            self.assertIn(msg, user.messages)


    # 7. When you’re logged in, are you prohibiting from adding a message as another user?
    # 5. When you’re logged out, are you prohibited from adding messages?
    def test_add_message_unauthorized_access(self):

        with self.client as c:

            resp = c.get('/messages/new', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    # 4. When you’re logged in, can you delete a message as yourself?
    def test_delete_message(self):
        """ test deleting a message as a logged-in user """

        # ADD MESSAGE TO USER'S MESSAGE LIST
        msg = Message(text="this is testing")
        self.testuser.messages.append(msg)        
        db.session.commit()

        with self.client as c:
            self.do_login(c, self.testuser)

            user = User.query.get(self.testuser.id)
            msg = user.messages[0]

            resp = c.post(f'/messages/{msg.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(msg.text, html)

    # 8. When you’re logged in, are you prohibiting from deleting a message as another user?
    # 6. When you’re logged out, are you prohibited from deleting messages?
    def test_delete_message_unauthorized_access(self):
        
        # ADD MESSAGE TO USER'S MESSAGE LIST
        msg = Message(text="this is testing")
        self.testuser.messages.append(msg)        
        db.session.commit()

        with self.client as c:

            user = User.query.get(self.testuser.id)
            msg = user.messages[0]

            resp = c.post(f'/messages/{msg.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_message_show(self):

        msg = Message(text="This is testing", user_id=self.testuser.id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:

            msg = Message.query.first()

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, html)


