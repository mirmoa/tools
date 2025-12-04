import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 계정 정보
COUPANG_ID = "alfm1991"
COUPANG_PW = "$als$Ehdvkf29!"

# 로그 디렉토리 생성
os.makedirs('log', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'log/test_{datetime.now().strftime("%y%m%d_%H%M%S")}.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

step = 0

def save_screenshot(driver, name):
    """스크린샷 저장"""
    global step
    step += 1
    filename = f'log/{step:02d}_{name}.png'
    driver.save_screenshot(filename)
    logger.info(f"스크린샷 저장: {filename}")
    logger.info(f"현재 URL: {driver.current_url}")

def setup_driver():
    """웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    
    # 쿠키 관련 설정
    chrome_options.add_argument('--enable-cookies')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome-profile')
    
    # 봇 감지 우회
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def test_full_flow():
    driver = None
    try:
        logger.info("========== 전체 플로우 테스트 시작 ==========")
        
        driver = setup_driver()
        logger.info("웹드라이버 설정 완료")
        wait = WebDriverWait(driver, 30)
        
        # 1. 기본 도메인 접속
        logger.info(">>> 기본 도메인 접속")
        driver.get("https://wing.coupang.com")
        time.sleep(3)
        save_screenshot(driver, "wing_main")
        
        # 2. 쿠키 설정
        logger.info(">>> 쿠키 설정")
        cookies = [
            {"name": "locale", "value": "ko", "domain": ".coupang.com"},
            {"name": "wing-locale", "value": "ko", "domain": ".coupang.com"},
            {"name": "x-coupang-accept-language", "value": "ko-KR", "domain": ".coupang.com"},
            {"name": "x-coupang-target-market", "value": "KR", "domain": ".coupang.com"}
        ]
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                logger.info(f"쿠키 설정: {cookie['name']}")
            except Exception as e:
                logger.warning(f"쿠키 실패: {cookie['name']} - {e}")
        
        driver.refresh()
        time.sleep(2)
        save_screenshot(driver, "after_cookie")
        
        # 3. 로그인 페이지 접속
        logger.info(">>> 로그인 페이지 접속")
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB")
        time.sleep(5)
        save_screenshot(driver, "login_page")
        
        # 4. 아이디 입력
        logger.info(">>> 아이디 입력")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.execute_script("arguments[0].value = arguments[1]", username_field, COUPANG_ID)
        time.sleep(1)
        save_screenshot(driver, "id_entered")
        
        # 5. 비밀번호 입력
        logger.info(">>> 비밀번호 입력")
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        driver.execute_script("arguments[0].value = arguments[1]", password_field, COUPANG_PW)
        time.sleep(1)
        save_screenshot(driver, "pw_entered")
        
        # 6. 로그인 버튼 클릭
        logger.info(">>> 로그인 버튼 클릭")
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "kc-login")))
        save_screenshot(driver, "before_login_click")
        driver.execute_script("arguments[0].click();", login_button)
        
        # 7. 로그인 후 대기
        logger.info(">>> 로그인 후 대기")
        time.sleep(3)
        save_screenshot(driver, "after_login_3sec")
        
        time.sleep(5)
        save_screenshot(driver, "after_login_8sec")
        
        # 8. 광고관리 메뉴 찾기
        logger.info(">>> 광고관리 메뉴 찾기")
        try:
            ad_menu = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-bigfoot-component='lnb-menu-ad-management']"))
            )
            logger.info("광고관리 메뉴 발견!")
            save_screenshot(driver, "menu_found")
            
            # 9. 메뉴 클릭
            logger.info(">>> 광고관리 메뉴 클릭")
            driver.execute_script("arguments[0].click();", ad_menu)
            time.sleep(3)
            save_screenshot(driver, "after_menu_click")
            
            # 10. 테이블 로드 대기
            logger.info(">>> 테이블 로드 대기")
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".rt-tbody")))
                logger.info("테이블 발견!")
                save_screenshot(driver, "table_loaded")
                logger.info("========== 테스트 성공! ==========")
            except:
                logger.error("테이블 로드 실패")
                save_screenshot(driver, "table_failed")
                
        except Exception as e:
            logger.error(f"광고관리 메뉴 찾기 실패: {e}")
            save_screenshot(driver, "menu_not_found")
            
            # 페이지 소스 일부 저장
            logger.info("페이지 소스 (앞 3000자):")
            logger.info(driver.page_source[:3000])
        
    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        if driver:
            save_screenshot(driver, "error")
    finally:
        if driver:
            driver.quit()
            logger.info("웹드라이버 종료")

if __name__ == "__main__":
    test_full_flow()
