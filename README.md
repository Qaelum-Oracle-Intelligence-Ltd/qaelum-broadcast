# QAELUM Build Broadcast

Plain-English engineering updates on the QAELUM build, for a small named audience.

`index.html` carries only encrypted content (AES-256-GCM, key derived from a passcode with PBKDF2-SHA256, 600,000 iterations). Without the passcode the page shows a lock screen and the file is unreadable. No edition text is stored in this repository in the clear.

`tools/build.py` and `tools/template.html` rebuild the page from the edition data. The passcode is supplied at build time and is never committed.

`tools/make_master.py` builds Nahum's private master page from the same template, so the master and this page always look the same. Each change shows who opened, reviewed and merged it, with the review story in order.

`tools/verify_edition.py` checks an edition against the GitHub record before it is published: line counts, who opened and merged each change, every story time, and every quote word for word. It also checks the "Ask the team" desks: quotes word for word, the star arithmetic of the ratings, and every measured response time.

The "Ask the team" section has three desks: Nahum, Thomas and an independent AI reviewer. Viewers give their name first; it stays on their own phone. Founder desks answer only with what each founder actually wrote on GitHub, measured facts, and answers the founders wrote themselves. Nothing is generated in the page and nothing is sent anywhere, except a question or rating a viewer chooses to send through WhatsApp.

Nahum · QAELUM Oracle Intelligence
