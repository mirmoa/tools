import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 로그 디렉토리 생성
os.makedirs('log', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'log/{datetime.now().strftime("%y%m%d")}test_log.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """웹드라이버 설정"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        
        # 봇 감지 우회를 위한 추가 설정
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # JavaScript 코드 실행으로 웹드라이버 감지 우회
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        logger.info("웹드라이버 설정 완료")
        return driver
    except Exception as e:
        logger.error(f"웹드라이버 설정 실패: {str(e)}")
        raise

def test_login_page():
    """로그인 페이지 테스트"""
    driver = None
    try:
        driver = setup_driver()
        
        # 쿠키 설정을 위해 일단 도메인에 접속
        driver.get("https://wing.coupang.com")
        
        # 쿠키 설정
        cookies = [
            {"name": "locale", "value": "ko"},
            {"name": "wing-locale", "value": "ko"},
            {"name": "x-coupang-accept-language", "value": "ko-KR"},
            {"name": "x-coupang-target-market", "value": "KR"}
        ]
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                logger.info(f"쿠키 설정: {cookie['name']}={cookie['value']}")
            except Exception as e:
                logger.warning(f"쿠키 설정 실패 ({cookie['name']}): {str(e)}")
        
        # 로그인 페이지 접속 - 명시적으로 한국어 설정 추가
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB&kc_locale=ko-KR")
        wait = WebDriverWait(driver, 15)
        
        # 언어 확인 및 설정
        try:
            # 언어 선택기가 로드될 때까지 대기
            select_element = wait.until(
                EC.presence_of_element_located((By.ID, "changeLocale"))
            )
            
            # 한국어 옵션 선택
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            select.select_by_visible_text("한국어")
            logger.info("언어를 한국어로 설정함")
            time.sleep(2)  # 언어 변경 적용 기다림
        except Exception as e:
            logger.warning(f"언어 설정 변경 시도 실패: {str(e)}")
        
        # 페이지 HTML 저장
        html_content = driver.page_source
        timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
        html_file = f'log/login_page_{timestamp}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"로그인 페이지 HTML 저장됨: {html_file}")
        
        # 스크린샷 저장
        screenshot_file = f'log/login_page_{timestamp}.png'
        driver.save_screenshot(screenshot_file)
        logger.info(f"로그인 페이지 스크린샷 저장됨: {screenshot_file}")
        
        # 페이지 타이틀 로깅
        logger.info(f"페이지 타이틀: {driver.title}")
        
        # 로그인 폼 요소들 확인
        login_form_elements = {
            'username': driver.find_elements(By.ID, "username"),
            'password': driver.find_elements(By.ID, "password"),
            'login_button': driver.find_elements(By.ID, "kc-login")
        }
        
        for element_name, elements in login_form_elements.items():
            if elements:
                logger.info(f"{element_name} 요소 발견됨")
            else:
                logger.warning(f"{element_name} 요소를 찾을 수 없음")
        
        logger.info("테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.info("웹드라이버 종료")

if __name__ == "__main__":
    test_login_page() 