from academia_mcp.tools.bitflip import extract_bitflip_info, propose_improvement_idea


def test_bitflip_extract_info() -> None:
    arxiv_id = "2409.06820"
    result = extract_bitflip_info(arxiv_id)
    assert result is not None
    assert "bit" in result
    assert "flip" in result
    assert "spark" in result


def test_bitflip_propose_improvement_idea() -> None:
    arxiv_id = "2503.07826"
    result = propose_improvement_idea(arxiv_id)
    assert result is not None
    assert "chain_of_reasoning" in result
    assert "flip" in result
    assert "spark" in result
