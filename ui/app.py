"""Streamlit UI for the shopping copilot — Fase 1a."""

from __future__ import annotations

import httpx
import streamlit as st
from httpx import HTTPStatus

API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Shopping Copilot", page_icon="🛒", layout="wide")
st.title("🛒 Shopping Copilot")
st.caption("Fase 1a — echo con Claude. El agente completo llega en Semana 2.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("¿Qué buscas hoy?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resp = httpx.post(
                API_URL,
                json={"messages": st.session_state.messages},
                timeout=60.0,
            )
        if resp.status_code != HTTPStatus.OK:
            st.error(f"Error {resp.status_code}: {resp.text}")
        else:
            data = resp.json()
            st.markdown(data["content"])
            st.caption(f"`{data['model']}` · in={data['input_tokens']} out={data['output_tokens']}")
            st.session_state.messages.append({"role": "assistant", "content": data["content"]})

with st.sidebar:
    st.subheader("Sesión")
    st.write(f"Mensajes: **{len(st.session_state.messages)}**")
    if st.button("🧹 Reset"):
        st.session_state.messages = []
        st.rerun()
