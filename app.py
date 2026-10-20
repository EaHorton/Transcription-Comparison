import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "transcription_comparison.db"

SERVICES = {
    "transkribus": {
        "name": "Transkribus",
        "tagline": "Specialist handwriting recognition for heritage collections",
        "description": "A powerful platform for historical documents, custom models, and large-scale archival work.",
        "color": "#d97757",
    },
    "seeklight": {
        "name": "Seeklight",
        "tagline": "Fast, flexible transcription for modern workflows",
        "description": "A streamlined option for teams that want quick results and an approachable interface.",
        "color": "#4f7cac",
    },
    "archivault": {
        "name": "Archivault",
        "tagline": "Organize and preserve your digitized archive",
        "description": "Built around discoverability, organization, and keeping project context close to every file.",
        "color": "#7c6aa6",
    },
    "ai-vision-ocr": {
        "name": "AI-Vision OCR",
        "tagline": "Vision-powered OCR for broad document coverage",
        "description": "A flexible AI approach for quickly testing a wide range of layouts and document types.",
        "color": "#3d927f",
    },
}

CATEGORIES = [
    ("cost", "Cost", "How affordable is the service for your project?"),
    ("ease_of_use", "Ease of use", "How intuitive is the workflow from upload to export?"),
    ("accuracy", "Accuracy", "How reliably does it capture the source material?"),
    ("features", "Features", "How well does it support your project's needs?"),
    ("speed", "Speed", "How quickly does it process your documents?"),
]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-key-change-me"),
        DATABASE=DATABASE,
    )
    if test_config:
        app.config.update(test_config)

    def get_db():
        if "db" not in getattr(app, "extensions", {}):
            app.extensions["db"] = sqlite3.connect(app.config["DATABASE"])
            app.extensions["db"].row_factory = sqlite3.Row
        return app.extensions["db"]

    def init_db():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS service_reviews (
                service TEXT PRIMARY KEY,
                ratings TEXT NOT NULL DEFAULT '{}',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for slug in SERVICES:
            db.execute(
                "INSERT OR IGNORE INTO service_reviews (service) VALUES (?)", (slug,)
            )
        db.commit()

    def close_db(_error=None):
        db = app.extensions.pop("db", None)
        if db is not None:
            db.close()

    app.teardown_appcontext(close_db)

    def get_reviews():
        init_db()
        rows = get_db().execute("SELECT * FROM service_reviews").fetchall()
        return {
            row["service"]: {
                "ratings": json.loads(row["ratings"]),
                "notes": row["notes"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    @app.context_processor
    def inject_navigation():
        return {"services": SERVICES, "categories": CATEGORIES}

    @app.route("/")
    def index():
        reviews = get_reviews()
        return render_template("index.html", reviews=reviews)

    @app.route("/service/<service>", methods=("GET", "POST"))
    def service(service):
        if service not in SERVICES:
            return render_template("404.html"), 404
        if request.method == "POST":
            ratings = {}
            for key, _label, _description in CATEGORIES:
                value = request.form.get(key, "").strip()
                if value and value.isdigit() and 1 <= int(value) <= 10:
                    ratings[key] = int(value)
            notes = request.form.get("notes", "").strip()
            db = get_db()
            init_db()
            db.execute(
                """
                UPDATE service_reviews
                SET ratings = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE service = ?
                """,
                (json.dumps(ratings), notes, service),
            )
            db.commit()
            flash(f"{SERVICES[service]['name']} review saved.", "success")
            return redirect(url_for("service", service=service))

        reviews = get_reviews()
        return render_template(
            "service.html",
            service=SERVICES[service],
            slug=service,
            review=reviews[service],
        )

    @app.route("/comparison")
    def comparison():
        reviews = get_reviews()
        summaries = []
        for slug, details in SERVICES.items():
            ratings = reviews[slug]["ratings"]
            total = sum(ratings.values())
            count = len(ratings)
            summaries.append(
                {
                    "slug": slug,
                    **details,
                    "ratings": ratings,
                    "total": total,
                    "count": count,
                    "average": round(total / count, 1) if count else 0,
                    "complete": count == len(CATEGORIES),
                }
            )
        return render_template("comparison.html", summaries=summaries)

    with app.app_context():
        init_db()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
