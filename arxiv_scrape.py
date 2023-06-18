"""The functions in this file allow you to scrape the daily new papers for exgalcosmo and extract the linkst to the PDFs."""

import requests
from bs4 import BeautifulSoup #!pip install beautifulsoup4
import re


def get_arxiv_links(new_papers_url):
    """Get the links to the PDFs of the daily new papers. Stop parsing once we see <h3>Cross-lists"""
    response = requests.get(new_papers_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Links are all in <dl> tag after New submissions
    cross_lists_tag = soup.find("h3", string=re.compile("New submissions"))
    # Get next tag
    cross_lists = cross_lists_tag.find_next("dl")
    links = cross_lists.find_all("a", attrs={"title": "Download PDF"})
    parsed_links = ["https://arxiv.org" + link["href"] for link in links]
    return remove_duplicates(parsed_links)
    #
    #links = soup.find_all("a", attrs={"title": "Download PDF"})
    #parsed_links = ["https://arxiv.org" + link["href"] for link in links]
    #return remove_duplicates(parsed_links)


def remove_duplicates(links):
    """Remove duplicate links."""
    no_dup = list(set(links))
    return sorted(no_dup, key=links.index)


def get_daily_links():
    """Get the links to the daily new papers."""
    new_papers_url = "https://arxiv.org/list/astro-ph.CO/new"
    links = get_arxiv_links(new_papers_url)
    return links

# Test the code
if __name__ == "__main__":
    links = get_daily_links()
    print(links)
    print(len(links))