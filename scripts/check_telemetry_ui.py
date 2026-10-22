"""Verify the included synthetic adapter through the actual HTTP and browser path."""
from pathlib import Path
import subprocess
import sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    sender=subprocess.Popen([sys.executable,'-m','scripts.send_telemetry'],cwd=ROOT)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch();page=browser.new_page(viewport={'width':1600,'height':1200})
            page.goto('http://127.0.0.1:8000');page.wait_for_function("document.getElementById('status').textContent.includes('complete')")
            page.locator('#live').click()
            page.wait_for_function("document.getElementById('liveStatus').textContent.includes('simulated-adapter-demo')")
            page.wait_for_function("document.getElementById('livePreview').hidden === false")
            first=page.locator('#liveStatus').inner_text();page.wait_for_timeout(1000);second=page.locator('#liveStatus').inner_text()
            assert first!=second,'Telemetry timestamp failed to advance'
            page.locator('#livePreview').scroll_into_view_if_needed();page.screenshot(path=str(ROOT/'results'/'telemetry-dashboard.png'),full_page=True)
            browser.close()
        print('External sender -> validated HTTP ingestion -> advancing browser telemetry verified')
    finally:
        sender.terminate();sender.wait(timeout=10)

if __name__=='__main__':main()
