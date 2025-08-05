#!/usr/bin/env python3
"""
Frontend Debug Testing Script
Uses Chrome DevTools Protocol to test yield curve functionality
"""

import json
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_chrome_with_devtools():
    """Setup Chrome with DevTools enabled"""
    chrome_options = Options()
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    # Don't add headless - we want to see the UI
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def test_yield_curves_tab(driver):
    """Test the Yield Curves tab functionality"""
    
    print("🔍 TESTING YIELD CURVES TAB")
    print("=" * 50)
    
    # Navigate to the app
    print("📍 Navigating to http://localhost:3501")
    driver.get("http://localhost:3501")
    
    # Wait for the app to load
    wait = WebDriverWait(driver, 10)
    
    try:
        # Click on Yield Curves tab
        print("📍 Looking for Yield Curves tab...")
        yield_curves_tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yield Curves')]"))
        )
        yield_curves_tab.click()
        print("✅ Clicked Yield Curves tab")
        
        # Wait for the component to load
        time.sleep(2)
        
        # Check for currency buttons
        print("📍 Checking currency selector buttons...")
        
        # Find G10 currency buttons
        g10_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NOK', 'SEK', 'NZD']
        g10_found = []
        
        for currency in g10_currencies:
            try:
                button = driver.find_element(By.XPATH, f"//button[text()='{currency}']")
                g10_found.append(currency)
                print(f"  ✅ Found G10 button: {currency}")
            except:
                print(f"  ❌ Missing G10 button: {currency}")
        
        # Find EM currency buttons
        em_currencies = ['DKK', 'ISK', 'PLN', 'CZK', 'HUF', 'CNH', 'KRW', 'SGD', 'THB', 'TWD', 'INR', 'PHP', 'HKD', 'MXN', 'TRY', 'ZAR', 'RUB']
        em_found = []
        
        for currency in em_currencies:
            try:
                button = driver.find_element(By.XPATH, f"//button[text()='{currency}']")
                em_found.append(currency)
                print(f"  ✅ Found EM button: {currency}")
            except:
                print(f"  ❌ Missing EM button: {currency}")
        
        total_found = len(g10_found) + len(em_found)
        print(f"\n📊 CURRENCY BUTTON SUMMARY:")
        print(f"   G10 Found: {len(g10_found)}/10 ({g10_found})")
        print(f"   EM Found: {len(em_found)}/17 ({em_found})")
        print(f"   Total Found: {total_found}/27")
        
        # Test clicking a currency button
        if g10_found:
            test_currency = g10_found[0]
            print(f"\n📍 Testing {test_currency} button click...")
            
            button = driver.find_element(By.XPATH, f"//button[text()='{test_currency}']")
            button.click()
            print(f"✅ Clicked {test_currency} button")
            
            # Wait for data loading
            time.sleep(3)
            
            # Check for chart SVG
            try:
                svg = driver.find_element(By.TAG_NAME, "svg")
                print("✅ Chart SVG found - curve rendered")
            except:
                print("❌ No chart SVG found")
        
        # Get console logs
        print("\n📍 Checking console logs...")
        logs = driver.get_log('browser')
        
        error_logs = [log for log in logs if log['level'] == 'SEVERE']
        warning_logs = [log for log in logs if log['level'] == 'WARNING']
        
        if error_logs:
            print(f"❌ Found {len(error_logs)} console errors:")
            for log in error_logs[-5:]:  # Show last 5
                print(f"   ERROR: {log['message']}")
        else:
            print("✅ No console errors")
            
        if warning_logs:
            print(f"⚠️  Found {len(warning_logs)} console warnings")
        
        return {
            'g10_found': len(g10_found),
            'em_found': len(em_found),
            'total_currencies': total_found,
            'errors': len(error_logs),
            'warnings': len(warning_logs)
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return None

def test_network_requests(driver):
    """Test Bloomberg API network requests"""
    
    print("\n🌐 TESTING NETWORK REQUESTS")
    print("=" * 50)
    
    # Enable network domain in DevTools
    driver.execute_cdp_cmd('Network.enable', {})
    
    # Clear network logs
    driver.execute_cdp_cmd('Network.clearBrowserCache', {})
    
    # Click EUR button to trigger API call
    try:
        eur_button = driver.find_element(By.XPATH, "//button[text()='EUR']")
        eur_button.click()
        print("✅ Clicked EUR button to trigger API call")
        
        # Wait for network request
        time.sleep(5)
        
        # Get network logs (this is tricky with Selenium, we'll check different way)
        print("📍 Checking if data loaded...")
        
        # Look for chart elements that indicate successful data load
        try:
            # Wait for chart to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            
            # Look for path elements (yield curve lines)
            paths = driver.find_elements(By.XPATH, "//svg//path[@stroke]")
            if paths:
                print(f"✅ Found {len(paths)} yield curve paths - data loaded successfully")
            else:
                print("❌ No yield curve paths found - data may not have loaded")
                
        except:
            print("❌ Chart did not appear - network request may have failed")
            
    except Exception as e:
        print(f"❌ Network test failed: {str(e)}")

def main():
    """Main test function"""
    
    print("🚀 FRONTEND DEBUG TESTING")
    print("=" * 70)
    print("Testing yield curve functionality with browser dev tools...")
    print()
    
    driver = None
    try:
        # Setup Chrome
        driver = setup_chrome_with_devtools()
        
        # Run tests
        ui_results = test_yield_curves_tab(driver)
        test_network_requests(driver)
        
        # Summary
        print("\n📋 TEST SUMMARY")
        print("=" * 50)
        if ui_results:
            print(f"✅ UI Test Results:")
            print(f"   - G10 Currencies: {ui_results['g10_found']}/10")
            print(f"   - EM Currencies: {ui_results['em_found']}/17") 
            print(f"   - Total Currencies: {ui_results['total_currencies']}/27")
            print(f"   - Console Errors: {ui_results['errors']}")
            print(f"   - Console Warnings: {ui_results['warnings']}")
            
            if ui_results['total_currencies'] >= 25:
                print("🎉 EXCELLENT: Nearly all currencies are rendering!")
            elif ui_results['total_currencies'] >= 20:
                print("👍 GOOD: Most currencies are rendering")
            else:
                print("⚠️  NEEDS WORK: Many currencies missing from UI")
        
        # Keep browser open for manual inspection
        print("\n🔍 Browser kept open for manual inspection...")
        print("Press Ctrl+C to close when done.")
        
        # Keep the browser open
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
            
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        print("Make sure Chrome is installed and dev server is running on localhost:3501")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()