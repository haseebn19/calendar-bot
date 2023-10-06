from lib import *


class UserDataHandler:
    """Class to handle user data, including encryption and decryption"""

    def __init__(self, encryption_key=None, data_folder=None):
        self.encryption_key = (encryption_key or os.getenv("ENCRYPTION_KEY")).encode()
        self.data_folder = pathlib.Path(data_folder or "user_data")

        # Ensure the events folder exists, create it if not
        self.data_folder.mkdir(parents=True, exist_ok=True)

    def get_user_file_path(self, user_id: str):
        """Method to get the file path for a specific user"""
        return self.data_folder / f"user_{user_id}.json"

    def load_user_data(self, user_id: str):
        """Method to load user data from an encrypted file"""
        user_file = self.get_user_file_path(user_id)
        cipher_suite = cryptography.fernet.Fernet(self.encryption_key)

        # If file doesn't exist or is empty, return an empty dictionary
        if not user_file.is_file() or user_file.stat().st_size == 0:
            return {}

        # Read and decrypt the data
        with user_file.open("rb") as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data)

    def save_user_data(self, user_id: str, data: list):
        """Method to save user data to an encrypted file"""
        user_file = self.get_user_file_path(user_id)
        cipher_suite = cryptography.fernet.Fernet(self.encryption_key)
        encrypted_data = cipher_suite.encrypt(json.dumps(data).encode())
        with user_file.open("wb") as file:
            file.write(encrypted_data)

    def set_user_timezone(self, user_id: str, timezone: str):
        """Method to set a user's timezone"""
        user_data = self.load_user_data(user_id)
        user_data["timezone"] = timezone
        self.save_user_data(user_id, user_data)

    def get_user_timezone(self, user_id: str):
        """Method to get a user's timezone"""
        user_data = self.load_user_data(user_id)
        return user_data.get("timezone")

    def add_event(self, user_id: str, new_event: dict):
        """Method to add an event to a user's data"""
        user_data = self.load_user_data(user_id)
        if "events" not in user_data:
            user_data["events"] = []

        event_id = len(user_data["events"])
        new_event["id"] = event_id  # Assign an ID to the new event
        user_data["events"].append(new_event)

        self.save_user_data(user_id, user_data)

    def get_privacy(self, user_id: str) -> str:
        """Method to get the privacy setting of a user"""
        user_data = self.load_user_data(user_id)
        return user_data.get("visibility", "private")

    def get_events(self, user_id: str) -> list:
        """Method to get the events of a user"""
        user_data = self.load_user_data(user_id)
        return user_data.get("events", [])

    def remove_event(self, user_id: str, event_id: int) -> str:
        """Method to remove an event by its ID"""
        user_data = self.load_user_data(user_id)
        if "events" not in user_data or not user_data["events"]:
            return "No events found."

        events = user_data["events"]
        event_index = next(
            (index for (index, event) in enumerate(events) if event["id"] == event_id),
            None,
        )

        if event_index is not None:
            event_name = events[event_index]["name"]
            events.pop(event_index)
            self.save_user_data(user_id, user_data)
            return f'Event "**{event_name}**" removed.'
        else:
            return "Event not found."

    def wipe_events(self, user_id: str) -> str:
        """Method to wipe all events for a user"""
        user_data = self.load_user_data(user_id)
        if "events" not in user_data or not user_data["events"]:
            return "No events found."

        user_data["events"] = []
        self.save_user_data(user_id, user_data)
        return "All events have been deleted."

    def set_privacy(self, user_id: str, visibility: str):
        """Method to set the privacy setting for a user"""
        user_data = self.load_user_data(user_id)
        user_data["visibility"] = visibility
        self.save_user_data(user_id, user_data)
