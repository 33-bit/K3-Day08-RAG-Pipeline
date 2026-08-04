# UniHelp Dark Navy + Teal UI Design

## Goal

Make the Streamlit chatbot comfortably readable for university students while
keeping the existing dark navy visual identity and every retrieval/generation
interaction unchanged.

## Problem Evidence

The supplied desktop screenshot shows three concrete readability failures:

1. Streamlit's application header is white, which breaks the dark shell.
2. Native suggestion buttons have white surfaces with nearly white text.
3. Chat output and citations sit on dark surfaces without an explicit,
   sufficiently bright text colour, making the answer difficult to read.

`app.py` already declares a navy gradient, a teal hero, source cards, badges,
sidebar controls, suggestion buttons, chat history, a chat input, and a source
expander. The redesign will restyle those existing components rather than
changing the RAG pipeline, session state, or response contract.

## Visual Direction

Use a compact "dark navy + teal" system:

| Token | Value | Use |
| --- | --- | --- |
| Canvas | `#0B1220` | application background |
| Surface | `#111C2E` | chat cards, controls, source cards |
| Surface-raised | `#18263B` | hover and assistant message |
| Border | `#2A3B55` | boundaries and inactive controls |
| Text-primary | `#F1F5F9` | headings and body copy |
| Text-secondary | `#B6C4D6` | captions and metadata |
| Teal | `#2DD4BF` | primary action, focus and links |
| Teal-deep | `#0F766E` | user message and active state |
| Amber | `#FBBF24` | PageIndex status only |
| Red | `#FB7185` | error state only |

The UI must not use a white page-level surface. Native Streamlit widgets must
receive explicit foreground and background colours; custom classes alone do not
style `st.button`, `st.chat_input`, tabs, and expanders.

## Components and Behaviour

### App shell and sidebar

- Style Streamlit's header/test-id toolbar with the canvas colour so the white
  strip disappears.
- Keep the sidebar expanded on desktop. Use an opaque navy surface and one
  low-contrast border; retain Top-K, threshold, reranking, and metric controls.
- Keep the coral "new conversation" control only as the destructive/reset
  accent; all normal interactive states use teal.

### Chat workspace

- Preserve the three tabs and the current hero copy.
- Give tabs an explicit inactive text colour, teal active underline, and
  visible hover state.
- Keep the hero as a dark teal gradient with primary text `#F1F5F9`; use the
  teal gradient only on the title, never on paragraph text.
- Style the existing suggestion buttons as navy cards with primary text, a teal
  border on hover, and teal keyboard focus. Do not change their callback or
  pending-query behaviour.
- Style the chat input as a raised navy surface with a teal focus ring and
  readable placeholder. Do not alter its submit or pending-query behaviour.
- Render student messages with a teal-deep background and assistant messages
  with a raised navy background. Body paragraphs, headings, inline code,
  citations and links within both bubbles must have explicit readable colours.

### Evidence and system state

- Keep the existing source expander and decimal score formatting (`0.0000`).
- Give expander headers, source-card file name, excerpt, source type badge,
  score and source link explicit palette colours.
- Keep existing semantic meanings: hybrid is teal, PageIndex is amber, speed is
  cyan, and error is red. These badges remain supplemental; their labels must
  convey the state without relying on colour alone.

## Architecture and File Boundaries

Only the presentation layer changes.

- `app.py`: make a CSS-only presentation change in the existing theme block.
  Retain the current widget tree, retrieval, generation, session-state, and
  source-rendering code paths exactly as they are.
- `tests/test_ui_helpers.py`: run existing contract tests unchanged. CSS pixel
  output is checked manually in the browser.
- No files in `src/task4_*`, `src/task5_*`, `src/task6_*`, `src/task8_*`,
  `src/task9_*`, or `src/task10_generation.py` are changed for this redesign.

## Acceptance Criteria

1. At 1440 px desktop width, no page-level white header/surface remains.
2. Suggestions, tabs, chat input, assistant text, source content and links are
   legible on the dark palette without selecting text.
3. Keyboard focus on buttons and input is visibly teal.
4. User can submit a suggestion, clear conversation, configure Top-K, send a
   chat question, read the answer, and open sources exactly as before.
5. Source scores stay formatted to four decimals and PageIndex/hybrid labels
   remain visible.
6. Python compilation and the UI-helper test file pass. A manual Streamlit
   browser check confirms the visual criteria above.

## Out of Scope

- Changing the retrieval algorithm, RRF settings, source schema, OpenRouter
  call, or response content.
- Adding authentication, mobile-specific navigation, file upload, analytics,
  or new pages.
