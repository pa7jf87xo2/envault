# envault

> A CLI tool for securely encrypting and syncing `.env` files across machines using age encryption.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envault
```

---

## Usage

**Encrypt a `.env` file:**

```bash
envault encrypt .env --output .env.age
```

**Decrypt on another machine:**

```bash
envault decrypt .env.age --output .env
```

**Sync with a remote (e.g., S3 or a shared path):**

```bash
envault push .env --remote s3://my-bucket/project/.env.age
envault pull --remote s3://my-bucket/project/.env.age --output .env
```

Keys are managed via [age](https://github.com/FiloSottile/age) and stored locally at `~/.config/envault/keys`.

---

## Requirements

- Python 3.8+
- [`age`](https://github.com/FiloSottile/age) installed and available on your `PATH`

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)