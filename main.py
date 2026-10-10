import os
import json
import base64
import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI(
    title="KachraLens",
    description="AI-powered waste reporting and cleanup verification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "kachralens.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_base64 TEXT NOT NULL,
            description TEXT,
            latitude REAL,
            longitude REAL,
            waste_type TEXT,
            problem_type TEXT,
            severity TEXT,
            priority TEXT,
            priority_score INTEGER,
            status TEXT DEFAULT 'pending',
            explanation TEXT,
            after_image_base64 TEXT,
            verification_confidence INTEGER,
            verification_explanation TEXT,
            solved_latitude REAL,
            solved_longitude REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()

# Safely add cleanup-location columns to existing databases without deleting reports.
def migrate_db():
    conn = get_db()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(reports)").fetchall()}
    if "solved_latitude" not in columns:
        conn.execute("ALTER TABLE reports ADD COLUMN solved_latitude REAL")
    if "solved_longitude" not in columns:
        conn.execute("ALTER TABLE reports ADD COLUMN solved_longitude REAL")
    conn.commit()
    conn.close()


migrate_db()


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "YOUR_GROQ_API_KEY_HERE":
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing. Add your Groq API key to .env"
        )

    return Groq(api_key=api_key)


def image_to_data_url(image_bytes: bytes, content_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{content_type};base64,{encoded}"


def analyze_waste_with_ai(
    image_data_url: str,
    description: str
):
    client = get_groq_client()

    prompt = f"""
You are KachraLens, an AI system for identifying garbage and waste problems in India.

Carefully inspect the actual visual contents of the uploaded image before classifying it.

User description:
{description or "No description provided."}

IMPORTANT IMAGE EVIDENCE RULES:
- Do not assume that every uploaded image contains garbage.
- Soil, rocks, sand, gravel, dry leaves on natural ground, plants, and ordinary construction terrain are NOT automatically garbage.
- Only identify waste when there is visible evidence of discarded material, litter, or dumped rubbish.
- Never invent plastic, bottles, bags, or other waste that is not clearly visible.
- If no waste is visible, use "No visible waste" for waste_type and problem_type.
- If the image is unclear, use "Uncertain" for waste_type and explain what prevents reliable identification.
- The user's description is context, not proof. The image itself must support the classification.
- When no waste is visible or the image is uncertain, set severity to "Low", priority to "low", and priority_score to 0.
- For confirmed waste, assess severity and priority only from the visible quantity, type, and context. Do not assign High severity merely because the image is outdoors.

Return ONLY valid JSON with exactly these fields:

{{
  "waste_type": "specific visible waste category, No visible waste, or Uncertain",
  "problem_type": "visible waste problem, No visible waste, or Uncertain",
  "severity": "Low or Medium or High",
  "priority": "low or medium or high",
  "priority_score": 0,
  "explanation": "brief explanation grounded in visible image evidence"
}}

Priority rules for CONFIRMED waste only:
- HIGH = clearly substantial or dangerous waste accumulation with visible evidence of significant risk.
- MEDIUM = noticeable waste accumulation with a moderate impact.
- LOW = small or limited waste accumulation.

priority_score must be an integer from 0 to 100.
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=500
    )

    text = response.choices[0].message.content

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON"
        )


def verify_cleanup_with_ai(
    before_image_url: str,
    after_image_url: str
):
    client = get_groq_client()

    prompt = """
You are KachraLens, an AI system that verifies whether a reported garbage location has actually been cleaned.

You will receive:
1. BEFORE image - the original garbage/waste report.
2. AFTER image - the claimed cleaned location.

Compare them carefully.

Return ONLY valid JSON:

{
  "status": "pending or partially_solved or solved",
  "confidence": 0,
  "explanation": "short explanation"
}

Rules:

SOLVED:
The major waste shown in the BEFORE image is clearly removed and the location is substantially cleaner.

PARTIALLY_SOLVED:
Some waste has been removed, but noticeable waste or the original problem remains.

PENDING:
The location appears essentially unchanged, the evidence is insufficient, or the garbage remains.

confidence must be an integer from 0 to 100.
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "text",
                        "text": "BEFORE IMAGE:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": before_image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": "AFTER IMAGE:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": after_image_url
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=400
    )

    text = response.choices[0].message.content

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid verification JSON"
        )


@app.get("/")
def home():
    return {
        "app": "KachraLens",
        "message": "See Waste. Take Action. Verify the Change.",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "server": "Healthy",
        "database": "Connected",
        "ai": "Configured" if os.getenv("GROQ_API_KEY") else "Not Configured"
    }


@app.post("/api/analyze")
async def analyze_report(
    image: UploadFile = File(...),
    description: str = Form(""),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None)
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )

    image_bytes = await image.read()

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 10 MB."
        )

    content_type = image.content_type
    image_data_url = image_to_data_url(image_bytes, content_type)

    ai_result = analyze_waste_with_ai(
        image_data_url,
        description
    )

    now = datetime.now().isoformat()

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO reports (
            image_base64,
            description,
            latitude,
            longitude,
            waste_type,
            problem_type,
            severity,
            priority,
            priority_score,
            status,
            explanation,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            image_data_url,
            description,
            latitude,
            longitude,
            ai_result.get("waste_type", "Unknown"),
            ai_result.get("problem_type", "Waste accumulation"),
            ai_result.get("severity", "Medium"),
            ai_result.get("priority", "medium"),
            int(ai_result.get("priority_score", 50)),
            "pending",
            ai_result.get("explanation", ""),
            now,
            now
        )
    )

    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "report_id": report_id,
        "status": "pending",
        "waste_type": ai_result.get("waste_type"),
        "problem_type": ai_result.get("problem_type"),
        "severity": ai_result.get("severity"),
        "priority": ai_result.get("priority"),
        "priority_score": ai_result.get("priority_score"),
        "explanation": ai_result.get("explanation"),
        "latitude": latitude,
        "longitude": longitude
    }


@app.delete("/api/reports")
def clear_all_reports():
    """Permanently delete every report and its stored cleanup-verification data."""
    conn = get_db()
    try:
        deleted = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        conn.execute("DELETE FROM reports")
        # Reset SQLite's generated report IDs when the sequence table exists.
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'reports'")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "success": True,
        "deleted_count": deleted,
        "message": f"Permanently deleted {deleted} report(s)."
    }


@app.get("/api/reports")
def get_reports():
    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            id,
            description,
            latitude,
            longitude,
            waste_type,
            problem_type,
            severity,
            priority,
            priority_score,
            status,
            explanation,
            verification_confidence,
            verification_explanation,
            solved_latitude,
            solved_longitude,
            created_at,
            updated_at
        FROM reports
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return {
        "success": True,
        "reports": [dict(row) for row in rows]
    }


@app.get("/api/reports/{report_id}")
def get_report(report_id: int):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM reports WHERE id = ?",
        (report_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return {
        "success": True,
        "report": dict(row)
    }


@app.post("/api/reports/{report_id}/verify")
async def verify_report(
    report_id: int,
    after_image: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None)
):
    if not after_image.content_type or not after_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM reports WHERE id = ?",
        (report_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    after_bytes = await after_image.read()

    if len(after_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="After image is empty."
        )

    after_image_url = image_to_data_url(
        after_bytes,
        after_image.content_type
    )

    verification = verify_cleanup_with_ai(
        row["image_base64"],
        after_image_url
    )

    status = verification.get(
        "status",
        "pending"
    )

    if status not in [
        "pending",
        "partially_solved",
        "solved"
    ]:
        status = "pending"

    confidence = int(
        verification.get("confidence", 50)
    )

    explanation = verification.get(
        "explanation",
        ""
    )

    now = datetime.now().isoformat()

    conn = get_db()

    conn.execute(
        """
        UPDATE reports
        SET
            after_image_base64 = ?,
            verification_confidence = ?,
            verification_explanation = ?,
            status = ?,
            solved_latitude = ?,
            solved_longitude = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            after_image_url,
            confidence,
            explanation,
            status,
            latitude,
            longitude,
            now,
            report_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "report_id": report_id,
        "status": status,
        "confidence": confidence,
        "explanation": explanation,
        "latitude": latitude,
        "longitude": longitude
    }


@app.get("/api/statistics")
def statistics():
    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM reports"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE status = 'pending'"
    ).fetchone()[0]

    partially_solved = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE status = 'partially_solved'"
    ).fetchone()[0]

    solved = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE status = 'solved'"
    ).fetchone()[0]

    high_priority = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE priority = 'high'"
    ).fetchone()[0]

    conn.close()

    return {
        "success": True,
        "total_reports": total,
        "pending": pending,
        "partially_solved": partially_solved,
        "solved": solved,
        "high_priority": high_priority
    }

