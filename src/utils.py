import unicodedata

import pandas as pd


def get_key_fingerprint(name: str) -> str:
    """
    Transforms a raw name string into a canonical fingerprint for safe comparison.

    Normalization Algorithm:
    1. Unicode Normalization (NFD): Decomposes characters (e.g., 'ã' becomes 'a' + '~').
    2. ASCII Encoding: Strips non-ASCII characters (removes the separated diacritics).
    3. Case Folding: Converts to lowercase.
    4. Whitespace Removal: Removes all spaces to handle "John Doe" vs "JohnDoe".

    Args:
        name (str): The raw input name (e.g., "João  Silva").

    Returns:
        str: The normalized key (e.g., "joaosilva").
    """
    if not isinstance(name, str):
        return ""

    nfkd_form = unicodedata.normalize("NFKD", name)
    only_ascii = nfkd_form.encode("ASCII", "ignore").decode("utf-8")

    return only_ascii.lower().replace(" ", "")


def parse_dates_safely(df: pd.DataFrame, column_name: str = "date") -> pd.DataFrame:
    df[column_name] = pd.to_datetime(
        df[column_name], dayfirst=True, format="mixed", errors="coerce"
    )

    invalid_rows = df[df[column_name].isna()]

    if not invalid_rows.empty:
        bad_indices = invalid_rows.index.tolist()
        raise ValueError(
            f"Date error:\n"
            f"The system could not parse dates in the following rows: {bad_indices}.\n"
            f"Please check for typos or ensure the format is correct (DD/MM/YYYY)."
        )

    df[column_name] = df[column_name].dt.date  # type: ignore

    return df
