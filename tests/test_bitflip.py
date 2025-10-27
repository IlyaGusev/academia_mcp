from academia_mcp.tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposals,
    score_research_proposals,
)


async def test_bitflip_score_research_proposals() -> None:
    arxiv_id = "2503.07826"
    bit = (await extract_bitflip_info(arxiv_id)).bit
    assert bit
    proposals = await generate_research_proposals(bit=bit, num_proposals=2)
    assert proposals.proposals
    assert len(proposals.proposals) == 2
    assert proposals.proposals[0].flip
    assert proposals.proposals[1].flip
    scores = await score_research_proposals(proposals.proposals)
    assert scores.proposals
    assert len(scores.proposals) == 2
    assert scores.proposals[0].spark is not None
    assert scores.proposals[1].spark is not None
    assert scores.proposals[0].strengths is not None
    assert scores.proposals[1].strengths is not None
    assert scores.proposals[0].weaknesses is not None
    assert scores.proposals[1].weaknesses is not None
