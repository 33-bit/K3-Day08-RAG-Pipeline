# UniHelp Contrast UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the UniHelp Streamlit interface legible in a dark navy + teal theme without changing retrieval, generation, or chat behaviour.

**Architecture:** Make a CSS-only presentation change in the existing `<style>` block in `app.py`. Verify the rendered Streamlit application in a browser at desktop width; a source-text CSS test is intentionally excluded because it would only detect string changes rather than a user-visible behaviour. The current widget tree, event callbacks, session state, RAG calls, and source contract remain untouched.

**Tech Stack:** Python 3.12, Streamlit 1.60, pytest 9, CSS injected by `st.markdown`.

## Global Constraints

- Modify only CSS inside `app.py`; do not alter Python control flow, widget calls, session state, retrieval, OpenRouter, or source rendering.
- Use `#0B1220` canvas, `#111C2E` surface, `#18263B` raised surface, `#F1F5F9` primary text, `#B6C4D6` secondary text, `#2DD4BF` teal, `#0F766E` teal-deep, and `#2A3B55` border.
- Preserve `st.chat_input`, all four suggestion-button keys, the three tabs, source expander, source score format `0.0000`, and sidebar controls.
- Verify with `.venv/bin/python -m pytest`; do not use the global Python or global Streamlit executable.

---

### Task 1: Apply and verify the contrast-only theme refresh

**Files:**
- Modify: `app.py:30-220`
- Test: `tests/test_ui_helpers.py`

**Interfaces:**
- Consumes: the existing Streamlit widget tree and CSS theme block.
- Produces: explicit dark navy + teal presentation for all native surfaces shown in the chat UI.

- [x] **Step 1: Record the visual failure baseline**

Use the supplied screenshot as the pre-change baseline. Record the three user-visible failures:

1. White Streamlit header breaks the dark shell.
2. White suggestion buttons have nearly white text.
3. Chat output and citations do not have an explicit readable foreground colour.

- [x] **Step 2: Replace only the CSS theme block in `app.py`**

In the existing `st.markdown` CSS string at `app.py:30-220`:

1. Declare the eight palette variables under `:root`, including the exact
   `--canvas` and `--text-primary` tokens asserted by the test.
2. Set `.stApp`, `[data-testid="stAppViewContainer"]`, and
   `[data-testid="stHeader"]` to `var(--canvas)` with primary text. Set the
   header's decoration and toolbar background to transparent/canvas so no white
   strip remains.
3. Restyle `[data-testid="stTabs"]` and its tab buttons with secondary
   inactive text, teal active text/bottom border, and a visible teal focus
   outline.
4. Restyle `[data-testid="stButton"] > button` with a navy surface, primary
   text, border, hover elevation and teal focus outline. Keep
   `[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]`
   as coral to preserve the reset affordance.
5. Restyle `[data-testid="stChatInput"]`, its textarea/input and send button
   with raised navy background, primary text, readable placeholder, teal focus
   outline and teal hover state.
6. Restyle `[data-testid="stChatMessage"]`, assistant and user message
   containers, all headings/paragraphs/list items, inline code and anchors so
   no Markdown answer, citation, or link inherits an unreadable default.
7. Restyle `[data-testid="stExpander"]`, its summary header and expanded body
   to use navy surfaces, primary labels, secondary excerpts and teal source
   links. Preserve all existing source-card/badge classes and score rendering.
8. Remove the unused `.quick-chip-btn` rules rather than adding a second button
   system.

Do not change any lines outside the CSS string.

- [x] **Step 3: Run automated safety checks**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_ui_helpers.py
.venv/bin/python -m py_compile app.py
git diff --check
```

Expected: existing UI response-contract tests pass, Python compiles, and
`git diff --check` prints no whitespace errors.

- [x] **Step 4: Run visual verification in the browser**

Start the app with:

```bash
.venv/bin/python -m streamlit run app.py
```

At 1440 px desktop width, verify the header is navy, not white; inactive and
active tabs are readable; four suggestion buttons have light text on navy;
the input placeholder is readable; an assistant answer and its source expander
are readable; and keyboard focus on a button and input is teal.

- [ ] **Step 5: Commit the isolated UI change**

Run:

```bash
git add app.py
git commit -m "style: improve UniHelp dark theme contrast"
```

Do not stage ChromaDB files or unrelated Task 10 files.
