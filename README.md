This project demonstrates several code examples using the [Bridgic](https://github.com/bitsky-tech/bridgic) framework. You can use `uv` or `pip` to set up the runtime environment.

## Using `uv` (Recommended)

### Install `uv`

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Refer to [Installing uv](https://docs.astral.sh/uv/getting-started/installation/) for details.

### Run Examples

```shell
uv run human_in_the_loop/code_assistant.py
uv run human_in_the_loop/reimbursement_automation.py
```

### Set up venv (Optional)

If you want to open and edit these example codes in an IDE, you’ll need to use the `uv` command to set up the venv.

```shell
uv venv
uv sync
```

## Using `pip`

### Install Dependencies

```shell
pip install -U bridgic
pip install -U bridgic-llms-openai
```

### Run Examples

```shell
python human_in_the_loop/code_assistant.py
python human_in_the_loop/reimbursement_automation.py
```


