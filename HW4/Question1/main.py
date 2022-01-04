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

        for row in csv_reader:
            print(f'User {row[0]} has password {hash_to_password_dict[row[1]]} that was matched to hash {row[1]}')

def salted_dictionary_attack():
    USERNAME_PASSWORD_TABLE_PATH = "salty-digitalcorp.txt"

    with open(USERNAME_PASSWORD_TABLE_PATH) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)

        for username, salt, hash in csv_reader:
            pass

if __name__ == "__main__":
    unsalted_dictionary_attack()