#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys
from pathlib import Path

import requests


KNOWN_PARAMS = {"query", "from_date", "to_date", "domains", "language", "sort_by", "count"}


def read_api_key() -> str:
    config = json.loads(Path("../config.json").read_text())
    return config["api_key"]


def build_request_params(params: dict, api_key: str) -> dict:
    request_params: dict = {
        "apiKey": api_key,
        "q": params["query"],
        "pageSize": params.get("count", 5),
    }
    if "from_date" in params:
        request_params["from"] = params["from_date"]
    if "to_date" in params:
        request_params["to"] = params["to_date"]
    if "domains" in params:
        request_params["domains"] = params["domains"]
    if "language" in params:
        request_params["language"] = params["language"]
    if "sort_by" in params:
        request_params["sortBy"] = params["sort_by"]
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

    if "query" not in params:
        print("Missing required parameter: query", file=sys.stderr)
        sys.exit(1)

    if "count" in params:
        count = params["count"]
        if not isinstance(count, int) or count < 1 or count > 20:
            print("Parameter 'count' must be an integer between 1 and 20", file=sys.stderr)
            sys.exit(1)

    api_key = read_api_key()
    request_params = build_request_params(params, api_key)

    response = requests.get("https://newsapi.org/v2/everything", params=request_params)

    if not response.ok:
        error_data = response.json()
        print(error_data.get("message", response.text), file=sys.stderr)
        sys.exit(1)

    data = response.json()
    articles = [trim_article(article) for article in data["articles"]]
    json.dump({"total_results": data["totalResults"], "articles": articles}, sys.stdout)


main()
