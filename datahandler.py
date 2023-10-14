from lib import *


class UserDataHandler:
    """C to handle user data, including encryption and decryption"""

    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.data_folder = pathlib.Path("user_data")
        self.data_folder.mkdir(parents=True, exist_ok=True)

    def _get_user_file_path(self, user_id: str):
        """Method to get the path to a user's data file"""
        return self.data_folder / f"user_{user_id}.json"

    def _load_user_data(self, user_id: str):
        """Method to load a user's data from a file"""
        user_file = self._get_user_file_path(user_id)
        cipher_suite = cryptography.fernet.Fernet(self.encryption_key)
        if not user_file.is_file() or user_file.stat().st_size == 0:
            return {}
        with user_file.open("rb") as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data)

    def _save_user_data(self, user_id: str, data: list):
        """Method to save a user's data to a file"""
        user_file = self._get_user_file_path(user_id)
        cipher_suite = cryptography.fernet.Fernet(self.encryption_key)
        encrypted_data = cipher_suite.encrypt(json.dumps(data).encode())
        with user_file.open("wb") as file:
            file.write(encrypted_data)

    def get_key(self, user_id: str, key: str, default=None):
        """Method to get a key from a user's data"""
        user_data = self._load_user_data(user_id)
        return user_data.get(key, default)

    def set_key(self, user_id: str, key: str, new_value):
        """Method to set a key in a user's data"""
        user_data = self._load_user_data(user_id)
        user_data[key] = new_value
        self._save_user_data(user_id, user_data)

    def add_event(self, user_id: str, new_event: dict):
        """Method to add an event to a user's data"""
        user_data = self._load_user_data(user_id)
        if "events" not in user_data:
            user_data["events"] = []

        event_id = len(user_data["events"])
        new_event["id"] = event_id  # Assign an ID to the new event
        user_data["events"].append(new_event)

        self._save_user_data(user_id, user_data)

    def remove_event(self, user_id: str, event_id: int) -> str:
        """Method to remove an event by its ID"""
        user_data = self._load_user_data(user_id)
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
            self._save_user_data(user_id, user_data)
            return f'Event "**{event_name}**" removed.'
        else:
            return "Event not found."

    def wipe_events(self, user_id: str) -> str:
        """Method to wipe all events for a user"""
        user_data = self._load_user_data(user_id)
        if "events" not in user_data or not user_data["events"]:
            return "No events found."

        user_data["events"] = []
        self._save_user_data(user_id, user_data)
        return "All events have been deleted."
