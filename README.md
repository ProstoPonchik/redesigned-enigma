# Moodle Login Script

This Python script automates the login process for the Johannes Kepler University (JKU) Moodle platform using Shibboleth authentication. It simulates the login flow, handling various HTTP requests and managing cookies to achieve a successful login.

## Features

- Automates Shibboleth authentication for JKU Moodle
- Handles complex login flow involving multiple redirects and token exchanges
- Provides timing information for login and course access

## Prerequisites

- Python 3.x
- Required Python packages:
  - requests
  - beautifulsoup4
  - urllib3
  - lxml

You can install the required packages using pip:

```
pip install requests beautifulsoup4 urllib3 lxml
```

## Usage

1. Clone the repository or download the script.
2. Open the script and replace the placeholders for `username` and `password` with your JKU credentials.
3. Run the script:

```
python moodle_login_script.py
```

The script will output:
- The user's name (extracted from the Moodle profile page)
- The time taken for the login process
- The title of a specific course (hardcoded in the script)
- The time taken to access the course page

## How it works

1. Initiates a session with Moodle to obtain necessary cookies
2. Performs Shibboleth authentication
3. Exchanges tokens and manages cookies for successful login
4. Accesses the user's profile page and a specific course page

## Security Note

This script contains sensitive operations involving login credentials. Never share your credentials or the modified script containing your credentials. Use this script responsibly and in accordance with JKU's terms of service.

## Disclaimer

This script is for educational purposes only. The authors are not responsible for any misuse or any violations of JKU's terms of service.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](link-to-your-issues-page) if you want to contribute.

## License

[MIT](https://choosealicense.com/licenses/mit/)
