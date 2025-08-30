import json

from academia_mcp.tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposal,
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
    result = json.loads(await generate_research_proposal(bit=bit))
    assert result is not None
    assert result["flip"]


async def test_bitflip_score_research_proposals() -> None:
    arxiv_id = "2503.07826"
    bit = json.loads(await extract_bitflip_info(arxiv_id))["bit"]
    proposal1 = await generate_research_proposal(bit=bit)
    proposal2 = await generate_research_proposal(bit=bit)
    scores = json.loads(await score_research_proposals([proposal1, proposal2]))
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
    proposal1 = await generate_research_proposal(bit=bit)
    proposal2 = await generate_research_proposal(bit=bit)
    scores = json.loads(await score_research_proposals(json.dumps([proposal1, proposal2])))
    assert scores
    assert len(scores) == 2
    assert scores[0]["spark"] is not None
    assert scores[1]["spark"] is not None
    assert scores[0]["strengths"] is not None
    assert scores[1]["strengths"] is not None
    assert scores[0]["weaknesses"] is not None
    assert scores[1]["weaknesses"] is not None
