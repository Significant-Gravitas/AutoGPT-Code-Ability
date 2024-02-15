from fuzzywuzzy import fuzz, process


def find_best_match(target: str, choices: list[str], threshold: int = 80):
    # First, try using the standard fuzzy matching
    match = process.extractOne(
        target, choices, scorer=fuzz.ratio, score_cutoff=threshold
    )

    # If no match is found, try partial matching as a fallback
    if not match:
        match = process.extractOne(
            target, choices, scorer=fuzz.partial_ratio, score_cutoff=threshold
        )

    # Optionally, you could add more conditions or checks here for other types of matches

    return match
