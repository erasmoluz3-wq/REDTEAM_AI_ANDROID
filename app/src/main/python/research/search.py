import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import ipaddress
import socket

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RedTeamAI/1.0)"
}

def validate_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Protocolo inválido")

    if not parsed.hostname:
        raise ValueError("URL inválida")

    addresses = socket.getaddrinfo(
        parsed.hostname, None, type=socket.SOCK_STREAM
    )

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Endereço privado bloqueado")

    return url


def search_web(query, limit=5):
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select(".result"):
        link = item.select_one(".result__a")
        snippet = item.select_one(".result__snippet")

        if not link:
            continue

        url = link.get("href", "")

        if "/l/?" in url:
            params = parse_qs(urlparse(url).query)
            url = params.get("uddg", [url])[0]

        results.append({
            "title": link.get_text(" ", strip=True),
            "url": url,
            "snippet": snippet.get_text(" ", strip=True)
            if snippet else ""
        })

        if len(results) >= min(max(limit, 1), 10):
            break

    return results


def read_page(url):
    validate_url(url)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15,
        allow_redirects=False
    )
    response.raise_for_status()

    if "text/html" not in response.headers.get("Content-Type", ""):
        raise ValueError("Conteúdo não é HTML")

    if len(response.content) > 2_000_000:
        raise ValueError("Página muito grande")

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup([
        "script", "style", "noscript", "header", "footer", "nav"
    ]):
        element.decompose()

    return {
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "url": url,
        "content": soup.get_text(" ", strip=True)[:12000]
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        for i, result in enumerate(
            search_web(args.query, args.limit), 1
        ):
            print(f"\n[{i}] {result['title']}")
            print(result["url"])
            print(result["snippet"])

    except Exception as error:
        print(f"Erro na pesquisa: {error}")
