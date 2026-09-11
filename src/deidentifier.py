from src.security import MappingStore


def _find_name_token(original, name_spans, store):
    for other_start, other_end, other_label in name_spans:
        if other_label != "NAME":
            continue

        other_value = store._name_values.get(
            (other_start, other_end)
        )

        if not other_value:
            continue

        if original == other_value:
            return store.get_token(other_value, "NAME")

        original_words = original.lower().split()
        other_words = other_value.lower().split()

        if len(original_words) == 1 and original_words[0] in other_words:
            return store.get_token(other_value, "NAME")

    return None


def deidentify(text, spans, store: MappingStore):
    spans = [
        span for span in spans
        if 0 <= span[0] < span[1] <= len(text)
        and text[span[0]:span[1]].strip()
    ]

    spans = sorted(
        spans,
        key=lambda s: (s[0], -(s[1] - s[0]))
    )

    name_spans = [
        span for span in spans
        if span[2] == "NAME"
    ]

    if not hasattr(store, "_name_values"):
        store._name_values = {}

    for start, end, label in name_spans:
        store._name_values[(start, end)] = text[start:end]

    replacements = []
    summary = {}

    for start, end, label in spans:
        original = text[start:end]

        if label == "NAME":
            token = _find_name_token(
                original,
                name_spans,
                store
            )

            if token is None:
                token = store.get_token(
                    original,
                    label
                )
        else:
            token = store.get_token(
                original,
                label
            )

        if token.startswith("MRN") and label == "MRN":
            token = token.replace("MRNMRN_", "MRN_")

        replacements.append(
            (start, end, token)
        )

        summary[label] = summary.get(label, 0) + 1

    masked = text

    for start, end, token in sorted(
        replacements,
        key=lambda x: x[0],
        reverse=True
    ):
        masked = (
            masked[:start]
            + token
            + masked[end:]
        )

    return masked, summary