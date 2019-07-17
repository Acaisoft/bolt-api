from hypothesis import given
import hypothesis.strategies as st

from services.execution_metrics.metadata_execution import _even_select


@given(sequence=st.sets(st.integers()), list_len_limit=st.integers(min_value=1, max_value=10000))
def test_even_select(sequence, list_len_limit):
    evenly_selected_len = len(_even_select(list(sequence), list_len_limit))
    if len(sequence) > list_len_limit:
        assert evenly_selected_len == list_len_limit
    else:
        assert evenly_selected_len == len(sequence)
