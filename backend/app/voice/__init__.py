"""Voice Duo: a real-time speech tutor ("Is 'hola amigo' correct?") built on Pipecat.

Same architecture as the Cat operator agent: streaming STT -> fast LLM -> streaming TTS, so Duo
starts speaking the first sentence while the rest is still being generated. Served over a
WebSocket (works behind any HTTPS proxy, unlike UDP WebRTC on most PaaS hosts).
"""
