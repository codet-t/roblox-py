# Replace "to_replace" in "originalString" with "replace_with" an "occurences" amount of times
# Example: replace_reverse("times", "s", "", 1) -> "time"
# i.e replace "s" in "times" with "", 1 time
def replace_reverse(original_string: str, to_replace: str, replace_with: str, occurrences: int = 1) -> str:
    reverse_splits: list[str] = original_string.rsplit(to_replace, occurrences)
    return replace_with.join(reverse_splits)