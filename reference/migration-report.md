# PSY migration review

Built **57 content pages plus one shared Privacy Policy** from **62 WordPress pages**.
Includes **21 current faculty biographies**, in worksheet order on the faculty index.
Every page uses the same temporary Saunders mural hero, with per-site JSON settings.

- Full-width, single-column content; no sidebars or WordPress layout styles.
- Useful sidebar links retained as plain links beneath the content.
- Both Overview pages retained; their introductory copy moved to Why Study PSY.
- Diversity and Program Areas use folders with index pages and supporting pages.
- Standalone Courses, Contact, and Support PSY live at the root.
- Tables use the shared styling and gray sections, with labeled cards below desktop width.
- 39 inline images copied locally; faculty portraits/contact/profile blocks omitted.
- Original Privacy Policy replaced by the single shared `/privacy.html`.

## Leftover pages, not published

- Lorey Takahashi (draft): https://psychology.manoa.hawaii.edu/?page_id=1411
- Kentaro Hayashi (draft): https://psychology.manoa.hawaii.edu/?page_id=1462
- OLD-applications-admissions (publish): https://psychology.manoa.hawaii.edu/old-applications-admissions/
- Leon James (publish): https://psychology.manoa.hawaii.edu/leon-james/
- Kelly Vitousek (publish): https://psychology.manoa.hawaii.edu/kelly-vitousek/
- Jillian Janowiak (publish): https://psychology.manoa.hawaii.edu/jillian-janowiak/

The five extra faculty pages are outside the reviewed 21-person list. The OLD admissions
page is superseded by the current Applications & Admissions page. Their original text is
saved in `reference/leftover-pages/`; the complete XML is also retained.

## Content to review tomorrow

- Why Study PSY now combines the existing undergraduate and graduate introductions;
  check the resulting copy and the concise Overview pages.
- Existing copy was migrated, not fact-checked: Home still mentions approaching a
  centennial, and CCBT's legacy emergency/contact numbers need verification before launch.
- Hero selection is intentionally deferred. No new photography or social preview image
  has been chosen for PSY.
- No browser visual review was available; the build and local-link/content checks passed.

## Validation

The normal local build and GitHub Pages `/psy/` build both passed. Checked all 58 pages
for local links/assets, a single H1, placeholder hero coverage, and absence of sidebars.
All 21 biographies retain the complete Background-and-beyond source text, without
faculty contact/photo blocks. Shared repository checks passed.
