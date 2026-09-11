import re


TOKEN_PATTERN = re.compile(
    r"\b(?:NAME|LOCATION|DATE|PHONE|FAX|MRN|SSN|EMAIL|ZIP|"
    r"ACCOUNT_NUM|HEALTH_PLAN|LICENSE|VEHICLE|DEVICE|URL|IP|"
    r"AGE_OVER_89|AGE|GEO|OTHER_ID|OTHER)_\d{3}\b"
)


def rehydrate(llm_text, store):
    unknown_tokens = []

    def replace_token(match):
        token = match.group(0)

        original = store.resolve(token)

        if original is None:
            if token not in unknown_tokens:
                unknown_tokens.append(token)

            return token

        return original

    rehydrated = TOKEN_PATTERN.sub(
        replace_token,
        llm_text
    )

    return rehydrated, unknown_tokens