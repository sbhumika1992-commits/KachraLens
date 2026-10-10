
# ♻️ KachraLens

### See the waste. Report the problem. Track the cleanup.

**An AI-assisted waste reporting and resolution-verification platform**

KachraLens helps people document waste hotspots, attach location
details, analyse reports with AI, and check cleanup progress using
before-and-after images.
:::

------------------------------------------------------------------------

## 🌍 Why KachraLens?

Waste problems are often noticed but not reported with enough detail to
help someone act. A useful report needs more than a complaint: it needs
visual evidence, a location, clear prioritisation, and a way to check
whether the issue was actually addressed.

**KachraLens brings these steps into one workflow**---from reporting a
waste hotspot to reviewing the cleanup evidence.

## ✨ Key Features

-   **📸 Image-based reporting** --- submit a photo of a waste issue
    with supporting details.
-   **📍 Location-aware reports** --- use browser geolocation, when
    permission is granted, to attach coordinates to a report.
-   **🤖 AI-assisted analysis** --- the backend is configured to use the
    Groq API for AI-related analysis of waste reports.
-   **🚦 Issue prioritisation** --- structure report information to help
    highlight issues that may need attention first.
-   **🧹 Cleanup verification workflow** --- submit a follow-up image
    and compare it with the original report to help assess whether the
    issue appears resolved.
-   **📊 Report tracking and statistics** --- backend routes support
    retrieving reports and summary statistics.
-   **🗃️ Persistent report storage** --- SQLite is used for report data
    in the current project setup.

> **Important:** AI results are estimates, not guaranteed proof that a
> site is clean. Confirm that image analysis, geolocation, persistence,
> and verification all work in the final build before describing them as
> fully implemented.

## 🔄 How It Works

1.  **Capture** --- a user selects a photo of a waste hotspot and
    provides relevant details.
2.  **Locate** --- the browser can request permission to capture the
    report's latitude and longitude.
3.  **Analyse** --- the frontend sends report information to the FastAPI
    backend, which calls the configured AI service where applicable.
4.  **Record** --- report information is stored and can be retrieved
    through the backend.
5.  **Follow up** --- a cleanup photo can be submitted for comparison
    with the original evidence.
6.  **Review** --- the system returns a verification assessment that
    should be treated as AI-assisted guidance and reviewed
    appropriately.

## 🧠 AI and Technology

  -----------------------------------------------------------------------
  Component                           Technology
  ----------------------------------- -----------------------------------
  Programming language                Python

  Backend framework                   FastAPI

  ASGI server                         Uvicorn

  AI API/client                       Groq API / Groq Python client

  Model ID configured in code         `qwen/qwen3.8-27b` --- verify
                                      current availability and successful
                                      requests

  Data storage                        SQLite

  Frontend                            HTML, CSS, JavaScript

  File/form handling                  `python-multipart`

  Environment configuration           `python-dotenv`

  Development environment             Visual Studio Code

  Location access                     Browser Geolocation API, if enabled
                                      in the deployed frontend
  -----------------------------------------------------------------------

## 🏗️ System Overview

``` text
User
  │
  ▼
KachraLens Web Interface
(HTML / CSS / JavaScript)
  │  HTTP requests + report images + optional coordinates
  ▼
FastAPI Backend
  ├── /api/analyze  → report analysis workflow
  ├── /verify       → before/after resolution assessment
  ├── /api/reports  → report retrieval
  └── /api/statistics → summary statistics
        │
        ├── Groq API → AI-related analysis
        └── SQLite   → report data
```

Endpoint names above reflect the current project notes; check the actual
backend routes before relying on them in a deployed setup.

## 🚀 Run Locally

### 1. Requirements

-   Python installed
-   Project source code
-   A Groq API key if the AI workflow is enabled

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the project using the
virtual environment's Python directly, or follow Microsoft's guidance
for execution policy settings.

### 3. Install dependencies

``` powershell
pip install -r requirements.txt
```

The current `requirements.txt` includes:

``` text
fastapi
uvicorn
python-multipart
python-dotenv
groq
```

### 4. Configure environment variables

Create a `.env` file in the backend/project directory expected by your
code:

``` env
GROQ_API_KEY=your_groq_api_key_here
```

Use the exact environment variable name referenced by your code. **Never
commit `.env` or expose a real API key in screenshots, videos, or a
public repository.**

### 5. Start the backend

From the directory containing `main.py`, run:

``` powershell
uvicorn main:app --reload
```

Open the API documentation at:

``` text
http://127.0.0.1:8000/docs
```

Open the frontend using the method and path configured in your project.
If the frontend calls the backend from a different origin, ensure the
backend's CORS settings allow that origin.

## 🔌 API Routes

The following routes are described in the current project setup. Confirm
the exact HTTP methods, request fields, and response formats in `/docs`
or the backend source before integrating other clients.

  Route               Purpose
  ------------------- ------------------------------------------
  `/api/analyze`      Submit a waste report for analysis
  `/verify`           Assess before-and-after cleanup evidence
  `/api/reports`      Retrieve reports
  `/api/statistics`   Retrieve report statistics

## 🔐 Privacy, Safety & Responsible AI

-   Request location permission only when needed and explain why it is
    being used.
-   Avoid publishing personal information or precise location data
    unnecessarily.
-   Keep API keys in environment variables; do not hard-code secrets.
-   Treat AI analysis and resolution scores as fallible assessments.
-   Do not claim a cleanup is definitively complete based only on an
    AI-generated result.
-   Test invalid uploads, missing coordinates, API failures, and
    uncertain image comparisons.

## 🧪 Before You Demo

-   [ ] The backend starts successfully.
-   [ ] The frontend can reach the backend.
-   [ ] A report can be submitted with an image.
-   [ ] Location permission and coordinate capture work, if this feature
    is enabled.
-   [ ] The configured Groq model ID is currently supported and a real
    API request succeeds.
-   [ ] Image content is actually sent to an image-capable model/service
    if image analysis is claimed.
-   [ ] The resolve workflow uses the analysis result and behaves
    correctly for unresolved, partially resolved, and resolved examples.
-   [ ] Reports and statistics reflect the stored data.
-   [ ] No secrets or private data appear in the repository or demo.

## 🛣️ Future Scope

-   Map-based waste hotspot visualisation
-   Status updates and notifications for reports
-   Human review or community confirmation for uncertain AI decisions
-   Analytics to identify recurring hotspots
-   Deployment with appropriate access controls and data-retention
    practices

## 🤝 Contributing

Contributions that improve usability, accessibility, reporting
reliability, location handling, AI transparency, and verification
quality are welcome. For changes, describe the problem, explain the
proposed improvement, and test the relevant workflow.

## 👩‍💻 Project

**KachraLens**\
*Making waste visible, actionable, and easier to track.*

Built as an AI-assisted civic cleanliness project. Update this README to
match the exact features, endpoints, model availability, and setup
instructions of the final submitted code.

------------------------------------------------------------------------

### AI Usage Disclosure

Generative AI tools may have assisted with development planning, code
guidance, troubleshooting, or documentation. The application is
configured to use the Groq API for its AI workflow. The exact model,
image-analysis capability, and implemented behaviour should be verified
against the final code and successful tests. The project team remains
responsible for reviewing the implementation and representing its
capabilities accurately.
