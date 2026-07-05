def generate_initials(name: str) -> str:
    """First letter of each word (max 2, uppercase) — e.g. 'Jane Smith' -> 'JS'."""
    letters = "".join(word[0] for word in name.split() if word)
    return letters[:2].upper()
