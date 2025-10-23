import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    print("➡ [드라이버 설정 시작] setup_driver 호출")
    
    chrome_options = Options()
    
    # 기본 Chrome 옵션
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    # User Agent 설정
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # 자동화 감지 방지
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Chrome 바이너리 경로 설정
    chrome_bin = os.getenv("GOOGLE_BIN", "/usr/bin/google-chrome")
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
        print(f"✅ [Chrome 바이너리] {chrome_bin} 사용")
    else:
        print(f"⚠️ [Chrome 바이너리] {chrome_bin} 없음, 기본 경로 사용")
    
    try:
        # WebDriverManager를 우선 사용 (자동 호환성 관리)
        print("🔄 [WebDriver] WebDriverManager로 ChromeDriver 자동 설치...")
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지 스크립트 추가
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            }
        )
        
        print("✅ [드라이버 설정 완료] webdriver 생성 성공")
        return driver
        
    except Exception as e:
        print(f"❌ [WebDriverManager 실패] {str(e)}")
        
        # WebDriverManager 실패 시 수동 경로 시도
        try:
            print("🔄 [WebDriver] 수동 설치된 ChromeDriver 사용...")
            chromedriver_path = "/usr/local/bin/chromedriver"
            
            if os.path.exists(chromedriver_path):
                print(f"✅ [ChromeDriver] {chromedriver_path} 발견")
                service = Service(chromedriver_path)
            else:
                print(f"⚠️ [ChromeDriver] {chromedriver_path} 없음, 기본 경로 사용...")
                chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
                service = Service(chromedriver_path)
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ [드라이버 설정 완료] 수동 경로로 webdriver 생성 성공")
            return driver
        except Exception as e2:
            print(f"❌ [드라이버 설정 실패] 수동 경로도 실패: {str(e2)}")
            raise e2
