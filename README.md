# Department of Psychology (PSY)

First content migration for the University of Hawaiʻi at Mānoa Department of Psychology.
The site uses the shared College of Social Sciences layouts, styles, branding, navigation,
contact data, icons, and assets in the sibling `css-shared` repository.

## Local development

```sh
npm ci
npm run dev
```

Preview: http://localhost:8085/

```sh
npm run build
npm run verify
```

## Source and review

- `src/`: 57 content pages; the shared build adds `/privacy.html`.
- `reference/migration-report.md`: short migration summary and leftovers.
- `reference/migration-report.json`: full source-to-destination map.
- `reference/psychologypsy.WordPress.2026-11-10.xml`: original export, never published.
- `reference/media-downloads.json`: local inline image download results.
- `scripts/migrate-wordpress.py`: reproducible migration (overwrites generated content).
- `scripts/verify-site.py`: checks built links/assets, hero coverage, and faculty bios.

The reviewed PSY worksheet and conversation determine the structure. Original WordPress
sidebar links are ordinary links below content. No sidebar layouts or faculty contact/photo
blocks were migrated. Faculty biographies start at Background. Undergraduate/Graduate
introductions moved to Why Study PSY; Overview pages remain concise program/resource guides.

## Shared configuration

Edit `../css-shared/src/data/units/psy/` for navigation, identity, hero settings,
hero assignments, analytics, search, and catalog links. All 58 page URLs currently use
`/media/heroes/saunders-mural/01.webp` as their temporary hero. `site-settings.json`
controls height, overlay, visibility, and layout guides.

## GitHub Pages

The included workflow builds with `/psy/` as the path prefix and deploys to GitHub Pages.
It checks out `cssweb-stack/css-shared` at `main`; commit the PSY shared-data changes there
before deploying this repository. Enable Pages with **GitHub Actions** as the source.
The workflow contains no repository secrets. No remote or publication has been configured
locally.

For a production-domain build, omit `SITE_PATH_PREFIX` and `SITE_ORIGIN`; production
identity is in the shared site settings. The Pages preview is deliberately noindex.
