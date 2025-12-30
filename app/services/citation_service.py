import hashlib

def generate_citation_id(article: dict) -> str:
    base = f"{article['title']}{article['year']}"
    return hashlib.md5(base.encode()).hexdigest()[:8]


def format_apa(article: dict) -> str:
    return (
        f"{article['title']} ({article['year']}). "
        f"{article['source']}. {article['link']}"
    )
