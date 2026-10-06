"""The real-time voice loop for Smarto.

    browser mic ─ws─► Silero VAD (local) ─► Deepgram nova-3 (multi: EN+ES) ─► Cerebras gpt-oss-120b
                                                                              │ (+ fast tools)
    browser speaker ◄─ws─ Deepgram Aura-2 ◄───────────────────────────────────┘

Latency choices (same as the Cat agent): streaming everything, Cerebras for ~1-2k tok/s inference
with low reasoning effort, the learner's profile pre-loaded into the prompt instead of fetched with a
tool call, and only cheap in-process tools. Heavy work (building a practice session) is handed to
the agent pipeline in the background so the voice never waits on it.
"""
import json

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.services.cerebras.llm import CerebrasLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.turns.user_mute import FunctionCallUserMuteStrategy, MuteUntilFirstBotCompleteUserMuteStrategy

from app.agents import learner_data
from app.agents import pipeline as tutor_pipeline
from app.core.db import SessionLocal
from app.models import TutorMessage, User
from app.voice.config import VoiceConfig

SYSTEM_PROMPT = """\
You are Smarto, a cheerful bird who tutors Spanish by VOICE inside the Smartalingo app. The learner
speaks English and is learning Spanish; they may say Spanish phrases and ask if they're right.

How you talk (this is read aloud):
- One or two short sentences, under 35 words. No lists, markdown, emojis or symbols.
- Speak English; use Spanish only for the phrases you are teaching.
- When they ask whether something is correct, start with the verdict ("Yes, perfect!" / "Almost!" /
  "Not quite.").
- When correcting, say the correct Spanish phrase, then the meaning in English.
- Gender/agreement matters: e.g. "hola amigo" is right for a male friend, "hola amiga" for a female.
- If the speech transcript looks garbled, guess the most likely Spanish phrase and confirm it.
- Encourage them, and mention their weak spots below only when relevant.
- If they want to practise something, call create_practice. For streak/XP questions call get_my_stats.
- Only help with language learning and this app.

What you know about this learner right now:
{profile}
"""

GREETING = (
    "Say hello to the learner by name in ENGLISH, in one short friendly sentence, and invite them to say a "
    "Spanish phrase they want checked. Do not give a verdict yet."
)


def learner_profile(user_id: int) -> tuple[str, str]:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        mastery = learner_data.concept_mastery(db, user)
        weak = [f"{m['name']} (mastery {m['mastery']:.0%})" for m in mastery if m["attempts"] >= 2][:3]
        mistakes = learner_data.recent_mistakes(db, user, 5)
        lines = [
            f"Name: {user.display_name}. Streak: {user.streak_count} days. Total XP: {user.total_xp}.",
            f"Weakest concepts: {', '.join(weak) or 'not enough data yet'}.",
            "Recent mistakes: " + "; ".join(
                f"answered '{m['learner_answer']}' instead of '{m['correct_answer']}' ({m['error_type']})"
                for m in mistakes if m["learner_answer"] and m["learner_answer"] != "(simulated)"
            )[:600],
        ]
        return user.display_name, "\n".join(lines)


def _make_llm(cfg: VoiceConfig, system: str):
    if cfg.llm_provider == "cerebras":
        return CerebrasLLMService(
            api_key=cfg.llm_api_key,
            settings=CerebrasLLMService.Settings(
                model=cfg.llm_model,
                system_instruction=system,
                extra={"reasoning_effort": "low"},  # gpt-oss: think briefly so speech starts fast
            ),
        )
    return OpenAILLMService(
        api_key=cfg.llm_api_key,
        settings=OpenAILLMService.Settings(model=cfg.llm_model, system_instruction=system),
    )


def build_worker(transport: BaseTransport, cfg: VoiceConfig, user_id: int) -> PipelineWorker:
    name, profile = learner_profile(user_id)

    async def get_my_stats(params: FunctionCallParams):
        """Get the learner's current streak, XP, hearts and gems."""
        with SessionLocal() as db:
            u = db.get(User, user_id)
            await params.result_callback(
                {"streak_days": u.streak_count, "total_xp": u.total_xp, "hearts": u.hearts, "gems": u.gems}
            )

    async def create_practice(params: FunctionCallParams, concept_keys: list[str]):
        """Build a personalized practice session on these concepts in the background. It appears on the
        learner's path as Smarto's Practice in about 30 seconds.

        Args:
            concept_keys: e.g. ["grammar.gender_articles"], ["verb.ser"], ["spelling.accents"],
                ["verb.comer_beber"], ["grammar.adjective_agreement"], ["grammar.plurals"].
        """
        tutor_pipeline.schedule(user_id, "voice", concept_keys[:3])
        await params.result_callback({"status": "building", "focus": concept_keys})

    vad = VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(confidence=0.7, start_secs=0.2, stop_secs=cfg.vad_stop_secs, min_volume=0.6)
        )
    )
    # nova-3 "multi" handles English questions with Spanish phrases mixed in ("is hola amigo right?").
    stt = DeepgramSTTService(
        api_key=cfg.deepgram_api_key,
        settings=DeepgramSTTService.Settings(model=cfg.stt_model, language=cfg.stt_language),
    )
    llm = _make_llm(cfg, SYSTEM_PROMPT.format(profile=profile))
    tts = DeepgramTTSService(api_key=cfg.deepgram_api_key, settings=DeepgramTTSService.Settings(voice=cfg.tts_voice))

    context = LLMContext(tools=[get_my_stats, create_practice])
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_mute_strategies=[MuteUntilFirstBotCompleteUserMuteStrategy(), FunctionCallUserMuteStrategy()],
        ),
    )

    pipeline = Pipeline([
        transport.input(), vad, stt, user_aggregator, llm, tts, transport.output(), assistant_aggregator,
    ])
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        setup_timeout_secs=60,
    )

    def save(role: str, content: str) -> None:
        if not content:
            return
        with SessionLocal() as db:
            db.add(TutorMessage(user_id=user_id, role=role, content=content[:2000], channel="voice"))
            db.commit()

    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(aggregator, strategy, message):
        logger.info(f"[voice u{user_id}] YOU: {message.content}")
        save("user", message.content)

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message):
        if message.content:
            logger.info(f"[voice u{user_id}] DUO: {message.content}")
            save("assistant", message.content)

    @worker.event_handler("on_pipeline_started")
    async def on_pipeline_started(worker, frame):
        context.add_message({"role": "developer", "content": f"{GREETING} Their name is {json.dumps(name)}."})
        await worker.queue_frames([LLMRunFrame()])

    return worker
