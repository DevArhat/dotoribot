import os

ENGRAVINGS_ABBR = {
    "원한": "원한",
    "돌격대장": "돌대",
    "마나효율증가": "마효증",
    "마나의흐름": "마흐",
    "예리한둔기": "예둔",
    "아드레날린": "아드",
    "기습의대가": "기습",
    "중갑착용": "중착",
    "슈퍼차지": "슈차",
    "타격의대가": "타대",
    "안정된상태": "안상",
    "바리케이드": "바리",
    "정밀단도": "정단",
    "속전속결": "속속",
    "각성": "각성",
    "결투의대가": "결대",
    "급소타격": "급타",
    "저주받은인형": "저받",
    "정기흡수": "정흡",
    "질량증가": "질증",
    "구슬동자": "구동",
    "최대마나증가": "최마증",
    "선수필승": "선필",
}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, 'bot.log')
KOSPI_TICKER_PATH = os.path.join(BASE_DIR, 'kospi_ticker.json')
TEST_LOG_PATH = os.path.join(BASE_DIR, 'test.log')
TIME_TABLE_PATH = os.path.join(BASE_DIR, 'time_table.json')