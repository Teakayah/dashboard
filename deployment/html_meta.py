import html
import re

RE_TITLE = re.compile(
    r'''
    <title[^>]*>  # Match the opening <title> tag and any attributes
    (.*?)         # Group 1: Non-greedily capture the inner text
    </title>      # Match the closing </title> tag
    ''',
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

RE_META_DESC = re.compile(
    r'''
    <meta[^>]*                  # Match the opening <meta tag and any attributes before 'name'
    name=["\']description["\']  # Match the name attribute with either single or double quotes
    [^>]*                       # Match any intermediate attributes before 'content'
    content=["\'](.*?)["\']     # Group 1: Non-greedily capture the actual description text
    ''',
    re.IGNORECASE | re.VERBOSE,
)

RE_SUBTITLE = re.compile(
    r'''
    <([a-zA-Z0-9]+)                              # Group 1: Capture the HTML opening tag name (e.g., div, span, p)
    [^>]*class=["\'][^"\']*subtitle[^"\']*["\']  # Ensure the tag has a class attribute containing 'subtitle'
    [^>]*>                                       # Match the remainder of the opening tag
    (.*?)                                        # Group 2: Non-greedily capture the inner content
    </\1>                                        # Use \1 backreference to match the exact closing tag from Group 1
    ''',
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_WHITESPACE = re.compile(r'\s+')

def extract_title(content: str, stem: str) -> str:
    m = RE_TITLE.search(content)
    raw = m.group(1).strip() if m else stem.replace('_', ' ').title()
    return html.unescape(raw)

def extract_description(content: str, filename: str, descriptions: dict | None = None) -> str:
    # 1. <meta name="description">
    m = RE_META_DESC.search(content)
    if m:
        return html.unescape(m.group(1).strip())

    # 2. Subtitle element
    m = RE_SUBTITLE.search(content)
    if m:
        text = RE_HTML_TAGS.sub('', m.group(2)).strip()
        text = RE_WHITESPACE.sub(' ', text)
        if len(text) > 120:
            text = text[:117] + '…'
        return html.unescape(text)

    # 3. Pre-generated description from descriptions.json
    desc = ''
    if descriptions:
        desc = descriptions.get(filename, '')
    return html.unescape(desc)
