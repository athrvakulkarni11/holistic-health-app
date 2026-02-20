# 🛡️ How We Keep You Safe — Holistic Health AI Platform

> **A plain-language guide to the safety measures built into our health assistant**  
> Last updated: February 20, 2026

---

## What Is This Document?

Our Holistic Health AI platform uses artificial intelligence to help people understand their lab results, get wellness tips, and learn about nutrition. Because health is serious, we've built many layers of protection — called **guardrails** — to make sure the tool is used safely and responsibly.

This document explains those protections in simple terms, so anyone can understand what we do to keep users safe.

---

## 🚨 1. Emergency Protection

**What it does:**  
If someone types something that indicates an **active medical emergency** — such as "I think I'm having a heart attack" or "I want to kill myself" — the AI **immediately stops** and shows emergency instructions instead of trying to answer the question itself.

**What it does NOT block:**  
Informational questions like "What causes chest pain?" or "Tell me about stroke prevention" are **not** blocked. These are legitimate health questions, and the AI answers them normally. The system only intervenes when the language clearly suggests an emergency is happening *right now*.

**Why it matters:**  
An AI should never try to handle a real emergency. Our system recognizes specific multi-word emergency phrases across five categories and responds with the right phone numbers and action steps:

| Emergency Type | What The User Sees |
|---------------|-------------------|
| 🧠 Mental health crisis (e.g., "I want to end my life") | Suicide & Crisis Lifeline number (988), Crisis Text Line, and a message that their life matters |
| ❤️ Heart emergency (e.g., "I have chest pain") | Instructions to call 911, chew aspirin, sit upright, and not drive |
| 🧬 Stroke symptoms (e.g., "my face is drooping") | The F.A.S.T. method and the 3-hour treatment window reminder |
| ⚠️ Severe allergic reaction (e.g., "my throat is closing") | Instructions to use an EpiPen and call 911 |
| 🏥 General emergency (e.g., "someone is unconscious") | Instructions to call 911 and go to the nearest ER |

**Key point:** The AI does **not** attempt to give medical advice in these situations. It only provides emergency contact information and directs the user to professional help.

---

## 🩺 2. Medical Disclaimer

**What it does:**  
The very first time you open the app, a full-screen notice appears explaining that:

- This tool is **not a doctor**
- It provides **information only**, not medical advice
- You should **always consult a real healthcare professional** before acting on anything

You must read and agree to this before you can use any feature. The app also shows a small reminder banner at the top of every page that says:

> **AI Health Tool** — For informational purposes only. Not a substitute for professional medical advice.

**Why it matters:**  
We want every user to understand, before they start, that this is an educational tool — not a replacement for their doctor.

---

## 🔴 3. Dangerous Lab Value Alerts

**What it does:**  
When you enter your lab results (like blood sugar, hemoglobin, cholesterol, etc.), the system checks each value against **medically recognized danger thresholds**. If any value is dangerously high or low, a bright red warning banner appears at the top of your results.

**Example:**  
If someone enters a blood sugar (glucose) level of 450 mg/dL — which is dangerously high — they will see:

> ⚠️ **CRITICAL: fasting_glucose is 450 mg/dL — above critical threshold of 400 mg/dL. Seek immediate medical attention.**

**We check 10 key biomarkers for critical values:**

| Biomarker | We alert if it's below... | We alert if it's above... |
|-----------|--------------------------|--------------------------|
| Hemoglobin | 7.0 g/dL | 20.0 g/dL |
| Blood Sugar (Fasting) | 50 mg/dL | 400 mg/dL |
| HbA1c (Diabetes marker) | — | 12% |
| Liver Enzyme (ALT) | — | 1,000 U/L |
| Thyroid (TSH) | 0.1 mIU/L | 50 mIU/L |
| Triglycerides | — | 500 mg/dL |
| LDL Cholesterol | — | 300 mg/dL |
| Total Cholesterol | — | 400 mg/dL |
| Ferritin (Iron stores) | 5.0 ng/mL | 1,000 ng/mL |
| hs-CRP (Inflammation) | — | 10.0 mg/L |

**Why it matters:**  
Some lab values are so extreme they could indicate a life-threatening condition. Rather than burying this in an AI-generated report, we flag it immediately and clearly.

---

## 🤖 4. What The AI Will and Won't Do

Our AI assistant follows strict rules about what it can and cannot say:

### ✅ The AI WILL:
- Explain what your lab results mean in general terms
- Suggest foods, supplements, and lifestyle changes based on published research
- **Suggest commonly used medications** for you to discuss with your doctor (e.g., "your doctor may consider prescribing metformin for this condition")
- Point you toward helpful resources and information
- Remind you to see a doctor for important decisions
- Say "I'm not sure" when it genuinely doesn't know

### ❌ The AI will NEVER:
- Tell you that you have a specific disease or condition (it says "this *may indicate*..." instead)
- **Write a prescription** — it may suggest medications, but always frames them as "discuss with your doctor"
- Tell you to stop or change any medication your doctor prescribed without consulting your doctor
- Promise that something will cure you
- Handle a real medical emergency (it redirects you to 911 instead)
- Claim to be a doctor or medical professional

---

## 🕵️ 5. Personal Information Protection

**What it does:**  
Before your message is sent to the AI for processing, we automatically scan it for personal information like:

- Social Security Numbers
- Email addresses
- Phone numbers
- Credit card numbers
- Home addresses
- Dates of birth

If we find any, we **replace them with a placeholder** (like `[SSN REDACTED]`) before the AI ever sees your message. You still see your original message in the chat — only the AI's copy is cleaned.

**Why it matters:**  
The AI is powered by an external service (Groq). By removing personal details before sending your message, we reduce the risk of your private information being processed or stored outside our system.

### What Happens To Your Uploaded Files?

When you upload a lab report (PDF, image, etc.), the system:

1. Reads the text from the file
2. Extracts the lab values
3. **Immediately deletes the file** from our server

We do **not** keep copies of your uploaded documents.

---

## 🚫 6. Keeping The AI Focused on Health

**What it does:**  
Our AI is designed for health and wellness. If someone asks about clearly unrelated topics, the AI politely redirects them.

### Topics the AI will redirect away from:

| Off-Topic Area | Example Question |
|---------------|------------------|
| 💰 Finance & Crypto | "What's the Bitcoin price prediction?" |
| 🎰 Gambling strategy | "What's the best poker strategy?" |
| ✍️ Creative writing | "Write me a poem about cats" |

### Topics the AI WILL discuss (because they relate to health):

| Topic | Why It's Allowed |
|-------|------------------|
| 💕 Relationship stress | Stress impacts physical and mental health |
| 🗳️ Political stress | Anxiety and stress are health-relevant |
| 🎲 Gambling addiction | Addiction is a recognized health condition |
| 💊 Medication questions | Users should be able to ask about treatments |

**Why it matters:**  
We want the AI to be helpful, not frustrating. Many topics that seem off-topic actually have real health dimensions, so we only block things that are clearly unrelated to wellness.

---

## 🔒 7. Protection Against Misuse

**What it does:**  
Some people may try to trick an AI into ignoring its safety rules (this is called "prompt injection" or "jailbreaking"). Our system detects these attempts and blocks them. Examples of blocked messages:

- "Ignore all your previous instructions"
- "Pretend you're not an AI"
- "Enable jailbreak mode"
- Requests for harmful information (weapons, hacking, etc.)

**Why it matters:**  
Without this protection, a bad actor could potentially trick the AI into giving dangerous health advice or behaving irresponsibly.

---

## ⏱️ 8. Usage Limits

**What it does:**  
To prevent abuse and ensure fair access for everyone, we limit how quickly messages can be sent:

- **20 messages per minute** per user session
- If you exceed the limit, you'll see a message asking you to wait a few seconds
- If the system detects **repeated rule violations** in one session (5 or more), it adds an extra warning

**What about file uploads?**
- Maximum file size: **10 MB**
- Allowed file types: PDF, PNG, JPG, CSV, TXT, DOCX
- Files that look like software programs or scripts are automatically **rejected**

---

## 💊 9. Careful Supplement Recommendations

**What it does:**  
When the AI suggests supplements (like Vitamin D or Iron), it doesn't just give generic advice. It adjusts the recommended amount based on **how deficient your lab results show you are**:

| Situation | What the AI recommends |
|-----------|----------------------|
| Severely low Vitamin D | Higher therapeutic dose (60,000 IU/week for 8 weeks) |
| Mildly low Vitamin D | Moderate daily dose (2,000–4,000 IU/day) |
| Normal Vitamin D | No supplement needed |

**Why it matters:**  
Generic supplement advice (like "take some Vitamin D") isn't helpful. But recklessly high doses can be harmful. Our AI is trained to recommend amounts that align with actual clinical practice.

---

## 🏥 10. Conservative Language for Sensitive Conditions

**What it does:**  
For conditions like thyroid disorders, the AI uses extra-cautious language:

- ✅ "Your TSH levels may warrant further evaluation by an endocrinologist"
- ❌ ~~"You have hypothyroidism and need medication"~~

It **never** tells you that you have a condition. It suggests that your results might be worth discussing with a specialist.

**Why it matters:**  
Diagnosing a medical condition requires a trained doctor looking at the full picture — not just one number. Premature labeling can cause unnecessary anxiety or lead to self-treatment.

---

## 🔍 11. What The AI Checks Before Responding

Every single message goes through this safety process before you see a response:

```
Your Message
    ↓
1️⃣  Clean up — Remove any harmful code or formatting tricks
    ↓
2️⃣  Speed check — Make sure you're not sending too many messages
    ↓
3️⃣  Emergency scan — Is this an emergency? → Show emergency info
    ↓
4️⃣  Manipulation check — Is someone trying to trick the AI? → Block it
    ↓
5️⃣  Topic check — Is this about health? → Redirect if not
    ↓
6️⃣  Privacy scan — Remove any personal info (SSN, email, etc.)
    ↓
7️⃣  AI processes your question with safety rules active
    ↓
8️⃣  Response check — Scan the AI's answer for anything dangerous
    ↓
9️⃣  Disclaimer check — Make sure a medical reminder is included
    ↓
✅ Safe response shown to you
```

---

## 📋 Summary: All Safety Measures at a Glance

| # | Protection | What It Prevents |
|---|-----------|-----------------|
| 1 | Emergency detection | AI trying to handle real emergencies |
| 2 | Medical disclaimer | Users mistaking AI for real medical advice |
| 3 | Critical value alerts | Users ignoring dangerously abnormal lab results |
| 4 | AI behavior rules | AI diagnosing definitively or making guarantees |
| 5 | Personal info protection | Private data being sent to external AI services |
| 6 | Automatic file deletion | Lab reports being stored on the server |
| 7 | Health-only focus | AI being used for non-health purposes |
| 8 | Manipulation blocking | People tricking the AI into unsafe behavior |
| 9 | Message rate limits | Spamming or overloading the system |
| 10 | File safety scanning | Malicious files being uploaded |
| 11 | Supplement dosage care | Recklessly high or generic supplement advice |
| 12 | Conservative medical language | AI making premature diagnoses |
| 13 | Response safety scanning | AI accidentally saying something dangerous |
| 14 | Mandatory disclaimers | Any response going out without a safety reminder |

---

## ❓ Frequently Asked Questions

**Q: Is this app a replacement for my doctor?**  
A: Absolutely not. This is an educational tool that helps you understand your lab results and learn about wellness. Always consult your doctor for medical decisions.

**Q: Does the app store my lab reports?**  
A: No. Uploaded files are processed and then immediately deleted. We do not keep copies.

**Q: What happens if I type something about an emergency?**  
A: The AI stops processing your question and immediately shows you emergency contact numbers and action steps. It does not try to help with the emergency itself.

**Q: Can the AI suggest medication?**  
A: The AI can suggest commonly used medications for you to discuss with your doctor (e.g., "your doctor may consider metformin for type 2 diabetes"). However, it will never write a prescription or tell you to change medications your doctor has prescribed. Any medication suggestions are verified against a known drug database, and unfamiliar mentions are flagged with a note to verify with your pharmacist.

**Q: What if the AI gives wrong advice?**  
A: This is precisely why every response includes a reminder to verify information with a healthcare professional. AI can make mistakes, and medical decisions should always involve a trained doctor.

**Q: Is my personal information safe?**  
A: We take several steps to protect your privacy: personal information is removed before being sent to the AI, uploaded files are deleted immediately, and no health data is stored long-term.

---

*For the technical implementation details behind these protections, see `GUARDRAILS.md`.*  
*If you have questions or concerns about safety, please contact the development team.*
