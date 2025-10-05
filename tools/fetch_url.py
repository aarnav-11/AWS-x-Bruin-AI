from __future__ import annotations

import re
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str, timeout: int = 15) -> str:
    print(f"[fetch_url] GET {url} (timeout={timeout}s)")
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        print(f"[fetch_url] OK {url} status={resp.status_code} len={len(resp.text)}")
        return resp.text
    except Exception as e:
        print(f"[fetch_url] ERROR {url}: {e}")
        return f"""<!-- FETCH_ERROR: {e} -->"""


def absolute_url(base_url: str, href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        prefix = "https:" if base_url.startswith("https") else "http:"
        return prefix + href
    # Basic relative resolution
    if href.startswith("/"):
        m = re.match(r"^(https?://[^/]+)", base_url)
        if m:
            return m.group(1) + href
    # Fallback simple join
    if base_url.endswith("/") or href.startswith("/"):
        return base_url + href
    return base_url + "/" + href


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(" \n ")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        href_abs = absolute_url(base_url, href)
        links.append(href_abs)
    return links


def crawl_website(root_url: str, max_pages: int = 5) -> Tuple[str, List[str]]:
    """
    Crawl a site up to ~1 depth, aggregate text content.
    Returns (combined_text, visited_urls)
    """
    visited: List[str] = []
    combined_text_parts: List[str] = []

    print(f"[crawl] root={root_url} max_pages={max_pages}")
    root_html = fetch_html(root_url)
    visited.append(root_url)
    combined_text_parts.append(extract_visible_text(root_html))
    links = extract_links(root_html, root_url)

    # Filter to same domain simple heuristic
    domain_match = None
    m = re.match(r"^(https?://[^/]+)", root_url)
    if m:
        domain_match = m.group(1)

    for link in links:
        if len(visited) >= max_pages:
            break
        if domain_match and not link.startswith(domain_match):
            continue
        if link in visited:
            continue
        print(f"[crawl] visiting {link}")
        html = fetch_html(link)
        visited.append(link)
        combined_text_parts.append(extract_visible_text(html))

    combined_text = "\n\n".join([p for p in combined_text_parts if p])
    print(f"[crawl] visited={len(visited)} pages")
    return combined_text, visited
