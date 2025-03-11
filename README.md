# telegram-calendar-bot

## Features

- generate calendar event from natural language descritions
- supporting relative time expressions

## example:

- "tomorrow 10am meeting with John for 40 minutes"
- "next friday go shopping at 18pm"
- "I have been worked on project X for 2 hours til now"

## TODO

## Deployment

- First you need to create a telegram bot and get the token. You can follow the instructions [here](https://core.telegram.org/bots)
- You need access to an openai style API. You will need an API key and an API endpoint.
- Prepare the credentials and the telegram ID you want to allow to use the bot and write them in a `.env` file. You can use the `.env.example` file as a template.
  - `OPENAI_API_URL` and `ADMIN_USER_IDS` is optional
  - `ALLOWED_TELEGRAM_USER_IDS` are comma separated list of telegram user ids that are allowed to use the bot
  - `MAX_INPUT_LENGTH` is the maximum number of characters that will be sent as content to the LLM API. Note that this does not include the template.
- Modify `prompt_template.txt` to your liking. This is a template to generate the prompt. It should contain the string `{content}` and `{disscussion}` which will be replaced by the content and the discussion of the message respectively.

### With Docker

- With docker-compose:

  Modify the `.env` file and `prompt_template.txt` as described above and specify their paths in the `docker-compose.yml` file.

  ```bash
  docker-compose up -d
  ```

- Without docker-compose:

  Modify the `.env` file and `prompt_template.txt` as described above and specify their paths in the following command.

  ```bash
  docker build -t telegram-calendar-bot https://github.com/simonmysun/telegram-calendar-bot.git
  docker run -d -v /path/to/.env:/app/.env:r -v /path/to/prompt_template.txt:/app/prompt_template.txt:r --name telegram-calendar-bot --init telegram-calendar-bot
  ```

### Without Docker

#### Clone the Repository

```bash
git clone https://github.com/simonmysun/telegram-calendar-bot.git
cd telegram-calendar-bot
```

### Create a Virtual Environment (Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate # On Windows use `venv\Scripts\activate`
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory of the project and add your credentials. You can use the `.env.example` file as a template.

## Running the Bot

```bash
python bot.py
```

## Usage


## License

This project is licensed under the BSD-3 License. See the [LICENSE](LICENSE) file for details.

