# QAELUM Build Broadcast

Plain-English engineering updates on the QAELUM build, for a small named audience.

`index.html` carries only encrypted content (AES-256-GCM, key derived from a passcode with PBKDF2-SHA256, 600,000 iterations). Without the passcode the page shows a lock screen and the file is unreadable. No edition text is stored in this repository in the clear.

`tools/build.py` and `tools/template.html` rebuild the page from the edition data. The passcode is supplied at build time and is never committed.

Nahum · QAELUM Oracle Intelligence
