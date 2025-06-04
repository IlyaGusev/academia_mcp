import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from huggingface_hub import HfApi, DatasetInfo, hf_hub_download

HF_API = HfApi()


def _format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def _clean_entry(entry: DatasetInfo) -> Dict[str, Any]:
    try:
        readme_path = hf_hub_download(repo_id=entry.id, repo_type="dataset", filename="README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
    except Exception:
        readme_content = ""

    return {
        "id": entry.id,
        "created_at": _format_date(entry.created_at),
        "last_modified": _format_date(entry.last_modified),
        "downloads": entry.downloads,
        "likes": entry.likes,
        "tags": entry.tags,
        "readme": readme_content,
    }


def _format_entries(entries: List[DatasetInfo]) -> str:
    clean_entries: List[Dict[str, Any]] = [_clean_entry(entry) for entry in entries]
    return json.dumps({"results": clean_entries}, ensure_ascii=False)


def hf_datasets_search(
    query: Optional[str] = None,
    search_filter: Optional[List[str]] = None,
    limit: Optional[int] = 5,
    sort_by: Optional[str] = "trending_score",
    sort_order: Optional[str] = "descending",
) -> str:
    """
    Search or filter HF datasets.

    Examples:
        List only the datasets in Russian for language modeling:
        hf_datasets_search(filter=(language:ru", "task_ids:language-modeling"))

        List all recent datasets with "text" in their name
        hf_datasets_search(query="text", sort_by="last_modified")

    Returns a JSON object serialized to a string. The structure is: {"results": [...]}
    Every item in the "results" has the following fields:
    ("id", "created_at", "last_modified", "downloads", "likes", "tags")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query for the exact match search.
        search_filter: A list of string to filter datasets.
        limit: The maximum number of items to return. limit=5 by default, limit=10 is the maximum.
        sort_by:
            The key with which to sort the resulting models.
            Possible values are "last_modified", "trending_score", "created_at", "downloads" and "likes".
            "trending_score" by default.
        sort_order: 2 sort orders: ascending, descending. descending by default.
    """
    direction: Optional[Literal[-1]] = -1 if sort_order == "descending" else None
    results = list(
        HF_API.list_datasets(
            search=query,
            sort=sort_by,
            direction=direction,
            limit=limit,
            filter=search_filter,
        )
    )
    return _format_entries(results)
