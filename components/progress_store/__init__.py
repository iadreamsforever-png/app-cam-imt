import os

import streamlit.components.v1 as components

_component = components.declare_component(
    "progress_store",
    path=os.path.join(os.path.dirname(__file__), "frontend"),
)


def progress_store(action, storage_key, value=None, default=None):
    return _component(
        action=action,
        storage_key=storage_key,
        value=value,
        default=default,
    )