from lib import *


class UserDataHandler:
    """Class to handle user data, including encryption and decryption"""

    def __init__(self, encryption_key, data_folder):
        self.encryption_key = encryption_key.encode()  # Key for encryption
        self.data_folder = pathlib.Path(data_folder)  # Folder to store event files

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
