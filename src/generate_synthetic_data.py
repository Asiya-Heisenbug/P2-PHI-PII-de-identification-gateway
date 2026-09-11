import argparse
import json
import random
import re
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

LABELS = [
    "NAME", "DATE", "PHONE", "EMAIL", "LOCATION",
    "MRN", "SSN", "URL", "IP", "ACCOUNT_NUM"
]

DIAGNOSES = [
    "hypertension",
    "type 2 diabetes mellitus",
    "chest pain",
    "shortness of breath",
    "acute bronchitis",
    "migraine",
    "lower back pain",
    "seasonal allergies",
    "gastroenteritis",
    "urinary tract infection"
]

MEDICATIONS = [
    "Amlodipine 5 mg once daily",
    "Metformin 500 mg twice daily",
    "Ibuprofen 400 mg as needed",
    "Cetirizine 10 mg once daily",
    "Omeprazole 20 mg once daily"
]


def rand_mrn():
    return "MRN" + str(random.randint(100000, 999999))


def rand_ssn():
    return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def rand_account():
    return "ACC" + str(random.randint(10000000, 99999999))


def make_entity_value(label):
    if label == "NAME":
        return fake.name()
    if label == "DATE":
        return fake.date(pattern="%d/%m/%Y")
    if label == "PHONE":
        return fake.numerify("##########")
    if label == "EMAIL":
        return fake.email()
    if label == "LOCATION":
        return f"{fake.city()} General Hospital"
    if label == "MRN":
        return rand_mrn()
    if label == "SSN":
        return rand_ssn()
    if label == "URL":
        return fake.url()
    if label == "IP":
        return rand_ip()
    if label == "ACCOUNT_NUM":
        return rand_account()
    raise ValueError(label)


def add_entity(text_parts, value, label):
    text_parts.append(value)
    return value, label


def build_note(adversarial=False):
    name = make_entity_value("NAME")
    dob = make_entity_value("DATE")
    phone = make_entity_value("PHONE")
    hospital = make_entity_value("LOCATION")
    visit_date = make_entity_value("DATE")
    mrn = make_entity_value("MRN")

    diagnosis = random.choice(DIAGNOSES)
    medication = random.choice(MEDICATIONS)

    email = make_entity_value("EMAIL")
    ssn = make_entity_value("SSN")
    account = make_entity_value("ACCOUNT_NUM")
    url = make_entity_value("URL")
    ip = make_entity_value("IP")

    templates = [
        (
            f"Patient: {name}\n"
            f"DOB: {dob}\n"
            f"Phone: {phone}\n\n"
            f"{name.split()[0]} was admitted to {hospital} on {visit_date} "
            f"with symptoms consistent with {diagnosis}.\n\n"
            f"Medical Record Number: {mrn}.\n"
            f"Email: {email}\n"
            f"SSN: {ssn}\n"
            f"Billing account: {account}\n"
            f"Portal: {url}\n"
            f"Source IP: {ip}\n"
        ),
        (
            f"The patient {name} visited {hospital} on {visit_date}.\n"
            f"Date of birth: {dob}.\n"
            f"Contact number: {phone}.\n"
            f"Record ID: {mrn}.\n"
            f"For follow-up, contact {email}.\n"
            f"Billing ID: {account}.\n"
            f"Clinical portal: {url}.\n"
            f"Accessing IP: {ip}.\n"
            f"Diagnosis: {diagnosis}.\n"
            f"Medication: {medication}.\n"
        ),
        (
            f"Clinical note for {name}.\n"
            f"The patient was seen at {hospital}.\n"
            f"Visit date: {visit_date}; DOB: {dob}.\n"
            f"Phone: {phone}; email: {email}.\n"
            f"MRN: {mrn}.\n"
            f"SSN: {ssn}; Account: {account}.\n"
            f"Web portal: {url}; IP address: {ip}.\n"
            f"Assessment: {diagnosis}.\n"
            f"Treatment: {medication}.\n"
        )
    ]

    text = random.choice(templates)

    entities = []

    for value, label in [
        (name, "NAME"),
        (dob, "DATE"),
        (phone, "PHONE"),
        (hospital, "LOCATION"),
        (visit_date, "DATE"),
        (mrn, "MRN"),
        (email, "EMAIL"),
        (ssn, "SSN"),
        (account, "ACCOUNT_NUM"),
        (url, "URL"),
        (ip, "IP")
    ]:
        for match in re.finditer(re.escape(value), text):
            entities.append((match.start(), match.end(), label))

    if adversarial:
        ambiguous = random.choice([
            ("Parkinson", "Parkinson's disease"),
            ("Addison", "Addison's disease"),
            ("Hodgkin", "Hodgkin's lymphoma"),
            ("Crohn", "Crohn's disease"),
            ("Grave", "Graves' disease")
        ])

        surname, condition = ambiguous

        extra = (
            f"\nDr. {surname} reviewed the case and found no evidence of {condition}.\n"
            f"Signed by {name}, attending physician.\n"
            f"Contact: {phone}\n"
            f"Reference: {mrn}\n"
        )

        text += extra

        for match in re.finditer(re.escape(name), text):
            entities.append((match.start(), match.end(), "NAME"))

        for match in re.finditer(re.escape(phone), text):
            entities.append((match.start(), match.end(), "PHONE"))

        for match in re.finditer(re.escape(mrn), text):
            entities.append((match.start(), match.end(), "MRN"))

    entities = sorted(set(entities))

    return text, entities


def tokenize_with_tags(text, entities):
    tokens = []
    tags = []

    for match in re.finditer(r"\S+", text):
        token_start = match.start()
        token_end = match.end()
        token = match.group()

        label = None
        entity_start = None

        for entity_start_pos, entity_end_pos, entity_label in entities:
            if token_start < entity_end_pos and token_end > entity_start_pos:
                label = entity_label
                entity_start = entity_start_pos
                break

        if label is None:
            tags.append("O")
        else:
            if token_start <= entity_start:
                tags.append("B-" + label)
            else:
                tags.append("I-" + label)

        tokens.append(token)

    return tokens, tags


def make_split(n, adversarial_frac=0.0):
    records = []

    n_adv = int(n * adversarial_frac)

    for i in range(n):
        adversarial = i < n_adv

        text, entities = build_note(adversarial=adversarial)
        tokens, tags = tokenize_with_tags(text, entities)

        records.append({
            "id": i,
            "text": text,
            "entities": [
                {
                    "start": start,
                    "end": end,
                    "label": label
                }
                for start, end, label in entities
            ],
            "tokens": tokens,
            "tags": tags,
            "adversarial": adversarial
        })

    return records


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--n_train", type=int, default=300)
    parser.add_argument("--n_val", type=int, default=60)
    parser.add_argument("--n_test", type=int, default=60)
    parser.add_argument("--n_adversarial", type=int, default=40)
    parser.add_argument("--out_dir", type=str, default="data")

    args = parser.parse_args()

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train = make_split(
        args.n_train,
        adversarial_frac=0.05
    )

    validation = make_split(
        args.n_val,
        adversarial_frac=0.10
    )

    adversarial_fraction = args.n_adversarial / max(args.n_test, 1)

    test = make_split(
        args.n_test,
        adversarial_frac=min(adversarial_fraction, 1.0)
    )

    for name, records in [
        ("train", train),
        ("validation", validation),
        ("test", test)
    ]:
        output_file = output_dir / f"{name}.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)

        print(
            f"{name}: {len(records)} notes written to {output_file}"
        )


if __name__ == "__main__":
    main()