# Developer Setup

Quick start guide for contributing to erebos.

## Prerequisites

- **Python 3.11+** (check: `python --version`)
- **Ollama** for local LLM testing (install: https://ollama.ai)
- **Git** for version control

## Initial Setup

1. **Clone the repository:**

   ```bash
   cd ~/Scriptorium/Devel/UncleTallest/organizations/continuity-bridge
   git clone https://github.com/continuity-bridge/Erebos.git
   cd Erebos
   ```

2. **Install development dependencies:**

   ```bash
   make install-dev
   # Or manually:
   pip install -e ".[dev]"
   ```

3. **Verify installation:**
   ```bash
   make test
   ```

## Development Workflow

### Running the Prototype

```bash
make run
# Or: python prototype_cli.py
```

### Testing

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/events/test_bus.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code automatically
make format

# Check code style (doesn't modify files)
make lint

# Individual tools:
black --check erebos  # Style check
pylint erebos         # Linter
mypy erebos           # Type checker
```

### Common Tasks

```bash
make help          # Show all available commands
make clean         # Remove build artifacts
make install       # Install without dev dependencies
```

## Project Structure

```
Erebos/
├── erebos/     # Main package
│   ├── events/              # Event system (EventBus, EventEmitter)
│   └── llm/                 # LLM clients (Ollama, Claude)
├── tests/                   # Test suite
│   └── events/             # Event system tests
├── docs/                    # Documentation
├── prototype_cli.py         # CLI demo
├── pyproject.toml          # Project metadata & config
└── Makefile                # Development tasks
```

## Git Workflow

1. **Create feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test:**

   ```bash
   make format    # Auto-format
   make lint      # Check style
   make test      # Run tests
   ```

3. **Commit and push:**

   ```bash
   git add .
   git commit -m "Brief description of changes"
   git push origin feature/your-feature-name
   ```

4. **Create pull request** on GitHub

## Code Style

- **Line length:** 100 characters max
- **Formatter:** Black (automatic via `make format`)
- **Docstrings:** Google style preferred
- **Type hints:** Encouraged but not required yet

## Testing Guidelines

- Write tests for new features
- Aim for >80% coverage
- Use descriptive test names: `test_<function>_<scenario>`
- Place tests in `tests/` mirroring package structure

## Troubleshooting

**Ollama not found:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**Import errors:**

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**Test failures:**

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/events/test_bus.py::test_subscribe_and_emit
```

## Next Steps

- See [PROTOTYPE.md](PROTOTYPE.md) for event system overview
- Check [docs/phase-2-implementation.md](docs/phase-2-implementation.md) for roadmap
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

---

**Questions?** Open an issue on GitHub or check the wiki.
