# Dashboard redesign validation

Validated on 3 November 2026 with Python 3.12 and Streamlit 1.66.0.

- `python -m pytest -q -p no:cacheprovider --basetemp=.test-tmp/verified-suite`:
  **30 passed**. The Windows sandbox prevented temporary-directory access; the
  successful run used the approved execution environment. One existing Starlette
  deprecation warning remains.
- `python -m ruff check frontend tests/test_dashboard.py`: **passed**.
- The regression suite covers API compatibility, isolated conversation memory,
  streaming persistence and failure, model availability, editable prompt selection
  without generation, category filters, history search, reopening and resetting chats,
  export control availability, confirmation/cancellation/deletion, and preference
  retention across navigation.

Tests mock Ollama; no live model generation was verified. Existing user data was
not used for the tests.

Live visual review was attempted in Chrome with a synthetic-data preview. Computer
Use stopped because it could not verify the browser URL, so desktop/mobile layout,
contrast, keyboard interaction, and downloaded file rendering still need live review.
Responsive CSS includes four-, two-, and single-column card layouts, explicit focus
styles, and reduced-motion/forced-color rules; these are implementation checks,
not a claim of completed visual or accessibility certification.

Composer follow-up: inspected the running Docker frontend (Streamlit 1.66.1),
rebuilt the frontend container, and visually checked the composer in Edge at
`http://127.0.0.1:8501/`. Confirmed the native inner border is removed and the
focused textarea no longer draws a rectangular outline. A single rounded outer
border provides the focus indicator. This targeted check does not replace the
full responsive/accessibility review described above.
