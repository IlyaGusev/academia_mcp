from academia_mcp.tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposals,
    score_research_proposals,
)


async def test_bitflip_extract_info() -> None:
    arxiv_id = "2409.06820"
    result = await extract_bitflip_info(arxiv_id)
    assert result is not None
    assert result.bit


async def test_bitflip_generate_research_proposal() -> None:
    arxiv_id = "2503.07826"
    bit = (await extract_bitflip_info(arxiv_id)).bit
    result = await generate_research_proposals(bit=bit, num_proposals=2)
    assert result.proposals
    assert len(result.proposals) == 2
    assert result.proposals[0].flip
    assert result.proposals[1].flip


async def test_bitflip_score_research_proposals_base() -> None:
    arxiv_id = "2503.07826"
    bit = (await extract_bitflip_info(arxiv_id)).bit
    proposals = await generate_research_proposals(bit=bit, num_proposals=2)
    scores = await score_research_proposals(proposals)
    assert scores.proposals
    assert len(scores.proposals) == 2
    assert scores.proposals[0].spark is not None
    assert scores.proposals[1].spark is not None
    assert scores.proposals[0].strengths is not None
    assert scores.proposals[1].strengths is not None
    assert scores.proposals[0].weaknesses is not None
    assert scores.proposals[1].weaknesses is not None
