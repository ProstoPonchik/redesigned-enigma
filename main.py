import requests
from bs4 import BeautifulSoup
import urllib3
import time
import argparse

urllib3.disable_warnings()

SHIB_LOGIN_URL = 'https://shibboleth.im.jku.at'
MOODLE_HOME_URL = 'https://moodle.jku.at/jku/my/'
MOODLE_LOGIN_URL = 'https://moodle.jku.at/jku/login/index.php'
MOODLE_LOGIN_BY_SHIB_URL = "https://moodle.jku.at/jku/auth/shibboleth/index.php"
MOODLE_PROFILE_URL = 'https://moodle.jku.at/jku/user/profile.php'

headers_for_auth = {
    'accept': 'text/html,application/xhtml+xml,application/xml',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}

headers_for_moodle = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
}


def request_get(url, headers=None, cookies=None, allow_redirects=False):
    if headers is None:
        headers = headers_for_auth
    if cookies is None:
        cookies = cookies
    return session.get(url, headers=headers, cookies=cookies, verify=False, allow_redirects=allow_redirects)


def request_post(url, data, headers=None, cookies=None, allow_redirects=False):
    if headers is None:
        headers = headers_for_auth
    if cookies is None:
        cookies = cookies
    return session.post(url, data=data, headers=headers, cookies=cookies, verify=False, allow_redirects=allow_redirects)


def create_payload(csrf_token, username, password):
    return {
        'csrf_token': csrf_token,
        'j_username': username,
        'j_password': password,
        "_eventId_proceed": "Login",
    }


def get_jsessionid_for_login():
    """START SESSION and GET MoodleSessionjkuSessionCookie"""
    moodle_session_cookie = {
        'MoodleSessionjkuSessionCookie': request_get(MOODLE_HOME_URL, headers=headers_for_moodle, allow_redirects=True).cookies['MoodleSessionjkuSessionCookie']}

    """SET MoodleSessionjkuSessionCookie COOKIE"""
    request_get(MOODLE_LOGIN_URL, cookies=moodle_session_cookie)

    """GET URL FOR SHIB REDIRECTION"""
    shib_page = request_get(MOODLE_LOGIN_BY_SHIB_URL, cookies=moodle_session_cookie)
    soup = BeautifulSoup(shib_page.text, 'lxml')
    TOKEN_URL_SHIB = soup.find('a').attrs['href']

    """GET JSESSIONID COOKIE"""
    shib_token_page = request_get(TOKEN_URL_SHIB)
    URL_SHIB_AUTH = shib_token_page.headers['Location']
    print(shib_token_page.cookies)

    jsessionid_cookie = {'JSESSIONID': shib_token_page.cookies['JSESSIONID']}
    """GET csrf_token FOR LOGIN"""
    shib_login = request_get(URL_SHIB_AUTH, cookies=jsessionid_cookie)
    soup = BeautifulSoup(shib_login.text, 'lxml')
    redirect_url = soup.find('form', attrs={'name': 'form1'}).attrs['action']
    csrf_token = soup.find('input', attrs={'name': 'csrf_token'}).attrs['value']

    return create_payload(csrf_token, username, password), redirect_url, jsessionid_cookie, moodle_session_cookie


def get_tokens_for_sso(payload, redirect_url, jsessionid_cookie):
    """POST LOGIN INTO SHIBBOLETH"""
    response = request_post(f'{SHIB_LOGIN_URL}{redirect_url}', data=payload, cookies=jsessionid_cookie,
                            allow_redirects=True)

    soup = BeautifulSoup(response.text, 'lxml')
    login_url_params = soup.find('form', attrs={'id': 'loginform'}).attrs['action']
    csrf_token = soup.find('input', attrs={'name': 'csrf_token'}).attrs['value']

    payload = create_payload(csrf_token, username, password)
    """GET RelayState and SAMLResponse FOR MOODLE_LOGIN_BY_SHIB_URL"""
    response = request_post(f'{SHIB_LOGIN_URL}{login_url_params}', data=payload, cookies=jsessionid_cookie)

    soup = BeautifulSoup(response.text, 'lxml')
    RelayState = soup.find('input', attrs={'name': 'RelayState'}).attrs['value']
    SAMLResponse = soup.find('input', attrs={'name': 'SAMLResponse'}).attrs['value']
    return RelayState, SAMLResponse


def set_shibsession_for_moodle(relay_state, saml_response, moodle_session_cookie):
    """GET _shibsession_ COOKIE"""
    response = request_post('https://moodle.jku.at/Shibboleth.sso/SAML2/POST',
                            data={"RelayState": relay_state, "SAMLResponse": saml_response})
    headers = response.headers
    shibsession_key, shibsession_value = "", ""
    shibsession_header = headers.get('Set-Cookie', '')
    if '_shibsession_' in shibsession_header:
        shibsession_value = shibsession_header.split('_shibsession_')[1].split('=')[1].split(';')[0]
        shibsession_key = shibsession_header.split('_shibsession_')[1].split('=')[0]
        shibsession_key = f'_shibsession_{shibsession_key}'

    # Set cookie for path "/"
    session.cookies.set(shibsession_key, shibsession_value, domain='moodle.jku.at', path='/')

    # Set cookie for path "/jku/"
    session.cookies.set('MoodleSessionjkuSessionCookie', moodle_session_cookie["MoodleSessionjkuSessionCookie"],
                        domain='moodle.jku.at', path='/jku/')
    print()
    response = request_get(MOODLE_LOGIN_BY_SHIB_URL, headers=headers_for_moodle)

    new_moodle_ses_cookie = response.headers["Set-Cookie"].split('=')[1].split(';')[0]

    session.cookies.set('MoodleSessionjkuSessionCookie', new_moodle_ses_cookie, domain='moodle.jku.at', path='/jku/')


if __name__ == '__main__':
    # start session
    start_time = time.time()
    session = requests.Session()
    # get all credentials and set them in cookies
    payload, redirect_url, jsessionid_cookie, moodle_session_cookie = get_jsessionid_for_login()
    RelayState, SAMLResponse = get_tokens_for_sso(payload, redirect_url, jsessionid_cookie)
    set_shibsession_for_moodle(RelayState, SAMLResponse, moodle_session_cookie)
    # get profile page in moodle
    response = request_get(MOODLE_PROFILE_URL, headers=headers_for_moodle)
    soup = BeautifulSoup(response.text, 'lxml')
    # check user name
    print(soup.find("title").text.split(":")[0])
    print(f"--- {time.time() - start_time} seconds ---")
    start_time = time.time()
    # check time go get course
    response = request_get("https://moodle.jku.at/jku/course/view.php?id=23653", headers=headers_for_moodle)
    soup = BeautifulSoup(response.text, 'lxml')
    print(soup.find("h1", attrs={'class': 'h2'}).text)
    print(f"--- {time.time() - start_time} seconds ---")
