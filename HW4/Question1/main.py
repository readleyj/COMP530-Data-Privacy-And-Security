import hashlib
import csv

DICTIONARY_ATTACK_FILE_PATH = "rockyou.txt"
OUTPUT_TABLE_PATH = "attack_table.csv"
HEADER = ['Password', 'Hash']

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
        writer.writerow(HEADER)

        for data in zip(passwords, password_hashes):
            writer.writerow(data)
