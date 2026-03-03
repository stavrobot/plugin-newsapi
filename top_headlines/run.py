#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys
from pathlib import Path

import requests


KNOWN_PARAMS = {"country", "category", "sources", "query", "count"}


def read_api_key() -> str:
    config = json.loads(Path("../config.json").read_text())
    return config["api_key"]


def build_request_params(params: dict, api_key: str) -> dict:
    request_params: dict = {
        "apiKey": api_key,
        "pageSize": params.get("count", 5),
    }
    if "country" in params:
        request_params["country"] = params["country"]
    if "category" in params:
        request_params["category"] = params["category"]
    if "sources" in params:
        request_params["sources"] = params["sources"]
    if "query" in params:
        request_params["q"] = params["query"]
    return request_params


def trim_article(article: dict) -> dict:
    return {
        "source": article["source"]["name"],
        "author": article.get("author"),
        "title": article.get("title"),
        "description": article.get("description"),
        "url": article.get("url"),
        "published_at": article.get("publishedAt"),
    }


def main() -> None:
    params = json.load(sys.stdin)

    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    # The API requires at least one filter; an empty request returns an error.
    filter_keys = {"country", "category", "sources", "query"}
    if not filter_keys.intersection(params):
        print(
            "At least one of 'country', 'category', 'sources', or 'query' must be provided",
            file=sys.stderr,
        )
        sys.exit(1)

    if "count" in params:
        count = params["count"]
        if not isinstance(count, int) or count < 1 or count > 20:
            print("Parameter 'count' must be an integer between 1 and 20", file=sys.stderr)
            sys.exit(1)

    api_key = read_api_key()
    request_params = build_request_params(params, api_key)

    response = requests.get("https://newsapi.org/v2/top-headlines", params=request_params)

    if not response.ok:
        error_data = response.json()
        print(error_data.get("message", response.text), file=sys.stderr)
        sys.exit(1)

    data = response.json()
    articles = [trim_article(article) for article in data["articles"]]
    json.dump({"total_results": data["totalResults"], "articles": articles}, sys.stdout)


main()
