import hashlib
import csv

DICTIONARY_ATTACK_FILE_PATH = "rockyou.txt"
OUTPUT_TABLE_PATH = "attack_table.csv"
OUTPUT_TABLE_HEADER = ["Password", "Hash"]

USERNAME_PASSWORD_TABLE_PATH = "digitalcorp.txt"

if __name__ == "__main__":
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
        line_count = 0

        for row in csv_reader:
            if line_count >= 1:
                print(f'User {row[0]} has password {hash_to_password_dict[row[1]]} that was matched to hash {row[1]}')

            line_count += 1


