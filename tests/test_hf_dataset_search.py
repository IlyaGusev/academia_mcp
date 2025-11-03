from academia_mcp.tools import hf_datasets_search


def test_hf_datasets_search_gazeta() -> None:
    response = hf_datasets_search(query="gazeta")
    assert response.results
    assert "IlyaGusev/gazeta" in str(response.results)


def test_hf_datasets_search_cifar() -> None:
    response = hf_datasets_search(query="CIFAR-10")
    assert response.results
    assert "uoft-cs/cifar10" in str(response.results)
