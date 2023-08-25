from lib import *


# Class to handle user data, including encryption and decryption
class UserDataHandler:
    def __init__(self, encryption_key, data_folder):
        self.encryption_key = encryption_key.encode()  # Key for encryption
        self.data_folder = pathlib.Path(data_folder)  # Folder to store event files

        # Ensure the events folder exists, create it if not
        self.events_folder.mkdir(parents=True, exist_ok=True)

    # Method to get the file path for a specific user
    def get_user_file_path(self, user_id: str):
        return self.data_folder / f"user_{user_id}.json"

    # Method to load user data from an encrypted file
    def load_user_data(self, user_id: str):
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

    # Method to save user data to an encrypted file
    def save_user_data(self, user_id: str, data: list):
        user_file = self.get_user_file_path(user_id)
        cipher_suite = cryptography.fernet.Fernet(self.encryption_key)
        encrypted_data = cipher_suite.encrypt(json.dumps(data).encode())
        with user_file.open("wb") as file:
            file.write(encrypted_data)

    # Method to set a user's timezone
    def set_user_timezone(self, user_id: str, timezone: str):
        user_data = self.load_user_data(user_id)
        user_data["timezone"] = timezone
        self.save_user_data(user_id, user_data)

    # Method to get a user's timezone
    def get_user_timezone(self, user_id: str):
        user_data = self.load_user_data(user_id)
        return user_data.get("timezone")
