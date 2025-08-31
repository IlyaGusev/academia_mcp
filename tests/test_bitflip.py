import json

from academia_mcp.tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposals,
    score_research_proposals,
)


async def test_bitflip_extract_info() -> None:
    arxiv_id = "2409.06820"
    result = json.loads(await extract_bitflip_info(arxiv_id))
    assert result is not None
    assert result["bit"]


async def test_bitflip_generate_research_proposal() -> None:
    arxiv_id = "2503.07826"
    bit = json.loads(await extract_bitflip_info(arxiv_id))["bit"]
    result = json.loads(await generate_research_proposals(bit=bit, num_proposals=2))
    assert result is not None
    assert len(result) == 2
    assert result[0]["flip"]
    assert result[1]["flip"]


async def test_bitflip_score_research_proposals_base() -> None:
    arxiv_id = "2503.07826"
    bit = json.loads(await extract_bitflip_info(arxiv_id))["bit"]
    proposals = await generate_research_proposals(bit=bit, num_proposals=2)
    scores = json.loads(await score_research_proposals(proposals))
    assert scores
    assert len(scores) == 2
    assert scores[0]["spark"] is not None
    assert scores[1]["spark"] is not None
    assert scores[0]["strengths"] is not None
    assert scores[1]["strengths"] is not None
    assert scores[0]["weaknesses"] is not None
    assert scores[1]["weaknesses"] is not None


async def test_bitflip_score_research_proposals_str() -> None:
    arxiv_id = "2503.07826"
    bit = json.loads(await extract_bitflip_info(arxiv_id))["bit"]
    proposals = await generate_research_proposals(bit=bit, num_proposals=2)
    scores = json.loads(await score_research_proposals(proposals))
    assert scores
    assert len(scores) == 2
    assert scores[0]["spark"] is not None
    assert scores[1]["spark"] is not None
    assert scores[0]["strengths"] is not None
    assert scores[1]["strengths"] is not None
    assert scores[0]["weaknesses"] is not None
    assert scores[1]["weaknesses"] is not None
