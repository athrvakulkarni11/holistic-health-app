# 🛡️ Guardrails & Protective Measures — Holistic Health AI Platform

> **Last updated:** February 20, 2026  
> **Module:** `app/guardrails.py` (centralized) + integrated across all layers  
> **Purpose:** Ensure user safety, data privacy, and responsible AI behavior in a health-facing application

---

## Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [Architecture](#2-architecture)
3. [Input Layer Guardrails](#3-input-layer-guardrails)
   - 3.1 [Input Sanitization](#31-input-sanitization)
   - 3.2 [Rate Limiting](#32-rate-limiting)
   - 3.3 [Message Length Enforcement](#33-message-length-enforcement)
   - 3.4 [File Validation & Safety Scanning](#34-file-validation--safety-scanning)
4. [AI/LLM Guardrails](#4-aillm-guardrails)
   - 4.1 [Emergency & Crisis Detection](#41-emergency--crisis-detection)
   - 4.2 [Adversarial / Prompt Injection Filtering](#42-adversarial--prompt-injection-filtering)
   - 4.3 [Off-Topic Deflection](#43-off-topic-deflection)
   - 4.4 [PII Detection & Redaction](#44-pii-detection--redaction)
   - 4.5 [System Prompt Safety Rules](#45-system-prompt-safety-rules)
   - 4.6 [Response Validation](#46-response-validation)
   - 4.7 [Disclaimer Enforcement](#47-disclaimer-enforcement)
5. [Clinical Safety Guardrails](#5-clinical-safety-guardrails)
   - 5.1 [Critical/Panic Value Detection](#51-criticalpanic-value-detection)
   - 5.2 [Supplement Dosage Rules](#52-supplement-dosage-rules)
   - 5.3 [Conservative Medical Language](#53-conservative-medical-language)
6. [Data Privacy & Security](#6-data-privacy--security)
   - 6.1 [Temporary File Deletion](#61-temporary-file-deletion)
   - 6.2 [API Key Management](#62-api-key-management)
   - 6.3 [Security Headers](#63-security-headers)
   - 6.4 [CORS Configuration](#64-cors-configuration)
   - 6.5 [Error Sanitization](#65-error-sanitization)
   - 6.6 [Request Size Limits](#66-request-size-limits)
7. [Frontend Guardrails](#7-frontend-guardrails)
   - 7.1 [Medical Disclaimer Modal](#71-medical-disclaimer-modal)
   - 7.2 [Persistent Safety Banner](#72-persistent-safety-banner)
   - 7.3 [Critical Value Alert Panels](#73-critical-value-alert-panels)
   - 7.4 [Client-Side Input Validation](#74-client-side-input-validation)
8. [Audit & Observability](#8-audit--observability)
9. [Testing](#9-testing)
10. [Configuration Reference](#10-configuration-reference)
11. [Future Improvements](#11-future-improvements)

---

## 1. Overview & Philosophy

This platform provides AI-powered health analysis based on biomarker data. Because it operates in the **health and wellness domain**, it carries elevated responsibility. Our guardrails are designed around three core principles:

| Principle | Description |
|-----------|-------------|
| **Do No Harm** | Never provide advice that could endanger a user. Always defer to professional medical care. |
| **Transparency** | Always make it clear that the AI is not a doctor and its output is informational only. |
| **Privacy First** | Minimize data retention, redact PII before LLM processing, and delete uploaded files immediately after extraction. |

### Defense-in-Depth

Guardrails are implemented at **every layer** of the stack — not just one. If one layer fails, others catch the issue:

```
User Input
  │
  ├─ 🖥️ Frontend Guardrails (client-side validation, modals, banners)
  │
  ├─ 🌐 API Layer (file validation, size limits, path traversal, security headers)
  │
  ├─ 🧠 AI Layer (sanitization, PII redaction, emergency detection, prompt safety)
  │
  ├─ 📊 Clinical Layer (critical values, dosage rules, language constraints)
  │
  └─ 📤 Output Layer (response validation, disclaimer enforcement)
```

---

## 2. Architecture

### Centralized Module: `app/guardrails.py`

All safety logic is centralized in a single module for maintainability. Other modules import from it:

```python
from app.guardrails import (
    run_input_guardrails,    # Full input pipeline
    run_output_guardrails,   # Full output pipeline
    check_critical_values,   # Biomarker panic values
    scan_file_content,       # File malware scanning
    sanitize_input,          # Text sanitization
    redact_pii,              # PII redaction
)
```

### Integration Points

| File | Guardrails Used |
|------|----------------|
| `app/chat_engine.py` | `run_input_guardrails`, `run_output_guardrails`, `redact_pii`, `sanitize_file_text` |
| `app/api.py` | `scan_file_content`, `check_critical_values`, `sanitize_input`, `log_safety_event` |
| `main.py` | Security headers middleware, request size limiting, global exception handler |
| `app/analytics_engine.py` | System prompt rules (supplement dosages, thyroid language, disclaimers) |
| `static/js/app.js` | Client-side length validation, safety banner, critical alert rendering |
| `static/index.html` | Disclaimer modal, safety banner, critical alert UI containers |

---

## 3. Input Layer Guardrails

### 3.1 Input Sanitization

**File:** `app/guardrails.py` → `sanitize_input()`

Cleans all user-provided text before processing:

| Threat | Mitigation |
|--------|------------|
| HTML injection | Strips all HTML tags via regex (`<[^>]+>`) |
| Script injection | Removes `javascript:`, `onXXX=` event handlers, `data:text/html` |
| Null byte injection | Strips null bytes and control characters (`\x00-\x08`, etc.) |
| Excessive whitespace | Normalizes spaces and limits consecutive newlines |
| Content overflow | Truncates to `MAX_MESSAGE_LENGTH` (5,000 characters) |

```python
# Example
sanitize_input("<script>alert('xss')</script>Hello")
# → "alert('xss')Hello"
```

**File text** has a separate sanitizer (`sanitize_file_text()`) with a 50,000 character limit and additional script-block removal.

### 3.2 Rate Limiting

**File:** `app/guardrails.py` → `RateLimiter` class

Prevents abuse by limiting message frequency per session:

| Parameter | Default | Environment Variable |
|-----------|---------|---------------------|
| Max requests per window | 20 | `RATE_LIMIT_REQUESTS` |
| Window duration | 60 seconds | `RATE_LIMIT_WINDOW_SECONDS` |

**Behavior:**
- Each session ID gets its own counter
- When the limit is hit, the user receives a clear message with the wait time
- Old entries are automatically cleaned up to prevent memory growth
- After **5 consecutive guardrail interventions** in a session, an additional warning is appended

### 3.3 Message Length Enforcement

**Enforced at two levels:**

| Level | Limit | Location |
|-------|-------|----------|
| Client-side (JS) | 5,000 characters | `static/js/app.js` → `sendChatMessage()` |
| Server-side (Python) | 5,000 characters | `app/guardrails.py` → `sanitize_input()` |

### 3.4 File Validation & Safety Scanning

**File validation** (`app/api.py` → `_validate_file()`):

| Check | Description |
|-------|-------------|
| Filename presence | Rejects empty filenames |
| Path traversal | Blocks `..` in filenames and validates with `os.path.basename()` |
| Extension whitelist | Only allows: `pdf`, `png`, `jpg`, `jpeg`, `csv`, `txt`, `docx` |
| File size | Maximum 10 MB (configurable via `MAX_UPLOAD_SIZE_MB`) |

**File content scanning** (`app/guardrails.py` → `scan_file_content()`):

| Threat | Detection Method |
|--------|-----------------|
| Windows executables | `MZ` magic bytes at file start |
| Linux executables | `\x7fELF` magic bytes |
| Shell scripts | `#!/` shebang detection |
| PHP scripts | `<?php` detection |
| ASP scripts | `<%` detection |
| Office macros | `vbaProject` / `VBAProject` in DOCX files |
| Decompression bombs | Files exceeding 50 MB |

---

## 4. AI/LLM Guardrails

### 4.1 Emergency & Crisis Detection

**File:** `app/guardrails.py` → `check_emergency()`

Detects emergency situations and **bypasses the LLM entirely**, returning an immediate intervention response with actionable instructions.

**5 Emergency Categories** (checked in priority order):

| Category | Example Keywords | Actions Provided |
|----------|-----------------|------------------|
| **Mental Health Crisis** | "suicide", "want to die", "self harm", "overdose on purpose" | 988 Lifeline, Crisis Text Line (741741), IASP resources, 911 |
| **Cardiac Emergency** | "heart attack", "chest pain", "crushing chest", "can't breathe" | Call 911, chew aspirin, sit upright, don't drive |
| **Stroke** | "stroke", "face drooping", "sudden numbness", "worst headache" | F.A.S.T. method, 3-hour treatment window warning |
| **Severe Allergic Reaction** | "anaphylaxis", "throat closing", "throat swelling", "epipen" | Use EpiPen, call 911, lie down, get to ER |
| **General Emergency** | "call 911", "bleeding profusely", "unconscious", "seizure" | Call 911, nearest ER, CPR if trained |

**Key Design Decision:** Emergency detection runs **before** the LLM call. If triggered, the AI never processes the message — only the pre-written, expert-reviewed intervention is shown.

### 4.2 Adversarial / Prompt Injection Filtering

**File:** `app/guardrails.py` → `check_adversarial()`

Detects attempts to manipulate the AI or misuse it:

| Pattern Category | Examples |
|-----------------|----------|
| Prompt injection | "ignore all previous instructions", "forget your guidelines" |
| Role-swapping | "you are now a hacker", "pretend you're not an AI" |
| Jailbreaking | "DAN mode", "jailbreak" |
| Harmful content | "how to make a bomb", "how to hack" |
| Illicit substances | Drug synthesis, manufacture requests |

**Response:** A polite redirect explaining the AI's health-focused scope.

### 4.3 Off-Topic Deflection

**File:** `app/guardrails.py` → `check_off_topic()`

Gently redirects users who ask about non-health topics:

| Blocked Topics | Examples |
|---------------|----------|
| Finance / Crypto | "bitcoin price prediction", "stock advice" |
| Creative writing | "write me a poem", "generate a story" |
| Politics | "election", "democrat", "republican" |
| Gambling | "casino strategy", "poker tips" |
| Relationships | "dating advice", "ex-boyfriend" |

**Response:** Lists the AI's actual capabilities (biomarkers, nutrition, supplements, lifestyle, health conditions) and asks the user to rephrase.

### 4.4 PII Detection & Redaction

**File:** `app/guardrails.py` → `redact_pii()`

Protects user privacy by detecting and redacting PII **before** the text is sent to the external LLM (Groq):

| PII Type | Pattern | Redaction Label |
|----------|---------|-----------------|
| Social Security Numbers | `XXX-XX-XXXX` | `[SSN REDACTED]` |
| Email addresses | Standard email regex | `[EMAIL REDACTED]` |
| Phone numbers | US phone format (with/without country code) | `[PHONE REDACTED]` |
| Credit card numbers | 16-digit card format | `[CARD REDACTED]` |
| IP addresses | IPv4 format | `[IP REDACTED]` |
| Dates of birth | "DOB: MM/DD/YYYY" patterns | `[DOB REDACTED]` |
| Street addresses | Number + street name + type | `[ADDRESS REDACTED]` |

**Important:** The user sees their original message in the chat UI. Only the version sent to the LLM is redacted.

**High-risk PII** (SSN, credit cards) triggers a safety event log via `has_sensitive_pii()`.

### 4.5 System Prompt Safety Rules

**File:** `app/chat_engine.py` → `ChatEngine.SYSTEM_PROMPT`

The AI's base personality includes **10 hard safety rules**:

1. Not a doctor, nurse, pharmacist, or licensed provider
2. Never diagnose conditions — use "may indicate", "consistent with"
3. Never prescribe medications
4. Never advise stopping, starting, or changing prescribed medications
5. Never provide emergency medical advice — direct to 911
6. Always recommend consulting a healthcare professional
7. Never claim to substitute professional care
8. Flag serious symptoms and advise medical attention
9. Be honest about uncertainty
10. No guarantees about health outcomes

Additionally, a **safety reinforcement system message** is injected into every LLM call:

```python
{
    "role": "system",
    "content": "SAFETY REMINDER: You MUST include a brief disclaimer..."
}
```

### 4.6 Response Validation

**File:** `app/guardrails.py` → `validate_response()`

Scans every AI response for dangerous patterns before returning to the user:

| Dangerous Pattern | Example |
|-------------------|---------|
| Dangerous dosing | "take the entire bottle" |
| Lethal references | "lethal dose", "fatal amount" |
| Dangerous mixing | "mix with alcohol/bleach" |
| Medication interference | "stop taking all your medications" |
| Anti-doctor sentiment | "no need to see a doctor" |
| False guarantees | "guaranteed cure", "100% fix" |
| Replacement advice | "replace your medication with..." |

**Behavior:** If a dangerous pattern is detected, a prominent ⚠️ safety wrapper is prepended to the response.

### 4.7 Disclaimer Enforcement

**File:** `app/guardrails.py` → `ensure_disclaimer_in_response()`

Checks if the AI's response already contains a disclaimer by looking for indicator phrases like:
- "not a substitute"
- "consult a healthcare professional"
- "not a doctor"
- "seek professional"

If no disclaimer is found, appends:

> 🔹 *Reminder: I am an AI assistant, not a doctor. This is not medical advice. Always consult a healthcare professional for medical decisions.*

---

## 5. Clinical Safety Guardrails

### 5.1 Critical/Panic Value Detection

**File:** `app/guardrails.py` → `check_critical_values()`

Checks submitted biomarker values against clinically defined **critical/panic thresholds**:

| Biomarker | Critical Low | Critical High | Unit |
|-----------|-------------|---------------|------|
| Hemoglobin | < 7.0 | > 20.0 | g/dL |
| Fasting Glucose | < 50.0 | > 400.0 | mg/dL |
| HbA1c | — | > 12.0 | % |
| SGPT/ALT | — | > 1,000.0 | U/L |
| TSH | < 0.1 | > 50.0 | mIU/L |
| Triglycerides | — | > 500.0 | mg/dL |
| LDL | — | > 300.0 | mg/dL |
| Total Cholesterol | — | > 400.0 | mg/dL |
| Ferritin | < 5.0 | > 1,000.0 | ng/mL |
| hs-CRP | — | > 10.0 | mg/L |

**Behavior:**
- Critical findings are returned as a `critical_alerts` array in the API response
- The frontend renders a **prominent red pulsing alert banner** at the top of results
- The banner auto-scrolls into view to ensure visibility
- Each alert includes the biomarker name, actual value, threshold, and a message urging immediate medical attention

### 5.2 Supplement Dosage Rules

**File:** `app/analytics_engine.py` → System prompt rules

The LLM is instructed to provide **treatment-level dosages** based on deficiency severity, not generic preventive doses:

| Supplement | Deficient Dose | Insufficient Dose |
|-----------|---------------|-------------------|
| Vitamin D | 60,000 IU/week × 8 weeks → 2,000 IU/day | 2,000–4,000 IU/day |
| Vitamin B12 | 1,000–2,000 mcg/day × 8–12 weeks | 500–1,000 mcg/day |
| Iron (Ferritin) | 65–200 mg elemental iron/day | 30–65 mg/day |

### 5.3 Conservative Medical Language

**File:** `app/analytics_engine.py` → System prompt rules

For sensitive conditions like thyroid disorders, the AI is explicitly instructed to use conservative language:

- ✅ "may warrant further evaluation"
- ✅ "consider discussing with your endocrinologist"
- ✅ "monitoring is recommended"
- ❌ ~~"you need to start medication"~~
- ❌ ~~"you have hypothyroidism"~~

---

## 6. Data Privacy & Security

### 6.1 Temporary File Deletion

**Files:** `app/api.py`, `app/file_processor.py`

Uploaded files are deleted **immediately** after text extraction:

```python
# Privacy Guard Rail: Clean up file immediately after extraction
try:
    if os.path.exists(filepath):
        os.remove(filepath)
except Exception as e:
    print(f"Warning: Could not delete temporary file {filepath}: {e}")
```

No uploaded files are retained on the server.

### 6.2 API Key Management

**File:** `app/config.py`

- All API keys (Groq, SerpAPI) are loaded from **environment variables**
- The `.env` file is **gitignored** and never committed
- Warnings are logged if keys are missing, but the app still starts (with degraded functionality)

### 6.3 Security Headers

**File:** `main.py` → `SecurityHeadersMiddleware`

Every response includes:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable browser XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer leakage |
| `Permissions-Policy` | Disables camera, mic, geo, payment, USB, magnetometer | Restrict browser APIs |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'; ...` | Restrict content sources |
| `Cache-Control` | `no-store` (API routes only) | Prevent caching of health data |

### 6.4 CORS Configuration

**File:** `main.py` + `app/config.py`

| Environment | Behavior |
|-------------|----------|
| Development | Allows `localhost:8050`, `127.0.0.1:8050`, `localhost:3000` |
| Production | Configurable via `CORS_ORIGINS` env var; defaults to same-origin |

Only `GET`, `POST`, and `DELETE` methods are allowed. Only `Content-Type` and `Authorization` headers are permitted.

### 6.5 Error Sanitization

**File:** `main.py` → `global_exception_handler`

In production, internal error details are **never** exposed to clients:

```python
# Production response:
{"detail": "An internal error occurred. Please try again later."}

# NOT:
{"detail": "KeyError: 'hemoglobin' at line 42 in analytics_engine.py"}
```

Individual endpoints also sanitize error messages:
```python
raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")
# NOT: detail=str(e)
```

### 6.6 Request Size Limits

**File:** `main.py` → `RequestSizeLimitMiddleware`

Maximum request body: **15 MB** (slightly above the 10 MB file upload limit to account for multipart overhead).

Requests exceeding this limit receive a `413 Payload Too Large` response before any processing occurs.

---

## 7. Frontend Guardrails

### 7.1 Medical Disclaimer Modal

**Files:** `static/index.html`, `static/js/app.js`

- **Blocks all interaction** until the user explicitly agrees to the medical disclaimer
- Requires checking a checkbox before the "I Agree" button becomes clickable
- Acceptance is stored in `localStorage` so it only shows once per browser
- Contains clear language: "AI-generated information... not a substitute for professional medical judgment"

### 7.2 Persistent Safety Banner

**Files:** `static/index.html`, `static/js/app.js`, `static/css/styles.css`

A subtle but always-visible banner at the top of the content area:

> **AI Health Tool** — For informational purposes only. Not a substitute for professional medical advice. [Learn more](#)

- **"Learn more"** re-opens the full disclaimer modal
- **Dismissible** via ✕ button; preference saved in `localStorage`
- Styled with a warm gradient (amber → red) on a dark background

### 7.3 Critical Value Alert Panels

**Files:** `static/index.html`, `static/js/app.js`, `static/css/styles.css`

When critical biomarker values are detected by the backend:

- A **red pulsing border banner** appears at the top of the results section
- Each critical biomarker is listed with its value, threshold, and direction (HIGH/LOW)
- The page **auto-scrolls** to the alert for guaranteed visibility
- Present in **both** the form-based analysis and file upload analysis views
- Banner includes: "These values are outside safe ranges. Please contact your healthcare provider or visit an emergency room immediately."

### 7.4 Client-Side Input Validation

**File:** `static/js/app.js`

| Validation | Limit | Behavior |
|-----------|-------|----------|
| Chat message length | 5,000 chars | Toast error, prevents send |
| File size | 10 MB | Toast error, prevents upload |
| File type | pdf, png, jpg, jpeg, csv, txt, docx | Toast error, prevents upload |
| Required fields | Age + Gender for analysis | Toast error, prevents submit |

---

## 8. Audit & Observability

**File:** `app/guardrails.py` → `log_safety_event()`

All safety-related events are logged with structured output:

```
[SAFETY:EMERGENCY] [session=abc-123] 2026-02-20T15:00:00 — Category: mental_health_crisis
[SAFETY:ADVERSARIAL] [session=abc-123] 2026-02-20T15:01:00 — Adversarial input detected
[SAFETY:PII_REDACTED] [session=abc-123] 2026-02-20T15:02:00 — Redacted PII types: ['ssn', 'email']
[SAFETY:RATE_LIMIT] [session=abc-123] 2026-02-20T15:03:00 — Rate limit hit
[SAFETY:FILE_REJECTED] 2026-02-20T15:04:00 — File 'report.pdf' rejected: executable detected
[SAFETY:CRITICAL_VALUES] 2026-02-20T15:05:00 — Critical biomarker values detected: ['hemoglobin']
[SAFETY:REPEATED_VIOLATIONS] [session=abc-123] 2026-02-20T15:06:00 — Session has 5 interventions
```

**Event types logged:**
- `EMERGENCY` — Crisis/emergency keyword detected
- `ADVERSARIAL` — Prompt injection or adversarial attempt
- `OFF_TOPIC` — Non-health query deflected
- `PII_WARNING` — High-risk PII (SSN/credit card) in input
- `PII_REDACTED` — PII was redacted before LLM call
- `RATE_LIMIT` — Rate limit exceeded
- `FILE_REJECTED` — File failed safety scan
- `CRITICAL_VALUES` — Panic biomarker values detected
- `REPEATED_VIOLATIONS` — Multiple guardrail triggers in one session

---

## 9. Testing

**File:** `test_guardrails.py`

A comprehensive test suite with **27 automated tests** covering:

| Category | Tests |
|----------|-------|
| Input sanitization | HTML stripping, null byte removal, length truncation |
| PII redaction | SSN detection, email detection, redaction verification |
| Emergency detection | Cardiac, mental health, stroke, false positive check |
| Adversarial filtering | Prompt injection, jailbreak, normal query pass-through |
| Off-topic detection | Crypto, gambling, normal health query pass-through |
| Critical values | Low hemoglobin, high glucose, normal value pass-through |
| File scanning | PDF pass, executable block, PHP script block |
| Response validation | Disclaimer auto-append |
| Full pipeline | Normal message, emergency, adversarial — end-to-end |

**Run tests:**
```bash
python test_guardrails.py
```

**Expected output:**
```
Results: 27 passed, 0 failed out of 27 tests
🎉 ALL TESTS PASSED!
```

---

## 10. Configuration Reference

All security-related configuration is in `app/config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | `""` | Groq LLM API key (required for AI features) |
| `SERPAPI_KEY` | `""` | SerpAPI key for web search context |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum file upload size in MB |
| `CORS_ORIGINS` | Auto-detected | Comma-separated allowed origins |
| `ENVIRONMENT` | `"production"` | Set to `"development"` for debug features |
| `RATE_LIMIT_REQUESTS` | `20` | Max messages per rate limit window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window duration |

**Constants in `app/guardrails.py`:**

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_MESSAGE_LENGTH` | 5,000 | Max characters per chat message |
| `MAX_FILE_TEXT_LENGTH` | 50,000 | Max characters from file extraction |
| `MAX_MESSAGES_PER_MINUTE` | 20 | Rate limit threshold |
| `MAX_SESSIONS_PER_IP` | 50 | Max concurrent sessions (reserved) |

---

## 11. Future Improvements

The following enhancements are recommended for production deployment:

| Area | Improvement | Priority |
|------|-------------|----------|
| **Logging** | Replace `print()` audit logs with structured logging (e.g., Python `logging` module → ELK/CloudWatch) | High |
| **Rate limiting** | Move from in-memory to Redis-backed rate limiting for multi-instance deployments | High |
| **PII detection** | Add ML-based NER for name detection (current regex approach doesn't catch proper names) | Medium |
| **Content moderation** | Add a dedicated moderation API (e.g., OpenAI Moderation, Perspective API) as a secondary check | Medium |
| **Session management** | Add session expiration and cleanup for long-running servers | Medium |
| **HTTPS enforcement** | Add HSTS header and redirect HTTP → HTTPS in production | High |
| **Input validation** | Add schema validation for biomarker ranges (e.g., hemoglobin can't be 500 g/dL) | Medium |
| **Audit trail** | Persist safety events to database for compliance reporting | High |
| **Testing** | Add integration tests that verify the full API → guardrail → LLM → response chain | Medium |
| **Localization** | Add emergency numbers for non-US regions (currently US-centric: 911, 988) | Low |

---

## Guardrail Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │ Input Sanitize   │  Strip HTML, scripts, null bytes
            │ (guardrails.py)  │  Truncate to max length
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Rate Limiter     │  20 req/min per session
            │ (guardrails.py)  │──── BLOCKED? → Return wait msg
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Emergency Check  │  5 categories, 60+ keywords
            │ (guardrails.py)  │──── DETECTED? → Return crisis
            └────────┬─────────┘     intervention (skip LLM)
                     │
                     ▼
            ┌──────────────────┐
            │ Adversarial Check│  Injection, jailbreak, harmful
            │ (guardrails.py)  │──── DETECTED? → Return warning
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Off-Topic Check  │  Crypto, gambling, politics...
            │ (guardrails.py)  │──── DETECTED? → Redirect msg
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ PII Redaction    │  SSN, email, phone, CC...
            │ (guardrails.py)  │  Redact in LLM copy only
            └────────┬─────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   GROQ LLM CALL      │  With safety system prompt
         │   (chat_engine.py)   │  + safety reinforcement msg
         └───────────┬───────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Response Validate│  Check for dangerous patterns
            │ (guardrails.py)  │  Add warning wrapper if found
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Disclaimer Check │  Ensure medical disclaimer
            │ (guardrails.py)  │  present; append if missing
            └────────┬─────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   SAFE RESPONSE TO USER                      │
└─────────────────────────────────────────────────────────────┘
```

---

*This document is maintained alongside the codebase. For implementation details, refer to `app/guardrails.py` and `test_guardrails.py`.*
