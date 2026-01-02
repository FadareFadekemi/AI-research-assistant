def format_authors_apa(authors: list[str]) -> str:
    """
    Reference list author formatting (APA 7th).
    """
    formatted = []

    for name in authors:
        parts = name.split()
        if len(parts) == 1:
            formatted.append(parts[0])
        else:
            last = parts[-1]
            initials = " ".join(f"{p[0]}." for p in parts[:-1])
            formatted.append(f"{last}, {initials}")

    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} & {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def format_in_text_citation(authors: list[str], year: int | str) -> str:
    """
    APA in-text citation formatting.
    """
    if not authors:
        return f"(n.d.)"

    first_author_last = authors[0].split()[-1]

    if len(authors) == 1:
        return f"({first_author_last}, {year})"
    elif len(authors) == 2:
        second_author_last = authors[1].split()[-1]
        return f"({first_author_last} & {second_author_last}, {year})"
    else:
        return f"({first_author_last} et al., {year})"


def format_apa_reference(source: dict) -> str:
    """
    APA 7th reference list entry.
    """
    authors = format_authors_apa(source.get("authors", []))
    year = source.get("year", "n.d.")
    title = source.get("title", "")
    journal = source.get("journal")
    doi = source.get("doi")
    url = source.get("url")

    citation = f"{authors} ({year}). {title}."

    if journal:
        citation += f" {journal}."

    if doi:
        citation += f" https://doi.org/{doi}"
    elif url:
        citation += f" {url}"

    return citation
