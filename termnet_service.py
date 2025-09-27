"""TermNet FastAPI Service with OTel, Retrieval, and Security."""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest
import faiss
import numpy as np
import yaml
from contextlib import asynccontextmanager

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///termnet_ledger.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OTel setup
resource = Resource(attributes={"service.name": "termnet"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="localhost:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Metrics
run_counter = Counter("termnet_runs_total", "Total number of runs")
run_duration = Histogram("termnet_run_duration_seconds", "Run duration")
grounding_score = Histogram("termnet_grounding_score", "Grounding scores")

# Models
class RunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tools: Optional[List[str]] = Field(default_factory=list)

class RunResponse(BaseModel):
    trace_id: str
    result: Any
    duration: float
    grounding_score: Optional[float] = None

class TraceEntry(Base):
    __tablename__ = "traces"

    id = Column(String, primary_key=True)
    task = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)
    result = Column(JSON)
    spans = Column(JSON)
    grounding_score = Column(Float, nullable=True)

# Retrieval system
class RetrievalStack:
    def __init__(self, dimension=384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []

    def add_document(self, text: str, embedding: np.ndarray):
        self.documents.append(text)
        self.index.add(embedding.reshape(1, -1))

    def search(self, query_embedding: np.ndarray, k: int = 5):
        distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
        return [(self.documents[i], float(distances[0][j]))
                for j, i in enumerate(indices[0]) if i < len(self.documents)]

    def check_grounding(self, query: str, context: str) -> Dict[str, Any]:
        """Check if query is grounded in context."""
        # Simplified grounding check
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        overlap = len(query_words & context_words)
        score = overlap / len(query_words) if query_words else 0.0

        return {
            "grounded": score > 0.3,
            "score": score,
            "overlap_words": list(query_words & context_words)
        }

# Security dispatcher
class SecurityDispatcher:
    def __init__(self, manifest_path: str = "tools_manifest.yml"):
        self.manifest = self._load_manifest(manifest_path)

    def _load_manifest(self, path: str) -> Dict:
        if Path(path).exists():
            with open(path) as f:
                return yaml.safe_load(f)
        return {"allowed_tools": [], "arg_schemas": {}}

    def validate_tool_call(self, tool: str, args: Dict) -> bool:
        if tool not in self.manifest.get("allowed_tools", []):
            return False

        schema = self.manifest.get("arg_schemas", {}).get(tool, {})
        for required_arg in schema.get("required", []):
            if required_arg not in args:
                return False

        return True

# Agent logic
class TermNetAgent:
    def __init__(self, retrieval: RetrievalStack, cache: redis.Redis, dispatcher: SecurityDispatcher):
        self.retrieval = retrieval
        self.cache = cache
        self.dispatcher = dispatcher

    @tracer.start_as_current_span("reason")
    async def reason(self, task: str, context: Dict) -> Dict:
        """Reasoning phase."""
        return {
            "task": task,
            "context": context,
            "plan": f"Execute task: {task}"
        }

    @tracer.start_as_current_span("act")
    async def act(self, plan: Dict, tools: List[str]) -> Dict:
        """Action phase."""
        actions = []
        for tool in tools:
            if self.dispatcher.validate_tool_call(tool, {}):
                actions.append(f"Execute {tool}")

        return {
            "actions": actions,
            "status": "completed"
        }

    @tracer.start_as_current_span("observe")
    async def observe(self, actions: Dict) -> Dict:
        """Observation phase."""
        return {
            "observations": f"Executed {len(actions.get('actions', []))} actions",
            "success": True
        }

    async def run(self, task: str, context: Dict, tools: List[str]) -> Dict:
        """Main agent loop."""
        with tracer.start_as_current_span("agent_run") as span:
            span.set_attribute("task", task)

            # Check cache
            cache_key = f"task:{task}"
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)

            # RAO cycle
            reasoning = await self.reason(task, context)
            actions = await self.act(reasoning, tools)
            observations = await self.observe(actions)

            # Check grounding
            grounding = self.retrieval.check_grounding(task, str(context))

            result = {
                "reasoning": reasoning,
                "actions": actions,
                "observations": observations,
                "grounding": grounding
            }

            # Cache result
            await self.cache.setex(cache_key, 300, json.dumps(result))

            return result

# Dependency injection
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# App lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redis.from_url("redis://localhost:6379", decode_responses=True)
    app.state.retrieval = RetrievalStack()
    app.state.dispatcher = SecurityDispatcher()
    app.state.agent = TermNetAgent(app.state.retrieval, app.state.redis, app.state.dispatcher)
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    await app.state.redis.close()

# FastAPI app
app = FastAPI(title="TermNet", version="1.0.0", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest, db: Session = Depends(get_db)):
    """Execute agent task."""
    run_counter.inc()
    start_time = time.time()
    trace_id = str(uuid.uuid4())

    try:
        result = await app.state.agent.run(
            request.task,
            request.context,
            request.tools
        )

        duration = time.time() - start_time
        run_duration.observe(duration)

        # Save to ledger
        trace_entry = TraceEntry(
            id=trace_id,
            task=request.task,
            duration=duration,
            result=result,
            spans={"reason": True, "act": True, "observe": True},
            grounding_score=result.get("grounding", {}).get("score")
        )
        db.add(trace_entry)
        db.commit()

        if result.get("grounding", {}).get("score"):
            grounding_score.observe(result["grounding"]["score"])

        return RunResponse(
            trace_id=trace_id,
            result=result,
            duration=duration,
            grounding_score=result.get("grounding", {}).get("score")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str, db: Session = Depends(get_db)):
    """Get trace by ID."""
    trace = db.query(TraceEntry).filter(TraceEntry.id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return {
        "id": trace.id,
        "task": trace.task,
        "started_at": trace.started_at.isoformat(),
        "duration": trace.duration,
        "result": trace.result,
        "spans": trace.spans,
        "grounding_score": trace.grounding_score
    }

@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics."""
    return JSONResponse(
        content=generate_latest().decode("utf-8"),
        media_type="text/plain"
    )

@app.get("/agent.json")
async def get_agent_card():
    """Get A2A interop card."""
    return {
        "name": "TermNet",
        "version": "1.0.0",
        "capabilities": ["reasoning", "grounding", "tool_execution"],
        "endpoints": {
            "run": "/run",
            "trace": "/trace/{id}",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)