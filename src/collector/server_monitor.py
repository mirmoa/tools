import os
import sys
import subprocess
import time
import logging
import threading
import traceback
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class CoupangAdServerMonitor:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.is_monitoring = False
        self.driver_path = None
        self.max_retries = 3
        self.retry_interval = 30
        
        # 로깅 설정
        self.setup_logging()
        
        # 캠페인 및 비용 열 설정
        self.campaign_column = 0  # 캠페인명 열 인덱스
        self.cost_column = 5      # 비용 열 인덱스

    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger("CoupangAdMonitor")
        self.logger.setLevel(logging.INFO)

        # 로그 디렉토리 생성
        log_directory = "log"
        os.makedirs(log_directory, exist_ok=True)

        # 현재 날짜로 로그 파일 생성
        current_date = datetime.now().strftime("%y%m%d")
        log_filename = f"{log_directory}/{current_date}log.txt"

        # 파일 핸들러
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )

        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def initialize_webdriver(self):
        """셀레니움 웹드라이버 초기화"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if self.driver_path is None:
            try:
                self.driver_path = ChromeDriverManager().install()
                self.logger.info(f"🛠 드라이버 설치 완료: {self.driver_path}")
            except Exception as e:
                self.logger.error(f"❌ 드라이버 설치 실패: {str(e)}")
                raise

        service = Service(self.driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)

    def login_to_coupang(self):
        """쿠팡 로그인"""
        try:
            self.driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB")

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button = self.driver.find_element(By.ID, "kc-login")
            login_button.click()

            WebDriverWait(self.driver, 15).until(
                EC.url_to_be("https://advertising.coupang.com/marketing/dashboard/sales")
            )
            self.logger.info("로그인 성공")
            return True
        except Exception as e:
            self.logger.error(f"로그인 중 오류 발생: {str(e)}")
            return False

    def select_rows_per_page(self, rows):
        """페이지당 표시할 행 수 선택"""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
            )

            select_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[aria-label='rows per page']"))
            )

            self.driver.execute_script("arguments[0].scrollIntoView();", select_element)
            select_element.click()

            option_selector = f"select[aria-label='rows per page'] option[value='{rows}']"
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, option_selector))
            )

            options = select_element.find_elements(By.TAG_NAME, "option")
            for option in options:
                if option.get_attribute("value") == str(rows):
                    option.click()
                    self.logger.info(f"{rows}개 보기로 설정했습니다.")
                    break

            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
            )
            return True
        except Exception as e:
            self.logger.error(f"행 수 선택 중 오류 발생: {str(e)}")
            return False

    def get_filename(self):
        """이 메서드는 더 이상 사용되지 않습니다"""
        pass

    def save_to_local(self, data, current_hour):
        """데이터를 로컬 JSON 파일로 저장"""
        try:
            if not data:
                self.logger.warning("저장할 데이터가 없습니다.")
                return False

            # daily 디렉토리 생성
            os.makedirs("daily", exist_ok=True)

            # 날짜별 파일명 생성
            current_date = datetime.now()
            filename = f"daily/{current_date.strftime('%Y-%m-%d')}.json"
            
            try:
                # 기존 데이터 확인
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                else:
                    daily_data = {
                        "date": current_date.strftime("%Y-%m-%d"),
                        "hours": {},
                        "total_cost": 0,
                        "campaign_summary": {},
                        "last_updated": None
                    }

                # 현재 시간 데이터 추가
                hour_str = str(current_hour)
                hour_total_cost = sum(camp["cost"] for camp in data.values())
                
                daily_data["hours"][hour_str] = {
                    "timestamp": current_date.isoformat(),
                    "total_cost": hour_total_cost,
                    "campaign_count": len(data),
                    "campaigns": data
                }

                # 캠페인별 총합 업데이트
                for campaign_name, camp_data in data.items():
                    if campaign_name not in daily_data["campaign_summary"]:
                        daily_data["campaign_summary"][campaign_name] = {
                            "total_cost": 0,
                            "hours_collected": []
                        }
                    
                    # 이전 시간 데이터가 있으면 제거
                    if hour_str in daily_data["campaign_summary"][campaign_name]["hours_collected"]:
                        daily_data["campaign_summary"][campaign_name]["total_cost"] -= \
                            daily_data["hours"][hour_str]["campaigns"][campaign_name]["cost"]
                    
                    daily_data["campaign_summary"][campaign_name]["total_cost"] += camp_data["cost"]
                    if hour_str not in daily_data["campaign_summary"][campaign_name]["hours_collected"]:
                        daily_data["campaign_summary"][campaign_name]["hours_collected"].append(hour_str)

                # 전체 비용 업데이트
                daily_data["total_cost"] = sum(
                    camp["total_cost"] 
                    for camp in daily_data["campaign_summary"].values()
                )
                
                # 마지막 업데이트 시간 기록
                daily_data["last_updated"] = current_date.isoformat()

                # 데이터 저장
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(daily_data, f, ensure_ascii=False, indent=2)

                self.logger.info(f"✅ 로컬에 데이터 저장 완료: {filename} ({hour_str}시 데이터 업데이트)")
                return True

            except Exception as e:
                self.logger.error(f"❌ 파일 저장 실패: {str(e)}")
                traceback.print_exc()
                return False

        except Exception as e:
            self.logger.error(f"❌ 데이터 저장 중 오류: {str(e)}")
            traceback.print_exc()
            return False

    def collect_data(self):
        """표 영역 데이터 수집"""
        try:
            # 로딩 대기
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.ReactTable.contents-body-table.dashboard-react-table-revamp")
                )
            )

            # 로딩 완료 대기
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
            )

            table = self.driver.find_element(By.CSS_SELECTOR,
                                           "div.ReactTable.contents-body-table.dashboard-react-table-revamp")
            rows = table.find_elements(By.CSS_SELECTOR, ".rt-tbody .rt-tr-group")

            if not rows:
                self.logger.warning("⚠️ 캠페인 행이 없습니다.")
                return {}

            campaign_data = {}
            current_hour = datetime.now().hour

            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
                if not cells or len(cells) <= max(self.campaign_column, self.cost_column):
                    self.logger.warning("올바르지 않은 테이블 구조입니다.")
                    continue

                try:
                    campaign_name = cells[self.campaign_column].text.strip()
                    cost_text = cells[self.cost_column].text.strip()

                    if not campaign_name:
                        continue

                    if cost_text and any(c.isdigit() for c in cost_text):
                        cost = float(cost_text.replace(',', '').replace(' 원', ''))
                    else:
                        cost = 0

                    campaign_data[campaign_name] = {
                        "cost": cost,
                        "hour": current_hour,
                        "collected_at": datetime.now().isoformat()
                    }

                except Exception as e:
                    self.logger.warning(f"행 데이터 처리 중 오류: {str(e)}")
                    continue

            if campaign_data:
                save_success = self.save_to_local(campaign_data, current_hour)
                if save_success:
                    self.logger.info(f"총 {len(campaign_data)}개의 캠페인 데이터를 수집 및 저장했습니다.")
                else:
                    self.logger.error("데이터 저장에 실패했습니다.")
            else:
                self.logger.warning("수집된 캠페인 데이터가 없습니다.")

            return campaign_data

        except Exception as e:
            self.logger.error(f"데이터 수집 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return {}

    def save_campaign_data(self, campaign_data):
        """이 메서드는 더 이상 사용되지 않습니다"""
        pass

    def save_full_table_data(self, full_table_data):
        """이 메서드는 더 이상 사용되지 않습니다"""
        pass

    def monitoring_task(self):
        """모니터링 작업 실행"""
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                now = datetime.now()
                #minutes_to_wait = 1
                minutes_to_wait = 60 - now.minute  # 다시 정각 실행으로 변경

                if minutes_to_wait <= 5:
                    self.logger.info(f"⚠ {minutes_to_wait}분 후 데이터 수집이 시작됩니다!")
                    time.sleep(minutes_to_wait * 60)
                else:
                    self.logger.info(f"다음 정각까지 {minutes_to_wait}분 대기...")
                    time.sleep((minutes_to_wait - 5) * 60)
                    self.logger.info("⚠ 5분 후 데이터 수집이 시작됩니다!")
                    time.sleep(300)

                if not self.is_monitoring:
                    break

                self.logger.info("데이터 수집을 시작합니다.")

                success = False
                for attempt in range(self.max_retries):
                    driver_initialized = False
                    try:
                        self.logger.info(f"[시도 {attempt + 1}/{self.max_retries}] 데이터 수집 시작")
                        
                        self.initialize_webdriver()
                        driver_initialized = True

                        if not self.login_to_coupang():
                            raise Exception("로그인 실패")

                        self.select_rows_per_page(20)
                        campaign_data = self.collect_data()
                        
                        if not campaign_data:
                            raise Exception("수집된 데이터가 없습니다")

                        self.logger.info("✅ 데이터 수집 및 저장 완료")
                        success = True
                        break

                    except Exception as e:
                        self.logger.error(f"❌ 수집 실패 (시도 {attempt + 1}): {str(e)}")
                        traceback.print_exc()
                        time.sleep(self.retry_interval)

                    finally:
                        if driver_initialized and hasattr(self, 'driver'):
                            try:
                                self.driver.quit()
                                self.logger.info("웹드라이버 종료 완료")
                            except Exception as e:
                                self.logger.error(f"웹드라이버 종료 중 오류: {str(e)}")

                if not success:
                    self.logger.error("❌ 모든 시도 실패")

            except Exception as e:
                self.logger.error(f"❗ 모니터링 작업 중 치명적 오류 발생: {str(e)}")
                traceback.print_exc()
            
            finally:
                # 다음 정각까지 대기
                time.sleep(60)  # 최소 1분 대기

    def start(self):
        """모니터링 시작"""
        self.logger.info("모니터링을 시작합니다.")
        self.monitoring_task()

    def stop(self):
        """모니터링 중지"""
        self.is_monitoring = False
        self.logger.info("모니터링을 중지합니다.")

if __name__ == "__main__":
    # 환경 변수에서 인증 정보 가져오기
    username = os.getenv("COUPANG_USERNAME", "alfm1991")
    password = os.getenv("COUPANG_PASSWORD", "$als$Ehdvkf29!")

    monitor = CoupangAdServerMonitor(username, password)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
        print("\n프로그램을 종료합니다.")
    except Exception as e:
        print(f"예기치 않은 오류 발생: {str(e)}")
        monitor.stop() 