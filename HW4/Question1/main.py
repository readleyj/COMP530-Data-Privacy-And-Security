import hashlib
import csv

DICTIONARY_ATTACK_FILE_PATH = "rockyou.txt"


def unsalted_dictionary_attack():
    OUTPUT_TABLE_PATH = "attack_table.csv"
    OUTPUT_TABLE_HEADER = ["Password", "Hash"]

    USERNAME_PASSWORD_TABLE_PATH = "digitalcorp.txt"

    with open(DICTIONARY_ATTACK_FILE_PATH) as file:
        lines = file.readlines()
        passwords = [line.rstrip() for line in lines]

        password_hashes = [
            hashlib.sha512(password.encode('utf-8')).hexdigest()
            for password in passwords
        ]

    with open(OUTPUT_TABLE_PATH, 'w+') as file:
        writer = csv.writer(file)
        writer.writerow(OUTPUT_TABLE_HEADER)

        for data in zip(passwords, password_hashes):
            writer.writerow(data)

    hash_to_password_dict = {password_hash: password for password_hash, password in zip(password_hashes, passwords)}

    with open(USERNAME_PASSWORD_TABLE_PATH) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)

        for username, hash in csv_reader:
            print(f'User {username} has password {hash_to_password_dict[hash]} that was matched to hash {hash}')

def salted_dictionary_attack():
    USERNAME_PASSWORD_TABLE_PATH = "salty-digitalcorp.txt"

    with open(USERNAME_PASSWORD_TABLE_PATH) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)

        for username, salt, hash in csv_reader:
                with open(DICTIONARY_ATTACK_FILE_PATH) as file:
                    lines = file.readlines()
                    passwords = [line.rstrip() for line in lines]

                attack_table = {hashlib.sha512((salt + password).encode('utf-8')).hexdigest(): password for password in passwords}

                print(f'User {username} has password {attack_table[hash]} that was matched to hash {hash} with salt {salt}')

if __name__ == "__main__":
    print("Running unsalted dictionary attack")
    unsalted_dictionary_attack()

    print()

    print("Running salted dictionary attack")
    salted_dictionary_attack()