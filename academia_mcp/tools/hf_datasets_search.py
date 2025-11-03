from datetime import datetime
from typing import List, Literal, Optional

from huggingface_hub import DatasetInfo, HfApi, hf_hub_download
from pydantic import BaseModel, Field

HF_API = HfApi()


class HFDatasetsSearchEntry(BaseModel):  # type: ignore
    id: str = Field(description="ID of the dataset")
    created_at: str = Field(description="Created date of the dataset")
    last_modified: str = Field(description="Last modified date of the dataset")
    downloads: int = Field(description="Downloads of the dataset")
    likes: int = Field(description="Likes of the dataset")
    tags: List[str] = Field(description="Tags of the dataset")
    readme: str = Field(description="README of the dataset")


class HFDatasetsSearchResponse(BaseModel):  # type: ignore
    results: List[HFDatasetsSearchEntry] = Field(description="List of datasets")


def _format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def _clean_entry(entry: DatasetInfo) -> HFDatasetsSearchEntry:
    try:
        readme_path = hf_hub_download(repo_id=entry.id, repo_type="dataset", filename="README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
    except Exception:
        readme_content = ""

    return HFDatasetsSearchEntry(
        id=entry.id,
        created_at=_format_date(entry.created_at),
        last_modified=_format_date(entry.last_modified),
        downloads=entry.downloads,
        likes=entry.likes,
        tags=entry.tags,
        readme=readme_content,
    )


def _format_entries(entries: List[DatasetInfo]) -> HFDatasetsSearchResponse:
    clean_entries = [_clean_entry(entry) for entry in entries]
    return HFDatasetsSearchResponse(results=clean_entries)


def hf_datasets_search(
    query: Optional[str] = None,
    search_filter: Optional[List[str]] = None,
    limit: int = 5,
    sort_by: str = "trending_score",
    sort_order: str = "descending",
) -> HFDatasetsSearchResponse:
    """
    Search or filter HF datasets.

    Examples:
        List only the datasets in Russian for language modeling:
        hf_datasets_search(filter=(language:ru", "task_ids:language-modeling"))

        List all recent datasets with "text" in their name
        hf_datasets_search(query="text", sort_by="last_modified")

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
