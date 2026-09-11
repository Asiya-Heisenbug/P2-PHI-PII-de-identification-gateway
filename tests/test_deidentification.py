from src.deidentifier import deidentify
from src.detector import detect
from src.rehydrator import rehydrate
from src.security import MappingStore


def test_masking_is_position_based_for_ambiguous_substrings():
    text = (
        "Dr. Parkinson diagnosed Parkinson's disease. "
        "Wood Memorial Hospital treated Wood."
    )

    masked, _ = deidentify(text, detect(text), MappingStore())

    assert "NAME_001 diagnosed Parkinson's disease" in masked
    assert "Wood Memorial Hospital treated Wood" in masked


def test_zip_and_over_89_age_variants_are_detected_and_rehydrated():
    text = "ZIP: 02139; 94-year-old woman; pt is 92F; age: 91."
    store = MappingStore()
    masked, _ = deidentify(text, detect(text), store)

    assert masked.count("AGE_OVER_89_") == 3
    assert "ZIP_001" in masked

    restored, unknown = rehydrate(masked, store)

    assert restored == text
    assert unknown == []


def test_unknown_placeholder_is_not_invented_or_replaced():
    restored, unknown = rehydrate("Patient NAME-1 has NAME_001.", MappingStore())

    assert restored == "Patient NAME-1 has NAME_001."
    assert unknown == ["NAME_001"]


def test_ambulance_report_identifiers_are_protected():
    text = (
        "Patient Name Whitfield, Marcus D.\n"
        "Date of Birth 03/14/1987 (Age 36)\n"
        "Incident Date / Time 02/11/2024 17:42\n"
        "eastbound Route 9 near mile marker 14\n"
        "Piedmont County General Hospital\n"
        "Run Number EMS-2024-03318\n"
        "Crew: J. Okafor, NRP (Lead) / T. Bianchi, EMT-B."
    )

    masked, _ = deidentify(text, detect(text), MappingStore())

    assert "Whitfield, Marcus D." not in masked
    assert "03/14/1987" not in masked
    assert "Age 36" not in masked
    assert "02/11/2024 17:42" not in masked
    assert "Route 9" not in masked
    assert "Piedmont County General Hospital" not in masked
    assert "EMS-2024-03318" not in masked
    assert "J. Okafor" not in masked
    assert "T. Bianchi" not in masked


def test_patient_name_and_dob_context_are_protected():
    text = "Patient Whitfield, Marcus DOB 03/14/1987"
    store = MappingStore()

    masked, _ = deidentify(text, detect(text), store)

    assert "Whitfield, Marcus" not in masked
    assert "03/14/1987" not in masked
    assert "NAME_001" in masked
    assert "DATE_001" in masked

    restored, unknown = rehydrate(masked, store)
    assert restored == text
    assert unknown == []