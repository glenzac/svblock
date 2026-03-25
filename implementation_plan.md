# svblock — Phase-wise Implementation Plan

> A detailed, phase-ordered plan for building svblock from scratch.
> Each phase produces a testable, working increment.

---

## Dependency Graph & Parallelism

```
Phase 0  (Scaffolding)
  ├──→ Phase 1  (Data Model) ──→ Phase 2  (pyslang Parser) ──→ Phase 3  (Annotations)
  │                                                                │
  │                                  Phase 4  (Grouping) ←────────┘
  │                                      │
  └──→ Phase 5  (Text Metrics) ─────────┤
                                         ▼
                                  Phase 6  (Layout Engine)
                                         │
                                  Phase 7  (SVG Renderer)
                                         │
                                  Phase 8  (Theming)
                                         │
                                  Phase 9  (CLI — full integration)
                                         │
                          ┌──────┬───────┼───────┐
                          ▼      ▼       ▼       ▼
                     Phase 10  Phase 11  Phase 12  Phase 13
                     (E2E)     (Export)  (Sphinx)  (CI)
```

**Parallel opportunities:**
- Phases 1 and 5 can be built simultaneously
- Phases 10, 11, 12, 13 are all independent of each other

---

## Phase 0 — Project Scaffolding & Packaging

### What gets built
- `pyproject.toml` — metadata, dependencies, optional groups (`[png]`, `[pdf]`, `[sphinx]`, `[dev]`), `svblock` console entry point
- `src/svblock/__init__.py` with `__version__`
- Empty `__init__.py` for every subpackage: `parser/`, `model/`, `layout/`, `renderer/`, `exporters/`, `sphinx_ext/`
- `tests/` structure with `conftest.py` and `fixtures/` directory
- `ruff.toml` for linting config
- Minimal `cli.py` stub (only `--version`)

### Files
```
pyproject.toml
src/svblock/__init__.py
src/svblock/cli.py                 (stub: --version only)
src/svblock/config.py              (placeholder)
src/svblock/parser/__init__.py
src/svblock/model/__init__.py
src/svblock/layout/__init__.py
src/svblock/renderer/__init__.py
src/svblock/exporters/__init__.py
src/svblock/sphinx_ext/__init__.py
tests/__init__.py
tests/conftest.py
ruff.toml
```

### Acceptance criteria
- `pip install -e .` succeeds on Python 3.10+
- `python -c "import svblock; print(svblock.__version__)"` works
- `svblock --version` prints version and exits
- `pytest` runs, collects zero tests, exits cleanly
- `ruff check src/` passes

### Design considerations
- Use `src/` layout to avoid import shadowing during development
- `pyproject.toml` only (no `setup.py`). Build backend: `hatchling` or `setuptools`
- Pin `pyslang >= 6.0` as mandatory. `python_requires = ">=3.10"`
- Optional groups: `png` = `cairosvg`, `pdf` = `cairosvg`, `sphinx` = `sphinx>=5`, `dev` = `pytest, pytest-snapshot, ruff, mypy`
- The `svblock` entry point maps to `svblock.cli:main`

### Dependencies
None (first phase).

---

## Phase 1 — Data Model (`model/`)

### What gets built
- `port_types.py` — `PortDirection` enum (`INPUT`, `OUTPUT`, `INOUT`, `INTERFACE`, `REF`)
- `module_ir.py` — `PortDef`, `ParamDef`, `GroupDef`, `ModuleIR` dataclasses per architecture section 5

### Files
```
src/svblock/model/port_types.py
src/svblock/model/module_ir.py
src/svblock/model/__init__.py      (re-exports)
tests/test_model.py
```

### Acceptance criteria
- All dataclasses instantiate, serialize to dict, compare for equality
- `PortDirection` has all five members
- `ModuleIR` holds mixed port types (bus, scalar, interface) and params
- `GroupDef` holds `name`, optional `label`, and ordered `port_names` list
- `ModuleIR.__post_init__` validates no duplicate port names
- `pytest tests/test_model.py` passes

### Design considerations
- `bus_range` is `tuple[str, str] | None` — strings, not ints (parametric ranges like `WIDTH-1`)
- All `PortDef` fields keyword-only with sensible defaults for ergonomic construction
- Group order in `ModuleIR.groups` determines rendering order

### Dependencies
Phase 0.

---

## Phase 2 — pyslang Parser Integration (`parser/sv_extractor.py`)

### What gets built
- `sv_extractor.py` — Core functions:
  - `extract_modules(file_path, include_paths=None) -> list[ModuleIR]`
  - `extract_module(file_path, module_name) -> ModuleIR`
- Handles: ANSI/non-ANSI headers, `logic`/`wire`/`reg`, packed arrays (single & multi-dim), parameters (int/type/string/localparam), interface/modport ports
- Populates `is_bus`, `bus_range`, `is_interface`, `modport`, `has_clock_marker`, `has_active_low_marker`
- Custom `ParseError` exception for graceful error handling
- Test fixture `.sv` files covering each variant

### Files
```
src/svblock/parser/sv_extractor.py
src/svblock/parser/__init__.py     (re-exports)
tests/test_parser.py
tests/fixtures/simple_module.sv
tests/fixtures/bus_ports.sv
tests/fixtures/params.sv
tests/fixtures/interface_ports.sv
tests/fixtures/multi_module.sv
tests/fixtures/non_ansi.sv
```

### Acceptance criteria
- `extract_modules("simple_module.sv")` returns correct `ModuleIR`
- Bus ports: `is_bus=True`, correct `bus_range` as string tuple
- Interface ports: `is_interface=True`, `modport` set
- Multi-dim arrays: compact representation (e.g., `"[3:0][7:0]"`)
- Parametric ranges preserved as-is: `("WIDTH-1", "0")`
- Clock/active-low heuristics fire correctly on port names
- Multi-module files return multiple `ModuleIR` objects
- Unparseable files raise `ParseError` with user-friendly message

### Design considerations
- **This is the highest-risk phase.** The pyslang API must be explored carefully. Key classes: `pyslang.SyntaxTree`, `pyslang.Compilation`, `InstanceSymbol`, `PortSymbol`, `ParameterSymbol`
- Use `slang.Compilation` with `add_syntax_tree` for fully elaborated symbols
- Pass `include_paths` to slang's compilation options for `include` resolution
- Wrap all pyslang calls in try/except for friendly errors

### Dependencies
Phase 0, Phase 1.

---

## Phase 3 — Comment Annotation Parser (`parser/annotation.py`)

### What gets built
- `annotation.py` — Parses `// @sym key=value` from pyslang's CST trivia tokens
- `parse_annotations(syntax_tree, module_name) -> dict[str, dict[str, str]]` — maps port name to annotation key-value pairs
- Supported keys: `group`, `label`, `hide`, `bus`, `color`
- Integration into `sv_extractor.py`: annotations merged into `PortDef` fields

### Files
```
src/svblock/parser/annotation.py
tests/test_annotations.py
tests/fixtures/annotated_module.sv
tests/fixtures/partial_annotations.sv
```

### Acceptance criteria
- Annotations on the line above a port associate correctly
- Group annotations above consecutive ports apply to all until next annotation/blank line
- Quoted and unquoted values both work: `group="Clocks"` and `group=Clocks`
- `hide=true` marks port for exclusion
- `label="Custom Name"` overrides displayed name
- Malformed annotations produce a warning, not an error
- Unannotated ports get `group=None`

### Design considerations
- **Second highest risk.** pyslang's CST preserves trivia (comments) attached to tokens. Must walk CST, not elaborated AST
- Association logic: find `@sym` comment → find next port declaration token → associate
- Fallback if CST trivia API is insufficient: line-based scan of raw file text, correlating line numbers with port declarations from Phase 2
- Regex: `r'//\s*@sym\s+(.+)'` followed by key-value extraction

### Dependencies
Phase 2.

---

## Phase 4 — Heuristic Grouping (`layout/grouping.py`)

### What gets built
- `grouping.py` — `apply_grouping(module: ModuleIR) -> ModuleIR`
- When no `@sym` annotations: auto-groups by name patterns (clk→Clocks, rst→Resets, remaining inputs→Inputs, outputs→Outputs, interfaces→Interfaces)
- Explicit annotation groups take priority; heuristics fill gaps
- `--no-groups` mode: single default group

### Files
```
src/svblock/layout/grouping.py
tests/test_grouping.py
```

### Acceptance criteria
- Fully unannotated module gets complete heuristic grouping
- Partially annotated module: annotations respected, rest filled by heuristics
- Deterministic group order: explicit groups first (declaration order), then heuristic groups (Clocks, Resets, Inputs, Outputs, Interfaces)
- Pure function: returns new `ModuleIR`, no mutation of input

### Design considerations
- Clock/reset detection should be case-insensitive
- Patterns are hardcoded for v1, configurable in future versions

### Dependencies
Phase 1, Phase 3.

---

## Phase 5 — Text Metrics (`layout/text_metrics.py`)

### What gets built
- `text_metrics.py` — `measure_text(text: str, font_size: float, font_family: str = "monospace") -> float`
- Built-in character-width lookup table for monospace (port labels) and proportional (module name/group headers) fonts
- Optional `fonttools` integration for precise metrics when available

### Files
```
src/svblock/layout/text_metrics.py
tests/test_text_metrics.py
```

### Acceptance criteria
- `measure_text("clk", 14)` returns a positive float
- Monospace: all chars equal width; proportional: "W" wider than "i"
- Deterministic (same input → same output)
- Transparent fallback when `fonttools` not installed

### Design considerations
- Pre-measure ASCII 32-126 at reference size, store as dict, scale linearly
- This is the foundation for correct box sizing — inaccurate metrics cause clipped labels or oversized boxes

### Dependencies
Phase 0 only (standalone utility). **Can be built in parallel with Phases 1-4.**

---

## Phase 6 — Layout Engine (`layout/engine.py`)

### What gets built
- `engine.py` — Takes `ModuleIR` (with groups) + `LayoutConfig` → produces `LayoutSpec`
- `LayoutSpec` dataclass:
  - `box_x, box_y, box_width, box_height`
  - `header_rect` (for module name + params)
  - `pin_rows: list[PinRow]` — each with: port_name, side (LEFT/RIGHT), y_coordinate, label_text, decorator_type, bus_label, group membership
  - `group_separators: list[GroupSeparator]` — each with: y_coordinate, label
  - `total_width, total_height` (SVG canvas size, includes pin stubs)
- Implements all geometry rules from architecture section 7:
  - 20px/row (28px for interfaces), 18px group headers, min 240px width
  - Inputs left, outputs right, inout/interface right
  - 36px header + 16px per param line

### Files
```
src/svblock/layout/engine.py
tests/test_layout.py
```

### Acceptance criteria
- 4 inputs + 4 outputs → correct pin coordinates and sufficient box height
- Box width adjusts dynamically to longest label (via text_metrics)
- Minimum width enforced (240px)
- Group separators at correct y positions between groups
- Interface pins get 28px height
- Parameter section scales with param count
- Empty module produces minimal valid layout

### Design considerations
- **Completely decoupled from SVG.** Outputs pure geometry — enables future renderers without touching layout
- Pin placement: iterate groups, place inputs left/outputs right, track max y on each side, next group starts at `max(left_y, right_y) + group_header_height`
- Decorators always reserve 12px regardless of `--no-decorators` to keep layout stable
- `--width` maps to `LayoutConfig.min_width`, `--no-params`/`--no-groups` to booleans

### Dependencies
Phase 1, Phase 4, Phase 5.

---

## Phase 7 — SVG Renderer (`renderer/svg_renderer.py`)

### What gets built
- `svg_renderer.py` — `render_svg(layout: LayoutSpec, theme: dict, options: RenderOptions) -> str`
- Renders: SVG envelope + `<style>`, module box, header text, pin rows (lines + labels), pin decorators, group separators, `<title>` hover elements
- `RenderOptions`: `no_decorators`, `no_params`, `standalone` (for Sphinx)
- Stability: deterministic IDs (`port-{name}`, `group-{name}`, `param-{name}`), no timestamps, floats rounded to 2dp

### Files
```
src/svblock/renderer/svg_renderer.py
src/svblock/renderer/__init__.py
tests/test_renderer.py
tests/snapshots/                    (golden SVG directory)
```

### Acceptance criteria
- Output is valid SVG (parseable by `xml.etree.ElementTree`)
- Deterministic IDs and no non-deterministic content
- All five pin decorators render correctly:
  - Clock triangle (▷)
  - Active-low bubble (○)
  - Bus thick stroke
  - Interface diamond (◆)
  - Inout double-arrow (↔)
- CSS variables from theme injected into `<style>`
- `standalone=False` omits XML declaration and `xmlns`
- Snapshot tests pass against golden SVGs

### Design considerations
- Build SVG as string fragments joined at end (simpler than ElementTree construction; Jinja2 as future enhancement)
- Decorator helpers: `_clock_triangle(x, y) -> str`, `_inversion_bubble(x, y) -> str`, etc.
- Text anchoring: left-side labels `text-anchor="end"`, right-side labels `text-anchor="start"`
- `<title>` on each port contains full SV type string for hover tooltip

### Dependencies
Phase 6.

---

## Phase 8 — Theming (`renderer/themes.py`, `config.py`)

### What gets built
- `themes.py` — Four built-in themes as Python dicts: `default` (light), `dark`, `minimal` (monochrome), `print` (high-contrast B&W)
- `config.py` — `load_theme(theme_name_or_path: str) -> dict[str, str]` loads YAML/TOML and merges with base theme

### Files
```
src/svblock/renderer/themes.py
src/svblock/config.py
tests/test_themes.py
```

### Acceptance criteria
- `load_theme("default")` / `load_theme("dark")` return complete theme dicts
- `load_theme("path/to/custom.yaml")` loads and merges (custom overrides, missing keys fall back to default)
- All built-in themes have valid CSS variable values (no None, no missing keys)
- Partial custom themes get complete variable sets via merge

### Design considerations
- TOML primary (`tomllib` stdlib 3.11+ / `tomli` backport for 3.10), YAML optional via `pyyaml`
- Warn on unknown CSS variable names in custom themes

### Dependencies
Phase 7.

---

## Phase 9 — CLI (`cli.py`)

### What gets built
- Full CLI via `argparse` implementing all options from architecture section 9
- Orchestrates the complete pipeline: parse → annotate → group → layout → render → write
- `--list-modules` mode, `-v` diagnostics, error handling with exit codes

### Files
```
src/svblock/cli.py
tests/test_cli.py
```

### Acceptance criteria
- `svblock module.sv` produces SVG in current directory
- `svblock module.sv -o out.svg` writes to specified path
- `svblock multi.sv --list-modules` lists module names to stdout
- `svblock module.sv -m nonexistent` → error, exit code 1
- `svblock missing.sv` → "File not found", exit code 1
- Theme, format, and all flag combinations work together
- Exit codes: 0 = success, 1 = user error, 2 = parse error

### Design considerations
- Default output: `{module_name}.{format}` in CWD
- `-v` logs pyslang diagnostics to stderr

### Dependencies
Phases 1-8 (integration point).

---

## Phase 10 — End-to-End Tests & Snapshot Infrastructure

### What gets built
- Comprehensive `.sv` fixture library covering all documented scenarios
- Snapshot comparison infrastructure (render → compare against committed golden SVGs)
- `tests/update_snapshots.py` to regenerate golden files
- Real-world SV test files (OpenTitan/CVA6 snippets if license permits)

### Files
```
tests/test_e2e.py
tests/update_snapshots.py
tests/fixtures/clock_reset.sv
tests/fixtures/active_low.sv
tests/fixtures/interface_modport.sv
tests/fixtures/multidim_array.sv
tests/fixtures/type_params.sv
tests/fixtures/no_ports.sv
tests/fixtures/large_module.sv         (30+ ports)
tests/fixtures/heuristic_groups.sv     (no annotations)
tests/snapshots/*.svg                  (golden files)
```

### Acceptance criteria
- `pytest tests/test_e2e.py` passes on clean checkout
- Every fixture has a corresponding golden SVG
- Rendering changes cause snapshot failures with clear diffs
- At least one 15+ port mixed-type real-world test
- Malformed SV produces clear error, not crash

### Dependencies
Phases 0-9. **Can be built in parallel with Phases 11, 12, 13.**

---

## Phase 11 — PNG/PDF Exporters (`exporters/`)

### What gets built
- `png.py` — `svg_to_png(svg_string, output_path, scale=2.0)` via `cairosvg`, fallback to `rsvg-convert`/`inkscape`/`imagemagick` subprocess
- `pdf.py` — `svg_to_pdf(svg_string, output_path)` via `cairosvg` or `svglib+reportlab`
- `ExportError` with helpful install instructions
- CLI integration: `-f png` / `-f pdf`

### Files
```
src/svblock/exporters/png.py
src/svblock/exporters/pdf.py
src/svblock/exporters/__init__.py
tests/test_exporters.py
```

### Acceptance criteria
- `svblock fixture.sv -f png` → valid PNG (verify magic bytes)
- `svblock fixture.sv -f pdf` → valid PDF
- Missing deps → clear message: "Install with: `pip install svblock[png]`"
- Scale factor works correctly
- Tests skip gracefully when optional deps missing

### Dependencies
Phase 7, Phase 9. **Can be built in parallel with Phases 10, 12, 13.**

---

## Phase 12 — Sphinx Extension (`sphinx_ext/`)

### What gets built
- `__init__.py` — Sphinx `setup()` registration
- `directive.py` — `.. svblock::` directive with options: `:module:`, `:theme:`, `:caption:`, `:align:`, `:no-params:`, `:no-groups:`, `:no-decorators:`, `:width:`
- HTML builder: inline SVG (`standalone=False`). LaTeX builder: temp PNG/PDF image
- Reads `conf.py`: `svblock_default_theme`, `svblock_include_paths`, `svblock_default_format`

### Files
```
src/svblock/sphinx_ext/__init__.py
src/svblock/sphinx_ext/directive.py
tests/test_sphinx_ext.py
```

### Acceptance criteria
- Minimal Sphinx project with `extensions = ['svblock.sphinx_ext']` + `.. svblock::` builds cleanly
- HTML output contains inline SVG
- `:module:`, `:theme:`, `:caption:` options work
- `conf.py` defaults respected

### Design considerations
- Follow Sphinx's built-in `graphviz` extension pattern
- Direct Python import (no subprocess) for performance
- `svblock_include_paths` critical for resolving `` `include `` in Sphinx builds

### Dependencies
Phases 0-9, Phase 11 (for LaTeX). **Can be built in parallel with Phases 10, 11, 13.**

---

## Phase 13 — CI, Linting & Release Packaging

### What gets built
- `.github/workflows/ci.yml` — matrix (Python 3.10-3.13, Ubuntu; optional Windows/macOS), lint, typecheck, test, build
- `.github/workflows/release.yml` — tag-triggered, builds sdist+wheel, publishes to PyPI via trusted publishing (OIDC)
- `mypy` config in `pyproject.toml`
- `src/svblock/py.typed` marker

### Files
```
.github/workflows/ci.yml
.github/workflows/release.yml
src/svblock/py.typed
```

### Acceptance criteria
- Push to `main` triggers CI; all steps pass
- `v*` tag triggers release workflow
- `mypy src/svblock/` passes
- `ruff check src/ tests/` passes
- `python -m build` produces valid wheel and sdist

### Design considerations
- `pyslang` has platform-specific wheels. CI must run on platforms where pyslang wheels are available (Linux x86_64 guaranteed; Windows/macOS need verification)
- Snapshot tests in CI: golden files are committed, so CI just runs comparison. No environment differences since SVG is pure string output
- Use trusted publishing (OIDC) with PyPI rather than API tokens
- Add `CHANGELOG.md` at this point

### Dependencies
All prior phases. **Can be built in parallel with Phases 10, 11, 12.**

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| pyslang API underdocumented or changes between versions | Blocks Phases 2-3 | Pin version. Write thin adapter layer. Explore API with throwaway script before committing to design. |
| pyslang CST doesn't expose comments usably | Blocks Phase 3 | Fallback: line-based raw file scan, correlate line numbers with AST port declarations. |
| Text metrics inaccuracy → bad layouts | Visual quality | Ship conservative width estimates. `--width` override. `fonttools` optional precision backend. |
| cairosvg wheels unavailable on some platforms | PNG/PDF broken on those platforms | Document as optional. Subprocess fallback to Inkscape/rsvg-convert/ImageMagick. |
| pyslang missing wheels for niche platforms (e.g., Windows ARM) | Install failure | Document supported platforms. Post-v1: degraded mode with `pysvinst` fallback. |
| Large modules (100+ ports) → unwieldy diagrams | Usability | `--max-ports` option or auto-pagination in future version. V1 renders everything. |
